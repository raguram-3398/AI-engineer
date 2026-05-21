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