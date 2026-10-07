from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from vectorstore.embedder import BgeEmbedder
from vectorstore.models import (
    BGE_QUERY_PREFIX,
    DIMENSION,
    EmbeddingModelMismatchError,
    VectorStoreError,
)


class RecordingModel:
    def __init__(self, dim: int = DIMENSION) -> None:
        self.dim = dim
        self.seen: list[list[str]] = []

    def get_sentence_embedding_dimension(self) -> int:
        return self.dim

    def encode(self, texts: list[str], **kwargs: Any) -> np.ndarray:
        assert kwargs["prompt"] == "" and kwargs["normalize_embeddings"] is True
        self.seen.append(texts)
        return np.ones((len(texts), self.dim), dtype=np.float32)


def test_query_gets_prefix_documents_do_not() -> None:
    model = RecordingModel()
    emb = BgeEmbedder("bge", loader=lambda _: model)
    emb.embed_documents(["passage"])
    emb.embed_query("question")
    assert model.seen == [["passage"], [BGE_QUERY_PREFIX + "question"]]


def test_empty_documents_skip_the_model() -> None:
    model = RecordingModel()
    assert BgeEmbedder("bge", loader=lambda _: model).embed_documents([]) == []
    assert model.seen == []


def test_supports_renamed_dimension_method() -> None:
    model = SimpleNamespace(get_embedding_dimension=lambda: DIMENSION)
    assert BgeEmbedder("bge", loader=lambda _: model).model_id == "bge"


def test_wrong_dimension_model_is_rejected() -> None:
    with pytest.raises(EmbeddingModelMismatchError, match="768"):
        BgeEmbedder("big", loader=lambda _: RecordingModel(dim=768))


def test_load_failure_is_translated() -> None:
    def boom(_: str) -> Any:
        raise OSError("offline")

    with pytest.raises(VectorStoreError, match="offline"):
        BgeEmbedder("bge", loader=boom)
