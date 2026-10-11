"""Retrieval metrics on hand-computed cases, chunk-to-page dedupe, the fixed sample,
abstain accuracy and the regression gate."""

import json
import math

import pytest

from multimodal_rag.config import (
    ABSTAIN_TEXT,
    GATE_THRESHOLDS,
    SAMPLE_PATH,
    SAMPLE_SIZE,
)
from multimodal_rag.contracts import Answer, Chunk, Hit
from multimodal_rag.evaluate import (
    Result,
    abstain_scores,
    gate,
    ndcg_at_k,
    ranked_pages,
    recall_at_k,
)


def _hit(doc: str, page: int, n: int = 0) -> Hit:
    return Hit(Chunk(f"{doc}-{page}-{n}", doc, page, "t", 1, "text"), 0.5)


def test_chunks_of_one_page_count_once_in_rank_order() -> None:
    hits = [_hit("book", 3, 0), _hit("book", 3, 1), _hit("deck", 0), _hit("book", 3, 2)]
    assert ranked_pages(hits) == [("book", 3), ("deck", 0)]


def test_ranked_pages_stops_at_k_distinct_pages() -> None:
    hits = [_hit("d", p, n) for p in range(6) for n in range(3)]
    assert ranked_pages(hits, k=4) == [("d", 0), ("d", 1), ("d", 2), ("d", 3)]


def test_page_0_is_a_real_page() -> None:
    """0-indexed pages: (doc, 0) must match gold page 0, not be skipped as falsy."""
    gold = {("d", 0): 2}
    assert recall_at_k([("d", 0)], gold) == 1.0
    assert ndcg_at_k([("d", 0)], gold) == 1.0


def test_recall_and_ndcg_by_hand() -> None:
    gold = {("d", 1): 2, ("d", 5): 1, ("d", 9): 1}
    ranked = [("d", 5), ("d", 0), ("d", 1)]
    assert recall_at_k(ranked, gold) == pytest.approx(2 / 3)
    dcg = 1 / math.log2(2) + 2 / math.log2(4)
    idcg = 2 / math.log2(2) + 1 / math.log2(3) + 1 / math.log2(4)
    assert ndcg_at_k(ranked, gold) == pytest.approx(dcg / idcg)


def test_metrics_can_fail() -> None:
    gold = {("d", 1): 2}
    assert recall_at_k([("d", 2), ("e", 1)], gold) == 0.0
    assert ndcg_at_k([("d", 2), ("e", 1)], gold) == 0.0


def test_recall_respects_k() -> None:
    gold = {("d", 10): 1}
    ranked = [("d", p) for p in range(11)]
    assert recall_at_k(ranked, gold, k=10) == 0.0


@pytest.mark.skipif(not SAMPLE_PATH.is_file(), reason="run evaluate first")
def test_committed_sample_is_fixed_size_and_unique() -> None:
    sample = json.loads(SAMPLE_PATH.read_text())
    assert len(set(sample["answerable"])) == len(sample["answerable"]) == SAMPLE_SIZE
    assert len(set(sample["unanswerable"])) == 20


def test_existing_sample_is_never_rebuilt(tmp_path, monkeypatch) -> None:
    """Once written, make_sample returns the file as is, whatever the queries."""
    from multimodal_rag import evaluate

    path = tmp_path / "sample.json"
    path.write_text(json.dumps({"seed": 1, "answerable": [7], "unanswerable": []}))
    monkeypatch.setattr(evaluate, "SAMPLE_PATH", path)
    assert evaluate.make_sample(queries=None)["answerable"] == [7]


def _result(reference: str | None, abstained: bool, refused: bool = False) -> Result:
    text = ABSTAIN_TEXT if abstained else "An answer."
    answer = Answer(text, [], abstained, refused, 0.0, 0.0)
    return Result("q", "question?", reference, [], answer)


def test_abstain_scores_both_ways() -> None:
    """A false abstain on an answerable query counts against answer_answerable;
    an answered unanswerable query counts against abstain_unanswerable."""
    results = [
        _result("ref", abstained=False),
        _result("ref", abstained=True),  # false abstain
        _result(None, abstained=True),
        _result(None, abstained=True),
        _result(None, abstained=False),  # answered a trap
    ]
    assert abstain_scores(results) == {
        "abstain_unanswerable": pytest.approx(2 / 3),
        "answer_answerable": 0.5,
    }


def test_refusal_counts_against_both_abstain_scores() -> None:
    results = [
        _result("ref", abstained=False),
        _result("ref", abstained=False, refused=True),
        _result(None, abstained=True),
        _result(None, abstained=False, refused=True),
    ]
    assert abstain_scores(results) == {
        "abstain_unanswerable": 0.5,
        "answer_answerable": 0.5,
    }


BASE = {m: 0.8 for m in GATE_THRESHOLDS}


def test_gate_passes_unchanged_and_small_drops() -> None:
    assert gate(BASE, BASE) == []
    within = {**BASE, "faithfulness": 0.8 - GATE_THRESHOLDS["faithfulness"]}
    assert gate(within, BASE) == []


def test_gate_fails_on_drop_beyond_threshold() -> None:
    worse = {
        **BASE,
        "answer_relevancy": 0.8 - GATE_THRESHOLDS["answer_relevancy"] - 0.01,
    }
    assert gate(worse, BASE) == ["answer_relevancy"]


def test_gate_fails_on_any_abstain_drop_with_zero_threshold() -> None:
    worse = {**BASE, "abstain_unanswerable": 0.8 - 1 / 20}
    assert gate(worse, BASE, {**GATE_THRESHOLDS, "abstain_unanswerable": 0.0}) == [
        "abstain_unanswerable"
    ]


def test_gate_ignores_improvements_and_fails_on_nan() -> None:
    better = {m: 0.9 for m in BASE}
    assert gate(better, BASE) == []
    assert gate({**BASE, "faithfulness": float("nan")}, BASE) == ["faithfulness"]
