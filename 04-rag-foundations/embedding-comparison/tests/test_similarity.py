"""Pure math: known answers, contract violations, and no input mutation."""

import numpy as np
import pytest

from embeddings.similarity import (
    cosine_manual,
    cosine_matrix,
    l2_normalize,
    with_query_prefix,
)

TOL: float = 1e-6


def _v(*values: float) -> np.ndarray:
    return np.array(values, dtype=np.float32)


def test_cosine_known_angles() -> None:
    assert cosine_manual(_v(1, 0), _v(1, 0)) == pytest.approx(1.0, abs=TOL)
    assert cosine_manual(_v(1, 0), _v(0, 1)) == pytest.approx(0.0, abs=TOL)
    assert cosine_manual(_v(1, 0), _v(-1, 0)) == pytest.approx(-1.0, abs=TOL)
    assert cosine_manual(_v(1, 1), _v(1, 0)) == pytest.approx(np.sqrt(0.5), abs=TOL)


def test_cosine_ignores_length() -> None:
    """Scaling a vector changes the dot product but not the cosine."""
    a, b = _v(1, 2, 3), _v(3, 1, 2)
    assert cosine_manual(a * 10, b) == pytest.approx(cosine_manual(a, b), abs=TOL)


def test_cosine_equals_dot_for_unit_vectors() -> None:
    rng = np.random.default_rng(0)
    a, b = l2_normalize(rng.normal(size=(2, 384)).astype(np.float32))
    assert cosine_manual(a, b) == pytest.approx(float(np.dot(a, b)), abs=1e-5)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (_v(0, 0), _v(1, 0)),  # zero vector
        (_v(1, 0), _v(1, 0, 0)),  # dimension mismatch
        (np.ones((1, 2), dtype=np.float32), _v(1, 0)),  # 2-D input
    ],
)
def test_cosine_rejects_bad_input(a: np.ndarray, b: np.ndarray) -> None:
    with pytest.raises(ValueError):
        cosine_manual(a, b)


def test_l2_normalize_gives_unit_rows_and_copies() -> None:
    raw = np.array([[3, 4], [0, 2]], dtype=np.float32)
    before = raw.copy()
    out = l2_normalize(raw)
    assert np.allclose(np.linalg.norm(out, axis=1), 1.0)
    assert out.dtype == np.float32
    assert np.array_equal(raw, before)


def test_l2_normalize_rejects_zero_row() -> None:
    with pytest.raises(ValueError, match="zero vector"):
        l2_normalize(np.array([[1, 0], [0, 0]], dtype=np.float32))


def test_cosine_matrix_matches_manual_on_unnormalized_input() -> None:
    rng = np.random.default_rng(1)
    q = rng.normal(size=(3, 16)).astype(np.float32) * 5
    p = rng.normal(size=(4, 16)).astype(np.float32)
    m = cosine_matrix(q, p)
    assert m.shape == (3, 4)
    for i in range(3):
        for j in range(4):
            assert m[i, j] == pytest.approx(cosine_manual(q[i], p[j]), abs=1e-5)


def test_cosine_matrix_rejects_dimension_mismatch() -> None:
    with pytest.raises(ValueError, match="dimension mismatch"):
        cosine_matrix(np.ones((1, 3), np.float32), np.ones((1, 4), np.float32))


def test_with_query_prefix_returns_new_list() -> None:
    texts = ["a", "b"]
    out = with_query_prefix(texts, "Q: ")
    assert out == ["Q: a", "Q: b"]
    assert texts == ["a", "b"]
    copy = with_query_prefix(texts, "")
    assert copy == texts and copy is not texts
