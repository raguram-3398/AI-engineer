import pytest

from vectorstore.models import (
    DIMENSION,
    Chunk,
    EmbeddingModelMismatchError,
    Match,
    VectorStoreError,
)
from vectorstore.records import (
    build_filter,
    check_model,
    chunk_id,
    parse_matches,
    to_record,
)

CHUNK = Chunk(
    id="doc@20260301#p2", text="stipend $750", source="doc", page=2, date=20260301
)


def _match(model: str) -> Match:
    return Match("a", 0.9, "t", "doc", 1, 20260301, model)


def test_chunk_id_is_deterministic_and_version_aware() -> None:
    assert chunk_id("doc", 20260301, 2) == chunk_id("doc", 20260301, 2)
    assert chunk_id("doc", 20260301, 2) != chunk_id("doc", 20240115, 2)


def test_to_record_carries_model_and_all_metadata() -> None:
    record = to_record(CHUNK, [0.0] * DIMENSION, "BAAI/bge-small-en-v1.5")
    assert record["id"] == CHUNK.id
    assert record["metadata"] == {
        "text": "stipend $750",
        "source": "doc",
        "page": 2,
        "date": 20260301,
        "embedding_model": "BAAI/bge-small-en-v1.5",
    }


def test_to_record_rejects_wrong_dimension() -> None:
    with pytest.raises(ValueError, match="384"):
        to_record(CHUNK, [0.0] * 768, "m")


def test_to_record_rejects_non_yyyymmdd_date() -> None:
    bad = Chunk(id="x", text="t", source="s", page=1, date=2026)
    with pytest.raises(ValueError, match="YYYYMMDD"):
        to_record(bad, [0.0] * DIMENSION, "m")


def test_build_filter_none_when_unconstrained() -> None:
    assert build_filter() is None


def test_build_filter_source_only() -> None:
    assert build_filter(source="travel-policy") == {"source": {"$eq": "travel-policy"}}


def test_build_filter_combines_source_and_inclusive_date_range() -> None:
    assert build_filter("exp", 20260101, 20261231) == {
        "source": {"$eq": "exp"},
        "date": {"$gte": 20260101, "$lte": 20261231},
    }


def test_build_filter_rejects_inverted_range() -> None:
    with pytest.raises(ValueError, match="after"):
        build_filter(date_from=20261231, date_to=20260101)


def test_build_filter_rejects_string_date() -> None:
    with pytest.raises(ValueError):
        build_filter(date_from="2026-01-01")  # type: ignore[arg-type]


def test_parse_matches_converts_float_numbers_back_to_int() -> None:
    raw = [
        {
            "id": "a",
            "score": 0.8,
            "metadata": {
                "text": "t",
                "source": "s",
                "page": 3.0,
                "date": 20260301.0,
                "embedding_model": "m",
            },
        }
    ]
    [m] = parse_matches(raw)
    assert (m.page, m.date) == (3, 20260301)


def test_parse_matches_rejects_missing_metadata() -> None:
    with pytest.raises(VectorStoreError, match="embedding_model"):
        parse_matches(
            [
                {
                    "id": "a",
                    "score": 0.5,
                    "metadata": {"text": "t", "source": "s", "page": 1, "date": 1},
                }
            ]
        )


def test_check_model_passes_and_fails() -> None:
    check_model([_match("m")], "m")
    check_model([], "m")
    with pytest.raises(EmbeddingModelMismatchError, match="minilm"):
        check_model([_match("m"), _match("minilm")], "m")
