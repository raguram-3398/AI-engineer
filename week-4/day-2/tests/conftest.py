"""Shared fixtures."""

import pytest
from fakes import FakeEmbedder


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    """A fresh FakeEmbedder per test."""
    return FakeEmbedder()
