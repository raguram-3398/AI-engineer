"""Evaluate retrieval (free, no Claude): page-level recall@10 and NDCG@10 on all
364 English queries, the fixed eval sample, and the abstain threshold.

Run:  python -m multimodal_rag.evaluate
"""

import json
import logging
import math
import random
from collections import defaultdict

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from multimodal_rag.config import (
    ABSTAIN_PERCENTILE,
    ABSTAIN_SCORE,
    CORPUS_INDEX_PATH,
    EVAL_K,
    INDEX_NAME,
    PROJECT_DIR,
    QRELS_PATH,
    QUERIES_PATH,
    SAMPLE_PATH,
    SAMPLE_SEED,
    SAMPLE_SIZE,
    UNANSWERABLE_PATH,
    VISUAL_CONTENT,
)
from multimodal_rag.contracts import Hit
from multimodal_rag.retrieve import Retriever

Page = tuple[str, int]  # (doc_id, 0-indexed page)


def load_queries() -> pd.DataFrame:
    """The 364 English queries with `gold` = {(doc_id, page): grade 1 or 2} and
    `visual` = a relevant page holds chart, infographic, table or image content."""
    q = pd.read_parquet(QUERIES_PATH).query("language == 'english'").copy()
    q["query_id"] = q["query_id"].astype(int)
    corpus = pd.read_parquet(CORPUS_INDEX_PATH).set_index("corpus_id")
    qrels = pd.read_parquet(QRELS_PATH)
    qrels = qrels[qrels["query_id"].isin(q["query_id"])]

    gold: dict[int, dict[Page, int]] = defaultdict(dict)
    for r in qrels.itertuples():
        row = corpus.loc[r.corpus_id]
        gold[r.query_id][(row.doc_id, int(row.page_number_in_doc))] = int(r.score)
    q["gold"] = q["query_id"].map(gold)
    q["visual"] = q["content_type"].map(lambda ct: bool(VISUAL_CONTENT & set(ct)))
    return q.reset_index(drop=True)


def make_sample(queries: pd.DataFrame) -> dict:
    """The fixed eval sample: SAMPLE_SIZE answerable query ids + all unanswerable ids.

    Strata = query_type_for_generation x visual; each stratum gets its share of
    SAMPLE_SIZE by largest remainder. Written once to SAMPLE_PATH; if the file
    exists it is returned unchanged, so the sample never moves after Day 28.
    """
    if SAMPLE_PATH.is_file():
        return json.loads(SAMPLE_PATH.read_text())

    strata = queries.groupby(["query_type_for_generation", "visual"])["query_id"]
    groups = {key: sorted(ids) for key, ids in strata}
    exact = {k: SAMPLE_SIZE * len(ids) / len(queries) for k, ids in groups.items()}
    alloc = {k: int(v) for k, v in exact.items()}
    by_remainder = sorted(exact, key=lambda k: exact[k] - alloc[k], reverse=True)
    for k in by_remainder[: SAMPLE_SIZE - sum(alloc.values())]:
        alloc[k] += 1

    rng = random.Random(SAMPLE_SEED)
    answerable = sorted(
        qid for k in sorted(groups) for qid in rng.sample(groups[k], alloc[k])
    )
    unanswerable = [
        json.loads(line)["id"] for line in UNANSWERABLE_PATH.open(encoding="utf-8")
    ]
    sample = {
        "seed": SAMPLE_SEED,
        "answerable": answerable,
        "unanswerable": unanswerable,
    }
    SAMPLE_PATH.write_text(json.dumps(sample, indent=1) + "\n")
    return sample


def ranked_pages(hits: list[Hit], k: int = EVAL_K) -> list[Page]:
    """First k distinct (doc_id, page) in hit order: a book page yields ~3 chunks,
    so scoring chunks directly would crowd out other pages."""
    pages: list[Page] = []
    for h in hits:
        p = (h.chunk.doc_id, h.chunk.page)
        if p not in pages:
            pages.append(p)
        if len(pages) == k:
            break
    return pages


def recall_at_k(ranked: list[Page], gold: dict[Page, int], k: int = EVAL_K) -> float:
    """Share of all gold pages found in the top k (queries with > k gold pages
    cannot reach 1.0)."""
    return len(set(ranked[:k]) & gold.keys()) / len(gold)


def ndcg_at_k(ranked: list[Page], gold: dict[Page, int], k: int = EVAL_K) -> float:
    """NDCG with gain = qrel grade (1 critically, 2 fully relevant)."""
    dcg = sum(gold.get(p, 0) / math.log2(i + 2) for i, p in enumerate(ranked[:k]))
    ideal = sorted(gold.values(), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg


def abstain_threshold(top1: list[float], pct: float = ABSTAIN_PERCENTILE) -> float:
    """Top-1 score below which `pct`% of answerable queries fall."""
    return float(np.percentile(top1, pct))


def main() -> None:
    """Retrieval baseline on all 364 queries; threshold from the 304 non-sample."""
    logging.basicConfig(level=logging.WARNING)
    load_dotenv(PROJECT_DIR / ".env")
    queries = load_queries()
    sample = make_sample(queries)
    in_sample = queries["query_id"].isin(sample["answerable"])
    unanswerable = [
        json.loads(line)["query"] for line in UNANSWERABLE_PATH.open(encoding="utf-8")
    ]

    retriever = Retriever()
    rows = []
    for q in queries.itertuples():
        hits = retriever.search(q.query)
        ranked = ranked_pages(hits)
        rows.append(
            {
                "recall": recall_at_k(ranked, q.gold),
                "ndcg": ndcg_at_k(ranked, q.gold),
                "top1": hits[0].score,
                "short": len(ranked) < EVAL_K,
            }
        )
    res = pd.DataFrame(rows)
    ua_top1 = [retriever.search(u)[0].score for u in unanswerable]

    threshold = abstain_threshold(res.loc[~in_sample, "top1"].tolist())
    sample_top1 = res.loc[in_sample, "top1"]
    n_visual = int(queries.loc[in_sample, "visual"].sum())
    n_many_gold = int((queries.gold.map(len) > EVAL_K).sum())
    print(f"index {INDEX_NAME}, {len(queries)} queries, page-level @{EVAL_K}")
    print(f"recall@{EVAL_K}: {res.recall.mean():.4f}")
    print(f"NDCG@{EVAL_K}:   {res.ndcg.mean():.4f}")
    print(f"queries with < {EVAL_K} distinct pages in top chunks: {res.short.sum()}")
    print(f"queries with > {EVAL_K} gold pages: {n_many_gold}")
    print(
        f"sample: {len(sample['answerable'])} answerable ({n_visual} visual)"
        f" + {len(sample['unanswerable'])} unanswerable"
    )
    print(
        f"\nthreshold = p{ABSTAIN_PERCENTILE:g} of top-1 on the"
        f" {int((~in_sample).sum())} non-sample queries: {threshold:.4f}"
    )
    print(f"ABSTAIN_SCORE in config: {ABSTAIN_SCORE:.4f}")
    print("measured at that threshold (never tuned on these):")
    n_low = int((sample_top1 < threshold).sum())
    print(f"  sample answerable below it: {n_low}/{len(sample_top1)}")
    n_ua = sum(s < threshold for s in ua_top1)
    print(f"  unanswerable below it: {n_ua}/{len(ua_top1)}")
    print(
        f"  top-1 ranges  answerable {res.top1.min():.3f}-{res.top1.max():.3f}"
        f"  unanswerable {min(ua_top1):.3f}-{max(ua_top1):.3f}"
    )


if __name__ == "__main__":
    main()
