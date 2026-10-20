# Log Parser

**What it does:** Reads a server log file — the running diary a system writes about what it's doing — and turns each line into structured data: date, time, severity (INFO, WARNING, ERROR) and message. It then prints a summary of how many entries of each severity there are and how many errors occurred. Broken or incomplete lines are skipped instead of crashing the program.

**Why it's here:** My first program that works with real files and messy real-world data. Reading logs is how engineers find out what went wrong in a live system, and the same habits — skip bad input, fail clearly when the file is missing — carry into every later project.

**What I learned:**

- Reading files safely
- Turning raw text into structured records
- Handling missing files and malformed lines

**Run it:** `uv run python -m log_parser.main` · Tests: `uv run pytest` (7 passing)
