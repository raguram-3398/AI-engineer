# Chunking Comparison

**What it does:** Before an AI can search a document, the document has to be cut into small pieces ("chunks"). This project cuts the same 3-page handbook three different ways — every 800 characters, along paragraph and sentence breaks, and wherever the topic changes — then measures which way produces cleaner pieces and finds the right answers more often. It also loads text files and web pages the same way, so every piece knows which document and page it came from.

**Why it's here:** How you cut a document decides what the AI can find. A piece that stops halfway through a sentence can hide the answer. Measuring the choice, instead of guessing, is a habit that carried straight into my larger document search engine.

**Result:** All three found the right passage for 5 of 6 test questions. The difference was quality: cutting by topic split only 4 pieces mid-sentence, versus 17 and 19 for the other two, using fewer, fuller pieces (17 instead of 25).

| Method | Pieces | Average size (tokens) | Cut mid-sentence | Questions answered in top 3 |
|---|---|---|---|---|
| Every 800 characters | 25 | 130 | 19 | 5 of 6 |
| Paragraph and sentence breaks | 25 | 124 | 17 | 5 of 6 |
| Topic changes | 17 | 166 | 4 | 5 of 6 |

**What I learned:**

- Loading PDFs, text and web pages
- Three chunking methods and their trade-offs
- Measuring retrieval with a simple score instead of eyeballing

**Run it:** `uv run python -m chunking.main` · Tests: `uv run pytest` (20 passing; real-model test: `uv run pytest -m slow`)
