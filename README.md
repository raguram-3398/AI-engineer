# AI Engineer — 8-Week Study Plan

**Machine:** MacBook Air M3 · macOS · zsh
**Stack:** Python 3.12 · uv · ruff · black · pytest · Git · FastAPI · Pydantic · Anthropic SDK · OpenAI Whisper · Streamlit · Docker
**Repo:** `git@github.com:raguram-3398/AI-engineer.git`
**Log:** [`progress_log.md`](./progress_log.md)

---

## Status

| Phase | Weeks | Status |
|---|---|---|
| Phase 1 — Foundations | 1–2 | ✅ Complete |
| Phase 2 — LLM Engineering + RAG | 3–5 | Week 3 ✅ shipped · 4–5 pending |
| Phase 3 — Agentic Systems + Production | 6–8 | Pending |

**P1 live demo:** [huggingface.co/spaces/raguram3398/sales-intelligence](https://huggingface.co/spaces/raguram3398/sales-intelligence)

---

## Repository Structure

```
ai-engineer-plan/
├── week-1/   ← 6 CLI tools (Days 0–7)
├── week-2/   ← File I/O, APIs, OOP (Days 8–14)
└── week-3/
    └── p1-sales-intelligence/
        ├── src/{api,services,models,utils}/
        ├── tests/        ← 35 tests, 95% coverage
        ├── streamlit_app.py
        ├── Dockerfile · docker-compose.yml
        └── .github/workflows/ci.yml
```

**Three-layer pattern, every project:** input layer validates → logic layer raises typed errors → output layer catches and responds. In Week 3 this became the FastAPI route shape directly.

---

## Standing Rules

1. Type hints + docstring on every function, or it's not finished
2. `ruff check` → `black` → `pytest` before every commit
3. Timeout on every external call, no exceptions
4. Semantic commits only — `feat:` `fix:` `docs:` `refactor:` `test:` `chore:`
5. Raise typed exceptions, never return error strings
6. Clients (`AsyncAnthropic`, `AsyncOpenAI`) live at module level, never per-request
7. Nothing past the PII wall ever sees unscrubbed transcript data

---

## Week 1 — Python Foundations (Days 0–7)

Six CLI tools: Calculator → Number Guessing Game → Tip Calculator → Todo CLI → Word Frequency Counter → Text Analyzer → Refactor pass.

**Patterns that carried forward:**

| Pattern | Maps to (Week 3+) |
|---|---|
| Raise `ValueError`, never return `float \| str` | `TimeoutError` / `AnalysisError` at every service boundary |
| Immutable list transforms, original unchanged | PII scrubber returns new text, original kept for logging |
| `tasks[:i] + tasks[i+1:]` slicing | `messages[-max:]` context trimming |
| `.get(key, 0)` reflex | Safe access on Claude/Pinecone response dicts |
| `while result != "correct"` (visible stop condition) | Retry loop with `max_attempts` at the top, not buried in `break` |
| `pytest.raises(ValueError, match=...)` | Testing `AnalysisError` raised after exhausted retries |
| Stateless functions, no module-level mutation | Stateless FastAPI services (safe under concurrent load) |

---

## Week 2 — Production Python (Days 8–14)

Log Parser → Robust File Reader → Weather API Client → Git/README pass → Refactor pass → Book Class (OOP) → Phase 2 orientation.

**Patterns that carried forward:**

| Pattern | Maps to (Week 3+) |
|---|---|
| `with open()`, `tmp_path`, `pathlib` everywhere | CI-safe 35-test suite |
| Three-case error handling (missing → raise, empty → `[]`, bad → skip) | `TranscriptionResult \| None`, scrub-and-continue logic |
| Custom exception hierarchy in `exceptions.py` | `AnalysisError(attempts, last_error)` — structured, not just a message |
| `parse_weather()` separate from `get_weather()` | `extract_json()` separate from `call_claude()` |
| Pydantic for external data | `SalesCallAnalysis` schema, `Literal` sentiment enum |
| `timeout=10` rule (started Day 3) | `asyncio.wait_for` / `asyncio.timeout()` on Claude + Whisper |
| Class var vs instance var race-condition lesson | `_daily_spend` module-level, documented restart-reset limit |
| "What I did not build and why" | Three honest tradeoffs in every README, ready for interviews |

---

## Week 3 — P1: Sales Call Intelligence (Days 15–21) ✅ Shipped

**Pipeline:** Audio upload → Whisper transcription → confidence check → injection guard → PII scrub → context trim → Claude analysis (structured, retried) → cost tracking → Streamlit dashboard (streamed).

| Day | Built |
|---|---|
| 15 | Architecture diagram, no code — caught a missing confidence-check node before writing any |
| 16 | `AsyncAnthropic` wrapper, module-level `PROMPT_REGISTRY`, timeout via `asyncio.wait_for` |
| 17 | Pydantic output schema, 3-attempt error-fed retry (exact validation error → correction prompt) |
| 18 | FastAPI `/analyze` route, Whisper integration, async warmup exercises |
| 19 | PII scrubber, injection guard, context-budget trimmer — wired in that exact order |
| 20 | Token-streaming via `asyncio.Queue`, cost tracker, `__META__` sentinel, Streamlit UI |
| 21 | Full code review *before* tests, 35-test suite at 95% coverage, Docker, CI, HF Spaces deploy |

### Key patterns

- **Error-fed retry** — correction prompt includes what was asked, what came back, the exact Pydantic error, and what to send instead
- **`__META__` sentinel** — one HTTP connection carries both the live token stream and the final structured JSON, no second round-trip
- **Producer/consumer streaming** — `asyncio.Queue` with a `None` sentinel pushed in `finally`, so the consumer always terminates cleanly
- **Injection check before PII scrub, not after** — scrubbing first could mangle the exact phrase the injection guard needs to see
- **Client-per-request anti-pattern** — hit on Day 16 (`AsyncAnthropic()` instantiated inside the function), self-corrected proactively by Day 18
- **Code review before writing tests** — caught a wrong env var key (`ANTHROPIC_API_KEY` read where `OPENAI_API_KEY` was needed) and a dropped `response_format` param that mocked tests would have hidden

### Recurring bug classes (none caught by ruff/black — semantic, not style)

| Bug class | Example |
|---|---|
| Missing parens on instantiation | `client = AsyncAnthropic` (Days 16, 19) |
| Wrong method/property access | `client.message.create`, `.suffix()` called as a method |
| Typo'd field names, silently consistent | `is_low_confindence`, `wer_threshould` |
| Regex that compiles but matches wrong | `{13.16}` instead of `{13,16}` |
| Truthiness check on wrong object | `if not guard:` instead of `if not guard.is_safe:` |
| Computed value never wired to its field | `check_confidence()` result never assigned to the dataclass |

### Results

| Metric | Value |
|---|---|
| Tests / coverage | 35 passing / 95% |
| Avg latency | Whisper 17.5s · Claude 10.5s |
| Avg cost/call | $0.056 |
| PII scrubbed (test run) | 27 entities (12 email, 3 phone, 1 card, 11 amount) |
| Deployment | [HF Spaces](https://huggingface.co/spaces/raguram3398/sales-intelligence) |

### Documented, not fixed (the "100 users" list)

- Client-per-request → connection pool exhaustion (self-corrected)
- Unbuffered audio upload → up to 2.5GB in memory at the file-size limit
- Sync transcript trimming blocks the async event loop on long calls
- All streams stall together if Claude itself rate-limits — no request queue in front of it yet

### What I did not build and why

- Anthropic token-counting API → used a ~4 char/token estimate instead
- Regex name scrubbing → built, tested, removed after false positives on product names
- `jiwer` WER → used a heuristic (>30% repeated words) proxy instead
- `/analyse/stream` has no injection/PII guard yet — known gap vs. the main pipeline

---

## Six AI-Specific Failure Modes

| Failure | Mitigation | Seen in P1? |
|---|---|---|
| Prompt injection | Length limits, never concat raw input into system prompt | Yes — guard exists; streaming endpoint still has a gap |
| PII in the pipeline | Strip/mask before any Claude call or log | Yes — scrub wall; regex misses unstructured names (documented) |
| Embedding drift | Re-index on model change, document which model | Not yet — no RAG until Week 4 |
| Context poisoning | Validate LLM output between steps | Adjacent — error-fed retry validates against schema |
| Silent hallucination | Human spot-check after every change | Not yet formalized |
| Latency spikes | Timeout everywhere, degrade gracefully | Yes — timeouts in; graceful degradation under rate-limits still unsolved |

---

## Pre-Commit Checklist

- [ ] `ruff check src/` clean
- [ ] `black src/` reformatted
- [ ] `pytest` all green
- [ ] Type hints + docstring on every function
- [ ] Zero magic numbers