import json

import pytest
from fakes import CHUNKS, cite, raw, text

from citations.cite import (
    build_request,
    check_budget,
    parse_response,
    usd_for,
    worst_case_usd,
)
from citations.models import (
    ABSTAIN_TEXT,
    MAX_OUTPUT_TOKENS,
    CitationIntegrityError,
    CostLimitError,
)


def _req() -> dict[str, object]:
    return build_request("Meal allowance?", CHUNKS, model="m", max_tokens=100)


def test_one_document_per_chunk_with_citations_enabled() -> None:
    content = _req()["messages"][0]["content"]  # type: ignore[index]
    docs, question = content[:-1], content[-1]
    assert len(docs) == len(CHUNKS)
    assert all(d["citations"] == {"enabled": True} for d in docs)
    assert question == {"type": "text", "text": "Meal allowance?"}


def test_only_chunk_text_is_citable_metadata_goes_to_title_and_context() -> None:
    doc = _req()["messages"][0]["content"][0]  # type: ignore[index]
    assert doc["source"]["data"] == CHUNKS[0].text
    assert "2026-02-15" in doc["title"]
    assert json.loads(doc["context"])["chunk_id"] == "expense-2026-p2"


def test_build_request_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        build_request("q", (), model="m", max_tokens=1)
    with pytest.raises(ValueError):
        build_request("  ", CHUNKS, model="m", max_tokens=1)


def test_citation_maps_document_index_to_chunk() -> None:
    ans = parse_response(raw(text("$95 abroad", cite(CHUNKS, 0))), CHUNKS)
    assert ans.claims[0].citations[0].chunk.chunk_id == "expense-2026-p2"


def test_span_with_trailing_space_still_verifies() -> None:
    c = cite(CHUNKS, 1)
    assert CHUNKS[1].text[c["start_char_index"] : c["end_char_index"]].endswith(" ")
    parse_response(raw(text("x", c)), CHUNKS)  # must not raise


def test_mismatched_cited_text_raises() -> None:
    bad = {**cite(CHUNKS, 0), "cited_text": "Meals are reimbursed at $200."}
    with pytest.raises(CitationIntegrityError):
        parse_response(raw(text("x", bad)), CHUNKS)


def test_out_of_range_document_index_raises() -> None:
    bad = {**cite(CHUNKS, 0), "document_index": len(CHUNKS)}
    with pytest.raises(CitationIntegrityError):
        parse_response(raw(text("x", bad)), CHUNKS)


def test_non_char_location_citation_raises() -> None:
    bad = {**cite(CHUNKS, 0), "type": "page_location"}
    with pytest.raises(CitationIntegrityError):
        parse_response(raw(text("x", bad)), CHUNKS)


def test_empty_blocks_dropped_and_abstention_detected() -> None:
    ans = parse_response(raw(text("  "), text(ABSTAIN_TEXT)), CHUNKS)
    assert len(ans.claims) == 1 and ans.abstained


def test_cost_from_usage() -> None:
    ans = parse_response(raw(text("hi"), inp=1_000, out=100), CHUNKS)
    assert ans.cost.usd == pytest.approx(1_000 * 2 / 1e6 + 100 * 10 / 1e6)


def test_worst_case_prices_the_full_output_budget() -> None:
    assert worst_case_usd(1_000, MAX_OUTPUT_TOKENS) == usd_for(1_000, MAX_OUTPUT_TOKENS)
    assert worst_case_usd(1_000, MAX_OUTPUT_TOKENS) > usd_for(1_000, 50)


def test_budget_allows_limit_and_rejects_above() -> None:
    check_budget(0.02, limit=0.02)
    with pytest.raises(CostLimitError):
        check_budget(0.0201, limit=0.02)


def test_no_version_hints_removes_dates_and_version_rule() -> None:
    req = build_request("q", CHUNKS, model="m", max_tokens=1, version_hints=False)
    titles = [d["title"] for d in req["messages"][0]["content"][:-1]]  # type: ignore[index]
    assert titles[0] == "expense-policy, page 2"
    assert not any("effective" in t for t in titles)
    assert "version" not in str(req["system"])
    assert ABSTAIN_TEXT in str(req["system"])
