from collections import defaultdict

import pytest
from fakes import FakeIndex, HashEmbedder

from vectorstore.main import (
    CORPUS_PATH,
    QUERIES_PATH,
    evaluate,
    hit_at_1,
    ingest,
    load_chunks,
    load_queries,
)
from vectorstore.models import EmbeddingModelMismatchError
from vectorstore.records import build_filter

CHUNKS = load_chunks(CORPUS_PATH)
QUERIES = load_queries(QUERIES_PATH)


def test_data_ids_unique_and_every_expected_id_exists() -> None:
    ids = [c.id for c in CHUNKS]
    assert len(ids) == len(set(ids))
    assert {q.expected_id for q in QUERIES} <= set(ids)


def test_every_query_filter_is_valid_and_admits_its_answer() -> None:
    by_id = {c.id: c for c in CHUNKS}
    for q in QUERIES:
        build_filter(q.source, q.date_from, q.date_to)  # raises if malformed
        answer = by_id[q.expected_id]
        assert q.source in (None, answer.source), q.id
        assert q.date_from is None or answer.date >= q.date_from, q.id
        assert q.date_to is None or answer.date <= q.date_to, q.id


def test_version_queries_come_in_same_text_pairs_so_unfiltered_can_fail() -> None:
    """Same text -> same unfiltered top-1 -> at most half of each pair can hit."""
    groups: dict[str, set[str]] = defaultdict(set)
    for q in QUERIES:
        if q.kind == "version":
            groups[q.text].add(q.expected_id)
    assert groups and all(len(expected) == 2 for expected in groups.values())


def test_end_to_end_filters_beat_no_filter_on_versions() -> None:
    index, emb = FakeIndex(), HashEmbedder()
    assert ingest(index, emb, CHUNKS, "ns") == len(CHUNKS)
    results = evaluate(index, emb, QUERIES, "ns")
    versions = [r for r in results if r.query.kind == "version"]
    assert hit_at_1(versions, filtered=False) <= 0.5
    assert hit_at_1(versions, filtered=True) > hit_at_1(versions, filtered=False)


def test_evaluate_refuses_vectors_from_another_model() -> None:
    index = FakeIndex()
    ingest(index, HashEmbedder("old/minilm"), CHUNKS, "ns")
    with pytest.raises(EmbeddingModelMismatchError, match="old/minilm"):
        evaluate(index, HashEmbedder("BAAI/bge-small-en-v1.5"), QUERIES[:1], "ns")
