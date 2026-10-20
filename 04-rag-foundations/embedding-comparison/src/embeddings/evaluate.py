"""Measurement: everything here takes an embedder through EmbedderProtocol.

No file or network I/O. The embedder is the only dependency, so every function
runs against FakeEmbedder in tests and against the real models in main.
"""

import numpy as np

from embeddings.models import (
    FIRST_RANK,
    MIN_FLOOR_TEXTS,
    TOP_K,
    TRIPLET_CATEGORIES,
    EmbedderProtocol,
    Passage,
    RetrievalQuery,
    RetrievalResult,
    Triplet,
    TripletResult,
    TripletSummary,
)
from embeddings.similarity import (
    cosine_manual,
    cosine_matrix,
    l2_normalize,
    with_query_prefix,
)


def verify_manual_cosine(embedder: EmbedderProtocol, texts: list[str]) -> float:
    """Return the worst disagreement between three ways of scoring every pair.

    For each pair (i, j) compares:
      - cosine_manual (the formula, float64),
      - the raw dot product of the embedder's vectors,
      - cosine_matrix (one matrix multiply).
    Near-zero means the vectors really are unit length and the fast path is
    exact. A large value means embed() is NOT returning normalized vectors.
    """
    if not texts:
        raise ValueError("need at least one text to verify")
    vectors = embedder.embed(texts)
    matrix = cosine_matrix(vectors, vectors)
    worst = 0.0
    for i in range(len(texts)):
        for j in range(len(texts)):
            manual = cosine_manual(vectors[i], vectors[j])
            dot = float(np.dot(vectors[i].astype(np.float64), vectors[j]))
            worst = max(worst, abs(manual - dot), abs(manual - float(matrix[i, j])))
    return worst


def score_triplets(
    embedder: EmbedderProtocol, triplets: list[Triplet]
) -> list[TripletResult]:
    """Score sim(anchor, positive) and sim(anchor, negative) for each triplet.

    All 3n texts go to the model in ONE embed call (batching), then are split.
    No query prefix: triplets compare statements to statements, which is the
    symmetric use the BGE card says needs no instruction.
    """
    if not triplets:
        raise ValueError("need at least one triplet")
    n = len(triplets)
    texts = (
        [t.anchor for t in triplets]
        + [t.positive for t in triplets]
        + [t.negative for t in triplets]
    )
    vectors = l2_normalize(embedder.embed(texts))
    anchors, positives, negatives = vectors[:n], vectors[n : 2 * n], vectors[2 * n :]
    pos_scores = np.sum(anchors * positives, axis=1)
    neg_scores = np.sum(anchors * negatives, axis=1)
    return [
        TripletResult(triplet=t, pos_score=float(p), neg_score=float(q))
        for t, p, q in zip(triplets, pos_scores, neg_scores, strict=True)
    ]


def unrelated_floor(embedder: EmbedderProtocol, texts: list[str]) -> float:
    """Mean cosine between DIFFERENT texts (off-diagonal of the similarity matrix).

    This is the score a model gives to "nothing in common". It differs per
    model, which is why a raw threshold like 0.7 cannot be reused across models.
    """
    if len(texts) < MIN_FLOOR_TEXTS:
        raise ValueError(f"need at least {MIN_FLOOR_TEXTS} texts for a floor")
    vectors = embedder.embed(texts)
    matrix = cosine_matrix(vectors, vectors).astype(np.float64)
    off_diagonal = ~np.eye(len(texts), dtype=bool)
    return float(matrix[off_diagonal].mean())


def summarize_triplets(
    model: str, results: list[TripletResult], floor: float
) -> TripletSummary:
    """Collapse per-triplet results into one row: pass rates, margin, raw levels.

    Category order follows TRIPLET_CATEGORIES; categories with no triplets are
    omitted rather than reported as 0.
    """
    if not results:
        raise ValueError("need at least one result to summarize")
    by_category: dict[str, float] = {}
    for category in TRIPLET_CATEGORIES:
        in_category = [r for r in results if r.triplet.category == category]
        if in_category:
            by_category[category] = sum(r.passed for r in in_category) / len(
                in_category
            )
    return TripletSummary(
        model=model,
        pass_rate=sum(r.passed for r in results) / len(results),
        by_category=by_category,
        mean_margin=float(np.mean([r.margin for r in results])),
        mean_pos=float(np.mean([r.pos_score for r in results])),
        mean_neg=float(np.mean([r.neg_score for r in results])),
        unrelated_floor=floor,
    )


def evaluate_retrieval(
    embedder: EmbedderProtocol,
    passages: list[Passage],
    queries: list[RetrievalQuery],
    query_prefix: str,
    k: int = TOP_K,
) -> RetrievalResult:
    """Rank all passages for each query; report hit@1, hit@k, and MRR.

    The prefix is applied to QUERIES ONLY. Passages are embedded exactly as
    stored, as they would be at indexing time.
    Ties are broken by passage order (stable sort), so results are deterministic.
    MRR uses the full ranking, no cutoff: rank 5 still earns 1/5.
    """
    if not passages or not queries:
        raise ValueError("need at least one passage and one query")
    if k < FIRST_RANK:
        raise ValueError(f"k must be >= {FIRST_RANK}, got {k}")

    index_of = {p.id: i for i, p in enumerate(passages)}
    unknown = sorted({q.expected_id for q in queries} - index_of.keys())
    if unknown:
        raise ValueError(f"queries expect passages that do not exist: {unknown}")

    passage_vectors = embedder.embed([p.text for p in passages])
    query_texts = with_query_prefix([q.question for q in queries], query_prefix)
    query_vectors = embedder.embed(query_texts)
    scores = cosine_matrix(query_vectors, passage_vectors)

    ranks: list[int] = []
    for row, query in enumerate(queries):
        order = np.argsort(-scores[row], kind="stable")
        position = int(np.where(order == index_of[query.expected_id])[0][0])
        ranks.append(position + FIRST_RANK)

    n = len(queries)
    return RetrievalResult(
        model=embedder.model_name,
        prefix_used=bool(query_prefix),
        hit_at_1=sum(r == FIRST_RANK for r in ranks) / n,
        hit_at_k=sum(r <= k for r in ranks) / n,
        mrr=sum(1.0 / r for r in ranks) / n,
        k=k,
        ranks=tuple(ranks),
    )
