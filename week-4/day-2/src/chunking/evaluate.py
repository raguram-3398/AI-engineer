"""Measure chunking strategies: size statistics and retrieval hit@k. No I/O."""

import numpy as np
from langchain_core.documents import Document

from chunking.models import SENTENCE_ENDINGS, ChunkStats, EmbedderProtocol, EvalQuery


def is_mid_sentence(text: str) -> bool:
    """True if the chunk does not end on sentence punctuation."""
    return not text.rstrip().endswith(SENTENCE_ENDINGS)


def normalize_for_match(text: str) -> str:
    """Lowercase and collapse whitespace so PDF line breaks don't break matching."""
    return " ".join(text.split()).lower()


def chunk_stats(chunks: list[Document], max_tokens: int) -> ChunkStats:
    """Summarize annotated chunks (they must carry token_count metadata)."""
    if not chunks:
        raise ValueError("chunk_stats needs at least one chunk")
    token_counts = [int(c.metadata["token_count"]) for c in chunks]
    return ChunkStats(
        strategy=str(chunks[0].metadata["strategy"]),
        count=len(chunks),
        min_tokens=min(token_counts),
        mean_tokens=sum(token_counts) / len(token_counts),
        max_tokens=max(token_counts),
        over_limit=sum(1 for n in token_counts if n > max_tokens),
        mid_sentence=sum(1 for c in chunks if is_mid_sentence(c.page_content)),
    )


def hit_at_k(
    chunks: list[Document],
    queries: list[EvalQuery],
    embedder: EmbedderProtocol,
    k: int,
) -> float:
    """Fraction of queries whose expected substring appears in a top-k retrieved chunk.

    Ground truth is a verbatim substring, not a chunk ID, so all strategies are
    graded against the same answer regardless of where their boundaries fall.
    If a boundary cuts the substring in half, no chunk contains it — a miss,
    correctly, because no single chunk carries the full fact.
    """
    if not chunks or not queries:
        raise ValueError("hit_at_k needs at least one chunk and one query")
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    chunk_vectors = embedder.embed([c.page_content for c in chunks])
    query_vectors = embedder.embed([q.question for q in queries])
    scores = query_vectors @ chunk_vectors.T  # (n_queries, n_chunks) cosine matrix

    hits = 0
    for query, row in zip(queries, scores):
        top_indices = np.argsort(row)[::-1][:k]
        needle = normalize_for_match(query.expected_substring)
        if any(
            needle in normalize_for_match(chunks[i].page_content) for i in top_indices
        ):
            hits += 1
    return hits / len(queries)
