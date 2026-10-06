"""Measurement logic against fakes: correctness, prefix asymmetry, and that the
shipped eval is hard enough to fail."""

from pathlib import Path

import pytest
from fakes import FakeEmbedder, RecordingEmbedder, UnnormalizedEmbedder

from embeddings.data_io import load_passages, load_queries, load_triplets
from embeddings.evaluate import (
    evaluate_retrieval,
    score_triplets,
    summarize_triplets,
    unrelated_floor,
    verify_manual_cosine,
)
from embeddings.models import (
    COSINE_TOLERANCE,
    PASSAGES_FILE,
    QUERIES_FILE,
    TRIPLETS_FILE,
    Passage,
    RetrievalQuery,
    Triplet,
    TripletResult,
)

PREFIX: str = "Represent this sentence for searching relevant passages: "
BAG_OF_WORDS_CEILING: float = 0.5  # a meaning-blind model must not pass more than this


def _t(category: str = "negation") -> Triplet:
    return Triplet(anchor="a", positive="p", negative="n", category=category)


# --- verify_manual_cosine ----------------------------------------------------


def test_manual_cosine_agrees_for_unit_vectors(fake_embedder: FakeEmbedder) -> None:
    deviation = verify_manual_cosine(fake_embedder, ["red apple", "green apple", "x"])
    assert deviation <= COSINE_TOLERANCE


def test_manual_cosine_detects_unnormalized_embedder() -> None:
    """If embed() breaks the unit-norm contract, dot != cosine and this must say so."""
    deviation = verify_manual_cosine(UnnormalizedEmbedder(), ["red apple", "pear"])
    assert deviation > COSINE_TOLERANCE


# --- triplets ----------------------------------------------------------------


def test_triplet_with_shared_words_passes(fake_embedder: FakeEmbedder) -> None:
    trip = Triplet(
        anchor="the cat sat on the mat",
        positive="the cat sat on a rug",
        negative="stock prices rose sharply",
        category="paraphrase_no_overlap",
    )
    [result] = score_triplets(fake_embedder, [trip])
    assert result.passed and result.margin > 0


def test_role_reversal_ties_and_tie_counts_as_fail(fake_embedder: FakeEmbedder) -> None:
    """Same words, different order: a bag-of-words model scores the negative 1.0."""
    trip = Triplet(
        anchor="the vendor sued the client",
        positive="the supplier took the customer to court",
        negative="the client sued the vendor",
        category="role_reversal",
    )
    [result] = score_triplets(fake_embedder, [trip])
    assert result.neg_score == pytest.approx(1.0, abs=1e-6)
    assert not result.passed


def test_score_triplets_batches_into_one_call() -> None:
    rec = RecordingEmbedder()
    score_triplets(rec, [_t(), _t()])
    assert len(rec.calls) == 1 and len(rec.calls[0]) == 6


def test_summarize_pass_rates_and_margin() -> None:
    results = [
        TripletResult(_t("negation"), pos_score=0.9, neg_score=0.8),  # pass
        TripletResult(_t("negation"), pos_score=0.7, neg_score=0.7),  # tie -> fail
        TripletResult(_t("numbers"), pos_score=0.5, neg_score=0.9),  # fail
    ]
    s = summarize_triplets("m", results, floor=0.3)
    assert s.pass_rate == pytest.approx(1 / 3)
    assert s.by_category == {"negation": 0.5, "numbers": 0.0}
    assert s.mean_margin == pytest.approx((0.1 + 0.0 - 0.4) / 3)
    assert s.unrelated_floor == 0.3


def test_summarize_rejects_empty() -> None:
    with pytest.raises(ValueError):
        summarize_triplets("m", [], floor=0.0)


def test_unrelated_floor_excludes_self_similarity(fake_embedder: FakeEmbedder) -> None:
    """Diagonal entries are 1.0; including them would inflate the floor."""
    floor = unrelated_floor(fake_embedder, ["alpha beta", "gamma delta"])
    assert floor == pytest.approx(0.0, abs=1e-6)


def test_unrelated_floor_needs_two_texts(fake_embedder: FakeEmbedder) -> None:
    with pytest.raises(ValueError):
        unrelated_floor(fake_embedder, ["only one"])


# --- retrieval ---------------------------------------------------------------

PASSAGES = [
    Passage("pw", "reset your password in the portal"),
    Passage("food", "meals are reimbursed up to sixty dollars"),
    Passage("trip", "book flights through the travel portal"),
]


def test_retrieval_ranks_and_metrics(fake_embedder: FakeEmbedder) -> None:
    queries = [
        RetrievalQuery("how do I reset my password", "pw"),  # rank 1
        RetrievalQuery("travel portal for meals", "food"),  # lexically pulled to trip
    ]
    r = evaluate_retrieval(fake_embedder, PASSAGES, queries, query_prefix="", k=1)
    assert r.ranks[0] == 1
    assert r.ranks[1] > 1
    assert r.hit_at_1 == 0.5
    assert r.mrr == pytest.approx((1 + 1 / r.ranks[1]) / 2)
    assert r.prefix_used is False


def test_prefix_goes_on_queries_only() -> None:
    """The edge case that matters today: BGE's instruction must never touch passages."""
    rec = RecordingEmbedder()
    queries = [RetrievalQuery("reset password", "pw")]
    result = evaluate_retrieval(rec, PASSAGES, queries, query_prefix=PREFIX)
    passage_batch, query_batch = rec.calls
    assert passage_batch == [p.text for p in PASSAGES]
    assert not any(text.startswith(PREFIX) for text in passage_batch)
    assert all(text.startswith(PREFIX) for text in query_batch)
    assert result.prefix_used is True
    assert queries[0].question == "reset password"  # input not mutated


def test_retrieval_rejects_unknown_expected_id(fake_embedder: FakeEmbedder) -> None:
    with pytest.raises(ValueError, match="do not exist"):
        evaluate_retrieval(
            fake_embedder, PASSAGES, [RetrievalQuery("q", "ghost")], query_prefix=""
        )


def test_retrieval_rejects_bad_k(fake_embedder: FakeEmbedder) -> None:
    with pytest.raises(ValueError):
        evaluate_retrieval(
            fake_embedder, PASSAGES, [RetrievalQuery("q", "pw")], query_prefix="", k=0
        )


# --- the eval must be able to fail -------------------------------------------


def test_shipped_triplets_defeat_bag_of_words(
    fake_embedder: FakeEmbedder, data_dir: Path
) -> None:
    """If a meaning-blind model passed most triplets, the suite would be too easy."""
    triplets = load_triplets(data_dir / TRIPLETS_FILE)
    s = summarize_triplets("fake", score_triplets(fake_embedder, triplets), floor=0.0)
    assert s.pass_rate <= BAG_OF_WORDS_CEILING
    assert s.by_category["role_reversal"] == 0.0


def test_shipped_retrieval_is_not_at_ceiling_for_bag_of_words(
    fake_embedder: FakeEmbedder, data_dir: Path
) -> None:
    passages = load_passages(data_dir / PASSAGES_FILE)
    queries = load_queries(data_dir / QUERIES_FILE, {p.id for p in passages})
    r = evaluate_retrieval(fake_embedder, passages, queries, query_prefix="")
    assert r.hit_at_1 < 1.0
