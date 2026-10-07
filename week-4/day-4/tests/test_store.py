import pytest
from fakes import DEFAULT_SHAPE, FakeIndex, FakePinecone
from pinecone import NotFoundError, PineconeTimeoutError

from vectorstore.models import (
    DIMENSION,
    INDEX_READY_TIMEOUT_S,
    REQUEST_TIMEOUT_S,
    Chunk,
    EmbeddingModelMismatchError,
    VectorStoreError,
    VectorStoreTimeoutError,
)
from vectorstore.records import to_record
from vectorstore.store import ensure_index, search, upsert_records, wait_until_count


def _records(n: int) -> list[dict[str, object]]:
    return [
        to_record(
            Chunk(f"id{i}", f"text {i}", "s", i, 20260101),
            [1.0] + [0.0] * (DIMENSION - 1),
            "m",
        )
        for i in range(n)
    ]


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_ensure_index_creates_serverless_index_with_timeout() -> None:
    pc = FakePinecone()
    ensure_index(pc, "idx")  # type: ignore[arg-type]
    [created] = pc.created
    assert (created["dimension"], created["metric"]) == DEFAULT_SHAPE
    assert created["timeout"] == INDEX_READY_TIMEOUT_S


def test_ensure_index_reuses_matching_index() -> None:
    pc = FakePinecone(existing={"idx": DEFAULT_SHAPE})
    ensure_index(pc, "idx")  # type: ignore[arg-type]
    assert pc.created == []


def test_ensure_index_rejects_index_built_for_another_model() -> None:
    pc = FakePinecone(existing={"idx": (768, "cosine")})
    with pytest.raises(EmbeddingModelMismatchError, match="768"):
        ensure_index(pc, "idx")  # type: ignore[arg-type]


def test_ensure_index_translates_pinecone_timeout() -> None:
    pc = FakePinecone()
    pc.raise_on["has_index"] = PineconeTimeoutError("slow")
    with pytest.raises(VectorStoreTimeoutError):
        ensure_index(pc, "idx")  # type: ignore[arg-type]


def test_upsert_passes_timeout_and_returns_count() -> None:
    index = FakeIndex()
    assert upsert_records(index, _records(3), "ns") == 3
    [(_, kwargs)] = index.calls
    assert kwargs["timeout"] == REQUEST_TIMEOUT_S


def test_upsert_short_count_is_an_error() -> None:
    with pytest.raises(VectorStoreError, match="2 of 3"):
        upsert_records(FakeIndex(upsert_shortfall=1), _records(3), "ns")


def test_upsert_translates_api_error() -> None:
    index = FakeIndex()
    index.raise_on["upsert"] = NotFoundError("no such index")
    with pytest.raises(VectorStoreError, match="upsert failed"):
        upsert_records(index, _records(1), "ns")


def test_wait_until_count_survives_eventual_consistency_lag() -> None:
    index = FakeIndex(lag_polls=3)
    upsert_records(index, _records(2), "ns")
    clock = FakeClock()
    wait_until_count(index, "ns", 2, 10.0, 1.0, clock=clock, sleep=clock.sleep)
    assert clock.now == 3.0  # three empty polls, then visible


def test_wait_until_count_times_out() -> None:
    index = FakeIndex(lag_polls=100)
    upsert_records(index, _records(2), "ns")
    clock = FakeClock()
    with pytest.raises(VectorStoreTimeoutError, match="0/2"):
        wait_until_count(index, "ns", 2, 5.0, 1.0, clock=clock, sleep=clock.sleep)


def test_wait_until_count_fails_fast_on_stale_records() -> None:
    index = FakeIndex()
    upsert_records(index, _records(5), "ns")
    with pytest.raises(VectorStoreError, match="stale"):
        wait_until_count(index, "ns", 3, 5.0, 1.0)


def test_search_sends_filter_metadata_flag_and_timeout() -> None:
    index = FakeIndex()
    upsert_records(index, _records(2), "ns")
    flt = {"source": {"$eq": "s"}}
    matches = search(index, [1.0] + [0.0] * (DIMENSION - 1), 1, flt, "ns")
    _, kwargs = index.calls[-1]
    assert kwargs["filter"] == flt
    assert kwargs["include_metadata"] is True
    assert kwargs["timeout"] == REQUEST_TIMEOUT_S
    assert len(matches) == 1


def test_search_filter_with_no_matches_returns_empty() -> None:
    index = FakeIndex()
    upsert_records(index, _records(2), "ns")
    assert search(index, [1.0] * DIMENSION, 3, {"source": {"$eq": "nope"}}, "ns") == []


def test_search_translates_timeout() -> None:
    index = FakeIndex()
    index.raise_on["query"] = PineconeTimeoutError("slow")
    with pytest.raises(VectorStoreTimeoutError):
        search(index, [0.0] * DIMENSION, 3, None, "ns")


def test_search_rejects_bad_top_k() -> None:
    with pytest.raises(ValueError):
        search(FakeIndex(), [0.0] * DIMENSION, 0, None, "ns")
