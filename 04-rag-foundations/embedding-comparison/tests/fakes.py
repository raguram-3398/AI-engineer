"""Test doubles. Nothing here downloads a model or touches the network."""

import re
import zlib
from typing import Any

import numpy as np

from embeddings.models import FloatArray

FAKE_DIM: int = 256
FAKE_MAX_TOKENS: int = 64
FAKE_SPECIAL_TOKENS: int = 2  # mimics [CLS] + [SEP]
FAKE_MODEL_NAME: str = "fake/bag-of-words"


class FakeEmbedder:
    """Deterministic bag-of-words embedder: texts sharing words score higher.

    It has no notion of meaning, which makes it a useful lower bound: an eval
    that this fake aces is too easy. zlib.crc32 instead of hash() because
    Python's str hash is randomized per process.
    """

    def __init__(self, model_name: str = FAKE_MODEL_NAME) -> None:
        """Name only; there is nothing to load."""
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        """Fake hub id."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Bucket count."""
        return FAKE_DIM

    @property
    def max_tokens(self) -> int:
        """Fake truncation limit."""
        return FAKE_MAX_TOKENS

    def embed(self, texts: list[str]) -> FloatArray:
        """Hash each lowercase word into a bucket, then unit-normalize each row.

        A text with no words maps to a fixed bucket so no row is ever all zero.
        """
        vectors = np.zeros((len(texts), FAKE_DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            words = re.findall(r"[a-z0-9]+", text.lower()) or ["<empty>"]
            for word in words:
                vectors[row, zlib.crc32(word.encode()) % FAKE_DIM] += 1.0
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    def count_tokens(self, text: str) -> int:
        """Whitespace words plus two special tokens."""
        return len(text.split()) + FAKE_SPECIAL_TOKENS


class RecordingEmbedder(FakeEmbedder):
    """FakeEmbedder that remembers every batch it was asked to embed."""

    def __init__(self) -> None:
        """Start with an empty call log."""
        super().__init__()
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> FloatArray:
        """Record a copy of the batch, then embed it."""
        self.calls.append(list(texts))
        return super().embed(texts)


class UnnormalizedEmbedder(FakeEmbedder):
    """Breaks the unit-norm contract by scaling every vector by 3."""

    def embed(self, texts: list[str]) -> FloatArray:
        """Return vectors with norm 3 instead of 1."""
        return super().embed(texts) * np.float32(3.0)


class FakeTokenizer:
    """Mimics a Hugging Face tokenizer's encode()."""

    def encode(self, text: str, add_special_tokens: bool = True) -> list[int]:
        """One id per whitespace word, plus two specials if requested."""
        ids = list(range(len(text.split())))
        return [0, *ids, 0] if add_special_tokens else ids


class FakeSentenceTransformer:
    """The slice of the sentence-transformers API our embedder uses.

    Records encode() kwargs so tests can assert that prompt="" is passed and
    normalization is requested.
    """

    def __init__(
        self,
        dimension: int | None = 8,
        max_seq_length: int | None = 512,
        use_new_dimension_api: bool = True,
    ) -> None:
        """Configure what the fake reports about itself."""
        self._dimension = dimension
        self.max_seq_length = max_seq_length
        self.tokenizer = FakeTokenizer()
        self.encode_kwargs: list[dict[str, Any]] = []
        if use_new_dimension_api:
            self.get_embedding_dimension = self._dim
        else:
            self.get_sentence_embedding_dimension = self._dim

    def _dim(self) -> int | None:
        """Report the configured dimension."""
        return self._dimension

    def encode(self, texts: list[str], **kwargs: Any) -> np.ndarray:
        """Return float64 unit vectors (the wrapper must cast to float32)."""
        self.encode_kwargs.append(kwargs)
        dim = self._dimension or 1
        vectors = np.ones((len(texts), dim), dtype=np.float64)
        return vectors / np.sqrt(dim)
