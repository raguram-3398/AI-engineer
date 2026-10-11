"""Evaluate the pipeline.

Free retrieval eval (no Claude): page-level recall@10 and NDCG@10 on all 364
English queries, split by visual content type, and the fixed eval sample.
    python -m multimodal_rag.evaluate

Full eval (Claude): answers the fixed 60 + 20 sample, scores it with RAGAS, the
Haiku judge and the abstain rule, gates it against the last passed run and
appends it to data/scores.jsonl.
    python -m multimodal_rag.evaluate full "label"
"""

import json
import logging
import math
import random
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime

import anthropic
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from multimodal_rag.answer import answer, cost_usd
from multimodal_rag.config import (
    ANSWER_K,
    CLAUDE_MODEL,
    CLAUDE_TIMEOUT_S,
    CORPUS_INDEX_PATH,
    EMBED_MODEL,
    EVAL_K,
    EVAL_WORKERS,
    GATE_THRESHOLDS,
    INDEX_NAME,
    JUDGE_MAX_TOKENS,
    PRICE_IN_PER_MTOK,
    PRICE_OUT_PER_MTOK,
    PROJECT_DIR,
    QRELS_PATH,
    QUERIES_PATH,
    RAGAS_MAX_TOKENS,
    SAMPLE_PATH,
    SAMPLE_SEED,
    SAMPLE_SIZE,
    SCORES_PATH,
    UNANSWERABLE_PATH,
    VISION_CONTENT,
    VISUAL_CONTENT,
)
from multimodal_rag.contracts import Answer, Hit
from multimodal_rag.retrieve import QueryError, Retriever

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


def recall_by_content(ret: pd.DataFrame) -> dict[str, float]:
    """recall@10 over the queries whose relevant pages hold each VISION_CONTENT
    type (a query can count for several). Logged, not gated."""
    return {
        f"recall@10 {t}": float(
            ret.recall[ret.content_type.map(lambda c: t in c)].mean()
        )
        for t in VISION_CONTENT
    }


def retrieval_scores(queries: pd.DataFrame, retriever: Retriever) -> pd.DataFrame:
    """Per query: page-level recall@10, NDCG@10, whether the top chunks held
    fewer than EVAL_K distinct pages, and the query's content types."""
    rows = []
    for q in queries.itertuples():
        hits = retriever.search(q.query)
        ranked = ranked_pages(hits)
        rows.append(
            {
                "recall": recall_at_k(ranked, q.gold),
                "ndcg": ndcg_at_k(ranked, q.gold),
                "short": len(ranked) < EVAL_K,
                "content_type": set(q.content_type),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- full eval


@dataclass(frozen=True)
class Result:
    """One sample question run through the pipeline. `reference` is None for
    the unanswerable queries; `hits` are the ANSWER_K chunks Claude saw."""

    query_id: str
    question: str
    reference: str | None
    hits: list[Hit]
    answer: Answer


def run_sample(
    queries: pd.DataFrame,
    sample: dict,
    retriever: Retriever,
    client: anthropic.Anthropic,
) -> list[Result]:
    """Answer the 60 answerable then the 20 unanswerable sample queries.

    Search runs in order (one local embed + one Pinecone call each); the Claude
    calls run EVAL_WORKERS at a time. Raises QueryError like `answer`, naming
    the query.
    """
    by_id = queries.set_index("query_id")
    items = [
        (str(i), by_id.at[i, "query"], by_id.at[i, "answer"])
        for i in sample["answerable"]
    ]
    for line in UNANSWERABLE_PATH.open(encoding="utf-8"):
        u = json.loads(line)
        if u["id"] in sample["unanswerable"]:
            items.append((u["id"], u["query"], None))

    def answer_one(item: tuple, item_hits: list[Hit]) -> Answer:
        try:
            return answer(item[1], item_hits, client)
        except QueryError as e:
            raise QueryError(f"query {item[0]}: {e}") from e

    hits = [retriever.search(q) for _, q, _ in items]
    with ThreadPoolExecutor(EVAL_WORKERS) as pool:
        answers = list(pool.map(answer_one, items, hits))
    return [
        Result(qid, q, ref, h[:ANSWER_K], a)
        for (qid, q, ref), h, a in zip(items, hits, answers)
    ]


def answered(a: Answer) -> bool:
    """Claude answered from the documents: neither an abstain nor a refusal."""
    return not (a.abstained or a.refused)


def ragas_scores(results: list[Result]) -> tuple[pd.DataFrame, float]:
    """RAGAS scores per answerable result, plus the RAGAS dollar cost.

    Context precision and context recall (retrieved chunks vs the reference) are
    scored on every answerable result. Faithfulness and answer relevancy judge
    the answer text, so they are scored only where the pipeline answered: an
    abstain has no claims to check, yet RAGAS scored false abstains 0.65
    faithfulness on average (up to 1.0) on Day 29. Abstains are NaN in those two
    columns by design and are counted by `abstain_scores` instead.

    Judge = Haiku through LangChain (`bypass_temperature`: Haiku 5.5 rejects the
    parameter); embeddings = BGE, for answer relevancy only. A score RAGAS could
    not compute is also NaN; the caller reports those separately.
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas import EvaluationDataset, RunConfig, evaluate
    from ragas.cost import get_token_usage_for_anthropic
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        answer_relevancy,
        faithfulness,
    )

    llm = LangchainLLMWrapper(
        ChatAnthropic(
            model=CLAUDE_MODEL, max_tokens=RAGAS_MAX_TOKENS, timeout=CLAUDE_TIMEOUT_S
        ),
        bypass_temperature=True,
    )
    emb = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    )

    def score(rows: list[Result], metrics: list) -> tuple[pd.DataFrame, float]:
        data = EvaluationDataset.from_list(
            [
                {
                    "user_input": r.question,
                    "response": r.answer.text,
                    "retrieved_contexts": [h.chunk.text for h in r.hits],
                    "reference": r.reference,
                }
                for r in rows
            ]
        )
        out = evaluate(
            data,
            metrics=metrics,
            llm=llm,
            embeddings=emb,
            run_config=RunConfig(max_workers=EVAL_WORKERS),
            token_usage_parser=get_token_usage_for_anthropic,
            show_progress=False,
        )
        cost = out.total_cost(
            cost_per_input_token=PRICE_IN_PER_MTOK / 1e6,
            cost_per_output_token=PRICE_OUT_PER_MTOK / 1e6,
        )
        return out.to_pandas(), float(cost)

    answerable = [r for r in results if r.reference is not None]
    scored = [i for i, r in enumerate(answerable) if answered(r.answer)]
    ctx, ctx_cost = score(
        answerable, [LLMContextPrecisionWithReference(), LLMContextRecall()]
    )
    ans, ans_cost = score(
        [answerable[i] for i in scored], [faithfulness, answer_relevancy]
    )
    df = pd.DataFrame(
        {
            "faithfulness": np.nan,
            "answer_relevancy": np.nan,
            "context_precision": ctx["llm_context_precision_with_reference"],
            "context_recall": ctx["context_recall"],
        }
    )
    df.loc[scored, "faithfulness"] = ans["faithfulness"].to_numpy()
    df.loc[scored, "answer_relevancy"] = ans["answer_relevancy"].to_numpy()
    return df, ctx_cost + ans_cost


JUDGE_CRITERIA = ("faithfulness", "relevance", "completeness")
JUDGE_PROMPT = """You grade an answer to a question about FDA documents against a \
reference answer written from the same documents. Score each criterion 1-5.

- faithfulness: are the answer's facts consistent with the reference? 5 = nothing \
contradicts it, 1 = its main claim contradicts it. Facts the reference does not \
mention are not errors.
- relevance: does it answer the question that was asked? 5 = directly, 1 = not at all.
- completeness: does it contain the reference's key facts? 5 = all, 1 = none.

Do not reward length. If the answer says the documents do not contain the answer, \
score 1 on all three.

<question>{question}</question>
<reference>{reference}</reference>
<answer>{answer}</answer>"""
JUDGE_TOOL = {
    "name": "record_scores",
    "description": "Record the 1-5 scores and a one-sentence reason.",
    "input_schema": {
        "type": "object",
        "properties": {
            **{c: {"type": "integer", "enum": [1, 2, 3, 4, 5]} for c in JUDGE_CRITERIA},
            "reason": {"type": "string"},
        },
        "required": [*JUDGE_CRITERIA, "reason"],
    },
}


def judge(
    question: str, reference: str, ans: Answer, client: anthropic.Anthropic
) -> tuple[dict, float]:
    """Haiku scores `ans` 1-5 on JUDGE_CRITERIA against the reference answer.

    Returns ({criterion: score, "reason": str}, cost_usd). The tool call is forced,
    so the scores arrive as JSON matching JUDGE_TOOL. Raises QueryError on an API
    error or a score outside 1-5.
    """
    prompt = JUDGE_PROMPT.format(
        question=question, reference=reference, answer=ans.text
    )
    try:
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=JUDGE_MAX_TOKENS,
            tools=[JUDGE_TOOL],
            tool_choice={"type": "tool", "name": JUDGE_TOOL["name"]},
            messages=[{"role": "user", "content": prompt}],
            timeout=CLAUDE_TIMEOUT_S,
        )
    except anthropic.APIError as e:
        raise QueryError(f"judge call failed: {type(e).__name__}: {e}") from e
    scores = next(b.input for b in msg.content if b.type == "tool_use")
    if any(scores.get(c) not in range(1, 6) for c in JUDGE_CRITERIA):
        raise QueryError(f"judge returned invalid scores: {scores}")
    return scores, cost_usd(msg.usage)


def abstain_scores(results: list[Result]) -> dict[str, float]:
    """Abstain accuracy both ways, from `Answer.abstained` (ABSTAIN_TEXT with no
    citations): share of unanswerable results that abstained,
    and share of answerable results that were answered. A refusal is neither: it
    counts against both."""
    ua = [r.answer.abstained for r in results if r.reference is None]
    ans = [answered(r.answer) for r in results if r.reference is not None]
    return {
        "abstain_unanswerable": sum(ua) / len(ua),
        "answer_answerable": sum(ans) / len(ans),
    }


def gate(
    current: dict[str, float],
    accepted: dict[str, float],
    thresholds: dict[str, float] = GATE_THRESHOLDS,
) -> list[str]:
    """Names of gated metrics that dropped by more than their threshold vs the
    accepted run. A NaN current value fails: it cannot be shown not to drop."""
    return [
        m
        for m, thr in thresholds.items()
        if math.isnan(current[m]) or accepted[m] - current[m] > thr + 1e-9
    ]


def last_passed() -> dict | None:
    """The most recent logged run that passed the gate, or None if none yet."""
    if not SCORES_PATH.is_file():
        return None
    runs = [json.loads(line) for line in SCORES_PATH.open(encoding="utf-8")]
    passed = [r for r in runs if r["passed"]]
    return passed[-1] if passed else None


def log_run(record: dict) -> None:
    """Append one run to SCORES_PATH as a JSON line."""
    with SCORES_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_full(label: str) -> tuple[dict, pd.DataFrame]:
    """Full eval: retrieval metrics on 364 queries, answers on the sample, RAGAS
    + judge on the 60 answerable, abstain accuracy on all 80; gate vs the last
    passed run (the first run is the baseline and passes); log the run.

    Returns the logged record and the per-query table (for diagnosis).
    """
    load_dotenv(PROJECT_DIR / ".env")
    queries = load_queries()
    sample = make_sample(queries)
    retriever = Retriever()
    client = anthropic.Anthropic()

    ret = retrieval_scores(queries, retriever)
    results = run_sample(queries, sample, retriever, client)
    ragas_df, ragas_cost = ragas_scores(results)
    answerable = [r for r in results if r.reference is not None]
    with ThreadPoolExecutor(EVAL_WORKERS) as pool:
        judged = list(
            pool.map(
                lambda r: judge(r.question, r.reference, r.answer, client), answerable
            )
        )
    judge_df = pd.DataFrame([s for s, _ in judged])
    is_answered = [answered(r.answer) for r in answerable]

    per_query = pd.concat(
        [
            pd.DataFrame(
                {
                    "query_id": [r.query_id for r in answerable],
                    "abstained": [r.answer.abstained for r in answerable],
                    "refused": [r.answer.refused for r in answerable],
                    "top1": [r.hits[0].score for r in answerable],
                    "answer": [r.answer.text for r in answerable],
                }
            ),
            ragas_df.reset_index(drop=True),
            judge_df.add_prefix("judge_"),
        ],
        axis=1,
    )
    metrics = {
        "recall@10": float(ret.recall.mean()),
        "ndcg@10": float(ret.ndcg.mean()),
        **recall_by_content(ret),
        **{c: float(ragas_df[c].mean()) for c in ragas_df.columns},
        **{f"judge_{c}": float(judge_df[c].mean()) for c in JUDGE_CRITERIA},
        **abstain_scores(results),
    }
    cost = {
        "answers": sum(r.answer.cost_usd for r in results),
        "ragas": ragas_cost,
        "judge": sum(c for _, c in judged),
    }
    cost["total"] = sum(cost.values())

    accepted = last_passed()
    failed = gate(metrics, accepted["metrics"]) if accepted else []
    record = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "label": label,
        "index": INDEX_NAME,
        "metrics": metrics,
        "n_answered": sum(is_answered),
        "n_refused": sum(r.answer.refused for r in results),
        "nan": {  # scores RAGAS failed to compute; abstains are not scored by design
            "faithfulness": int(ragas_df.faithfulness[is_answered].isna().sum()),
            "answer_relevancy": int(
                ragas_df.answer_relevancy[is_answered].isna().sum()
            ),
            "context_precision": int(ragas_df.context_precision.isna().sum()),
            "context_recall": int(ragas_df.context_recall.isna().sum()),
        },
        "cost_usd": cost,
        "compared_to": accepted["ts"] if accepted else None,
        "failed": failed,
        "passed": not failed,
    }
    log_run(record)
    return record, per_query


def print_run(record: dict) -> None:
    """Metrics, NaN counts, cost and the gate verdict of one run."""
    base = last_passed() if not record["passed"] else None
    print(f"{record['ts']}  {record['label']}  ({record['index']})")
    for m, v in record["metrics"].items():
        mark = "  FAILED" if m in record["failed"] else ""
        print(f"  {m:22s} {v:.4f}{mark}")
    print(f"  answered (scored by faithfulness, relevancy): {record['n_answered']}")
    print(f"  refused (not gated): {record['n_refused']}")
    print("  NaN (RAGAS failed):", record["nan"])
    print("  cost $:", {k: round(v, 4) for k, v in record["cost_usd"].items()})
    verdict = "PASS" if record["passed"] else f"FAIL {record['failed']}"
    print(f"  gate vs {record['compared_to']}: {verdict}")
    if base:
        print("  accepted run kept:", base["ts"])


def main() -> None:
    """No argument: free retrieval eval. `full "label"`: the full eval."""
    logging.basicConfig(level=logging.WARNING)
    if sys.argv[1:2] == ["full"]:
        record, _ = run_full(sys.argv[2])
        print_run(record)
        return

    load_dotenv(PROJECT_DIR / ".env")
    queries = load_queries()
    sample = make_sample(queries)
    in_sample = queries["query_id"].isin(sample["answerable"])
    res = retrieval_scores(queries, Retriever())
    n_visual = int(queries.loc[in_sample, "visual"].sum())
    n_many_gold = int((queries.gold.map(len) > EVAL_K).sum())
    print(f"index {INDEX_NAME}, {len(queries)} queries, page-level @{EVAL_K}")
    print(f"recall@{EVAL_K}: {res.recall.mean():.4f}")
    print(f"NDCG@{EVAL_K}:   {res.ndcg.mean():.4f}")
    for name, value in recall_by_content(res).items():
        print(f"{name}: {value:.4f}")
    print(f"queries with < {EVAL_K} distinct pages in top chunks: {res.short.sum()}")
    print(f"queries with > {EVAL_K} gold pages: {n_many_gold}")
    print(
        f"sample: {len(sample['answerable'])} answerable ({n_visual} visual)"
        f" + {len(sample['unanswerable'])} unanswerable"
    )


if __name__ == "__main__":
    main()
