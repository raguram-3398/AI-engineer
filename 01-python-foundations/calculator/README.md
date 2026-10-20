# Calculator

**What it does:** A small command-line calculator. You type two numbers and an operation (+, −, ×, ÷), and it gives the answer. If you type something that isn't a number or a valid operation, it asks again instead of crashing. Dividing by zero gets a clear message instead of an error screen.

**Why it's here:** My first project. It's where I learned to keep the "math" part separate from the "talking to the user" part, so the math can be checked automatically. Every later project, including the AI ones, follows that same split.

**What I learned:**

- Separating logic from input/output
- Handling bad input gracefully
- Writing automated tests

**Run it:** `uv run python -m calculator.main` · Tests: `uv run pytest` (6 passing)
