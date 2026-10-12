"""Query-path edge cases: abstain without Claude, citation verification, the
0-indexed page, early stop, Pinecone down, query transforms. No network calls."""

from types import SimpleNamespace as NS

import pytest
from pinecone.errors import PineconeTimeoutError

from multimodal_rag.answer import answer, build_documents, verify_citations
from multimodal_rag.config import ABSTAIN_TEXT, QUERY_PREFIX, REFUSAL_TEXT
from multimodal_rag.contracts import Chunk, Hit
from multimodal_rag.retrieve import QueryError, Retriever, search_query

TEXT = "FDA approved 50 novel drugs in 2021. Most were small molecules."


def _hit(
    score: float = 0.8, page: int = 4, text: str = TEXT, kind: str = "text"
) -> Hit:
    return Hit(Chunk(f"deck-{page}-0", "deck", page, text, 12, kind), score)


def _cite(start: int, end: int, cited: str, doc: int = 0) -> NS:
    return NS(
        type="char_location",
        document_index=doc,
        start_char_index=start,
        end_char_index=end,
        cited_text=cited,
    )


class NoCallClient:
    """Fails the test if Claude is called."""

    @property
    def messages(self):
        raise AssertionError("Claude must not be called")


class FakeClient:
    """Returns one canned Messages API response."""

    def __init__(self, content: list, stop_reason: str = "end_turn") -> None:
        usage = NS(input_tokens=1000, output_tokens=100)
        self.response = NS(content=content, stop_reason=stop_reason, usage=usage)
        self.messages = self
        self.calls: list[dict] = []

    def create(self, **kwargs) -> NS:
        assert "temperature" not in kwargs  # Haiku 5.5 rejects it
        self.calls.append(kwargs)
        return self.response


def test_low_score_still_goes_to_claude() -> None:
    """No score threshold: query 218's gold page ranked 3rd at top-1 0.637."""
    content = [NS(type="text", text="50 drugs.", citations=[_cite(0, 36, TEXT[:36])])]
    result = answer("q", [_hit(score=0.30)], FakeClient(content))
    assert not result.abstained and result.cost_usd > 0


def test_no_hits_abstains_without_calling_claude() -> None:
    assert answer("q", [], NoCallClient()).abstained


def test_document_title_shows_1_indexed_page() -> None:
    """Page 4 in the data is the 5th PDF page a reader would open."""
    assert build_documents([_hit(page=4)])[0]["title"] == "deck p.5"


def test_citation_kept_only_if_quote_matches_chunk() -> None:
    hits = [_hit(page=4), _hit(page=9, text="Other text entirely.")]
    good = _cite(0, 36, TEXT[:36])
    wrong_span = _cite(0, 36, "FDA approved 60 novel drugs in 2021.")
    wrong_doc = _cite(0, 36, TEXT[:36], doc=1)
    content = [NS(type="text", text="50.", citations=[good, wrong_span, wrong_doc])]
    cites = verify_citations(content, hits)
    assert len(cites) == 1
    c = cites[0]
    assert (c.chunk_id, c.page, c.score) == ("deck-4-0", 4, 0.8)
    assert c.cited_text == "FDA approved 50 novel drugs in 2021." and not c.generated


def test_answer_with_citation_and_cost() -> None:
    content = [NS(type="text", text="50 drugs.", citations=[_cite(0, 36, TEXT[:36])])]
    result = answer("How many?", [_hit()], FakeClient(content))
    assert not result.abstained and len(result.citations) == 1
    assert result.cost_usd == pytest.approx((1000 * 0.10 + 100 * 0.50) / 1e6)


def test_claude_abstain_text_without_citations_is_abstain() -> None:
    content = [NS(type="text", text=ABSTAIN_TEXT, citations=None)]
    result = answer("Unrelated?", [_hit()], FakeClient(content))
    assert result.abstained and result.citations == []


def test_max_tokens_stop_raises() -> None:
    content = [NS(type="text", text="The answer is", citations=None)]
    with pytest.raises(QueryError, match="max_tokens"):
        answer("q", [_hit()], FakeClient(content, stop_reason="max_tokens"))


def test_vision_chunk_is_labelled_generated_for_claude_and_in_citations() -> None:
    hit = _hit(page=4, kind="vision")
    assert (
        build_documents([hit])[0]["title"] == "generated visual description, deck p.5"
    )
    content = [NS(type="text", text="50.", citations=[_cite(0, 36, TEXT[:36])])]
    assert verify_citations(content, [hit])[0].generated


def test_refusal_is_its_own_outcome() -> None:
    """Partial text and citations are discarded, cost is kept, not an abstain."""
    content = [NS(type="text", text="Partial", citations=[_cite(0, 36, TEXT[:36])])]
    result = answer("q", [_hit()], FakeClient(content, stop_reason="refusal"))
    assert result.refused and not result.abstained
    assert result.text == REFUSAL_TEXT and result.citations == []
    assert result.cost_usd > 0


def _retriever(index) -> Retriever:
    r = object.__new__(Retriever)  # skip loading BGE and connecting to Pinecone
    r.model = NS(encode=lambda text, normalize_embeddings: NS(tolist=lambda: [0.0]))
    r.chunks = {"deck-4-0": _hit().chunk}
    r.index = index
    return r


def test_pinecone_timeout_becomes_query_error() -> None:
    def query(**kwargs):
        raise PineconeTimeoutError("timed out")

    with pytest.raises(QueryError, match="Pinecone unavailable"):
        _retriever(NS(query=query)).search("q")


def test_id_missing_from_chunk_file_raises() -> None:
    """Index and chunks.jsonl from different ingest runs must not pass silently."""
    matches = [NS(id="deck-4-0", score=0.9), NS(id="deck-7-2", score=0.8)]
    index = NS(query=lambda **kwargs: NS(matches=matches))
    with pytest.raises(QueryError, match="deck-7-2"):
        _retriever(index).search("q")


def _reply(text: str) -> FakeClient:
    return FakeClient([NS(type="text", text=text, citations=None)])


def _query(text: str) -> FakeClient:
    """A forced record_query tool call, as the rewriter receives it."""
    return FakeClient([NS(type="tool_use", input={"query": text})], "tool_use")


def test_no_flags_no_history_does_not_call_claude() -> None:
    sq = search_query("q", NoCallClient(), rewrite_on=False, hyde_on=False)
    assert (sq.question, sq.text, sq.passage, sq.cost_usd) == ("q", "q", False, 0.0)


def test_follow_up_is_rewritten_with_history_and_answered_standalone() -> None:
    """A follow-up's pronoun only resolves through the earlier question, and
    `answer` takes no history, so Claude must get the standalone question."""
    client = _query("What were the reasons for ANDA refuse-to-receive decisions?")
    sq = search_query(
        "What were the main reasons for those?",
        client,
        ["What portion of ANDAs were refused in FY2018?"],
        rewrite_on=False,
        hyde_on=False,
    )
    prompt = client.calls[0]["messages"][0]["content"]
    assert "<earlier_question>What portion of ANDAs" in prompt
    assert sq.question == sq.text == client.response.content[0].input["query"]
    assert sq.cost_usd > 0


def test_rewrite_flag_changes_search_not_the_question_answered() -> None:
    sq = search_query("ANDAs FY12", _query("How many ANDAs in FY12?"), rewrite_on=True)
    assert (sq.question, sq.text) == ("ANDAs FY12", "How many ANDAs in FY12?")


def test_hyde_passage_embedded_without_query_prefix() -> None:
    """BGE is asymmetric: the HyDE passage goes on the passage side, like the
    indexed chunks; a question keeps QUERY_PREFIX."""
    sq = search_query("q", _reply("FDA approved 50 drugs."), hyde_on=True)
    assert sq.passage and sq.text == "FDA approved 50 drugs." and sq.question == "q"
    seen: list[str] = []
    r = _retriever(NS(query=lambda **kwargs: NS(matches=[])))
    r.model = NS(
        encode=lambda text, normalize_embeddings: seen.append(text)
        or NS(tolist=lambda: [0.0])
    )
    r.search(sq.text, passage=sq.passage)
    r.search("q")
    assert seen == ["FDA approved 50 drugs.", QUERY_PREFIX + "q"]
