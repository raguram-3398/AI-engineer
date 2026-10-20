"""SentenceTransformer wrapper satisfying EmbedderProtocol.

The only module that touches sentence-transformers, and it imports it lazily
inside the default loader, so tests never need the library or a model download.

Construct ONCE per model per process: loading costs seconds and hundreds of MB.
"""

import os
import sys
from collections.abc import Callable
from typing import Any

import numpy as np

from embeddings.exceptions import ModelLoadError
from embeddings.models import (
    HF_DOWNLOAD_TIMEOUT_ENV,
    HF_DOWNLOAD_TIMEOUT_S,
    HF_ETAG_TIMEOUT_ENV,
    HF_ETAG_TIMEOUT_S,
    NO_PREFIX,
    FloatArray,
)

ModelLoader = Callable[[str], Any]

_HUB_CONSTANTS_MODULE: str = "huggingface_hub.constants"
_HUB_TIMEOUT_ATTRIBUTES: tuple[tuple[str, str], ...] = (
    ("HF_HUB_DOWNLOAD_TIMEOUT", HF_DOWNLOAD_TIMEOUT_ENV),
    ("HF_HUB_ETAG_TIMEOUT", HF_ETAG_TIMEOUT_ENV),
)
_DIMENSION_METHODS: tuple[str, ...] = (
    "get_embedding_dimension",  # sentence-transformers >= 6
    "get_sentence_embedding_dimension",  # older releases
)


def configure_hub_timeouts(
    download_s: int = HF_DOWNLOAD_TIMEOUT_S, etag_s: int = HF_ETAG_TIMEOUT_S
) -> None:
    """Put a timeout on every Hugging Face Hub request made while loading a model.

    huggingface_hub reads these env vars ONCE, at import, with int(). So:
    - values must be whole seconds (a float string crashes the import), and
    - if the hub is already imported, the env var alone is too late, so the
      already-loaded constants are patched too.
    Values the user already exported are respected.
    """
    os.environ.setdefault(HF_DOWNLOAD_TIMEOUT_ENV, str(int(download_s)))
    os.environ.setdefault(HF_ETAG_TIMEOUT_ENV, str(int(etag_s)))
    constants = sys.modules.get(_HUB_CONSTANTS_MODULE)
    if constants is not None:
        for attribute, env_name in _HUB_TIMEOUT_ATTRIBUTES:
            setattr(constants, attribute, int(os.environ[env_name]))


def _default_loader(model_name: str) -> Any:
    """Set hub timeouts, then import and load the real model. Network on first run."""
    configure_hub_timeouts()
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _read_dimension(model: Any) -> int | None:
    """Return the output dimension across sentence-transformers versions."""
    for method_name in _DIMENSION_METHODS:
        method = getattr(model, method_name, None)
        if callable(method):
            value = method()
            return int(value) if value is not None else None
    return None


class SentenceTransformerEmbedder:
    """Local embedding model behind EmbedderProtocol.

    embed() never adds an instruction prefix, even if the model's config defines
    a default prompt: prefixing is the caller's job, done in exactly one place.
    """

    def __init__(self, model_name: str, loader: ModelLoader | None = None) -> None:
        """Load the model once.

        Raises ValueError for an empty name (programmer error) and ModelLoadError
        for anything that goes wrong while loading (timeout, offline, bad id).
        """
        if not model_name.strip():
            raise ValueError("model_name must be a non-empty Hugging Face model id")
        load = loader if loader is not None else _default_loader
        try:
            model = load(model_name)
        except Exception as e:  # boundary: requests, httpx, OSError, torch all differ
            raise ModelLoadError(f"could not load {model_name!r}: {e}") from e

        dimension = _read_dimension(model)
        max_tokens = getattr(model, "max_seq_length", None)
        if dimension is None or max_tokens is None:
            raise ModelLoadError(
                f"{model_name!r} does not report its dimension or max sequence length"
            )
        self._model = model
        self._model_name = model_name
        self._dimension = dimension
        self._max_tokens = int(max_tokens)

    @property
    def model_name(self) -> str:
        """Hub id this embedder was built from."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Vector length (384 for both MiniLM-L6 and bge-small)."""
        return self._dimension

    @property
    def max_tokens(self) -> int:
        """Tokens beyond this are dropped with no error (256 MiniLM, 512 BGE)."""
        return self._max_tokens

    def embed(self, texts: list[str]) -> FloatArray:
        """Return a (len(texts), dimension) float32 array of unit-norm rows.

        prompt="" overrides any default prompt stored in the model config.
        An empty input returns a (0, dimension) array instead of calling the model.
        """
        if not texts:
            return np.zeros((0, self._dimension), dtype=np.float32)
        vectors = self._model.encode(
            list(texts),
            prompt=NO_PREFIX,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def count_tokens(self, text: str) -> int:
        """Count tokens with the model's own tokenizer, [CLS] and [SEP] included."""
        return len(self._model.tokenizer.encode(text, add_special_tokens=True))
