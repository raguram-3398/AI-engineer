# Pinecone Vector Store

**What it does:** Moves document search from my laptop into Pinecone, a cloud database built for AI search. Every stored piece of text carries labels — which document, which page, what date, and which AI model turned it into numbers. The test asks: when a company has an old (2024) and a new (2026) version of the same policy with nearly identical wording, can search return the right version? Without labels it can't tell them apart; with a date filter it can.

**Why it's here:** Getting the wrong version of a policy is a quiet, dangerous failure: the answer looks right and is out of date. Labeling every piece with its date and its model also makes it safe to switch AI models later without mixing incompatible data.

**Result:** On 12 questions that each have an old and a new answer, search without a date filter found the right version only 6 times. Every one of the 6 misses returned the same page from the other year: a convincing but outdated (or not-yet-valid) answer. With the date filter it found the right version all 12 times. Questions with only one possible answer were right every time either way (6 of 6).

**What I learned:**

- Cloud vector databases
- Filtering search by labels like date and source
- Recording which model built the index

**Run it:** `uv run python -m vectorstore.main` (needs a free Pinecone key in `.env`) · Tests: `uv run pytest` (36 passing, no network needed)
