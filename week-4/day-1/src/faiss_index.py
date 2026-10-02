from enum import Enum

import faiss

from embeddings import FloatArray

class Metric(str, Enum):
    L2 = "l2"
    INNER_PRODUCT = "ip"

def build_faiss_index(embeddings: FloatArray, metric: Metric) -> faiss.Index:
    """Build a FAISS index containing the provided embeddings."""
    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a 2D array.")
    dimension = embeddings.shape[1]
    if metric is Metric.L2:
        index = faiss.IndexFlatL2(dimension)
    elif metric is Metric.INNER_PRODUCT:
        index = faiss.IndexFlatIP(dimension)
    else:
        raise ValueError(f"Unsupported metric: {metric}")
    index.add(embeddings)
    return index

def search_index(index: faiss.Index, query_embedding: FloatArray, k: int = 3) -> list[tuple[int, float]]:
    """Return the top-k document indices and similarity scores."""
    if k <= 0:
        raise ValueError("k must be greater than 0.")
    if query_embedding.ndim != 2 or query_embedding.shape[0] != 1:
        raise ValueError("Query Embedding must have shape (1, dimension).")
    # FAISS cannot return more results than the number of indexed vectors.
    k = min(k, index.ntotal)
    scores, indices = index.search(query_embedding, k)
    return [(int(doc_index), float(score)) for doc_index, score in zip(indices[0], scores[0], strict = True)]