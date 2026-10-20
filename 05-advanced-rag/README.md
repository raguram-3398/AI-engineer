# Advanced RAG — Multimodal RAG Engine

**What it is:** A question-answering system over 52 real FDA documents (2,313 pages of slide decks full of charts, plus two regulatory books). Ask a question in plain English and it finds the right pages, answers with a citation to the exact PDF and page for every claim, and says "not in the documents" instead of guessing when the answer isn't there. Every change to it was measured with an automatic quality test before it was kept.

**Real numbers** (the final system, run 5 times unchanged):
- 92% of the claims in its answers are supported by the pages it cites
- Declined all 20 trick questions whose answers aren't in the documents
- Finds a page that holds the answer in its top 10 results for 64% of 364 benchmark questions
- About $0.001 per answer, and 4–5 seconds to an answer on free cloud hardware

**How it works, briefly:** Pages are read (with text recognition for scanned pages, and AI-written descriptions of 524 chart-heavy slides), split into pieces and stored in a cloud search index. A question is matched by both meaning and keywords, the best pages are re-checked by a second model, and Claude writes the answer with citations. An evaluation pipeline scores every change against a fixed baseline and blocks any change that makes answers worse.

**What I learned:**

- Building a full document Q&A system end to end, from PDF to live app
- Measuring answer quality automatically (RAGAS, an AI judge) and using it to accept or reject changes
- Making charts and scanned pages searchable
- Knowing when an AI should decline to answer
- Setting a fixed baseline so quality can't slowly drift down

**Where it lives:** It has its own repository and a live demo:
- Code: [github.com/raguram-3398/Multimodal-RAG-Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine)
- Live demo: [huggingface.co/spaces/raguram3398/Multimodal-RAG-Engine](https://huggingface.co/spaces/raguram3398/Multimodal-RAG-Engine)
