import numpy as np

from embeddings import FloatArray

def cosine_search(embeddings: FloatArray, query_embedding: FloatArray, k: int = 3) -> list[tuple[int, float]]:
    """Return the top-k documents ranked by cosine similarity."""
    if k <= 0:
        raise ValueError("k must be greater than 0.")
    query = query_embedding[0]
    document_norm = np.linalg.norm(embeddings, axis = 1)
    query_norm = np.linalg.norm(query)
    denominator = document_norm * query_norm
    similarities = np.divide(embeddings @ query, denominator, out = np.zeros_like(document_norm), where = denominator != 0)
    k = min(k, len(embeddings))
    top_indices = np.argsort(similarities)[::-1][:k]
    return [(int(index), float(similarities[index])) for index in top_indices]
