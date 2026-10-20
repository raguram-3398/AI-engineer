# FAISS From Scratch

**What it does:** Searches 20 short tech statements by meaning, not by matching words. Ask "protecting customer data" and it finds "Customer information is encrypted before being stored" — even though the two share almost no words. It runs the same search three ways (two using FAISS, a search library used in industry, and one I wrote myself with plain math) and shows the results side by side.

**Why it's here:** This is the core idea behind every AI search and chat-over-documents system: turn text into numbers that capture meaning, then find the closest match. Building it by hand first meant I understood exactly what the library does before relying on it.

**What I learned:**

- Turning text into meaning vectors (embeddings)
- Similarity search
- Checking a library's results against my own implementation

**Result:** All three methods returned the same top 3 matches, in the same order, for all 3 test questions, with identical scores, so my hand-written version matches the library exactly. One honest miss: for "cost of ownership" the top match was a sentence that only shares the word "ownership", and the real answer ("total spend … $20,000") came second. Meaning-based search can still be pulled toward shared words.

**Run it:** `uv run python src/main.py` (first run downloads a small model)
