"""Answer: hits -> abstain, or Claude Haiku answer with verified citations.

Try one question:  python -m multimodal_rag.answer "your question"
"""

import logging
import sys
import time

import anthropic
from dotenv import load_dotenv

from multimodal_rag.config import (
    ABSTAIN_SCORE,
    ABSTAIN_TEXT,
    ANSWER_K,
    ANSWER_MAX_TOKENS,
    CLAUDE_MODEL,
    CLAUDE_TIMEOUT_S,
    PRICE_IN_PER_MTOK,
    PRICE_OUT_PER_MTOK,
    PROJECT_DIR,
)
from multimodal_rag.contracts import Answer, Citation, Hit
from multimodal_rag.retrieve import QueryError, Retriever

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You answer questions about FDA documents using only the documents provided. "
    "Cite the passages that support each claim. Do not use outside knowledge. "
    "If the documents do not contain the answer, reply with exactly this sentence "
    f"and nothing else: {ABSTAIN_TEXT}"
)


def build_documents(hits: list[Hit]) -> list[dict]:
    """One citable plain-text document per chunk; list position = document_index.

    The title shows the 1-indexed PDF page a reader would look up; every data
    structure keeps the 0-indexed page.
    """
    return [
        {
            "type": "document",
            "source": {
                "type": "text",
                "media_type": "text/plain",
                "data": h.chunk.text,
            },
            "title": f"{h.chunk.doc_id} p.{h.chunk.page + 1}",
            "citations": {"enabled": True},
        }
        for h in hits
    ]


def verify_citations(content: list, hits: list[Hit]) -> list[Citation]:
    """Citations from Claude's text blocks whose quote matches the chunk exactly.

    A citation is kept only if `cited_text == chunk.text[start:end]` for the chunk
    at its `document_index`; any other is dropped and logged.
    """
    out: list[Citation] = []
    for block in content:
        for c in getattr(block, "citations", None) or []:
            chunk = hits[c.document_index].chunk
            span = chunk.text[c.start_char_index : c.end_char_index]
            if c.type != "char_location" or span != c.cited_text:
                log.warning("dropped unverified citation of %s", chunk.chunk_id)
                continue
            score = hits[c.document_index].score
            out.append(
                Citation(chunk.chunk_id, chunk.doc_id, chunk.page, span, score, False)
            )
    return out


def cost_usd(usage) -> float:
    """Dollar cost of one Haiku call from its token usage."""
    return (
        usage.input_tokens * PRICE_IN_PER_MTOK
        + usage.output_tokens * PRICE_OUT_PER_MTOK
    ) / 1e6


def answer(question: str, hits: list[Hit], client: anthropic.Anthropic) -> Answer:
    """Abstain without calling Claude if the best hit scores below ABSTAIN_SCORE;
    otherwise answer from the top ANSWER_K hits with verified citations.

    Raises QueryError if the Claude call fails or does not end with `end_turn`
    (e.g. `max_tokens` cut the answer and its citations short).
    """
    t0 = time.monotonic()
    if not hits or hits[0].score < ABSTAIN_SCORE:
        return Answer(ABSTAIN_TEXT, [], True, 0.0, time.monotonic() - t0)

    hits = hits[:ANSWER_K]
    try:
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=ANSWER_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": build_documents(hits)
                    + [{"type": "text", "text": question}],
                }
            ],
            timeout=CLAUDE_TIMEOUT_S,
        )
    except anthropic.APIError as e:
        raise QueryError(f"Claude call failed: {type(e).__name__}: {e}") from e

    cost = cost_usd(msg.usage)
    log.info(
        "claude %s in=%d out=%d cost=$%.6f",
        msg.stop_reason,
        msg.usage.input_tokens,
        msg.usage.output_tokens,
        cost,
    )
    if msg.stop_reason != "end_turn":
        raise QueryError(f"Claude stopped with {msg.stop_reason} (cost ${cost:.6f})")

    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    citations = verify_citations(msg.content, hits)
    abstained = text == ABSTAIN_TEXT and not citations
    return Answer(text, citations, abstained, cost, time.monotonic() - t0)


def ask(question: str, retriever: Retriever, client: anthropic.Anthropic) -> Answer:
    """Retrieve, then answer; `latency_s` covers both."""
    t0 = time.monotonic()
    result = answer(question, retriever.search(question), client)
    return Answer(
        result.text,
        result.citations,
        result.abstained,
        result.cost_usd,
        time.monotonic() - t0,
    )


def main() -> None:
    """Answer the question given on the command line and print its citations."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    log.setLevel(logging.INFO)  # this module's cost line; not the HTTP libraries'
    load_dotenv(PROJECT_DIR / ".env")
    result = ask(sys.argv[1], Retriever(), anthropic.Anthropic())
    print(result.text, "\n")
    for c in result.citations:
        where = f"{c.doc_id} p.{c.page + 1} [{c.chunk_id}, {c.score:.3f}]"
        print(f"- {where} {c.cited_text!r}")
    print(
        f"\nabstained={result.abstained} cost=${result.cost_usd:.6f} "
        f"latency={result.latency_s:.2f}s"
    )


if __name__ == "__main__":
    main()
