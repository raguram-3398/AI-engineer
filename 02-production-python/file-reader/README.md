# File Reader

**What it does:** Reads a simple "key: value" text file (like name, age, city) and shows two things: a health check of the file — how many lines were valid and how many were broken — and the cleaned-up data itself. A missing file, an empty file or a broken line each gets its own clear, specific message instead of a crash.

**Why it's here:** It's where I learned to define my own error types, so the program can tell the difference between "the file isn't there", "the file is empty" and "this line is malformed", and react to each one properly. Every later project, including the AI ones, uses this pattern at the points where it talks to outside systems.

**What I learned:**

- Custom error types
- Failing clearly vs. skipping bad data
- Testing that the right error is raised

**Run it:** `uv run python -m file_reader.main` · Tests: `uv run pytest` (5 passing)
