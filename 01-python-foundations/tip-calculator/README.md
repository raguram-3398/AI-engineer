# Tip Calculator

**What it does:** Splits a restaurant bill. You enter the bill, the tip percentage and how many people are paying; it shows the tip, the total and what each person owes. Typing a negative number, zero or letters gets a retry prompt instead of a crash.

**Why it's here:** A small, everyday problem with real money math. The calculations live in their own file and are tested on their own, including the case of splitting between zero people, which is rejected with a clear message.

**What I learned:**

- Small pure functions that each do one job
- Guarding against impossible inputs
- Testing that errors are raised when they should be

**Run it:** `uv run python -m tip_calculator.main` · Tests: `uv run pytest` (4 passing)
