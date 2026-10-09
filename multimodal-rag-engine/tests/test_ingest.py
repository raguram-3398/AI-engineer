"""Ingest edge cases that occur in the real data: page alignment, page-safe chunks,
the 510-token limit, sentences longer than the limit."""

import json
import re

import pandas as pd
import pytest
from transformers import AutoTokenizer
from unstructured.documents.elements import NarrativeText, Title

from multimodal_rag.config import (
    CHUNKS_PATH,
    CORPUS_INDEX_PATH,
    EMBED_MODEL,
    MAX_TOKENS,
    PDF_DIR,
)
from multimodal_rag.ingest import Page, chunk_page, load_pdf, split_to_limit

needs_dataset = pytest.mark.skipif(
    not PDF_DIR.is_dir(), reason="dataset is gitignored; not present here"
)


@pytest.fixture(scope="session")
def count():
    tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
    return lambda t: len(tok(t, add_special_tokens=False, verbose=False)["input_ids"])


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", text.lower()))


def _best_dataset_page(page: Page, n_pages: int) -> tuple[int, dict[int, float]]:
    """Which dataset page (same number or a neighbour) shares most words with `page`."""
    gold = (
        pd.read_parquet(CORPUS_INDEX_PATH)
        .query("doc_id == @page.doc_id")
        .set_index("page_number_in_doc")["markdown"]
    )
    ours = _words(page.text)
    overlap = {
        g: len(ours & _words(gold[g])) / len(ours)
        for g in range(max(0, page.page - 1), min(n_pages, page.page + 2))
    }
    return max(overlap, key=overlap.get), overlap


@needs_dataset
def test_text_pages_align_with_dataset_page_numbers() -> None:
    """Each text-layer page matches the dataset's page with the same 0-indexed
    number better than its neighbours (an off-by-one would match a neighbour)."""
    n_pages = 15
    pages = load_pdf(PDF_DIR / "AAMkeynoteChoe2021.pdf", n_pages)
    assert [p.page for p, _ in pages] == list(range(n_pages))
    for page, _ in pages:
        if not page.ocr:
            best, overlap = _best_dataset_page(page, n_pages)
            assert best == page.page, overlap


@needs_dataset
def test_ocr_page_aligns_with_dataset_page_number() -> None:
    """Page 1 of this deck has no text layer. OCR renders it with pdftoppm, which
    is 1-indexed; without the +1 we would OCR page 0 and match it instead."""
    n_pages = 12
    page, elements = load_pdf(PDF_DIR / "Tmorton_NASEM_SOW_4.pdf", n_pages)[1]
    assert page.ocr and elements == []
    best, overlap = _best_dataset_page(page, n_pages)
    assert best == 1, overlap


def test_split_packs_sentences_under_limit(count) -> None:
    text = " ".join(f"Sentence number {i} is about drug approvals." for i in range(200))
    pieces = split_to_limit(text, count)
    assert len(pieces) > 1
    assert all(count(p) <= MAX_TOKENS for p in pieces)
    assert " ".join(pieces).split() == text.split()  # nothing lost or reordered


def test_split_breaks_a_single_oversized_sentence_by_words(count) -> None:
    # one sentence, ~1,600 tokens
    sentence = " ".join(["pharmacovigilance"] * 400) + "."
    pieces = split_to_limit(sentence, count)
    assert len(pieces) >= 3
    assert all(count(p) <= MAX_TOKENS for p in pieces)
    assert " ".join(pieces).split() == sentence.split()


def test_book_page_chunks_stay_on_page_and_under_limit(count) -> None:
    paragraph = " ".join(
        f"Resistance finding {i} was reported in 2019." for i in range(60)
    )
    elements = [Title("Chapter 3"), NarrativeText(paragraph), Title("Summary")]
    text = "\n\n".join(e.text for e in elements)
    chunks = chunk_page(Page("book", 41, text, ocr=False), elements, True, count)
    assert len(chunks) >= 2
    assert [c.chunk_id for c in chunks] == [f"book-41-{n}" for n in range(len(chunks))]
    assert all(c.page == 41 and c.doc_id == "book" for c in chunks)
    assert all(c.n_tokens == count(c.text) <= MAX_TOKENS for c in chunks)


def test_empty_page_yields_no_chunk(count) -> None:
    assert chunk_page(Page("deck", 3, "", ocr=True), [], False, count) == []


@pytest.mark.skipif(not CHUNKS_PATH.is_file(), reason="run ingest first")
def test_written_chunks_respect_the_contract() -> None:
    """Regression check on the committed chunks.jsonl."""
    rows = [json.loads(line) for line in CHUNKS_PATH.open(encoding="utf-8")]
    ids = [r["chunk_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert all(r["chunk_id"].startswith(f"{r['doc_id']}-{r['page']}-") for r in rows)
    assert all(0 < r["n_tokens"] <= MAX_TOKENS for r in rows)
