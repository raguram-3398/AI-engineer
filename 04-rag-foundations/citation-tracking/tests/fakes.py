"""Test doubles: no network, no API key."""

from collections.abc import Callable, Mapping

from citations.models import CitedChunk, RawResponse

EXP_2026_P2 = CitedChunk(
    chunk_id="expense-2026-p2",
    source="expense-policy",
    page=2,
    date=20260215,
    text=(
        "While travelling for work, meals are reimbursed up to a daily allowance "
        "of $75 within the United States and $95 internationally. Alcohol is never "
        "reimbursable, including at client dinners."
    ),
    score=0.86,
)
EXP_2024_P2 = CitedChunk(
    chunk_id="expense-2024-p2",
    source="expense-policy",
    page=2,
    date=20240201,
    text=(
        "While travelling for work, meals are reimbursed up to a daily allowance "
        "of $60 within the United States and $80 internationally. Alcohol is not "
        "reimbursable unless a client is present and a senior manager approves it "
        "in advance."
    ),
    score=0.85,
)
TRAVEL_P1 = CitedChunk(
    chunk_id="travel-2025-p1",
    source="travel-policy",
    page=1,
    date=20250901,
    text=(
        "Book all flights and hotels through Navan so that bookings appear on the "
        "duty-of-care map. Hotel rates are capped at $250 per night in tier-one "
        "cities such as New York, San Francisco, and London, and $180 per night "
        "elsewhere. Meals during travel follow the expense policy."
    ),
    score=0.71,
)
CHUNKS = (EXP_2026_P2, EXP_2024_P2, TRAVEL_P1)


def first_sentence_span(chunk: CitedChunk) -> tuple[int, int]:
    """Span of the first sentence INCLUDING the trailing space, like the API."""
    end = chunk.text.find(". ")
    return 0, len(chunk.text) if end == -1 else end + 2


def cite(chunks: tuple[CitedChunk, ...], index: int) -> dict[str, object]:
    """A char_location citation of chunk `index`'s first sentence."""
    start, end = first_sentence_span(chunks[index])
    return {
        "type": "char_location",
        "cited_text": chunks[index].text[start:end].strip(),
        "document_index": index,
        "document_title": chunks[index].source,
        "start_char_index": start,
        "end_char_index": end,
    }


def text(t: str, *citations: dict[str, object]) -> dict[str, object]:
    block: dict[str, object] = {"type": "text", "text": t}
    if citations:
        block["citations"] = list(citations)
    return block


def raw(*blocks: dict[str, object], inp: int = 900, out: int = 60) -> RawResponse:
    return RawResponse(blocks=tuple(blocks), input_tokens=inp, output_tokens=out)


class FakeClient:
    """Answers via `respond(request) -> RawResponse`; records every call."""

    def __init__(
        self,
        respond: Callable[[Mapping[str, object]], RawResponse],
        input_tokens: int = 900,
    ) -> None:
        self._respond = respond
        self._input_tokens = input_tokens
        self.created: list[Mapping[str, object]] = []

    def count_tokens(self, request: Mapping[str, object]) -> int:
        return self._input_tokens

    def create(self, request: Mapping[str, object]) -> RawResponse:
        self.created.append(request)
        return self._respond(request)
