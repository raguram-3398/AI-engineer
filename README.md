# AI Engineer — 8-Week Study Plan

**Machine:** MacBook Air M3 · macOS · zsh  
**Stack:** Python 3.12 · uv · ruff · black · pytest · Git  
**Repo:** `git@github.com:raguram-3398/AI-engineer.git`  
**Log:** [`progress_log.md`](./progress_log.md)

---

## Structure

```
ai-engineer-plan/
├── README.md
├── week-1/
│   ├── day-1/   ← CLI Calculator
│   ├── day-2/   ← Number Guessing Game
│   ├── day-3/   ← Tip Calculator
│   ├── day-4/   ← Todo CLI
│   ├── day-5/   ← Word Frequency Counter
│   ├── day-6/   ← Text Analyzer
│   └── day-7/   ← Week 1 Refactor Pass
├── week-2/
│   └── day-1/   ← Log File Parser
│   ...
```

---

## Week 1 — Python Foundations

**Theme:** Build six CLI tools using production-grade Python patterns — typed functions, pure logic vs IO separation, immutable state, validated input, and a full test suite for every project.

| Day | Project | Topics |
|-----|---------|--------|
| 0 | Environment setup | pyenv, uv, ruff, black, pytest, GitHub SSH |
| 1 | CLI Calculator | Variables, type hints, `ValueError`, boundary pattern |
| 2 | Number Guessing Game | Conditionals, `while True` vs `while condition`, loop termination |
| 3 | Tip Calculator | Pure functions, scope, docstrings, guard clauses |
| 4 | Todo CLI | `list[str]` state, immutable transformations, slicing |
| 5 | Word Frequency Counter | `dict[str, int]`, `.get()`, sets, ranked output |
| 6 | Text Analyzer | String methods, `re.split()`, f-strings, composite returns |
| 7 | Refactor pass | DRY, function extraction, test coverage, production cleanup |

### Architecture Pattern (applied every day)

```
src/
└── <project>/
    ├── __init__.py
    ├── <logic>.py   ← pure functions only — no input(), no print()
    └── main.py      ← I/O, validation loops, program flow

tests/
└── test_<logic>.py  ← pytest, covers pure functions only
```

Every project follows the same three-layer boundary:

```
input layer (main.py)   →   validate, retry, own the UX
logic layer (*.py)      →   pure functions, raise ValueError, return typed results
output layer (main.py)  →   catch exceptions, format and print
```

### Key Patterns Established

**Typed exceptions over mixed return types.** `calculate()` raises `ValueError`, never returns `float | str`. Callers catch at the boundary.

**Immutable list transformations.** `add_task()`, `remove_task()`, `complete_task()` all return new lists — never mutate arguments. Tests verify the original is unchanged.

**`.get(key, default)` reflex.** Used throughout Day 5 and Day 6 for safe dictionary access. Direct key access is never used where the key might be absent.

**Granular input validation.** Each getter function owns its own `while True` retry loop. Bad input on one field never resets the others.

**`pytest.raises(ValueError, match=...)`** — testing the right exception with the right message, not just that something raised.

**Duplication as the extraction signal.** When the same logic appears twice, it becomes a named function. `clean_words()`, `is_valid_index()`, `get_unique_word_count()` all emerged this way.

### What Week 1 Maps To

| Week 1 pattern | Week 3+ equivalent |
|---|---|
| `ValueError` at boundaries | FastAPI 422 + Pydantic field errors |
| `while result != "correct"` | Agent loop with `max_iterations` guard |
| Immutable list transformations | Conversation history trimming |
| `dict[str, int]` accumulation | Token cost tracker |
| `re.split()` for sentences | PII scrubber with `re.sub()` |
| Pure functions, no module-level state | Stateless FastAPI service functions |

---

## Toolchain

```bash
# Per-project setup (Week 1)
uv venv .venv
source .venv/bin/activate
pip install ruff black pytest pytest-asyncio

# Daily workflow
ruff check .
black .
pytest
git add . && git commit -m "type: message" && git push
```

**Commit convention:** `feat:` / `fix:` / `refactor:` / `docs:`

---


# Day 8 — File I/O · Error Handling · Log File Parser

**Week/Day:** Week 2, Day 1  
**Topic:** File I/O with `pathlib`, context managers, graceful failure handling, `pyproject.toml` setup

---

## What I Built

A resilient log file ingestion pipeline. Reads raw `.log` files line by line, parses each into a typed `LogEntry` dataclass, and handles every failure mode without crashing the system.

```
week-2/day-1/
├── pyproject.toml
├── src/
│   └── log_parser/
│       ├── __init__.py
│       ├── parser.py    ← pure parsing functions
│       └── main.py      ← file I/O and program flow
├── logs/
│   └── sample.log
└── tests/
    └── test_log_parser.py
```

---

## pyproject.toml Setup

Starting from Day 8, `PYTHONPATH=src` is replaced with a `pyproject.toml` that makes `src/` the package root. No more prefixing every command.

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "log-parser"
version = "0.1.0"
requires-python = ">=3.12"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
src = ["src"]
line-length = 88

[tool.black]
line-length = 88
```

**Install the package in editable mode once after setup:**

```bash
pip install -e .
```

After this, imports work from anywhere without `PYTHONPATH=src`:

```python
# Before (Week 1)
# PYTHONPATH=src pytest

# After (Week 2+)
pytest
```

---

## Core Logic

### `parser.py` — Pure Logic Layer

**`LogEntry` dataclass**

```python
@dataclass
class LogEntry:
    date: str
    time: str
    level: str
    message: str
```

**`parse_line(line: str) -> LogEntry | None`**  
Splits the line using `maxsplit=3`. Returns `None` for any malformed input — never raises, never crashes the pipeline.

**`parse_log_file(filepath: Path) -> list[LogEntry]`**  
Three failure cases handled separately:
- Missing file → raises `FileNotFoundError`
- Empty file → returns `[]`
- Malformed line → skips silently, continues

**`filter_by_level(entries, level: str) -> list[LogEntry]`**  
Returns a new filtered list. Pure — no mutation.

**`get_level_counts(entries) -> dict[str, int]`**  
Uses `.get(level, 0) + 1` accumulation pattern — same as Day 5's word counter, applied to log levels.

### `main.py` — IO Layer

Builds the log file path using `Path(__file__).parent` — no hardcoded strings, works on any machine. Calls `parse_log_file`, displays entries and summary, handles `FileNotFoundError` at the boundary.

---

## Failure Design

```
raw log file
→ file exists?          missing → raise FileNotFoundError
→ file has content?     empty   → return []
→ line parseable?       bad     → return None, skip and continue
→ LogEntry objects
→ filter + aggregate
→ display
```

`parse_line()` returning `LogEntry | None` instead of raising is a deliberate design choice — one bad line should never stop the other 9,999. The caller filters `None` out and continues.

---

## Tests

```python
# Valid line parses to correct LogEntry
def test_parse_line_valid():

# Malformed line returns None
def test_parse_line_invalid():

# Filter by level returns correct subset
def test_filter_by_level():

# Level counts aggregate correctly
def test_get_level_counts():

# Missing file raises FileNotFoundError
def test_parse_log_file_missing():

# Malformed lines in file are skipped
def test_parse_log_file_skips_malformed():

# Empty file returns empty list (uses tmp_path fixture)
def test_parse_log_file_empty():
```

`tmp_path` is a pytest fixture that creates a temporary directory, cleaned up after the test. Tests using `tmp_path` work in any CI environment with no local filesystem dependency.

---

## Tools Used

- `pathlib` — OS-independent path construction
- `dataclasses` — typed structured data model
- `with open(...)` — guaranteed file handle cleanup
- `pytest` + `tmp_path` fixture — CI-safe file tests
- `ruff` · `black` · `Git`
- `pyproject.toml` + `pip install -e .` — replaces `PYTHONPATH=src`

---

## Key Takeaways

**`with open(...)` is non-negotiable.** Guarantees file handle closure even if an exception is raised mid-read. A leaked handle under concurrent load accumulates until the OS kills the process.

**`parse_line()` returning `None` is a pipeline resilience pattern.** The Week 4 document loader uses the same shape: one unparseable chunk returns `None`, the caller skips it, the other 9,999 chunks process normally.

**`tmp_path` makes tests portable.** Tests tied to local file paths break silently in CI Docker containers. `tmp_path` works everywhere, forever.

**`pyproject.toml` with `pip install -e .` is the production standard.** `PYTHONPATH=src` is a workaround; editable installs are how real packages resolve imports. Every project from here uses this setup.

---
