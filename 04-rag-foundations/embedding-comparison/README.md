# Embedding Comparison

**What it does:** AI search works by turning sentences into lists of numbers that capture meaning. This project puts two popular free models (MiniLM and BGE) head to head on the same tests: can they tell that two differently-worded sentences mean the same thing, and can they be fooled by sentences that share words but mean something different? It also checks my own similarity math against the library's.

**Why it's here:** It shows where meaning-based search breaks. That's why my later search engine adds keyword search and a second "re-checking" model on top.

**Result:**
- On 21 realistic questions over 16 policy passages, both models put the right passage first 18 times; BGE had it in the top 3 every time, MiniLM 20 of 21.
- On 25 deliberately tricky sentence pairs, MiniLM passed 3 and BGE 8. Both failed every "who did what to whom" case: "The vendor sued the client" and "The client sued the vendor" look almost identical to them (similarity 0.998).
- BGE's recommended search instruction didn't help on this data.
- My hand-written similarity math matched the library to 7 decimal places.

**What I learned:**

- What embeddings capture and what they miss (negation, numbers, who-did-what)
- Comparing models on the same test set
- Why a search index must be rebuilt when the model changes

**Run it:** `uv run python -m embeddings.main` (first run downloads both models) · Tests: `uv run pytest` (50 passing; real-model test: `uv run pytest -m slow`)
