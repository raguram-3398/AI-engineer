"""Orchestration only: load data, build each model once, run evals, print tables.

Run from week-4/day-3:  PYTHONPATH=src python -m embeddings.main
First run downloads both models (~90 MB MiniLM, ~130 MB BGE) from the HF Hub.
"""

import sys
import time
from pathlib import Path

from embeddings.data_io import load_passages, load_queries, load_triplets
from embeddings.embedder import SentenceTransformerEmbedder
from embeddings.evaluate import (
    evaluate_retrieval,
    score_triplets,
    summarize_triplets,
    unrelated_floor,
    verify_manual_cosine,
)
from embeddings.exceptions import EmbeddingError
from embeddings.models import (
    BGE_NAME,
    BGE_QUERY_PREFIX,
    COSINE_TOLERANCE,
    DATA_DIR_NAME,
    MINILM_NAME,
    NO_PREFIX,
    PASSAGES_FILE,
    PROJECT_ROOT_DEPTH,
    QUERIES_FILE,
    TEXTS_PER_TRIPLET,
    TRIPLETS_FILE,
    ModelSpec,
    RetrievalResult,
    TripletSummary,
)
from embeddings.report import (
    format_rank_grid,
    format_retrieval_table,
    format_triplet_table,
    rule,
)
from embeddings.similarity import with_query_prefix

MODEL_SPECS: tuple[ModelSpec, ...] = (
    ModelSpec(name=MINILM_NAME, query_prefix=NO_PREFIX),
    ModelSpec(name=BGE_NAME, query_prefix=BGE_QUERY_PREFIX),
)
_MS_PER_S: float = 1000.0


def _data_dir() -> Path:
    """week-4/day-3/data, resolved from this file's location."""
    return Path(__file__).resolve().parents[PROJECT_ROOT_DEPTH] / DATA_DIR_NAME


def main() -> None:
    """Run every eval for every model and print the README tables."""
    data = _data_dir()
    try:
        triplets = load_triplets(data / TRIPLETS_FILE)
        passages = load_passages(data / PASSAGES_FILE)
        queries = load_queries(data / QUERIES_FILE, {p.id for p in passages})
    except EmbeddingError as e:
        print(f"data error: {e}", file=sys.stderr)
        sys.exit(1)
    print(
        f"data: {len(triplets)} triplets, {len(passages)} passages, "
        f"{len(queries)} queries"
    )

    anchors = [t.anchor for t in triplets]
    summaries: list[TripletSummary] = []
    retrievals: list[RetrievalResult] = []

    for spec in MODEL_SPECS:
        print(rule(spec.name))
        started = time.perf_counter()
        try:
            embedder = SentenceTransformerEmbedder(spec.name)  # once per model
        except EmbeddingError as e:
            print(f"model error: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"loaded in {time.perf_counter() - started:.1f}s")

        longest_passage = max(embedder.count_tokens(p.text) for p in passages)
        longest_query = max(
            embedder.count_tokens(text)
            for text in with_query_prefix(
                [q.question for q in queries], spec.query_prefix
            )
        )
        print(
            f"dim={embedder.dimension}  max_tokens={embedder.max_tokens}  "
            f"longest passage={longest_passage} tok  "
            f"longest query (with this model's prefix)={longest_query} tok"
        )

        deviation = verify_manual_cosine(embedder, anchors)
        status = "OK" if deviation <= COSINE_TOLERANCE else "MISMATCH"
        print(
            f"manual vs dot vs matrix cosine, max deviation: {deviation:.2e} {status}"
        )

        started = time.perf_counter()
        results = score_triplets(embedder, triplets)
        ms_per_text = (
            (time.perf_counter() - started)
            * _MS_PER_S
            / (TEXTS_PER_TRIPLET * len(triplets))
        )
        print(f"embed latency: {ms_per_text:.1f} ms/text (batched, CPU/MPS)")

        floor = unrelated_floor(embedder, anchors)
        summaries.append(summarize_triplets(spec.name, results, floor))

        failed = [r for r in results if not r.passed]
        print(f"triplets failed: {len(failed)}/{len(results)}")
        for r in failed:
            print(
                f"  [{r.triplet.category}] pos={r.pos_score:.3f} "
                f"neg={r.neg_score:.3f}  {r.triplet.anchor}"
            )

        retrievals.append(evaluate_retrieval(embedder, passages, queries, NO_PREFIX))
        if spec.query_prefix:
            retrievals.append(
                evaluate_retrieval(embedder, passages, queries, spec.query_prefix)
            )

    print(rule("Triplets: pass rate by category (higher = better)"))
    print(format_triplet_table(summaries))
    print(rule("Retrieval (BGE run twice: without and with query instruction)"))
    print(format_retrieval_table(retrievals))
    print(rule("Rank of the correct passage per query (* = not rank 1)"))
    print(format_rank_grid(retrievals, queries))


if __name__ == "__main__":
    main()
