"""Pinecone I/O edge: create/validate the index, upsert, wait, search.

Every Pinecone exception is translated into this package's hierarchy here,
so nothing above this module imports from pinecone.
"""

import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

from pinecone import Pinecone, PineconeError, PineconeTimeoutError, ServerlessSpec

from vectorstore.models import (
    CLOUD,
    DIMENSION,
    INDEX_READY_TIMEOUT_S,
    METRIC,
    REGION,
    REQUEST_TIMEOUT_S,
    UPSERT_BATCH_SIZE,
    EmbeddingModelMismatchError,
    Match,
    VectorStoreError,
    VectorStoreTimeoutError,
)
from vectorstore.records import parse_matches


class IndexClient(Protocol):
    """The three data-plane calls this module uses (a pinecone.Index fits)."""

    def upsert(self, **kwargs: Any) -> Any: ...

    def query(self, **kwargs: Any) -> Any: ...

    def describe_index_stats(self, **kwargs: Any) -> Any: ...


def _translate(action: str, e: PineconeError) -> VectorStoreError:
    """Map a Pinecone exception onto our hierarchy, keeping the message."""
    if isinstance(e, PineconeTimeoutError):
        return VectorStoreTimeoutError(f"{action} timed out: {e}")
    return VectorStoreError(f"{action} failed: {e}")


def ensure_index(pc: Pinecone, name: str) -> IndexClient:
    """Return a client for `name`, creating the serverless index if missing.

    An existing index with the wrong dimension or metric raises
    EmbeddingModelMismatchError: it was built for a different model.
    """
    try:
        if pc.has_index(name):
            desc = pc.describe_index(name)
            if desc.dimension != DIMENSION or desc.metric != METRIC:
                raise EmbeddingModelMismatchError(
                    f"index {name!r} is {desc.dimension}-d/{desc.metric}, "
                    f"expected {DIMENSION}-d/{METRIC}"
                )
        else:
            pc.create_index(
                name=name,
                dimension=DIMENSION,
                metric=METRIC,
                spec=ServerlessSpec(cloud=CLOUD, region=REGION),
                timeout=INDEX_READY_TIMEOUT_S,
            )
        return pc.index(name=name)
    except PineconeError as e:
        raise _translate(f"ensure_index({name!r})", e) from e


def upsert_records(
    index: IndexClient, records: Sequence[Mapping[str, object]], namespace: str
) -> int:
    """Upsert in batches; return how many records Pinecone accepted.

    Batched upsert does not raise when one batch fails, it reports it,
    so a short count is turned into an error here.
    """
    if not records:
        return 0
    try:
        response = index.upsert(
            vectors=list(records),
            namespace=namespace,
            batch_size=UPSERT_BATCH_SIZE,
            show_progress=False,
            timeout=REQUEST_TIMEOUT_S,
        )
    except PineconeError as e:
        raise _translate("upsert", e) from e
    count = int(response.upserted_count)
    if count != len(records):
        raise VectorStoreError(f"upserted {count} of {len(records)} records")
    return count


def namespace_count(index: IndexClient, namespace: str) -> int:
    """Records currently visible in `namespace` (0 if it doesn't exist yet)."""
    try:
        stats = index.describe_index_stats(timeout=REQUEST_TIMEOUT_S)
    except PineconeError as e:
        raise _translate("describe_index_stats", e) from e
    summary = stats.namespaces.get(namespace)
    return int(summary.vector_count) if summary is not None else 0


def wait_until_count(
    index: IndexClient,
    namespace: str,
    expected: int,
    timeout_s: float,
    poll_s: float,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Block until `namespace` holds exactly `expected` records.

    Pinecone is eventually consistent: upsert returns before records are
    searchable. Querying too early returns partial results with no error.
    More records than expected means stale records from an earlier run,
    which waiting will never fix, so that raises immediately.
    """
    deadline = clock() + timeout_s
    while True:
        count = namespace_count(index, namespace)
        if count == expected:
            return
        if count > expected:
            raise VectorStoreError(
                f"namespace {namespace!r} has {count} records, expected {expected}: "
                "stale records from an earlier run; delete the namespace and re-ingest"
            )
        if clock() >= deadline:
            raise VectorStoreTimeoutError(
                f"only {count}/{expected} records visible after {timeout_s}s"
            )
        sleep(poll_s)


def search(
    index: IndexClient,
    vector: Sequence[float],
    top_k: int,
    flt: Mapping[str, object] | None,
    namespace: str,
) -> list[Match]:
    """Nearest neighbours of `vector`, restricted by `flt` (None = no filter)."""
    if top_k < 1:
        raise ValueError(f"top_k must be >= 1, got {top_k}")
    try:
        response = index.query(
            vector=list(vector),
            top_k=top_k,
            filter=dict(flt) if flt else None,
            namespace=namespace,
            include_metadata=True,
            timeout=REQUEST_TIMEOUT_S,
        )
    except PineconeError as e:
        raise _translate("query", e) from e
    raw = [
        {"id": m.id, "score": m.score, "metadata": m.metadata} for m in response.matches
    ]
    return parse_matches(raw)
