"""Day 23 tests: loaders, chunkers, and evaluators. No network, no model download."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from fakes import FakeEmbedder
from langchain_core.documents import Document

from chunking.chunkers import (
    annotate_tokens,
    chunk_fixed,
    chunk_recursive,
    chunk_semantic,
    find_breakpoints,
)
from chunking.evaluate import chunk_stats, hit_at_k, is_mid_sentence
from chunking.exceptions import EmptyDocumentError, FetchError, LoaderError
from chunking.loaders import load_pdf, load_text, load_web
from chunking.models import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SEMANTIC_BREAKPOINT_PERCENTILE,
    EvalQuery,
)

REQUIRED_KEYS: set[str] = {
    "source",
    "page",
    "doc_type",
    "strategy",
    "chunk_index",
    "char_count",
}
TEST_SIZE: int = 50
TEST_OVERLAP: int = 10

SizeChunker = Callable[[list[Document], int, int], list[Document]]


def make_page(text: str, page: int = 1) -> Document:
    """A loader-shaped Document for chunker tests."""
    return Document(
        page_content=text,
        metadata={"source": "test.pdf", "page": page, "doc_type": "pdf"},
    )


LONG_PAGE: Document = make_page("Retrieval quality depends on chunking. " * 20, page=3)


# --- Loaders -------------------------------------------------------------------


def test_load_text_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(LoaderError, match="File not found"):
        load_text(tmp_path / "nope.txt")


def test_load_text_empty_file_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_text("   \n  ", encoding="utf-8")
    with pytest.raises(EmptyDocumentError):
        load_text(empty)


def test_load_text_sets_metadata(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello world", encoding="utf-8")
    [doc] = load_text(path)
    assert doc.metadata == {"source": str(path), "page": 1, "doc_type": "text"}


def test_load_pdf_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(LoaderError, match="File not found"):
        load_pdf(tmp_path / "nope.pdf")


def test_load_web_timeout_raises_fetch_error() -> None:
    with (
        patch("chunking.loaders.requests.get", side_effect=requests.Timeout),
        pytest.raises(FetchError, match="Timed out"),
    ):
        load_web("https://example.com", timeout=0.01)


def test_load_web_passes_timeout_to_requests() -> None:
    with (
        patch(
            "chunking.loaders.requests.get", side_effect=requests.Timeout
        ) as mock_get,
        pytest.raises(FetchError),
    ):
        load_web("https://example.com", timeout=4.0)
    assert mock_get.call_args.kwargs["timeout"] == 4.0


# --- Chunkers ------------------------------------------------------------------


@pytest.mark.parametrize("chunker", [chunk_fixed, chunk_recursive])
def test_size_based_chunkers_preserve_metadata(chunker: SizeChunker) -> None:
    chunks = chunker([LONG_PAGE], TEST_SIZE, TEST_OVERLAP)
    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert REQUIRED_KEYS <= chunk.metadata.keys()
        assert chunk.metadata["page"] == 3
        assert chunk.metadata["chunk_index"] == i


@pytest.mark.parametrize("chunker", [chunk_fixed, chunk_recursive])
def test_short_page_yields_one_chunk(chunker: SizeChunker) -> None:
    chunks = chunker([make_page("Short page.")], CHUNK_SIZE, CHUNK_OVERLAP)
    assert len(chunks) == 1
    assert chunks[0].page_content == "Short page."


def test_fixed_chunks_overlap() -> None:
    chunks = chunk_fixed([LONG_PAGE], TEST_SIZE, TEST_OVERLAP)
    tail_of_first = chunks[0].page_content[-TEST_OVERLAP:]
    assert chunks[1].page_content.startswith(tail_of_first)


def test_chunkers_do_not_mutate_input() -> None:
    original = dict(LONG_PAGE.metadata)
    chunk_fixed([LONG_PAGE], TEST_SIZE, TEST_OVERLAP)
    assert LONG_PAGE.metadata == original


def test_invalid_overlap_raises() -> None:
    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_fixed([LONG_PAGE], TEST_SIZE, TEST_SIZE)


def test_find_breakpoints_single_sentence_has_none(fake_embedder: FakeEmbedder) -> None:
    vectors = fake_embedder.embed(["Only one sentence here."])
    assert find_breakpoints(vectors, SEMANTIC_BREAKPOINT_PERCENTILE) == []


def test_semantic_splits_on_topic_shift(fake_embedder: FakeEmbedder) -> None:
    page = make_page(
        "Cats purr softly. Cats sleep often. "
        "Databases store rows. Databases index rows."
    )
    chunks = chunk_semantic([page], fake_embedder, SEMANTIC_BREAKPOINT_PERCENTILE)
    assert [c.page_content for c in chunks] == [
        "Cats purr softly. Cats sleep often.",
        "Databases store rows. Databases index rows.",
    ]


def test_annotate_flags_over_limit(fake_embedder: FakeEmbedder) -> None:
    short = make_page("five words in this chunk")
    long = make_page("word " * 40)
    annotated = annotate_tokens([short, long], fake_embedder)
    assert annotated[0].metadata["over_limit"] is False
    assert annotated[1].metadata["over_limit"] is True


# --- Evaluation ----------------------------------------------------------------


def test_is_mid_sentence() -> None:
    assert is_mid_sentence("This stops in the mid") is True
    assert is_mid_sentence("This ends cleanly.  ") is False


def test_chunk_stats_counts(fake_embedder: FakeEmbedder) -> None:
    raw = chunk_fixed([LONG_PAGE], TEST_SIZE, TEST_OVERLAP)
    stats = chunk_stats(annotate_tokens(raw, fake_embedder), fake_embedder.max_tokens)
    assert stats.strategy == "fixed"
    assert stats.count == len(raw)
    assert stats.over_limit == 0
    assert stats.mid_sentence > 0  # a 50-char window rarely lands on a period


def test_hit_at_k_finds_and_misses(fake_embedder: FakeEmbedder) -> None:
    chunks = [
        make_page("Cats purr when they are content."),
        make_page("Postgres stores rows in tables."),
        make_page("The capital of France is Paris."),
    ]
    found = [EvalQuery("Where does Postgres store rows?", "stores rows in tables")]
    missing = [EvalQuery("Where does Postgres store rows?", "not in any chunk")]
    assert hit_at_k(chunks, found, fake_embedder, k=1) == 1.0
    assert hit_at_k(chunks, missing, fake_embedder, k=3) == 0.0


def test_hit_at_k_rejects_bad_k(fake_embedder: FakeEmbedder) -> None:
    with pytest.raises(ValueError, match="k must be positive"):
        hit_at_k([LONG_PAGE], [EvalQuery("q", "a")], fake_embedder, k=0)


# --- Integration (real model) ----------------------------------------------------


@pytest.mark.slow
def test_recursive_at_chunk_size_never_exceeds_real_limit() -> None:
    """The edge case that matters today, checked against the real tokenizer."""
    pytest.importorskip("sentence_transformers")
    from chunking.embedder import Embedder

    embedder = Embedder()
    text = "Retrieval augmented generation grounds answers in source documents. " * 60
    chunks = annotate_tokens(
        chunk_recursive([make_page(text)], CHUNK_SIZE, CHUNK_OVERLAP), embedder
    )
    assert all(not c.metadata["over_limit"] for c in chunks)
