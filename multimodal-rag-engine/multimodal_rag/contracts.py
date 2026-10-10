"""Stage contracts: frozen dataclasses passed between pipeline stages.

Kept apart from `ingest.py` so the query path (retrieve, answer, UI) never
imports `unstructured`, spaCy or tesseract.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    """One PDF page. `page` is 0-indexed (dataset convention); `ocr` = text from OCR."""

    doc_id: str
    page: int
    text: str
    ocr: bool


@dataclass(frozen=True)
class Chunk:
    """One embeddable unit: <= MAX_TOKENS BGE tokens, never crosses a page.

    `chunk_id` is `doc_id-page-n` (n = 0, 1, ... within the page), so re-running
    ingest overwrites the same Pinecone records instead of duplicating them.
    """

    chunk_id: str
    doc_id: str
    page: int
    text: str
    n_tokens: int
    kind: str  # "text" today; "vision" from Day 30


@dataclass(frozen=True)
class Hit:
    """One retrieved chunk and its cosine similarity to the query."""

    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Citation:
    """A verified quote: `cited_text` is exactly `chunk.text[start:end]` of `chunk_id`.

    `page` is 0-indexed. `score` is the retrieval score of the cited chunk.
    `generated` marks quotes from generated vision descriptions (Day 30).
    """

    chunk_id: str
    doc_id: str
    page: int
    cited_text: str
    score: float
    generated: bool


@dataclass(frozen=True)
class Answer:
    """What the pipeline returns for one question.

    `abstained` = no answer from the documents (score below the threshold, or
    Claude replied with ABSTAIN_TEXT and cited nothing). `cost_usd` is 0 when
    Claude was not called.
    """

    text: str
    citations: list[Citation]
    abstained: bool
    cost_usd: float
    latency_s: float
