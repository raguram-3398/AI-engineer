"""Pure similarity math. No I/O, no model, no mutation of inputs.

cosine(a, b) = (a . b) / (||a|| * ||b||)

For unit vectors the denominator is 1, so cosine equals the dot product.
That is why FAISS IndexFlatIP on normalized vectors ranks exactly like cosine.
"""

import numpy as np

from embeddings.models import FloatArray

_VECTOR_NDIM: int = 1
_MATRIX_NDIM: int = 2


def l2_normalize(vectors: FloatArray) -> FloatArray:
    """Return a new 2-D array whose rows have unit L2 norm.

    Raises ValueError if the input is not 2-D or any row is all zeros: a zero
    vector has no direction, so its cosine with anything is undefined (0/0).
    """
    if vectors.ndim != _MATRIX_NDIM:
        raise ValueError(f"expected a 2-D array, got shape {vectors.shape}")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0.0):
        raise ValueError("cannot normalize a zero vector: cosine would be 0/0")
    return (vectors / norms).astype(np.float32)


def cosine_manual(a: FloatArray, b: FloatArray) -> float:
    """Cosine similarity written out from the formula, accumulated in float64.

    Deliberately does not assume a and b are normalized, so it can be used to
    check that the library's vectors really are unit length (then this equals
    a plain dot product).

    Raises ValueError on shape mismatch, non-1-D input, or a zero vector.
    """
    if a.ndim != _VECTOR_NDIM or b.ndim != _VECTOR_NDIM:
        raise ValueError(f"expected 1-D vectors, got {a.shape} and {b.shape}")
    if a.shape != b.shape:
        raise ValueError(f"dimension mismatch: {a.shape} vs {b.shape}")
    a64 = a.astype(np.float64)
    b64 = b.astype(np.float64)
    dot = float(np.sum(a64 * b64))
    norm_a = float(np.sqrt(np.sum(a64 * a64)))
    norm_b = float(np.sqrt(np.sum(b64 * b64)))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("cosine is undefined for a zero vector")
    return dot / (norm_a * norm_b)


def cosine_matrix(queries: FloatArray, passages: FloatArray) -> FloatArray:
    """Return the (n_queries, n_passages) cosine matrix in one matrix multiply.

    Both inputs are re-normalized defensively, so the result is correct even if
    a caller passes raw (unnormalized) vectors.
    Raises ValueError if the vector dimensions differ.
    """
    if queries.ndim != _MATRIX_NDIM or passages.ndim != _MATRIX_NDIM:
        raise ValueError(
            f"expected 2-D arrays, got {queries.shape} and {passages.shape}"
        )
    if queries.shape[1] != passages.shape[1]:
        raise ValueError(
            f"dimension mismatch: {queries.shape[1]} vs {passages.shape[1]}"
        )
    return (l2_normalize(queries) @ l2_normalize(passages).T).astype(np.float32)


def with_query_prefix(texts: list[str], prefix: str) -> list[str]:
    """Return a NEW list with `prefix` prepended to every text.

    This is the only place in the project that applies a query instruction.
    Call it on queries only. An empty prefix returns an unchanged copy.
    """
    return [f"{prefix}{text}" for text in texts]
