# Day 24 — Embeddings: MiniLM vs BGE, measured

Week 4 · Day 3. Opens the embedding black box from Days 22–23. The same text is
embedded by two 384-dim models, cosine is checked by hand, and both models are
scored on the failures a bi-encoder cannot see.

## What it measures

| Eval | Question it answers | Why it can fail |
|---|---|---|
| Manual cosine check | Do `formula`, `dot product`, and `matrix multiply` agree? | Any vector that isn't unit length breaks dot == cosine |
| Hard-negative triplets (25) | Does the paraphrase beat a same-words-different-meaning sentence? | Negation, numbers, and role reversal barely move a single sentence vector |
| Unrelated floor | What does this model score for "nothing in common"? | Different per model, so raw thresholds aren't portable |
| Retrieval (21 queries, 16 passages) | hit@1, hit@3, MRR. BGE runs with and without its query instruction | Queries are worded away from their passage; neighbours share topic words |

A bag-of-words baseline passes **2/25** triplets and gets **hit@1 = 0.24** on retrieval (tests enforce this ceiling), so the suite isn't trivially solvable by word overlap.

## Run

```bash
cd week-4/day-3
pytest                                   # 50 fast tests, no downloads
pytest -m slow                           # loads real BGE
PYTHONPATH=src python -m embeddings.main # downloads both models on first run
```

## Embedding models

| Model | Dim | Max tokens | Pooling | Query instruction |
|---|---|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | 256 | mean | none |
| `BAAI/bge-small-en-v1.5` | 384 | 512 | CLS | `Represent this sentence for searching relevant passages: ` (queries only) |

Same dimension does **not** mean compatible. Vectors from the two models live in different spaces. An index built with one model must be fully re-embedded to switch to the other. This is the embedding-drift rule; the model id goes in index metadata from Day 25 on.

## Results (fill from `main` output on the M3)

### Triplets — pass rate by category

| Model | Pass | neg | num | role | para | poly | Margin | Mean pos | Mean neg | Floor |
|---|---|---|---|---|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | | | | | | | | | | |
| bge-small-en-v1.5 | | | | | | | | | | |

### Retrieval

| Model | Prefix | hit@1 | hit@3 | MRR |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | no | | | |
| bge-small-en-v1.5 | no | | | |
| bge-small-en-v1.5 | yes | | | |

Embed latency (ms/text, batched): MiniLM ___ · BGE ___ · Manual-cosine max deviation: ___

### Findings

- Which categories failed for both models, and why a single vector can't fix them:
- Did the query instruction help, hurt, or tie on this data? Which queries moved?
- Floor vs mean-pos gap per model — what a "0.7" means for each:

## What I did not build and why

- **No reranker.** The cross-encoder fix for negation, numbers, and role reversal is Week 5 Day 4. Today only shows the failure.
- **No BM25.** Lexical matching would catch "30 vs 90 days" and lose the paraphrases. Hybrid retrieval is Week 5 Day 2.
- **No threshold tuning.** With 21 queries any tuned cutoff would overfit. The floor is reported instead, so the comparison stays scale-free.
- **Only two small models.** Comparing the bge base/large variants needs more RAM and doesn't change the lesson.
- **Encoding has no timeout.** It's local CPU/MPS work, not a network call. Hub downloads are timed out (30 s download, 10 s etag).

## What would break at 100 users

See the Day 24 notes: model construction per request, unbatched encode under concurrency, and the fact that `evaluate_retrieval` re-embeds the whole corpus on every call (O(corpus) per query, which a real index avoids).
