"""Pure core: build a citations request, parse and verify the response, price it."""

import json
from collections.abc import Mapping, Sequence

from citations.models import (
    ABSTAIN_TEXT,
    AS_OF_DATE,
    INPUT_USD_PER_MTOK,
    MAX_USD_PER_CALL,
    OUTPUT_USD_PER_MTOK,
    TOKENS_PER_MTOK,
    Citation,
    CitationIntegrityError,
    CitedAnswer,
    CitedChunk,
    Claim,
    CostLimitError,
    CostRecord,
    RawResponse,
)

# Run A: unchanged from the first run, so A's scores stay comparable.
SYSTEM_PROMPT: str = (
    f"Today is {AS_OF_DATE}. Answer the question using only the documents provided. "
    "Some documents are different versions of the same policy; each title shows its "
    "effective date. Unless the question names a version, answer from the version in "
    "effect today. If the documents do not contain the answer, reply with exactly "
    f"{ABSTAIN_TEXT} and nothing else."
)
# Ablation B: same prompt minus the date and the version rule.
SYSTEM_PROMPT_NO_VERSION: str = (
    "Answer the question using only the documents provided. If the documents do "
    f"not contain the answer, reply with exactly {ABSTAIN_TEXT} and nothing else."
)


def _format_date(yyyymmdd: int) -> str:
    s = str(yyyymmdd)
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"


def _title(c: CitedChunk, version_hints: bool) -> str:
    if version_hints:
        return f"{c.source} (effective {_format_date(c.date)}), page {c.page}"
    return f"{c.source}, page {c.page}"


def build_documents(
    chunks: Sequence[CitedChunk], version_hints: bool = True
) -> list[dict[str, object]]:
    """One plain-text document per chunk, citations enabled on every one.

    Only `chunk.text` is citable. Version and identity go in `title` (the model
    needs the date to pick a version) and `context` (stringified metadata);
    neither can ever appear in `cited_text`. With version_hints=False the title
    has no date (ablation B).
    """
    return [
        {
            "type": "document",
            "source": {"type": "text", "media_type": "text/plain", "data": c.text},
            "title": _title(c, version_hints),
            "context": json.dumps(
                {"chunk_id": c.chunk_id, "source": c.source, "page": c.page}
            ),
            "citations": {"enabled": True},
        }
        for c in chunks
    ]


def build_request(
    query: str,
    chunks: Sequence[CitedChunk],
    *,
    model: str,
    max_tokens: int,
    version_hints: bool = True,
) -> dict[str, object]:
    """Messages API request: documents first, question last.

    Document i in this request is chunks[i]; parse_response relies on that order.
    version_hints=False removes dates from titles and the version rule from the
    system prompt (ablation B).
    Raises ValueError on an empty query or no chunks (programmer error).
    """
    if not query.strip():
        raise ValueError("query is empty")
    if not chunks:
        raise ValueError("no chunks to cite from")
    content = [
        *build_documents(chunks, version_hints),
        {"type": "text", "text": query},
    ]
    return {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT if version_hints else SYSTEM_PROMPT_NO_VERSION,
        "messages": [{"role": "user", "content": content}],
    }


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _verify(raw: Mapping[str, object], chunks: Sequence[CitedChunk]) -> Citation:
    """Map one API citation to its chunk and check the cited text is really there."""
    if raw.get("type") != "char_location":
        raise CitationIntegrityError(f"unexpected citation type {raw.get('type')!r}")
    index, start, end = (
        raw["document_index"],
        raw["start_char_index"],
        raw["end_char_index"],
    )
    cited_text = str(raw["cited_text"])
    if not isinstance(index, int) or not 0 <= index < len(chunks):
        raise CitationIntegrityError(f"document_index {index!r} out of range")
    chunk = chunks[index]
    if not (isinstance(start, int) and isinstance(end, int)):
        raise CitationIntegrityError("char indices are not integers")
    if not 0 <= start < end <= len(chunk.text):
        raise CitationIntegrityError(
            f"chars [{start}, {end}) outside {chunk.chunk_id} (len {len(chunk.text)})"
        )
    # End index is exclusive and the span may include the space after a sentence,
    # so compare whitespace-normalized text, not raw strings.
    if _normalize(chunk.text[start:end]) != _normalize(cited_text):
        raise CitationIntegrityError(f"cited_text does not match {chunk.chunk_id}")
    return Citation(chunk=chunk, cited_text=cited_text, start_char=start, end_char=end)


def usd_for(input_tokens: int, output_tokens: int) -> float:
    """Exact cost of a finished call at MODEL_ID prices."""
    return (
        input_tokens * INPUT_USD_PER_MTOK + output_tokens * OUTPUT_USD_PER_MTOK
    ) / TOKENS_PER_MTOK


def worst_case_usd(input_tokens: int, max_tokens: int) -> float:
    """Upper bound before the call: counted input plus the full output budget."""
    return usd_for(input_tokens, max_tokens)


def check_budget(worst_case: float, limit: float = MAX_USD_PER_CALL) -> None:
    """Raise CostLimitError if the call could cost more than `limit`."""
    if worst_case > limit:
        raise CostLimitError(f"worst case ${worst_case:.4f} exceeds ${limit:.4f}")


def parse_response(raw: RawResponse, chunks: Sequence[CitedChunk]) -> CitedAnswer:
    """Turn response blocks into verified claims.

    Every citation is checked against the chunk it points to; any mismatch raises
    CitationIntegrityError. Non-text blocks and empty text blocks are dropped.
    """
    claims: list[Claim] = []
    for block in raw.blocks:
        if block.get("type") != "text":
            continue
        text = str(block.get("text", ""))
        if not text.strip():
            continue
        cites = block.get("citations") or []
        if not isinstance(cites, list):
            raise CitationIntegrityError("citations is not a list")
        claims.append(
            Claim(text=text, citations=tuple(_verify(c, chunks) for c in cites))
        )
    full_text = "".join(c.text for c in claims)
    return CitedAnswer(
        claims=tuple(claims),
        abstained=ABSTAIN_TEXT in full_text,
        cost=CostRecord(
            input_tokens=raw.input_tokens,
            output_tokens=raw.output_tokens,
            usd=usd_for(raw.input_tokens, raw.output_tokens),
        ),
    )
