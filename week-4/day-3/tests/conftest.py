"""Shared fixtures."""

from pathlib import Path

import pytest
from fakes import FakeEmbedder

DATA_DIR: Path = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    """A fresh FakeEmbedder per test."""
    return FakeEmbedder()


@pytest.fixture
def data_dir() -> Path:
    """The real data folder shipped with the project."""
    return DATA_DIR
