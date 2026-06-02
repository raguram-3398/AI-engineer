# AI Engineer — 8-Week Study Plan

**Machine:** MacBook Air M3 · macOS · zsh  
**Stack:** Python 3.12 · uv · ruff · black · pytest · Git  
**Repo:** `git@github.com:raguram-3398/AI-engineer.git`  
**Log:** [`progress_log.md`](./progress_log.md)

---

## Status

Phase 1 complete. Starting Phase 2 (Week 3) next.

| Phase | Weeks | Status |
|---|---|---|
| Phase 1 — Foundations | Weeks 1–2 | ✅ Complete |
| Phase 2 — LLM Engineering + RAG | Weeks 3–5 | Starting |
| Phase 3 — Agentic Systems + Production | Weeks 6–8 | Pending |

---

## Repository Structure

```
ai-engineer-plan/
├── README.md
├── progress_log.md
├── week-1/
│   ├── day-1/   ← CLI Calculator
│   ├── day-2/   ← Number Guessing Game
│   ├── day-3/   ← Tip Calculator
│   ├── day-4/   ← Todo CLI
│   ├── day-5/   ← Word Frequency Counter
│   ├── day-6/   ← Text Analyzer
│   └── day-7/   ← Week 1 Refactor Pass
└── week-2/
    ├── day-1/   ← Log File Parser
    ├── day-2/   ← Robust File Reader
    ├── day-3/   ← Weather API Client
    ├── day-4/   ← Git + README pass
    ├── day-5/   ← Refactor pass (comprehensions, Optional[T])
    ├── day-6/   ← Book Class (OOP)
    └── day-7/   ← Week 2 audit + Phase 2 orientation
```

---

## Architecture Pattern — Applied Every Day

Every project follows the same three-layer structure. No exceptions.

```
src/
└── <project>/
    ├── __init__.py
    ├── <logic>.py   ← pure functions only — no input(), no print()
    └── main.py      ← I/O, validation loops, program flow

tests/
└── test_<logic>.py  ← pytest, covers pure functions only
```

**Three-layer boundary:**

```
input layer   (main.py)    →  validate, retry, own the UX
logic layer   (<logic>.py) →  pure functions, raise, return typed results
output layer  (main.py)    →  catch exceptions, format and print
```

**Project setup from Week 2 onward:**

```toml
# pyproject.toml — replaces PYTHONPATH=src
[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
src = ["src"]
line-length = 88
```

```bash
pip install -e .   # editable install — imports work everywhere without PYTHONPATH
```

---

## Standing Rules — Never Violated

1. A function without type hints on every argument and return value is not finished
2. A function without a docstring is not finished
3. `ruff check` → `black` → `pytest` before every commit
4. Timeout on every external API call — from Week 2 Day 3, forever
5. Semantic commits only — `feat:` `fix:` `docs:` `refactor:` `test:` `chore:`
6. `tmp_path` for all file-based tests — CI-safe, no local filesystem dependency
7. `pytest.raises(ExceptionType, match=...)` for all exception tests — never `try/assert False`
8. Pure functions never call `input()` or `print()` — display and logic never mix

---

## Daily Workflow

```bash
cd week-X/day-Y
source .venv/bin/activate
# write code
ruff check src/
black src/
pytest
git add .
git commit -m "feat: description in present tense"
git push
```

---

## Week 1 — Python Foundations

**Theme:** Build six CLI tools using production-grade patterns. The apps are throwaway. The habits are not.

### Projects

| Day | Project | Core topics |
|---|---|---|
| 0 | Environment setup | pyenv, uv, ruff, black, pytest, GitHub SSH, pytest.ini |
| 1 | CLI Calculator | Type hints, `ValueError`, boundary pattern, `pytest.raises` |
| 2 | Number Guessing Game | Conditionals, `while True` vs `while condition`, loop termination |
| 3 | Tip Calculator | Pure functions, scope, docstrings, guard clauses |
| 4 | Todo CLI | `list[str]`, immutable transformations, slicing, `is_valid_index()` |
| 5 | Word Frequency Counter | `dict[str, int]`, `.get()`, sets, ranked output |
| 6 | Text Analyzer | String methods, `re.split()`, f-strings, composite returns |
| 7 | Refactor pass | DRY, function extraction, test coverage, production cleanup |

### Key Patterns Established in Week 1

**Typed exceptions over mixed return types.**
`calculate()` raises `ValueError`, never returns `float | str`. A function that returns either a value or an error string forces callers to check `isinstance()` to detect failure — untraceable at 100 concurrent requests. Raise at the logic layer. Catch at the boundary.

**Immutable list transformations.**
`add_task()`, `remove_task()`, `complete_task()` all return new lists — never mutate the argument. Tests verify the original is unchanged: `assert tasks == ["study"]`. If a function modifies its argument in place, you lose the original for logging and debugging. Immutability is observability.

**The slicing pattern.**
`remove_task()` uses `tasks[:index] + tasks[index + 1:]` — builds a new list from slices. This is the exact pattern the Week 3 conversation trimmer uses: `messages[-max_messages:]`. Same mental model, different domain.

**`.get(key, default)` reflex.**
`counts.get(word, 0) + 1` — never crashes on first occurrence. Direct key access `counts[word]` raises `KeyError` on any missing key. In AI engineering, missing keys are everywhere: Claude's response JSON might not have a `"confidence"` key, Pinecone metadata might not have a `"page"` field, the cost tracker might not have an entry for a new request ID. Build the reflex now.

**Granular input validation.**
Each getter owns its own `while True` retry loop. Bad input on `get_num_people()` never forces the user to re-enter the bill amount. This maps to Pydantic field-level validation in Week 3 — a 422 identifies exactly which field failed, not a generic "try again."

**Duplication as the extraction signal.**
When the same logic appears twice, it becomes a named function. `clean_words()`, `is_valid_index()`, `get_unique_word_count()` all emerged from noticing duplication. In Week 3, multiple pipeline steps that all clean text before processing become one `clean_text()` called from everywhere.

**`while condition` for process loops.**
`while result != "correct"` makes the termination rule visible at the loop level. `while True + break` buries it. For input validation, `while True` is correct. For process loops — agents, retries, iterations — the stopping condition belongs at the top. In Week 7, every agent loop has an explicit termination condition and a `max_iterations` ceiling.

**`pytest.raises(ValueError, match=...)`.**
Tests the right exception with the right message, not just that something raised. This is exactly how retry logic gets tested in Week 3 — when Claude returns malformed JSON, the test asserts a specific typed exception with a specific message was raised.

**Stateless service functions.**
`count_words()` starts fresh with an empty `counts` dict on every call. A `counts` dict at module level would accumulate across users — at 100 concurrent requests, every user's data bleeds into each other. Stateless pure functions are safe under concurrent load. Module-level state is a race condition.

### What Week 1 Maps To

| Week 1 pattern | Week 3+ equivalent |
|---|---|
| `ValueError` raised, caught at boundary | FastAPI 422 + Pydantic field errors |
| `while result != "correct"` | Agent loop with `max_iterations` guard |
| Immutable list transformations | Conversation history trimming |
| `dict[str, int]` accumulation with `.get()` | Token cost tracker |
| `re.split()` for sentence splitting | PII scrubber with `re.sub()` |
| `get_summary()` returning `dict[str, int | float]` | Pipeline cost/metrics dict |
| Pure functions, no module-level state | Stateless FastAPI service functions |
| `pytest.raises(ValueError, match=...)` | Testing LLM retry logic |

---

## Week 2 — Production Python

**Theme:** File I/O, error handling, external APIs, object-oriented design, Git discipline. Every pattern maps directly to a Week 3 component.

### Projects

| Day | Project | Core topics |
|---|---|---|
| 8 | Log File Parser | `with open()`, `pathlib`, streaming, three-case error handling, `tmp_path` |
| 9 | Robust File Reader | Custom exception hierarchy, `finally`, typed failure contracts |
| 10 | Weather API Client | `requests`, Pydantic, `.env`, timeout rule, parse/fetch separation |
| 11 | Git + README pass | Semantic commits, branching workflow, portfolio READMEs |
| 12 | Refactor pass | List comprehensions, `lambda`, `Optional[T]`, `T \| None` |
| 13 | Book Class | Classes vs dataclasses, `__init__`, `__str__`, three-way decision rule |
| 14 | Week 2 audit + Phase 2 orientation | Final code audit, Phase 2 reading |

### Key Patterns Established in Week 2

**The `with` statement is non-negotiable.**
`with open(...) as f:` guarantees file handle closure even if an exception is raised mid-read. `f = open(...)` without a context manager is a resource leak — at 100 concurrent requests, 100 leaked handles accumulate until the OS kills the process.

**Streaming vs loading.**
`for line in file:` processes one line at a time — never holds the whole file in memory. `file.readlines()` loads everything at once. At 100 concurrent requests each parsing a 500MB file, streaming costs kilobytes; loading costs 50GB. The log parser uses streaming by default.

**`pathlib` for all file paths.**
`Path(__file__).parent.parent / "data" / "sample.log"` builds a path relative to the source file — works on any machine, in any Docker container, regardless of where the script is run from. Hardcoded string paths break the moment someone clones the repo to a different directory structure.

**`tmp_path` for all file-based tests.**
pytest's `tmp_path` fixture creates a temporary directory that pytest cleans up after the test. Tests using `tmp_path` work in any CI environment. Tests that hardcode `"../logs/sample.log"` break silently in CI Docker containers.

**The three-case error handling pattern.**
Every file loader and document parser follows this structure:
- Missing resource → raise immediately
- Empty resource → return empty collection (`[]`)
- Malformed item → skip, continue, never crash the pipeline

The log parser uses `LogEntry | None` from `parse_line()` — return `None`, let the caller filter and continue. One bad line never stops the other 9,999. The Week 4 document loader uses the same structure.

**Custom exception hierarchies.**
`FileReaderError` as base, `FileNotFoundError`, `FileEmptyError`, `FileParseError` as subclasses. Callers can catch one specific failure or the entire failure domain with one handler. All exception types live in `exceptions.py` — one file, all imports from one source of truth. In Week 3 this becomes `LLMError`, `LLMParseError`, `LLMTimeoutError`, `CostLimitExceededError`.

**`finally` for guaranteed cleanup.**
`finally:` runs whether or not an exception was raised — and even if the exception was not caught. In Week 6, database connections close in `finally` blocks. Cleanup code that must always run belongs here.

**The timeout rule — starts Week 2 Day 3, never stops.**
Every external call gets `timeout=10`. No exceptions. Claude API, Whisper, Pinecone, databases — all of them. A call without a timeout can hang forever, hold a thread, and accumulate until the server falls over.

**Parse/fetch separation.**
`parse_weather()` is a separate function from `get_weather()`. Parsing logic is testable with hardcoded dictionaries — no network access needed. In Week 3, every Claude response parser is separate from its API caller for the same reason: fast, network-free tests that never flake.

**Pydantic for external data.**
Raw API responses are unstructured. Pydantic models enforce shape at parse time. If the API renames a field, the code raises `ValidationError` immediately rather than silently returning `None` buried in a pipeline. `response_data.get("temperature")` is silent failure. `WeatherResponse(**data)` is immediate, typed failure.

**The three-way object decision rule.**
- Use a **function** when it's just a transformation — `scrub_pii()`, `clean_words()`
- Use a **dataclass** when it's just data — `LogEntry`, `BookData`, Pydantic response models
- Use a **class** when you have state and behavior together — structured loggers, API clients, agent state managers

**Class variables vs instance variables.**
`Book.total_books` is shared across all instances. `self.title` is unique per instance. At 100 concurrent users, a class variable shared across instances is a race condition — two requests can increment it simultaneously and one increment gets lost. In production, shared counters live in Redis or PostgreSQL, not Python class variables. The class variable is the right learning tool; knowing its production limit is the interview answer.

**Never call `datetime.now()` inside domain logic.**
`get_age(self, current_year: int) -> int` — time is passed in as an argument, never fetched internally. A method that calls `datetime.now()` internally returns different results on different days — it's impure and can't be tested with a fixed expected value.

**Semantic commits from Day 11, forever.**
`feat:` `fix:` `docs:` `refactor:` `test:` `chore:` — no capital letters, no period, present tense, under 72 characters. A hiring manager who scrolls your commit history sees `feat: add hybrid retrieval with BM25 and Pinecone` vs `update`. The former tells a story. The latter tells nothing.

**"What I did not build and why" in every README.**
Not an apology. A demonstration of engineering judgment — intentional tradeoffs, not accidental omissions. Three answers per project, ready to give in any interview. Examples:
- "No persistent storage — out of scope for a CLI demo. In production: PostgreSQL with user_id and timestamp."
- "No retry on API calls — the pattern is introduced in Week 3 with exponential backoff."

### What Week 2 Maps To

| Week 2 pattern | Week 3+ equivalent |
|---|---|
| Three-case error handling | Document loader (missing PDF raises, empty returns `[]`, bad page skips) |
| `exceptions.py` hierarchy | LLM exception types — `LLMParseError`, `LLMTimeoutError`, `CostLimitExceededError` |
| `parse_weather()` separate from `get_weather()` | Claude response parser separate from API caller |
| Pydantic response models | Typed structured outputs from Claude |
| `timeout=10` on every call | Claude, Whisper, Pinecone, database — all timed |
| `tmp_path` in tests | CI-safe test suite throughout all projects |
| `finally` for cleanup | Database connection close in Week 6 |
| `dataclass` for structured data | Agent state, retrieval chunks, log entries |
| Semantic commits | Readable commit history through Week 8 |

---

## Phase 1 → Phase 2 Mapping

Every habit built in Phase 1 maps directly to a Week 3 component. Nothing was busywork.

| Phase 1 habit | Week 3+ application |
|---|---|
| `list` slicing — `tasks[:index] + tasks[index+1:]` | Conversation trimmer — `messages[-max_messages:]` |
| `dict.get(key, 0) + 1` accumulation | Token cost tracker per request |
| Exception hierarchy in `exceptions.py` | `LLMError`, `LLMParseError`, `LLMTimeoutError` |
| `timeout=10` on every external call | Claude API, Whisper, Pinecone — all timed |
| `re.split()` in text analyzer | `re.sub()` in PII scrubber |
| Pure functions, no module-level state | Stateless FastAPI service layer |
| `parse_weather()` separate from `get_weather()` | Claude response parser separate from API caller |
| `pytest.raises(ValueError, match=...)` | Testing LLM retry — malformed JSON raises `LLMParseError` |
| `get_summary()` returning `dict[str, int \| float]` | Cost/metrics dict — `{"request_id": ..., "cost_usd": 0.004}` |
| `dataclass` for `LogEntry` | Typed response models for Claude structured output |
| `while result != "correct"` | Agent loop with `max_iterations` guard |
| Immutable transformations + test original unchanged | PII scrubber returns new cleaned list, original retained for logging |

---

## Pre-Commit Checklist — Run Every Day

Before every `git commit`, check all six:

- [ ] `ruff check src/` — zero errors
- [ ] `black src/` — reformatted
- [ ] `pytest` — all tests pass
- [ ] Every function has type hints on every argument and return value including `-> None`
- [ ] Every function has a docstring stating its promise
- [ ] Zero magic numbers — every constant is named

---

## Six AI-Specific Failure Modes — Read Before Week 3

These failures don't throw errors. They fail invisibly.

| Failure | What happens | Mitigation |
|---|---|---|
| **Prompt injection** | User input manipulates LLM behaviour | Input length limits, content filtering, never concatenate raw user input into system prompts |
| **PII in the pipeline** | Real names and financials in logs create liability | Strip/mask before Claude calls and before logging |
| **Embedding drift** | Changing embedding models makes old vectors incomparable | Re-index everything on model change, document which model produced the current index |
| **Context poisoning** | Early bad outputs compound across agent steps | Validate LLM outputs between steps before feeding into state |
| **Silent hallucination** | LLM is confidently wrong, high RAGAS score doesn't mean correct | Human spot-check 5–10 outputs after every system change |
| **Latency spikes** | External calls hang under load | Timeout on every external call, degrade gracefully |