# Word Counter

**What it does:** Paste in any text and it tells you how many words it has, how many different words, and the five most common ones. Capital letters and punctuation are ignored, so "Hello," and "hello" count as the same word.

**Why it's here:** My first text-processing program — cleaning messy text and counting it. It's the same kind of work an AI pipeline does before text reaches a model: normalize it first, then measure it.

**What I learned:**

- Cleaning text
- Counting with dictionaries
- Sorting results
- Handling empty input

**Run it:** `uv run python -m word_counter.main` · Tests: `uv run pytest` (6 passing)
