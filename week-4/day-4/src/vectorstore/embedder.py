"""Embedder Protocol and the BGE implementation.

The only module that imports sentence-transformers, and only inside the
default loader, so tests never need the library or a download.
Construct ONCE per process: loading takes seconds and hundreds of MB.
"""

import os
from collections.abc import Callable, Sequence
from typing import Any, Protocol

from vectorstore.models import (
    BGE_QUERY_PREFIX,
    DIMENSION,
    HF_DOWNLOAD_TIMEOUT_S,
    HF_ETAG_TIMEOUT_S,
    EmbeddingModelMismatchError,
    VectorStoreError,
)

ModelLoader = Callable[[str], Any]


class Embedder(Protocol):
    """Anything that turns documents and queries into unit-length vectors."""

    @property
    def model_id(self) -> str: ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def _default_loader(model_id: str) -> Any:
    """Put timeouts on Hub downloads, then import and load the real model."""
    # huggingface_hub reads these once, at import, so set them before importing.
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", str(HF_DOWNLOAD_TIMEOUT_S))
    os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", str(HF_ETAG_TIMEOUT_S))
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_id)


class BgeEmbedder:
    """bge-small-en-v1.5: documents embedded as-is, queries with the BGE prefix."""

    def __init__(self, model_id: str, loader: ModelLoader | None = None) -> None:
        """Load the model once.

        Raises VectorStoreError if loading fails, and
        EmbeddingModelMismatchError if its dimension doesn't match the index.
        """
        load = loader if loader is not None else _default_loader
        try:
            model = load(model_id)
        except Exception as e:  # boundary: OSError, requests, torch errors all differ
            raise VectorStoreError(f"could not load {model_id!r}: {e}") from e
        # renamed in sentence-transformers 6; support both spellings
        get_dim = getattr(model, "get_embedding_dimension", None) or getattr(
            model, "get_sentence_embedding_dimension"
        )
        dim = get_dim()
        if dim != DIMENSION:
            raise EmbeddingModelMismatchError(
                f"{model_id!r} outputs {dim} dims, index expects {DIMENSION}"
            )
        self._model = model
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        """Hub id, written into every record's metadata."""
        return self._model_id

    def _encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            prompt="",  # never let a config default prompt sneak in
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(x) for x in row] for row in vectors]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed passages with no prefix. Empty input returns []."""
        return self._encode(list(texts)) if texts else []

    def embed_query(self, text: str) -> list[float]:
        """Embed one query with BGE's retrieval instruction prepended."""
        return self._encode([BGE_QUERY_PREFIX + text])[0]
