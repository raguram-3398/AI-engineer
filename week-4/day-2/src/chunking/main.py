"""Day 23: load three document types, chunk one PDF three ways, compare with numbers."""

from pathlib import Path

from langchain_core.documents import Document

from chunking.chunkers import (
    annotate_tokens,
    chunk_fixed,
    chunk_recursive,
    chunk_semantic,
)
from chunking.embedder import Embedder
from chunking.evaluate import chunk_stats, hit_at_k
from chunking.exceptions import LoaderError
from chunking.loaders import load_eval_queries, load_pdf, load_text, load_web
from chunking.models import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    PREVIEW_CHARS,
    PREVIEW_CHUNKS,
    SEMANTIC_BREAKPOINT_PERCENTILE,
    TOP_K,
    ChunkStats,
)

DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"
PDF_PATH: Path = DATA_DIR / "sample.pdf"
TEXT_PATH: Path = DATA_DIR / "sample.txt"
QUERIES_PATH: Path = DATA_DIR / "eval_queries.json"
WEB_URL: str = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"


def print_loaded(label: str, docs: list[Document]) -> None:
    """One summary line per loaded source."""
    total_chars = sum(len(d.page_content) for d in docs)
    print(
        f"{label:<5} {len(docs):>3} docs  {total_chars:>8,} chars  "
        f"source={docs[0].metadata['source']}"
    )


def print_previews(chunks: list[Document]) -> None:
    """Show the first few chunks so boundaries can be compared by eye."""
    strategy = chunks[0].metadata["strategy"]
    print(f"\n--- {strategy.upper()} (first {PREVIEW_CHUNKS} chunks) ---")
    for chunk in chunks[:PREVIEW_CHUNKS]:
        meta = chunk.metadata
        flat = " ".join(chunk.page_content.split())
        print(f"[#{meta['chunk_index']} p{meta['page']} {meta['token_count']} tok]")
        print(f"  START: {flat[:PREVIEW_CHARS]}")
        print(f"  END:   ...{flat[-PREVIEW_CHARS:]}")


def print_table(rows: list[tuple[ChunkStats, float]], max_tokens: int) -> None:
    """Print a Markdown table, ready to paste into the README."""
    print(
        f"\nEmbedder token limit: {max_tokens}   chunk_size={CHUNK_SIZE} chars   "
        f"overlap={CHUNK_OVERLAP}   k={TOP_K}\n"
    )
    print(
        "| Strategy | Chunks | Min tok | Mean tok | Max tok "
        "| Over limit | Mid-sentence | hit@k |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for s, hit_rate in rows:
        print(
            f"| {s.strategy} | {s.count} | {s.min_tokens} | {s.mean_tokens:.0f} | "
            f"{s.max_tokens} | {s.over_limit} | {s.mid_sentence} | {hit_rate:.2f} |"
        )


def main() -> None:
    """Load, chunk, measure, print."""
    embedder = Embedder()  # constructed once, reused everywhere
    print(
        f"Embedding model: {embedder.model_name} (max {embedder.max_tokens} tokens)\n"
    )

    try:
        pdf_docs = load_pdf(PDF_PATH)
        print_loaded("PDF", pdf_docs)
        print_loaded("TEXT", load_text(TEXT_PATH))
        queries = load_eval_queries(QUERIES_PATH)
    except LoaderError as e:
        print(f"Cannot continue: {e}")
        raise SystemExit(1) from e

    try:
        print_loaded("WEB", load_web(WEB_URL))
    except LoaderError as e:
        print(f"WEB   skipped: {e}")  # optional source; never blocks the comparison

    strategies = [
        chunk_fixed(pdf_docs, CHUNK_SIZE, CHUNK_OVERLAP),
        chunk_recursive(pdf_docs, CHUNK_SIZE, CHUNK_OVERLAP),
        chunk_semantic(pdf_docs, embedder, SEMANTIC_BREAKPOINT_PERCENTILE),
    ]

    rows: list[tuple[ChunkStats, float]] = []
    for raw_chunks in strategies:
        chunks = annotate_tokens(raw_chunks, embedder)
        print_previews(chunks)
        rows.append(
            (
                chunk_stats(chunks, embedder.max_tokens),
                hit_at_k(chunks, queries, embedder, TOP_K),
            )
        )

    print_table(rows, embedder.max_tokens)


if __name__ == "__main__":
    main()
