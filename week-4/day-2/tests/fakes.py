"""Test doubles. FakeEmbedder lets every test run without downloading a model."""

import re
import zlib

import numpy as np

from chunking.models import FloatArray

FAKE_DIM: int = 256
FAKE_MAX_TOKENS: int = 20
FAKE_SPECIAL_TOKENS: int = 2  # mimics [CLS] + [SEP]


class FakeEmbedder:
    """Deterministic bag-of-words embedder: texts sharing words get higher cosine.

    zlib.crc32 instead of hash(): Python's str hash is randomized per process,
    which would make tests non-deterministic.
    """

    def __init__(self, max_tokens: int = FAKE_MAX_TOKENS) -> None:
        """Set the token limit this fake pretends to have."""
        self._max_tokens = max_tokens

    @property
    def max_tokens(self) -> int:
        """Fake truncation limit."""
        return self._max_tokens

    def embed(self, texts: list[str]) -> FloatArray:
        """Hash each word into a bucket, then unit-normalize each row."""
        vectors = np.zeros((len(texts), FAKE_DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in re.findall(r"[a-z]+", text.lower()):
                vectors[row, zlib.crc32(word.encode()) % FAKE_DIM] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms > 0)

    def count_tokens(self, text: str) -> int:
        """Whitespace words plus two special tokens."""
        return len(text.split()) + FAKE_SPECIAL_TOKENS
