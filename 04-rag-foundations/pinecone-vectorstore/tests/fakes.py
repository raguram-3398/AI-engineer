"""In-memory stand-ins for Pinecone and the embedding model. No network."""

import hashlib
import math
import re
from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

from vectorstore.models import DIMENSION, METRIC

_WORD = re.compile(r"[a-z0-9$]+")


class HashEmbedder:
    """Deterministic bag-of-words vectors: shared words -> higher cosine."""

    def __init__(self, model_id: str = "fake/hash-bow") -> None:
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * DIMENSION
        for word in _WORD.findall(text.lower()):
            v[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMENSION] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


def _matches(metadata: Mapping[str, Any], flt: Mapping[str, Any] | None) -> bool:
    """The subset of Pinecone filter semantics this project uses."""
    for field, cond in (flt or {}).items():
        value = metadata.get(field)
        for op, target in cond.items():
            ok = {
                "$eq": lambda: value == target,
                "$gte": lambda: value is not None and value >= target,
                "$lte": lambda: value is not None and value <= target,
            }[op]()
            if not ok:
                return False
    return True


class FakeIndex:
    """Brute-force index. `lag_polls` stats calls report 0 before records show."""

    def __init__(self, lag_polls: int = 0, upsert_shortfall: int = 0) -> None:
        self.records: dict[str, dict[str, dict[str, Any]]] = {}
        self.lag_polls = lag_polls
        self.upsert_shortfall = upsert_shortfall
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.raise_on: dict[str, Exception] = {}

    def upsert(self, **kwargs: Any) -> Any:
        self.calls.append(("upsert", kwargs))
        if "upsert" in self.raise_on:
            raise self.raise_on["upsert"]
        ns = self.records.setdefault(kwargs["namespace"], {})
        for r in kwargs["vectors"]:
            ns[r["id"]] = r
        return SimpleNamespace(
            upserted_count=len(kwargs["vectors"]) - self.upsert_shortfall
        )

    def describe_index_stats(self, **kwargs: Any) -> Any:
        self.calls.append(("stats", kwargs))
        if self.lag_polls > 0:
            self.lag_polls -= 1
            return SimpleNamespace(namespaces={})
        return SimpleNamespace(
            namespaces={
                ns: SimpleNamespace(vector_count=len(recs))
                for ns, recs in self.records.items()
            }
        )

    def query(self, **kwargs: Any) -> Any:
        self.calls.append(("query", kwargs))
        if "query" in self.raise_on:
            raise self.raise_on["query"]
        q = kwargs["vector"]
        hits = [
            SimpleNamespace(
                id=r["id"],
                score=sum(a * b for a, b in zip(q, r["values"])),
                # Pinecone returns numeric metadata as floats
                metadata={
                    k: float(v) if isinstance(v, int) else v
                    for k, v in r["metadata"].items()
                },
            )
            for r in self.records.get(kwargs["namespace"], {}).values()
            if _matches(r["metadata"], kwargs.get("filter"))
        ]
        hits.sort(key=lambda h: h.score, reverse=True)
        return SimpleNamespace(matches=hits[: kwargs["top_k"]])


class FakePinecone:
    """Control plane: has_index / describe_index / create_index / index."""

    def __init__(self, existing: dict[str, tuple[int, str]] | None = None) -> None:
        self.existing = dict(existing or {})
        self.created: list[dict[str, Any]] = []
        self.raise_on: dict[str, Exception] = {}
        self.index_client = FakeIndex()

    def has_index(self, name: str) -> bool:
        if "has_index" in self.raise_on:
            raise self.raise_on["has_index"]
        return name in self.existing

    def describe_index(self, name: str) -> Any:
        dimension, metric = self.existing[name]
        return SimpleNamespace(dimension=dimension, metric=metric)

    def create_index(self, **kwargs: Any) -> Any:
        self.created.append(kwargs)
        self.existing[kwargs["name"]] = (kwargs["dimension"], kwargs["metric"])
        return SimpleNamespace(name=kwargs["name"])

    def index(self, name: str) -> FakeIndex:
        return self.index_client


DEFAULT_SHAPE: tuple[int, str] = (DIMENSION, METRIC)
