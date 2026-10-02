from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

FloatArray = NDArray[np.float32]

class Embedder:
    """Generate text embeddings using a SentenceTransformer model."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedding model."""
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str], *, normalize: bool = True) -> FloatArray:
        """Convert text into normalized float32 embedding vectors."""
        embeddings = self._model.encode(list(texts), normalize_embeddings = normalize, convert_to_numpy = True)
        return np.asarray(embeddings, dtype = np.float32)