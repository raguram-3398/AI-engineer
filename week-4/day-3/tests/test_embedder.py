"""Embedder wrapper: contract, exception translation, hub timeouts.

Fast tests use FakeSentenceTransformer through the `loader` seam. The slow test
downloads the real BGE model: run it with `pytest -m slow`.
"""

import os
import sys
import types

import numpy as np
import pytest
from fakes import FakeSentenceTransformer

from embeddings.embedder import SentenceTransformerEmbedder, configure_hub_timeouts
from embeddings.exceptions import ModelLoadError
from embeddings.models import (
    BGE_NAME,
    HF_DOWNLOAD_TIMEOUT_ENV,
    HF_DOWNLOAD_TIMEOUT_S,
    HF_ETAG_TIMEOUT_ENV,
    HF_ETAG_TIMEOUT_S,
)

BGE_DIM: int = 384
BGE_MAX_TOKENS: int = 512


def _build(fake: FakeSentenceTransformer) -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder("fake/model", loader=lambda _name: fake)


def test_embed_returns_float32_and_forces_empty_prompt() -> None:
    fake = FakeSentenceTransformer(dimension=8)
    embedder = _build(fake)
    out = embedder.embed(["a", "b"])
    assert out.shape == (2, 8) and out.dtype == np.float32
    kwargs = fake.encode_kwargs[0]
    assert kwargs["prompt"] == ""  # overrides any default prompt in model config
    assert kwargs["normalize_embeddings"] is True


def test_embed_empty_list_skips_model() -> None:
    fake = FakeSentenceTransformer(dimension=8)
    out = _build(fake).embed([])
    assert out.shape == (0, 8)
    assert fake.encode_kwargs == []


def test_reads_dimension_from_old_api() -> None:
    embedder = _build(FakeSentenceTransformer(dimension=5, use_new_dimension_api=False))
    assert embedder.dimension == 5


def test_metadata_and_token_count() -> None:
    embedder = _build(FakeSentenceTransformer(dimension=8, max_seq_length=256))
    assert embedder.model_name == "fake/model"
    assert embedder.max_tokens == 256
    assert embedder.count_tokens("three word text") == 5  # + [CLS] [SEP]


@pytest.mark.parametrize(
    "error",
    [TimeoutError("read timed out"), OSError("offline"), RuntimeError("bad weights")],
)
def test_load_failures_become_model_load_error(error: Exception) -> None:
    def failing_loader(_name: str) -> FakeSentenceTransformer:
        raise error

    with pytest.raises(ModelLoadError) as info:
        SentenceTransformerEmbedder("fake/model", loader=failing_loader)
    assert info.value.__cause__ is error


@pytest.mark.parametrize(
    "fake",
    [
        FakeSentenceTransformer(dimension=None),
        FakeSentenceTransformer(max_seq_length=None),
    ],
)
def test_missing_model_metadata_is_load_error(fake: FakeSentenceTransformer) -> None:
    with pytest.raises(ModelLoadError, match="does not report"):
        _build(fake)


def test_empty_model_name_is_programmer_error() -> None:
    called: list[str] = []
    with pytest.raises(ValueError):
        SentenceTransformerEmbedder("  ", loader=lambda name: called.append(name))
    assert called == []


def test_hub_timeouts_set_as_whole_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(HF_DOWNLOAD_TIMEOUT_ENV, raising=False)
    monkeypatch.delenv(HF_ETAG_TIMEOUT_ENV, raising=False)
    monkeypatch.delitem(sys.modules, "huggingface_hub.constants", raising=False)
    configure_hub_timeouts()
    assert os.environ[HF_DOWNLOAD_TIMEOUT_ENV] == str(HF_DOWNLOAD_TIMEOUT_S)
    assert os.environ[HF_ETAG_TIMEOUT_ENV] == str(HF_ETAG_TIMEOUT_S)
    int(os.environ[HF_DOWNLOAD_TIMEOUT_ENV])  # the hub parses with int()


def test_hub_timeouts_patch_already_imported_hub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If huggingface_hub was imported first, env vars alone are too late."""
    monkeypatch.delenv(HF_DOWNLOAD_TIMEOUT_ENV, raising=False)
    monkeypatch.delenv(HF_ETAG_TIMEOUT_ENV, raising=False)
    fake_constants = types.SimpleNamespace(
        HF_HUB_DOWNLOAD_TIMEOUT=10, HF_HUB_ETAG_TIMEOUT=10
    )
    monkeypatch.setitem(sys.modules, "huggingface_hub.constants", fake_constants)
    configure_hub_timeouts()
    assert fake_constants.HF_HUB_DOWNLOAD_TIMEOUT == HF_DOWNLOAD_TIMEOUT_S
    assert fake_constants.HF_HUB_ETAG_TIMEOUT == HF_ETAG_TIMEOUT_S


def test_hub_timeouts_respect_user_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HF_DOWNLOAD_TIMEOUT_ENV, "120")
    monkeypatch.delitem(sys.modules, "huggingface_hub.constants", raising=False)
    configure_hub_timeouts()
    assert os.environ[HF_DOWNLOAD_TIMEOUT_ENV] == "120"


@pytest.mark.slow
def test_real_bge_contract() -> None:
    embedder = SentenceTransformerEmbedder(BGE_NAME)
    vectors = embedder.embed(["hello world", "goodbye"])
    assert embedder.dimension == BGE_DIM
    assert embedder.max_tokens == BGE_MAX_TOKENS
    assert vectors.shape == (2, BGE_DIM)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)
