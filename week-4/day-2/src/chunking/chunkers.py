"""Three chunking strategies plus token annotation. No I/O.

All strategies chunk page by page, so a chunk never spans two pages and its
`page` metadata is always exact. The cost: a paragraph that crosses a page
break is cut in two. Exact citations were chosen over that paragraph.
"""

import re
from itertools import pairwise

import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chunking.models import (
    STRATEGY_FIXED,
    STRATEGY_RECURSIVE,
    STRATEGY_SEMANTIC,
    EmbedderProtocol,
    FloatArray,
)

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _validate_sizes(chunk_size: int, chunk_overlap: int) -> None:
    """Raise ValueError unless 0 <= overlap < size."""
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError(
            f"chunk_overlap must be in [0, {chunk_size}), got {chunk_overlap}"
        )


def _make_chunk(parent: Document, text: str, strategy: str) -> Document:
    """Build a chunk inheriting the parent's metadata (source, page, doc_type)."""
    return Document(
        page_content=text,
        metadata={**parent.metadata, "strategy": strategy, "char_count": len(text)},
    )


def _number_chunks(chunks: list[Document]) -> list[Document]:
    """Return new Documents with a global chunk_index — the future chunk ID."""
    return [
        Document(page_content=c.page_content, metadata={**c.metadata, "chunk_index": i})
        for i, c in enumerate(chunks)
    ]


def chunk_fixed(
    docs: list[Document], chunk_size: int, chunk_overlap: int
) -> list[Document]:
    """Slide a fixed character window over each page, ignoring all structure."""
    _validate_sizes(chunk_size, chunk_overlap)
    step = chunk_size - chunk_overlap
    chunks: list[Document] = []
    for doc in docs:
        text = doc.page_content
        for start in range(0, len(text), step):
            piece = text[start : start + chunk_size]
            if piece.strip():
                chunks.append(_make_chunk(doc, piece, STRATEGY_FIXED))
            if start + chunk_size >= len(text):
                break  # window reached the end; another would be pure overlap
    return _number_chunks(chunks)


def chunk_recursive(
    docs: list[Document], chunk_size: int, chunk_overlap: int
) -> list[Document]:
    """Split on paragraphs, then lines, then words, until each piece fits chunk_size."""
    _validate_sizes(chunk_size, chunk_overlap)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = [
        _make_chunk(doc, piece, STRATEGY_RECURSIVE)
        for doc in docs
        for piece in splitter.split_text(doc.page_content)
    ]
    return _number_chunks(chunks)


def split_sentences(text: str) -> list[str]:
    """Collapse whitespace (PDFs break lines mid-sentence) and split after . ! ?"""
    collapsed = " ".join(text.split())
    return [s for s in _SENTENCE_BOUNDARY.split(collapsed) if s]


def find_breakpoints(vectors: FloatArray, breakpoint_percentile: float) -> list[int]:
    """Return sentence indices where a new chunk should start.

    Distance between neighbours is 1 - cosine (vectors are unit-normalized, so
    cosine is a plain dot product). A break goes wherever the distance is above
    the given percentile of all distances on this page — i.e. the biggest
    topic shifts relative to this page, not an absolute threshold.
    """
    if len(vectors) < 2:
        return []
    similarities = np.sum(vectors[:-1] * vectors[1:], axis=1)
    distances = 1.0 - similarities
    threshold = float(np.percentile(distances, breakpoint_percentile))
    return [i + 1 for i, distance in enumerate(distances) if distance > threshold]


def group_sentences(sentences: list[str], breakpoints: list[int]) -> list[list[str]]:
    """Cut the sentence list at each breakpoint index."""
    bounds = [0, *breakpoints, len(sentences)]
    return [sentences[a:b] for a, b in pairwise(bounds) if a < b]


def chunk_semantic(
    docs: list[Document], embedder: EmbedderProtocol, breakpoint_percentile: float
) -> list[Document]:
    """Group consecutive sentences until the embedding similarity drops sharply.

    Note: there is no size cap. A long single-topic page becomes one chunk,
    which may exceed the embedder's token limit — that is a finding to measure,
    not a bug to hide. This strategy also costs one embedding call per page at
    ingest time; fixed and recursive cost nothing until indexing.
    """
    if not 0 < breakpoint_percentile < 100:
        raise ValueError(
            f"breakpoint_percentile must be in (0, 100), got {breakpoint_percentile}"
        )
    chunks: list[Document] = []
    for doc in docs:
        sentences = split_sentences(doc.page_content)
        if not sentences:
            continue
        breakpoints = find_breakpoints(embedder.embed(sentences), breakpoint_percentile)
        for group in group_sentences(sentences, breakpoints):
            chunks.append(_make_chunk(doc, " ".join(group), STRATEGY_SEMANTIC))
    return _number_chunks(chunks)


def annotate_tokens(
    chunks: list[Document], embedder: EmbedderProtocol
) -> list[Document]:
    """Add token_count and over_limit using the embedder's own tokenizer.

    over_limit=True means the embedder will silently drop this chunk's tail.
    """
    limit = embedder.max_tokens
    annotated: list[Document] = []
    for chunk in chunks:
        token_count = embedder.count_tokens(chunk.page_content)
        annotated.append(
            Document(
                page_content=chunk.page_content,
                metadata={
                    **chunk.metadata,
                    "token_count": token_count,
                    "over_limit": token_count > limit,
                },
            )
        )
    return annotated
