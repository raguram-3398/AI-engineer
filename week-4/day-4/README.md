# Day 25 — Pinecone + metadata filtering

Week 4 · Day 4. The corpus moves from a throwaway local index into a Pinecone
serverless index. Every chunk carries `source`, `page`, `date`, and
`embedding_model`. The eval checks whether filters retrieve the right
**version** of a policy when unfiltered search can't.

## Embedding model for this index

| Index | Namespace | Model | Dim | Metric | Query prefix |
|---|---|---|---|---|---|
| `day25-bge-small-en-v1-5` | `policies` | `BAAI/bge-small-en-v1.5` | 384 | cosine | `Represent this sentence for searching relevant passages: ` |

The model id appears in three places: the index name, the `embedding_model`
field on every record, and this table. `evaluate` raises
`EmbeddingModelMismatchError` if any hit came from a different model.
`ensure_index` raises it if the existing index has the wrong dimension or metric.

## Re-indexing procedure (model change)

Vectors from two models are not comparable, even at the same dimension. Never
mix them in one index.

1. Set `MODEL_ID`, `DIMENSION`, `INDEX_NAME` (new name, e.g. `...-bge-base-en-v1-5`)
   and the query prefix in `models.py`.
2. Run `main`. It creates the new index and re-embeds the full corpus into it.
3. Re-run the eval on the new index and record before/after scores below.
4. Switch readers to the new index name. Delete the old index only after that.

If the corpus shrinks (chunks removed), `wait_until_count` stops with a "stale
records" error. Delete the namespace in the Pinecone console and re-run.

## Run

```bash
cd week-4/day-4
pytest                                       # 36 tests, fakes only: no network, no model
PYTHONPATH=src python -m vectorstore.main    # needs PINECONE_API_KEY; downloads BGE first run
```

## Data

- `data/corpus.jsonl`: 18 chunks from 4 sources. `remote-work-policy` and
  `expense-policy` each exist in a 2024 and a 2026 version, with near-identical
  wording and different numbers.
- `data/queries.json`: 18 queries.
  - `version` (12): six questions, each asked twice with the same text, once
    scoped to 2026 and once to 2024. Same text gives the same unfiltered top-1,
    so unfiltered hit@1 on this group is **at most 0.50 by construction**
    (a test enforces the pairing). This is what makes the eval able to fail.
  - `source` (3): topics shared between the travel and expense policies.
  - `control` (3): single-version security handbook, no filter needed.

## Results (fill from `main` output on the M3)

| Kind | n | hit@1 unfiltered | hit@1 filtered |
|---|---|---|---|
| version | 12 | | |
| source | 3 | | |
| control | 3 | | |
| ALL | 18 | | |

### Findings

- On version queries, how many unfiltered misses returned the *other version of the right page* (stale answer) vs. an unrelated page?
- Any filtered misses? If so, the filter was right but the embedding ranked the wrong page inside that version.
- Did the controls pass? A control miss is an embedding problem, not a filter problem.

## What I did not build and why

- **No LangChain `PineconeVectorStore`.** The raw SDK makes the record shape, filter, and consistency wait visible.
- **No delete/update by metadata.** The re-index procedure above uses a new index instead.
- **No hybrid/sparse vectors.** That's Week 5 Day 2.
- **No async or concurrent queries.** 36 sequential queries are fine for an eval.
