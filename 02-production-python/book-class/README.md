# Book Class

**What it does:** Models books in code two ways side by side — a regular class and a "dataclass" — each knowing its title, author, page count and year. A book can describe itself, say whether it's a long read (over 300 pages) and how old it is. The dataclass version also rejects impossible data, like zero pages or a year before 1000.

**Why it's here:** It's where I learned when to use which building block: a class when something has both data and behavior, a dataclass when it's mostly data, and a plain function when it's just a transformation. That rule shaped how every later project is organized.

**What I learned:**

- Classes vs. dataclasses
- Validating data when it's created
- Shared counters across all objects

**Run it:** `uv run python -m books.main` · Tests: `uv run pytest` (7 passing)
