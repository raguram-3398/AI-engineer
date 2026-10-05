"""SentenceTransformer wrapper satisfying EmbedderProtocol.

Construct ONCE per process. Loading the model costs hundreds of MB of RAM;
constructing it per request is the Day 16/18 client-per-request mistake again.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from chunking.models import EMBED_MODEL_NAME, FloatArray


class Embedder:
    """Local embedding model with a token counter that matches what it embeds."""

    def __init__(self, model_name: str = EMBED_MODEL_NAME) -> None:
        """Load the model. Slow and memory-heavy — do this once."""
        self.model_name: str = model_name
        self._model = SentenceTransformer(model_name)

    @property
    def max_tokens(self) -> int:
        """Tokens beyond this are dropped before embedding, with no error."""
        return int(self._model.max_seq_length)

    def embed(self, texts: list[str]) -> FloatArray:
        """Return unit-normalized vectors, so dot product equals cosine similarity."""
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.astype(np.float32)

    def count_tokens(self, text: str) -> int:
        """Count tokens with the model's own tokenizer, including [CLS] and [SEP]."""
        return len(self._model.tokenizer.encode(text, add_special_tokens=True))
