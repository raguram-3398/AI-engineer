"""Ingest the policy corpus into Pinecone, then compare unfiltered vs filtered hit@1.

Run from week-4/day-4:  PYTHONPATH=src python -m vectorstore.main
Needs PINECONE_API_KEY in the environment or a .env file in a parent folder.
"""

import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from vectorstore.embedder import BgeEmbedder, Embedder
from vectorstore.models import (
    FRESHNESS_POLL_S,
    FRESHNESS_TIMEOUT_S,
    INDEX_NAME,
    MODEL_ID,
    NAMESPACE,
    REQUEST_TIMEOUT_S,
    TOP_K,
    Chunk,
    EvalQuery,
    VectorStoreError,
)
from vectorstore.records import build_filter, check_model, chunk_id, to_record
from vectorstore.store import (
    IndexClient,
    ensure_index,
    search,
    upsert_records,
    wait_until_count,
)

DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"
CORPUS_PATH: Path = DATA_DIR / "corpus.jsonl"
QUERIES_PATH: Path = DATA_DIR / "queries.json"


@dataclass(frozen=True)
class QueryResult:
    """Top-1 id for one query, without and with its filter."""

    query: EvalQuery
    unfiltered_top1: str | None
    filtered_top1: str | None


def load_chunks(path: Path) -> list[Chunk]:
    """Read corpus.jsonl; ids are derived, never stored, so they stay stable."""
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
        return [
            Chunk(
                id=chunk_id(r["source"], r["date"], r["page"]),
                text=r["text"],
                source=r["source"],
                page=r["page"],
                date=r["date"],
            )
            for r in rows
        ]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        raise VectorStoreError(f"bad corpus file {path}: {e}") from e


def load_queries(path: Path) -> list[EvalQuery]:
    """Read queries.json; missing filter fields mean 'no constraint'."""
    try:
        rows = json.loads(path.read_text())
        return [
            EvalQuery(
                id=r["id"],
                kind=r["kind"],
                text=r["text"],
                expected_id=r["expected_id"],
                source=r.get("source"),
                date_from=r.get("date_from"),
                date_to=r.get("date_to"),
            )
            for r in rows
        ]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        raise VectorStoreError(f"bad queries file {path}: {e}") from e


def ingest(
    index: IndexClient, embedder: Embedder, chunks: Sequence[Chunk], namespace: str
) -> int:
    """Embed, upsert, and wait until every record is searchable."""
    vectors = embedder.embed_documents([c.text for c in chunks])
    records = [to_record(c, v, embedder.model_id) for c, v in zip(chunks, vectors)]
    count = upsert_records(index, records, namespace)
    wait_until_count(index, namespace, count, FRESHNESS_TIMEOUT_S, FRESHNESS_POLL_S)
    return count


def evaluate(
    index: IndexClient,
    embedder: Embedder,
    queries: Sequence[EvalQuery],
    namespace: str,
) -> list[QueryResult]:
    """Run each query twice (no filter, its filter); keep the top-1 id of each."""
    results: list[QueryResult] = []
    for q in queries:
        vector = embedder.embed_query(q.text)
        flt = build_filter(q.source, q.date_from, q.date_to)
        plain = search(index, vector, TOP_K, None, namespace)
        filtered = search(index, vector, TOP_K, flt, namespace)
        check_model([*plain, *filtered], embedder.model_id)
        results.append(
            QueryResult(
                query=q,
                unfiltered_top1=plain[0].id if plain else None,
                filtered_top1=filtered[0].id if filtered else None,
            )
        )
    return results


def hit_at_1(results: Sequence[QueryResult], filtered: bool) -> float:
    """Fraction of queries whose top-1 is the expected chunk."""
    if not results:
        return 0.0
    hits = sum(
        (r.filtered_top1 if filtered else r.unfiltered_top1) == r.query.expected_id
        for r in results
    )
    return hits / len(results)


def format_report(results: Sequence[QueryResult]) -> str:
    """Per-query table, then hit@1 by query kind and overall."""
    lines = [f"{'query':<5} {'kind':<8} {'unfiltered':<10} {'filtered':<8}  expected"]
    for r in results:
        plain_ok = "ok" if r.unfiltered_top1 == r.query.expected_id else "MISS"
        filt_ok = "ok" if r.filtered_top1 == r.query.expected_id else "MISS"
        lines.append(
            f"{r.query.id:<5} {r.query.kind:<8} {plain_ok:<10} {filt_ok:<8}  "
            f"{r.query.expected_id}"
        )
        if plain_ok == "MISS":
            lines.append(f"{'':<15}unfiltered got: {r.unfiltered_top1}")
        if filt_ok == "MISS":
            lines.append(f"{'':<15}filtered got:   {r.filtered_top1}")
    lines.append("")
    lines.append(
        f"{'kind':<8} {'n':>3}  {'hit@1 unfiltered':>16}  {'hit@1 filtered':>14}"
    )
    kinds = sorted({r.query.kind for r in results})
    for kind in [*kinds, "ALL"]:
        group = [r for r in results if kind in ("ALL", r.query.kind)]
        lines.append(
            f"{kind:<8} {len(group):>3}  {hit_at_1(group, False):>16.2f}  "
            f"{hit_at_1(group, True):>14.2f}"
        )
    return "\n".join(lines)


def main() -> int:
    """Wire the real Pinecone client and BGE model; return a process exit code."""
    from dotenv import find_dotenv, load_dotenv
    from pinecone import Pinecone

    load_dotenv(find_dotenv(usecwd=True))
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY is not set (env or .env)", file=sys.stderr)
        return 1
    try:
        chunks = load_chunks(CORPUS_PATH)
        queries = load_queries(QUERIES_PATH)
        embedder = BgeEmbedder(MODEL_ID)
        pc = Pinecone(api_key=api_key, timeout=REQUEST_TIMEOUT_S)
        index = ensure_index(pc, INDEX_NAME)
        count = ingest(index, embedder, chunks, NAMESPACE)
        print(
            f"index={INDEX_NAME} namespace={NAMESPACE} records={count} model={MODEL_ID}"
        )
        print(format_report(evaluate(index, embedder, queries, NAMESPACE)))
    except VectorStoreError as e:
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
