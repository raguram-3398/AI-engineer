# AI Engineer — Study Log

---

# 📘 Day 0 — Environment + Tooling Setup

## 🧠 Focus

Set up a complete Python development environment, Git workflow, and project structure for a 56-day AI Engineer learning plan.

---

## 📚 Key Concepts

- Local development environment setup  
- Python version management (pyenv)  
- Virtual environments (uv)  
- Git initialization and remote repository linking  
- SSH authentication with GitHub  
- Production-grade Python tooling setup (ruff, black, pytest)  

---

## 🧱 Build

AI Engineer Development Environment

Configured full local + remote development system:

- Python 3.12.0 installed and managed via pyenv  
- Virtual environment created using uv  
- Git repository initialized and connected to GitHub  
- VS Code configured as primary IDE  
- Development tools installed:
  - ruff
  - black
  - pytest
  - pytest-asyncio  
- Project structure created for weekly/daily learning system  

---

## 🧩 Structure
ai-engineer-plan/
├── .gitignore
├── README.md
└── week-1/
└── day-1/
├── .venv/
└── pytest.ini

---

## 🛠️ Tools Used

- Homebrew → system package manager  
- pyenv → Python version management  
- uv → virtual environment management  
- Git → version control system  
- GitHub → remote repository hosting  
- VS Code → code editor  
- Ruff → linting (code quality checks)  
- Black → code formatting  
- Pytest → testing framework  

---

## 🔁 Workflow Learned

Install tools  
→ Configure Python  
→ Create virtual environment  
→ Initialize Git repo  
→ Connect GitHub  
→ Install dev dependencies  
→ Verify tooling  

---

## ⚠️ Key Learnings

- Git tracks files only after `git add`  
- Virtual environments must be activated per session  
- VS Code changes must be saved before execution (Cmd + S)  
- Tooling (ruff/black/pytest) should live inside project environment  
- Project structure must be simple and scalable from day 1  

---

## 🚀 Outcome

- Fully functional Python development environment  
- GitHub-connected project workspace  
- Reproducible virtual environment setup  
- Installed production-grade Python tooling  
- Ready foundation for CLI project development  

---

# 📘 Day 1 — CLI Calculator + Dev Workflow

## 🧠 Focus

Python fundamentals + building a CLI calculator with proper engineering workflow using testing, linting, formatting, and Git.

---

## 📚 Key Concepts

- Variables and data types (int, str, float)  
- print() and input() behavior  
- Type conversion (int(input()))  
- Type hints for function contracts  
- Function decomposition (input → logic → output)  
- Tuple unpacking  
- Control flow (if / elif / else)  
- Error handling (try / except)  
- Loop-based input validation  

---

## 🧱 Build

CLI Calculator:

- Addition, subtraction, multiplication, division  
- Input validation for numbers and operators  
- Division-by-zero protection  
- Safe retry loops for invalid inputs  
- Error handling for non-numeric input  

Final behavior:

- User enters numbers and operation interactively  
- Invalid inputs are handled without crashing  
- Calculation returns correct result or error message  

---

## 🧩 Structure

- `get_numbers()` → handles numeric input + validation  
- `get_operation()` → handles operator validation  
- `calculate()` → core arithmetic logic + error handling  
- `main()` → orchestrates full program flow  

---

## 🛠️ Tools Used

- Ruff → linting (bugs, unsafe patterns, unused variables)  
- Black → auto-formatting  
- Pytest → unit testing (6/6 passed)  
- Git → version control + GitHub deployment  

---

## 🔁 Workflow Learned

Code  
→ Ruff  
→ Black  
→ Pytest  
→ Git Add  
→ Commit  
→ Push  

---

## ⚠️ Key Learnings

- `input()` always returns a string  
- VS Code must be saved before running code  
- Terminal ≠ Python input runtime  
- Git only tracks files after `git add`  
- Validation should be handled per step, not full restart  
- Functions should be modular (input / logic / output separation)  

---

## 🚀 Outcome

- Built first production CLI application  
- Implemented full validation + error handling system  
- Understood Python execution flow  
- Learned professional tooling workflow  
- Successfully shipped project to GitHub with tests

---

# 📘 Day 2 — Conditionals, Loops & Control Flow Systems (Number Guessing Game)

---

## 🧠 Focus

Build a CLI number guessing game while learning core **production control flow patterns**: conditionals, loops, validation boundaries, and safe termination logic.

---

## 📚 Key Concepts

- Conditional routing (`if / elif / else`)
- Loop patterns:
  - `while True + break`
  - bounded loops (`while condition`)
- Input validation vs business logic separation
- Pure logic vs IO separation (`game.py` vs `main.py`)
- Safe input handling with `try / except`
- Max iteration / termination guards
- Python import system (`PYTHONPATH=src`)
- Unit testing with pytest
- `src/` based project structure

---

## 🧱 Build

### 🎯 Number Guessing Game (CLI System)

- Random secret number within user-defined range  
- Safe range validation (`lower < upper`)  
- Input-safe guessing (no crashes)  
- Feedback signals:
  - `"too_high"`
  - `"too_low"`
  - `"correct"`
- Attempt counter tracking  
- Replay loop system  
- Fully modular structure (logic vs IO separation)

---

## 🧩 Structure

src/
└── guessing_game/
├── game.py → pure logic
├── main.py → IO + control flow

tests/
└── test_checkguess.py

---

## 🔧 Core Functions

### game.py
- `generate_secret_number(lower, upper)` → random number generator  
- `check_guess(guess, secret)` → returns comparison signal  
- `is_valid_range(lower, upper)` → validates range rule  

### main.py
- `get_range()` → safe range input loop  
- `get_guess()` → safe validated input loop  
- `play_game()` → main game loop with attempts + exit logic  
- `main()` → replay controller  

---

## 🧪 Testing

- Unit tests using :contentReference[oaicite:0]{index=0}  
- Tested `check_guess()`:
  - too high
  - too low
  - correct  
- All tests passed

---

## 🛠️ Tools Used

- ruff → code quality checks  
- black → formatting  
- pytest → unit testing  
- Git + GitHub → version control  
- PYTHONPATH → import resolution  

---

## 🔁 Workflow Learned

Code → Test → Lint → Format → Commit → Push

---

## ⚠️ Key Learnings

- Loops must always have termination conditions or safety limits  
- Input validation must be separate from business logic  
- Pure functions should not handle IO  
- `input()` always returns string → must be validated  
- Python imports depend on runtime config (`PYTHONPATH`)  
- `src/` layout requires explicit import handling  
- Infinite loops are production risks (APIs / agents)  

---

## 🚨 Engineering Insight

Any loop interacting with external input must have a **hard exit condition** (max attempts or break rule).

This directly maps to:
- API retry systems  
- LLM execution loops  
- AI agent orchestration (Week 7 preview)  

---

## 🚀 Outcome

- Built structured CLI guessing game  
- Implemented safe input + validation loops  
- Separated logic and IO layers (production pattern)  
- Introduced unit testing for core logic  
- Learned controlled loop design with termination guarantees  
- Understood Python import system via `src` architecture  

---

# 📘 Day 3 — Functions, Scope & Pure Logic Systems (Tip Calculator)

## 🧠 Focus

Learn production-safe function design using pure functions, scope boundaries, type hints, docstrings, and clean IO separation by building a modular tip calculator system.

---

# 📚 Key Concepts

- Function definition with `def`
- `return` vs `print`
- Function scope (local vs global)
- Pure functions vs side effects
- Type hints for function contracts
- Docstrings as API-style guarantees
- Guard clauses with `ValueError`
- Function composition
- Logic vs IO separation (`calculator.py` vs `main.py`)
- Deterministic function behavior
- Unit testing pure functions with `pytest`

---

# 🧱 Build

## 💰 Tip Calculator (Pure Function System)

Built a modular CLI tip calculator using production-style architecture:

- Tip calculation
- Total bill calculation
- Bill splitting per person
- Zero-division protection via `ValueError`
- Fully separated logic and IO layers
- Typed functions with docstrings
- Unit-tested pure computation layer

---

# 🧩 Structure

```text
week-1/day-3/
├── src/
│   └── tip_calculator/
│       ├── __init__.py
│       ├── calculator.py
│       └── main.py
└── tests/
    └── test_calculator.py
```

---

# 🔧 Core Functions

## calculator.py (Pure Logic Layer)

### calculate_tip(bill_amount, tip_percentage)

Returns calculated tip amount from bill and percentage.

### calculate_total(bill_amount, tip_amount)

Returns total bill amount including tip.

### split_bill(total_amount, num_people)

Returns per-person split amount.

Raises:
- ValueError if num_people <= 0

---

## main.py (IO + Program Flow Layer)

### get_bill_amount()

Gets and converts bill input from user.

### get_tip_percentage()

Gets and converts tip percentage input.

### get_num_people()

Gets and converts number of people input.

### main()

Controls application flow:

- collects input
- calls pure functions
- handles errors
- prints results

---

# 🧪 Testing

Unit tests written using pytest.

### Test coverage:

- calculate_tip() happy path
- calculate_total() happy path
- split_bill() happy path
- split_bill() raises ValueError on zero people

All tests passed successfully.

---

# 🛠️ Tools Used

- ruff → linting and code quality checks
- black → automatic formatting
- pytest → unit testing
- Git + GitHub → version control
- PYTHONPATH=src → import resolution

---

# 🔁 Workflow Learned

Code  
→ Ruff  
→ Black  
→ Pytest  
→ Git Add  
→ Commit  
→ Push  

---

# ⚠️ Key Learnings

- return gives reusable output; print() only displays output
- Pure functions should not use input() or print()
- Same input should always produce same output
- Global state creates unpredictable behavior
- Validation should live inside the function that owns the rule
- Small pure functions compose better than large mixed functions
- Docstrings describe function promises, not implementation details
- Type hints improve reliability and readability
- IO boundaries must stay isolated from business logic

---

# 🚨 Engineering Insight

A production-safe function:

- takes explicit input
- operates only on local data
- returns deterministic output
- does not modify external state

This directly maps to:

- token counters
- PII scrubbers
- retry wrappers
- cost calculators
- AI preprocessing pipelines

Pure functions are the foundation of testable AI systems.

---

# 🚀 Outcome

Built first fully modular pure-function application.

Implemented:

- typed function contracts
- scope-safe logic
- guard clause validation
- deterministic computation layer
- clean IO separation
- unit-tested pure functions

Understood how production systems isolate:

- business logic
- side effects
- validation

---

# 📘 Day 4 — Lists, State Transformation & Todo CLI System

---

## 🧠 Focus

Learn how to model real-world state using `list[str]` and build predictable state transformation functions through a fully typed Todo CLI system with strict separation between **pure logic (tasks.py)** and **IO orchestration (main.py)**.

This introduces the core AI engineering concept of **collection-based state management**, used in:
- chat history pipelines
- retrieval systems
- token trimming
- agent memory systems

---

## 📚 Key Concepts

- list[str] as application state
- Indexing and slicing as transformation tools
- Pure vs impure list operations
- In-place mutation vs returning new state
- Centralized validation via is_valid_index()
- Guard clauses using ValueError
- Separation of:
  - business logic (tasks.py)
  - IO + control flow (main.py)
- CLI loop as state transition engine

---

## 🧱 Build

Todo CLI system where all state is:

    tasks: list[str]

Every operation returns a NEW list instead of mutating state.

Core behavior:
- add tasks
- remove tasks
- complete tasks
- validate indices
- menu-driven CLI loop

---

## 🧩 Structure

week-1/day-4/
├── src/
│   └── todo/
│       ├── __init__.py
│       ├── tasks.py
│       └── main.py
└── tests/
    └── test_tasks.py

---

## 🔧 Core Functions

### tasks.py (Pure Logic Layer)

add_task(tasks, task) -> list[str]
- returns tasks + [task]
- does NOT mutate original list

remove_task(tasks, index) -> list[str]
- validates index
- returns tasks[:index] + tasks[index+1:]
- raises ValueError if invalid

complete_task(tasks, index) -> list[str]
- transforms task into "[DONE] task"
- rebuilds list using slicing
- returns new list

get_task(tasks, index) -> str
- returns single task safely
- validates index first

is_valid_index(tasks, index) -> bool
- returns 0 <= index < len(tasks)
- shared validation rule

---

### main.py (IO Layer)

display_tasks(tasks)
- prints indexed tasks
- no logic

get_menu_choice()
- reads user input

get_task_input()
- reads task string

get_index_input(tasks)
- loops until valid index is entered
- uses is_valid_index()

main()
- owns application state: tasks = []
- runs menu loop:
  1 view
  2 add
  3 complete
  4 remove
  5 quit
- reassigns state after every operation

---

## 🧪 Testing

pytest focuses ONLY on tasks.py

Tests verify:
- correct output
- immutability
- error handling
- validation logic

Example pattern:

def test_add_task():
    tasks = ["study"]

    result = add_task(tasks, "exercise")

    assert result == ["study", "exercise"]
    assert tasks == ["study"]

---

## 🛠️ Tools Used

- ruff → linting
- black → formatting
- pytest → testing
- Git + GitHub → version control
- PYTHONPATH=src → import resolution

---

## 🔁 Workflow

Code → Ruff → Black → Pytest → Git Add → Commit → Push

---

## ⚠️ Key Learnings

- Lists are application state
- Slicing = safe transformation
- append/remove mutate state (avoid in pure logic)
- validation must be centralized
- IO must never mix with logic
- functions should return new state
- CLI = state transition loop
- guard clauses prevent invalid system states

---

## 🚨 Engineering Insight

State pipeline:

    input state → validate → transform → output state

Maps directly to:
- AI memory systems
- chat history trimming
- retrieval pipelines
- agent execution loops

Todo CLI = simplified state engine used in production systems.

---

## 🚀 Outcome

Built a fully typed state-driven CLI system with:

- immutable transformations
- strict validation layer
- clean IO separation
- testable pure functions
- production-style architecture

---

# 📘 Day 5 — Dictionaries, Sets & Word Frequency System

## 🧠 Focus

Learn how production systems represent structured state using dictionaries and sets, and build a fully typed word frequency engine with clean separation between pure logic (`counter.py`) and IO orchestration (`main.py`).

This is the first real step into AI-style data pipelines where raw text is transformed into structured, queryable state.

---

## 📚 Key Concepts

- `dict[str, int]` as structured state (token → count mapping)
- `.get()` pattern for safe incremental updates
- `.items()` for key-value iteration
- `.values()` for aggregation
- `set[str]` for uniqueness tracking
- `sorted()` with key functions for ranking
- tuple pairs `(word, count)` as structured outputs
- pure functions vs IO separation
- empty input as valid system state
- deterministic transformations

---

## 🧱 Build

Word Frequency Analysis System:

Transforms raw text into structured frequency insights.

Pipeline:

raw text  
→ normalization  
→ tokenization  
→ counting  
→ ranking  
→ reporting  

Core features:
- lowercase normalization
- punctuation removal
- word frequency counting
- top-N word extraction
- unique word counting
- total word volume calculation

---

## 🧩 Structure

week-1/day-5/
├── src/
│   └── word_counter/
│       ├── __init__.py
│       ├── counter.py
│       └── main.py
└── tests/
    └── test_counter.py

---

## 🔧 Core Functions

### counter.py (Pure Logic Layer)

clean_text(text)
- lowercases input
- removes punctuation
- returns normalized string

count_words(text)
- builds frequency dictionary using `.get(key, 0) + 1`
- returns `{}` for empty input

get_top_words(counts, n)
- sorts dictionary using value-based sorting
- returns top-N `(word, count)` tuples

get_unique_word_count(counts)
- returns `len(counts)`

get_total_word_count(counts)
- returns `sum(counts.values())`

---

### main.py (IO Layer)

get_text_input()
- reads raw multiline input
- returns full string

display_results(counts, n)
- formats output
- calls pure functions for derived metrics
- handles empty dictionary safely

main()
- orchestrates flow:
  input → process → analyze → display

---

## 🧪 Testing

Tests focus only on pure logic functions:

- clean_text normalizes correctly
- count_words produces correct frequency map
- empty input returns empty dict
- get_top_words returns correctly sorted output
- aggregate functions return correct totals

Testing principle:
pure functions = deterministic + testable

---

## 🛠️ Tools Used

- ruff → linting
- black → formatting
- pytest → unit testing
- Git + GitHub → version control
- Python typing → structured contracts

---

## 🔁 Workflow

Code  
→ Clean  
→ Test  
→ Lint  
→ Format  
→ Commit  
→ Push  

---

## ⚠️ Key Learnings

- dictionaries model structured state efficiently
- `.get()` prevents key errors in incremental counting
- sets enforce uniqueness automatically
- `.items()` enables structured iteration
- `.values()` enables aggregation without keys
- sorted() converts unordered state into ranked output
- empty input must be handled as valid state
- pure functions ensure repeatable behavior
- IO must remain separate from transformation logic

---

## 🚨 Engineering Insight

This system is a full text-to-state transformation pipeline:

raw text  
→ normalization  
→ tokenization  
→ aggregation  
→ ranking  
→ reporting  

This is the same architecture used in:
- embedding pipelines
- retrieval systems
- log aggregation systems
- cost tracking systems
- dataset preprocessing layers

Core principle:

state must be deterministic, not accidental

---

## 🚀 Outcome

Built a production-style word frequency engine with:

- structured dictionary-based state model
- safe incremental counting
- deterministic ranking system
- clean IO vs logic separation
- fully testable pure functions
- reusable transformation pipeline design

Foundation established for multi-stage data pipelines in Week 6

---

# 📘 Day 6 — Strings, F-Strings & Text Analyzer System

## 🧠 Focus

Learn production-safe string processing using Python string methods and f-strings by building a fully typed text analysis pipeline with strict separation between pure logic (`analyzer.py`) and IO orchestration (`main.py`).

This is the foundation of real AI text pipelines: prompts, logs, transcripts, and embeddings all start as strings.

---

## 📚 Key Concepts

- `.split()` for tokenization
- `.strip()` for whitespace cleanup
- `.join()` for reconstruction
- `.lower()` for normalization
- `.isalpha()` for filtering noise
- `re.split()` for multi-delimiter splitting
- f-strings for formatted output
- `:.2f` precision formatting
- dictionary-based composite return types
- tuple unpacking in loops
- deterministic sorted outputs
- empty input as valid state

---

## 🧱 Build

Text Analyzer System:

Transforms raw text into structured metrics.

Pipeline:

raw text  
→ normalization  
→ splitting  
→ filtering  
→ aggregation  
→ reporting  

Core features:
- word count
- sentence count
- average word length
- character frequency
- top word ranking
- unique word count
- formatted CLI output

---

## 🧩 Structure

week-1/day-6/
├── src/
│   └── text_analyzer/
│       ├── __init__.py
│       ├── analyzer.py
│       └── main.py
└── tests/
    └── test_analyzer.py

---

## 🔧 Core Functions

### analyzer.py (Pure Logic Layer)

count_sentences(text)
- splits using punctuation delimiters
- filters empty segments

count_words(text)
- uses whitespace split
- returns 0 for empty input

get_average_word_length(text)
- removes punctuation using character filter
- guards against division by zero

get_character_frequency(text)
- lowercases input
- counts alphabetic characters only

get_top_words(text, n)
- normalizes text
- builds frequency map
- sorts by frequency descending

get_summary(text)
- returns combined dictionary of all metrics
- reuses pure functions

---

### main.py (IO Layer)

get_text_input()
- collects multiline input
- stops on empty line
- joins lines into single string

display_analysis(text)
- calls analyzer functions
- formats output using f-strings
- prints top words and character frequency

main()
- controls execution flow
- handles empty input safely

---

## 🧪 Testing

Tests cover:

- sentence counting accuracy
- word counting correctness
- punctuation stripping behavior
- average word length precision handling
- character filtering rules
- summary dictionary structure

Testing principle:
pure functions = deterministic + fully testable

---

## 🛠️ Tools Used

- ruff → linting
- black → formatting
- pytest → unit testing
- Git + GitHub → version control
- Python typing → structured contracts

---

## 🔁 Workflow

Code  
→ Clean  
→ Test  
→ Lint  
→ Format  
→ Commit  
→ Push  

---

## ⚠️ Key Learnings

- `.split()` handles whitespace edge cases automatically
- `.strip()` prevents hidden whitespace bugs
- `.join()` reconstructs cleaned tokens
- `.isalpha()` isolates valid characters
- `re.split()` enables multi-delimiter parsing
- empty input must never crash the system
- dictionaries enable structured multi-metric returns
- sorted outputs ensure deterministic behavior
- f-strings provide clean production formatting

---

## 🚨 Engineering Insight

This system represents a full string-to-insight pipeline:

raw text  
→ cleaning  
→ tokenization  
→ filtering  
→ aggregation  
→ reporting  

This is identical to production systems used in:
- prompt engineering pipelines
- log analysis systems
- PII scrubbing tools
- embedding preprocessing
- chatbot memory processing

Core principle:

strings are the universal input format of AI systems

---

## 🚀 Outcome

Built a production-style text analysis engine with:

- robust string processing pipeline
- deterministic aggregation logic
- composite metric dictionary output
- clean IO vs logic separation
- fully testable pure functions
- formatted CLI reporting layer

Foundation established for prompt pipelines and structured text processing in Week 7

---

# 📘 Day 8 — File I/O + Log Parser System (Production Ingestion Pipeline)

---

## 🧠 Focus

Build a resilient file ingestion system that converts raw log files into structured typed data while safely handling missing files, malformed lines, and external data failures without crashing.

This is the foundation of real-world systems like log processors, dataset loaders, and AI ingestion pipelines.

---

## 📚 Key Concepts

- context managers for safe file handling (`with open`)
- pathlib for OS-independent file paths
- line-by-line streaming for memory efficiency
- structured parsing into dataclasses
- graceful failure handling using `None` pattern
- separation of IO vs pure logic
- aggregation using dictionary patterns
- filtering without mutating input state

---

## 🧱 Build

Log Parser Pipeline:

raw log file  
→ file validation  
→ streaming read  
→ line parsing  
→ skip malformed entries  
→ structured LogEntry objects  
→ filtering + aggregation  

Failure rules:
- missing file → raise FileNotFoundError  
- empty file → return empty list  
- malformed line → skip safely  

---

## 🧩 Structure

week-2/day-1/  
├── src/  
│   └── log_parser/  
│       ├── __init__.py  
│       ├── parser.py  
│       └── main.py  
└── logs/  
    └── sample.log  

---

## 🔧 Core Functions

### parser.py (logic layer)

LogEntry:
    date: str  
    time: str  
    level: str  
    message: str  

parse_line(line: str) → LogEntry | None  
    split line using maxsplit=3  
    return None if invalid  
    return structured LogEntry  

parse_log_file(filepath: Path) → list[LogEntry]  
    check file exists  
    open file using context manager  
    iterate line-by-line  
    skip invalid lines  
    return list of LogEntry  

filter_by_level(entries, level: str) → list[LogEntry]  
    return new filtered list  
    no mutation  

get_level_counts(entries) → dict[str, int]  
    use dict.get(key, 0) + 1 pattern  
    return frequency map  

---

### main.py (IO layer)

display_entries(entries)  
    print formatted logs  

display_summary(entries)  
    print level counts  

main()  
    build path using Path(__file__).parent  
    call parse_log_file  
    display results  

---

## 🧪 Testing

Tests cover:
- valid parsing into LogEntry  
- malformed line returns None  
- filtering correctness  
- count aggregation accuracy  
- missing file raises error  
- malformed lines are skipped safely  

Principle: pure logic = deterministic + fully testable

---

## 🛠️ Tools Used

- pathlib → safe OS-independent paths  
- with open → guaranteed resource cleanup  
- dataclasses → structured data model  
- pytest → unit testing  
- ruff → linting  
- black → formatting  
- Git + GitHub → version control  

---

## 🔁 Workflow

code  
→ validate file  
→ parse safely  
→ transform data  
→ test logic  
→ lint  
→ format  
→ commit  
→ push  

---

## ⚠️ Key Learnings

- external files are always unreliable  
- file operations must always use context managers  
- parsing must isolate bad data, not crash system  
- `None` is a valid signal for invalid input  
- IO must be separate from business logic  
- pathlib removes environment dependency issues  
- streaming files is more scalable than loading into memory  
- aggregation patterns repeat across all data systems  

---

## 🚨 Engineering Insight

This system is a minimal ingestion engine:

raw file → validation → parsing → filtering → aggregation → output  

This is identical to:
- AI document loaders  
- log ingestion systems  
- ETL pipelines  
- embedding preprocessing systems  

Core principle:

never trust external input → always design for failure  

---

## 🚀 Outcome

Built a production-style log ingestion pipeline with:

- safe file handling  
- structured parsing with dataclasses  
- resilient failure handling  
- pure function separation  
- streaming-based processing  
- aggregation + filtering utilities  
- fully testable architecture  

---

