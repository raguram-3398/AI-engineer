# Todo CLI

**What it does:** A simple to-do list in the terminal. From a menu you can view your tasks, add one, mark one as done, remove one, or exit. Empty tasks and task numbers that don't exist are rejected with a clear message, and a task can't be marked done twice.

**Why it's here:** My first program that manages a changing list of data. Every change creates a new, updated list instead of editing the old one in place, which makes the behavior predictable and easy to test. The tests check that the original list is never changed by accident.

**What I learned:**

- Managing state safely
- Menu-driven programs
- Testing edge cases like invalid positions

**Run it:** `uv run python -m todo.main` · Tests: `uv run pytest` (7 passing)
