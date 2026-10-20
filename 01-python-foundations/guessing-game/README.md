# Guessing Game

**What it does:** The computer picks a secret number in a range you choose, and you try to guess it. After each guess it tells you "too high" or "too low", and when you get it right it tells you how many tries it took. Invalid input (letters, numbers outside the range, a range that doesn't make sense) gets a friendly retry prompt.

**Why it's here:** It's my first program with a real loop and state — it keeps track of the secret number and the attempts until the game ends. The game rules are kept separate from the screen prompts, so the rules can be tested automatically, including that the random number always stays inside the range.

**What I learned:**

- Loops with a clear stop condition
- Validating user input
- Testing code that uses randomness

**Run it:** `uv run python -m guessing_game.main` · Tests: `uv run pytest` (6 passing)
