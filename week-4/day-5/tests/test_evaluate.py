import pytest
from fakes import CHUNKS, cite, raw, text

from citations.cite import parse_response
from citations.evaluate import aggregate, score_case, states_a_number
from citations.models import ABSTAIN_TEXT, EvalCase


def _case(
    kind: str = "version", gold: tuple[str, ...] = ("expense-2026-p2",)
) -> EvalCase:
    return EvalCase("t", kind, "q", CHUNKS, frozenset(gold))


def test_correct_version_scores_perfectly() -> None:
    ans = parse_response(raw(text("$75 a day", cite(CHUNKS, 0))), CHUNKS)
    s = score_case(_case(), ans)
    assert (s.precision, s.recall, s.stale) == (1.0, 1.0, False)


def test_stale_version_is_grounded_but_wrong() -> None:
    # Passes the integrity check (no exception) yet cites the 2024 chunk.
    ans = parse_response(raw(text("$60 a day", cite(CHUNKS, 1))), CHUNKS)
    s = score_case(_case(), ans)
    assert s.stale and s.precision == 0.0 and s.recall == 0.0


def test_extra_non_gold_citation_lowers_precision_only() -> None:
    ans = parse_response(
        raw(text("$75 a day", cite(CHUNKS, 0), cite(CHUNKS, 2))), CHUNKS
    )
    s = score_case(_case(), ans)
    assert (s.precision, s.recall, s.stale) == (0.5, 1.0, False)


def test_multi_source_half_recall() -> None:
    ans = parse_response(raw(text("$95 abroad", cite(CHUNKS, 0))), CHUNKS)
    s = score_case(_case("multi_source", ("expense-2026-p2", "travel-2025-p1")), ans)
    assert s.recall == 0.5


def test_abstain_case_ok_only_without_citations() -> None:
    abstain = _case("abstain", ())
    good = parse_response(raw(text(ABSTAIN_TEXT)), CHUNKS)
    bad = parse_response(raw(text("Yes", cite(CHUNKS, 2))), CHUNKS)
    assert score_case(abstain, good).abstain_ok is True
    assert score_case(abstain, bad).abstain_ok is False


def test_uncited_numbers_count_but_years_do_not() -> None:
    assert states_a_number("The allowance is $75.")
    assert not states_a_number("Under the 2026 policy, ")
    ans = parse_response(
        raw(text("Under the 2026 policy, "), text("it is $75.")), CHUNKS
    )
    assert score_case(_case(), ans).uncited_claims == 1


def test_aggregate_by_kind() -> None:
    good = parse_response(raw(text("x", cite(CHUNKS, 0))), CHUNKS)
    stale = parse_response(raw(text("x", cite(CHUNKS, 1))), CHUNKS)
    report = aggregate([score_case(_case(), good), score_case(_case(), stale)])
    assert report["version"]["precision"] == pytest.approx(0.5)
    assert report["version"]["stale_rate"] == pytest.approx(0.5)
    assert report["ALL answerable"]["n"] == 2
