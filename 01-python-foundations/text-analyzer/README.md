# Text Analyzer

**What it does:** Paste in a paragraph and get a quick report: how many words and sentences it has, how many different words, the average word length, the five most used words, and how often each letter appears.

**Why it's here:** The last and largest of the foundation projects — it combines everything before it into one tool, with 14 automated tests covering tricky cases like extra spaces, punctuation and empty text. Known limit: a decimal number like "3.14" is counted as a sentence break, because sentences are split on . ! and ?.

**What I learned:**

- Breaking a bigger problem into small, testable pieces
- Pattern matching on text
- Writing tests for edge cases first

**Run it:** `uv run python -m text_analyzer.main` · Tests: `uv run pytest` (14 passing)
