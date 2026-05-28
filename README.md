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

# Day 9 — Custom Exceptions · Error Handling · File Reader

**Week/Day:** Week 2, Day 2  
**Topic:** Custom exception hierarchies, typed failure handling, parsing contracts, `finally` cleanup guarantees

---

## What I Built

A resilient file reader pipeline with typed custom exceptions, layered error handling, parsing statistics, and strict separation between logic, display, and exception layers.

    week-2/day-2/
    ├── pyproject.toml
    ├── data/
    │   └── sample.txt
    ├── src/
    │   └── file_reader/
    │       ├── __init__.py
    │       ├── exceptions.py   ← centralized exception hierarchy
    │       ├── reader.py       ← pure parsing + statistics logic
    │       └── main.py         ← I/O and program flow
    └── tests/
        └── test_reader.py

---

## Core Logic

### `exceptions.py` — Exception Layer

Centralized typed exception hierarchy:

    class FileReaderError(Exception):
        """Base exception for all file reader errors."""

    class FileNotFoundError(FileReaderError):
        """Raised when the requested file does not exist."""

    class FileEmptyError(FileReaderError):
        """Raised when the file exists but contains no content."""

    class FileParseError(FileReaderError):
        """Raised when a line cannot be parsed into the expected format."""

All file-reader failures inherit from `FileReaderError`, allowing callers to:
- catch one specific failure
- or catch the entire file-reader failure domain

---

### `reader.py` — Pure Logic Layer

**`read_file(filepath: Path) -> list[str]`**  
Reads file contents safely using `pathlib`. Raises:
- `FileNotFoundError` if file is missing
- `FileEmptyError` if file exists but contains no usable content

Returns cleaned file lines only on success.

**`parse_line(line: str) -> dict[str, str]`**  
Parses a single `key:value` line into:

    {
        "key": "name",
        "value": "Alice",
    }

Uses `split(":", maxsplit=1)` to preserve additional `:` characters inside values.

Malformed lines raise `FileParseError`.

**`parse_file(filepath: Path) -> list[dict[str, str]]`**  
Calls `read_file()`, parses every line, skips malformed entries, and continues processing the rest of the dataset.

Malformed rows are handled per-line:

    except FileParseError:
        continue

This creates partial-failure tolerance — one bad row never destroys the entire ingestion pipeline.

**`get_statistics(lines: list[str]) -> dict[str, int]`**  
Tracks:
- total lines
- valid lines
- error lines

Uses parsing attempts themselves to calculate error rates.

Example return:

    {
        "total_lines": 6,
        "valid_lines": 5,
        "error_lines": 1,
    }

---

## `main.py` — IO Layer

Builds the file path using `Path("data/sample.txt")`, calls parsing/statistics functions, displays results, and catches typed exceptions at the application boundary.

Uses:

    except FileReaderError as error:

to safely handle all file-reader-specific failures.

Uses:

    finally:
        print("File reading complete")

to guarantee cleanup/logging behavior whether execution succeeds or fails.

---

## Failure Design

    raw file
    → file exists?          missing → raise FileNotFoundError
    → file has content?     empty   → raise FileEmptyError
    → line parseable?       bad     → raise FileParseError
    → parse_file() catches malformed rows
    → valid parsed entries
    → statistics aggregation
    → display

Unlike Day 8:
- malformed parsing now raises typed exceptions
- callers decide recovery behavior
- failure contracts stay explicit and composable

---

## Tests

    # Missing file raises FileNotFoundError
    def test_read_file_raises_for_missing_file()

    # Empty file raises FileEmptyError
    def test_read_file_raises_for_empty_file()

    # Valid line parses correctly
    def test_parse_line_parses_valid_line()

    # Malformed line raises FileParseError
    def test_parse_line_raises_for_invalid_line()

    # Statistics return correct counts
    def test_get_statistics_returns_correct_counts()

Uses:
- `pytest.raises(...)`
- `tmp_path`
- isolated filesystem testing
- typed exception assertions

---

## Tools Used

- `pathlib` — platform-safe filesystem paths
- custom exception classes — typed failure contracts
- `pytest.raises(...)` — exception validation
- `tmp_path` fixture — portable filesystem testing
- `finally` — guaranteed cleanup execution
- `ruff` · `black` · `pytest` · `Git`
- `pyproject.toml` + `pip install -e .`

---

## Key Takeaways

**Typed exceptions create scalable failure architecture.**  
Callers can recover differently from missing files, empty files, and malformed parsing.

**Custom exception hierarchies become shared system contracts.**  
Every layer imports the same error vocabulary from one source of truth.

**Returning `None` and raising exceptions solve different problems.**  
Day 8 treated malformed rows as ignorable. Day 9 treats parsing failures as explicit typed states.

**`finally` guarantees execution.**  
Critical for cleanup paths that must run regardless of crashes or uncaught exceptions.

**Stable machine-facing schemas matter.**  
Internal data structures use predictable snake_case keys:
- `total_lines`
- `valid_lines`
- `error_lines`

Human formatting belongs only in the display layer.

**Logic, I/O, and error handling remain isolated.**  
Pure functions never print. Display functions never parse. Exception types remain centralized in `exceptions.py`.

---

# Day 10 — Dependency Management · Env Vars · HTTP APIs · Typed API Client

**Week/Day:** Week 2, Day 3  
**Topic:** Virtual environments, requirements.txt, environment variables (.env), HTTP requests, API integration, Pydantic-based response validation

---

## What I Built

A production-style weather CLI system that integrates with a real external API (Open-Meteo), loads configuration from environment variables, performs HTTP requests with strict timeout rules, and converts unstructured JSON into validated Pydantic models.

week-2/day-3/
├── .env
├── .gitignore
├── requirements.txt
├── src/
│   └── weather/
│       ├── __init__.py
│       ├── client.py     ← HTTP + parsing + Pydantic models
│       └── main.py       ← CLI orchestration + user I/O
└── tests/
    └── test_weather.py

---

## Environment Setup

Virtual environments isolate dependencies per project:

    python -m venv .venv
    source .venv/bin/activate

All dependencies are installed into .venv, not system Python.

---

## Dependency Management

Installed libraries:

    requests
    pydantic
    python-dotenv

Frozen into deterministic build file:

    pip freeze > requirements.txt

This ensures identical environments across:
- local machine
- CI pipelines
- production containers

---

## Environment Variables (.env)

Secrets and configuration are stored outside code:

    ANTHROPIC_API_KEY=sk-test-fake

Loaded using dotenv:

    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.environ.get("ANTHROPIC_API_KEY")

Key principle:
- secrets never hardcoded
- .env never committed to git
- configuration separated from logic

---

## Core Logic — client.py

### Pydantic Models

    class CurrentWeather(BaseModel):
        temperature: float
        windspeed: float
        weathercode: int

    class WeatherResponse(BaseModel):
        latitude: float
        longitude: float
        current_weather: CurrentWeather

Purpose:
- enforce structure at runtime
- prevent silent key errors
- convert raw JSON → typed object

---

### parse_weather(data)

    def parse_weather(data: dict) -> WeatherResponse:
        return WeatherResponse(
            latitude=data["latitude"],
            longitude=data["longitude"],
            current_weather=CurrentWeather(
                temperature=data["current"]["temperature_2m"],
                windspeed=data["current"]["wind_speed_10m"],
                weathercode=data["current"]["weather_code"],
            ),
        )

Key idea:
- external API shape is unstable
- internal schema is stable
- mapping layer isolates change

---

### get_weather(latitude, longitude)

    def get_weather(latitude: float, longitude: float) -> WeatherResponse:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m,weather_code",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            data = data[-1]

        return parse_weather(data)

Failure handling:
- Timeout → network delay protection
- ConnectionError → offline handling
- HTTPError → bad status codes
- list response → normalized to single object

Rule enforced:
Every external call uses timeout=10

---

## CLI Layer — main.py

### get_coordinates()

    def get_coordinates() -> tuple[float, float]:
        lat = float(input("Enter latitude: "))
        lon = float(input("Enter longitude: "))
        return lat, lon

---

### display_weather(weather)

    def display_weather(weather: WeatherResponse) -> None:
        print("Temperature:", weather.current_weather.temperature)
        print("Wind Speed:", weather.current_weather.windspeed)
        print("Weather Code:", weather.current_weather.weathercode)

---

### main()

    def main() -> None:
        try:
            lat, lon = get_coordinates()
            weather = get_weather(lat, lon)
            display_weather(weather)

        except Exception as error:
            print("Error:", error)

---

## Failure Design

user input
→ invalid float?        ValueError handled
→ HTTP request          timeout / connection / HTTP error handled
→ API response          normalized (list → dict)
→ schema validation     Pydantic enforces structure
→ final object          safe WeatherResponse

---

## Tests

    def test_parse_weather_valid():
        data = {
            "latitude": 33.21,
            "longitude": -97.13,
            "current": {
                "temperature_2m": 28.5,
                "wind_speed_10m": 12.3,
                "weather_code": 1,
            }
        }

        result = parse_weather(data)
        assert result.current_weather.temperature == 28.5

    def test_parse_weather_missing_field_fails():
        data = {
            "latitude": 33.21,
            "longitude": -97.13,
            "current": {
                "temperature_2m": 28.5,
                "wind_speed_10m": 12.3,
            }
        }

        try:
            parse_weather(data)
            assert False
        except Exception:
            assert True

---

## Tools Used

- requests — HTTP client  
- pydantic — runtime schema validation  
- python-dotenv — environment variable loading  
- venv — dependency isolation  
- .env + .gitignore — secret management  
- timeout=10 — enforced network safety rule  
- pip freeze — deterministic builds  
- pytest — validation testing framework  

---

## Key Takeaways

1. External APIs are never stable  
   → normalize shape and fields  

2. Pydantic enforces contracts  
   → unsafe dict → validated object  

3. HTTP is failure-prone  
   → always timeout + handle exceptions  

4. Config must be external  
   → .env keeps secrets out of code  

5. Architecture is layered  

CLI
→ HTTP client
→ parser
→ Pydantic model


---

# Day 11 — Classes · Dataclasses · State Modeling · Typed Object Design

**Week/Day:** Week 2, Day 4  
**Topic:** Classes, instance variables, class variables, methods, dataclasses, object state, validation patterns

---

## What I Built

A production-style book modeling system implemented in two versions:
- regular class (`Book`)
- dataclass (`BookData`)

The project demonstrates:
- stateful object design
- shared vs per-instance state
- pure methods
- dataclass validation
- typed modeling
- production-style testability

week-2/day-4/
├── src/
│   └── books/
│       ├── __init__.py
│       ├── book_class.py
│       ├── book_dataclass.py
│       └── main.py
└── tests/
    └── test_books.py

---

## Core Object Design

### Regular Class — Book

    class Book:
        total_books: int = 0
        LONG_BOOK_THRESHOLD: int = 300

Purpose:
- combines state + behavior
- owns business logic
- tracks shared system state

Instance variables:

    self.title
    self.author
    self.pages
    self.year

Shared class variables:

    Book.total_books
    Book.LONG_BOOK_THRESHOLD

Key principle:
- instance variables belong to one object
- class variables belong to the class itself

---

## __init__

    def __init__(self, title, author, pages, year):

Purpose:
- initializes object state
- attaches data to self
- increments shared counter

    Book.total_books += 1

Key idea:
- every new instance mutates shared class state

---

## __str__

    def __str__(self) -> str:
        return f"{self.title} by {self.author} ({self.year})"

Purpose:
- human-readable object representation
- automatic formatting during print()

Rule:
- return strings
- never print inside __str__

---

## is_long()

    def is_long(self) -> bool:
        return self.pages > Book.LONG_BOOK_THRESHOLD

Purpose:
- encapsulates business rule
- avoids magic numbers

Key idea:
- behavior should live with the object that owns the data

---

## get_age()

    def get_age(self, current_year: int) -> int:
        return current_year - self.year

Purpose:
- pure calculation
- deterministic and testable

Rule enforced:
- never call datetime.now() inside domain logic
- inject time as input

---

## summary()

    def summary(self) -> str:
        return f"..."

Purpose:
- formatted structured output
- presentation-safe helper method

---

## Dataclass Version — BookData

    @dataclass
    class BookData:
        title: str
        author: str
        pages: int
        year: int

Purpose:
- lightweight structured data container
- auto-generates:
    - __init__
    - __repr__
    - __eq__

Key idea:
- use dataclass when object is mostly data

---

## __post_init__

    def __post_init__(self) -> None:
        if self.pages <= 0:
            raise ValueError(...)

        if self.year < 1000:
            raise ValueError(...)

Purpose:
- validation after dataclass initialization
- prevents invalid object state

Key principle:
- invalid data should fail immediately

---

## CLI Demonstration — main.py

Demonstrated:
- creating multiple Book objects
- shared class variable behavior
- dataclass auto-generated representation
- method usage
- object formatting

Verified:
- Book.total_books increments globally across instances

---

## Failure Design

user creates invalid object
→ ValueError raised immediately

shared state mutation
→ tracked through class variable

pure calculations
→ deterministic and testable

dataclass validation
→ invalid state blocked at creation

---

## Tests

    test_str_format()
    test_is_long()
    test_get_age()
    test_total_books()
    test_invalid_pages()
    test_invalid_year()

Validated:
- string formatting
- long-book logic
- age calculation
- shared state behavior
- validation guards

---

## Tools Used

- classes
- dataclasses
- instance variables
- class variables
- __init__
- __str__
- __post_init__
- pytest
- type hints
- f-strings

---

## Key Takeaways

1. Classes model state + behavior together
   → useful for agents, clients, workflows

2. Dataclasses reduce boilerplate
   → ideal for structured data containers

3. Class variables are shared globally
   → useful for counters and config

4. Pure methods are easier to test
   → inject dependencies instead of hardcoding

5. Validation belongs near object creation
   → fail fast on invalid state

6. Architecture matters even in small systems

CLI
→ object model
→ validation
→ tests