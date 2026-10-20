# Citation Tracking

**What it does:** Gives Claude a question plus the passages a search returned, and makes it answer using only those passages, with every claim linked to the exact passage, document, page and date it came from. The links are then checked against a hand-made answer key: did it cite the right sources, did it cite an outdated policy, and did it correctly say "I don't know" when the passages don't contain the answer? Every call's cost is measured, and any call that could cost more than 2 cents is refused before it's sent.

**Why it's here:** An AI answer is only trustworthy if you can check where it came from. Citations make every claim auditable — and measuring them showed that a citation can be real and still point to the wrong, outdated document.

**Result:** 12 test questions, run twice with Claude Sonnet:

| | With document dates shown to Claude | Without dates |
|---|---|---|
| Right sources cited (of those needed) | 100% | 95% |
| Citations that were correct | 95% | 70% |
| Answers citing an outdated policy | 0 of 10 | 6 of 10 |
| Unanswerable questions correctly declined | 2 of 2 | 2 of 2 |

Without the dates, Claude usually still picked the newer policy in its wording, but cited the old version alongside it, so the answer looked well-sourced while pointing at outdated rules. Giving each passage its effective date removed that completely. Cost: about half a cent per answer ($0.057 for all 12).

**What I learned:**

- Getting verifiable citations from Claude
- Scoring citations against an answer key
- Cost limits on every AI call
- Why document dates matter as much as document text

**Run it:** `uv run python -m citations.main` (needs an Anthropic key in `.env`; about $0.06 per run) · Without dates: `uv run python -m citations.main --no-version-hints` · Tests: `uv run pytest` (26 passing, no network needed)
