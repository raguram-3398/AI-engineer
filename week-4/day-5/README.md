# Day 26 — Citation tracking

Week 4 · Day 5. Turns retrieved chunks into an answer where every claim carries
a verified citation (chunk_id, source, page, effective date, retrieval score),
keeps each Claude call under a cost limit, and scores the citations against gold
labels.

Retrieval is **frozen**: each case in `data/cases.json` carries the chunks
retrieval returned (Day 25 corpus, Day 25-style scores). Any score change comes
from the citation layer only. Live Pinecone is wired in on Day 27.

## Files

| File | Role |
|---|---|
| `models.py` | constants (model, prices, limits), frozen dataclasses, exceptions |
| `cite.py` | pure: build the request, parse + verify citations, cost math |
| `evaluate.py` | pure: citation precision / recall, stale flag, abstention |
| `main.py` | case loader, `LLMClient` Protocol + Anthropic adapter, run, report |

## Model and cost

| Model | Input | Output | Max output | Per-call limit (worst case) |
|---|---|---|---|---|
| `claude-sonnet-5-5` | $2 / MTok | $10 / MTok | 400 tokens | $0.02 |

Before each call: `count_tokens` + the full `max_tokens` budget gives a worst
case; above the limit the call is refused. After each call: exact cost from
`usage`. The run warns once total spend passes $0.50.

## Run

```bash
cd week-4/day-5
pytest                                     # 25 tests, fakes only, no network
PYTHONPATH=src python -m citations.main    # needs ANTHROPIC_API_KEY
```

## Data

12 cases over the Day 25 corpus:

- `version` (5): both the 2024 and 2026 versions of the page are retrieved; in
  v2 and v4 the stale version scores higher. v5 asks about the 2024 version
  explicitly, so the old chunk is gold.
- `multi_source` (3): the answer needs two documents.
- `control` (2): single-version document.
- `abstain` (2): retrieved chunks do not answer the question.

## Metrics

Precision and recall are chunk-level against gold labels: a cheap proxy for
ALCE's citation precision/recall, which use an NLI model per statement.

- **precision**: share of cited chunks that are gold.
- **recall**: share of gold chunks that were cited.
- **stale**: cited the same page of the other policy version. The citation
  passes the integrity check and is still wrong.
- **uncited**: answer blocks with no citation that state a number (years
  excluded).
- **abstain_ok**: nothing cited on an unanswerable question.

## Results (fill from `main` output on the M3)

| Kind | n | precision | recall | stale rate | uncited | abstain ok |
|---|---|---|---|---|---|---|
| version | 5 | | | | | |
| multi_source | 3 | | | | | |
| control | 2 | | | | | |
| abstain | 2 | | | | | |
| ALL answerable | 10 | | | | | |

Total cost: $

### Findings

- Any stale citations? Which case, and was the stale chunk ranked first?
- Any precision below 1.00: was the extra citation wrong, or a reasonable
  supporting cite the gold labels did not include?
- Did both abstain cases cite nothing?

## What I did not build and why

- **No live retrieval.** Frozen chunks isolate the citation layer; Day 27 joins them.
- **No NLI-based citation scoring.** Gold labels are enough for 12 cases.
- **No structured outputs.** The API rejects citations + structured outputs together.
- **No streaming.** `citations_delta` handling is not needed for an eval.
