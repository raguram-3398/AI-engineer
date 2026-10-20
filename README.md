# From Python to Production AI: The Build Log

How I learned to build reliable AI software, one tested project at a time.

Every folder here is a small, self-contained project with a plain-language README. They build on each other, from command-line tools to two AI products that are live online.

---

## Featured Projects

| Project | What it does | Headline numbers | Links |
|---|---|---|---|
| **Sales Call Intelligence** | Upload a sales call recording; get its objections, action items, sentiment and summary, streamed live. Private details are removed before the AI sees the call. | about $0.06 per call · 95% of code covered by tests · 27 of 27 personal details removed in the privacy test | [Code](https://github.com/raguram-3398/Sales-Intelligence) · [Live demo](https://huggingface.co/spaces/raguram3398/sales-intelligence) |
| **Multimodal RAG Engine** | Ask questions about 52 FDA documents (2,313 pages, many of them charts); every answer cites the exact PDF and page, and it says so when the answer isn't there. | 92% of answer claims supported by the cited pages · 20 of 20 trick questions declined · about $0.001 per answer | [Code](https://github.com/raguram-3398/Multimodal-RAG-Engine) · [Live demo](https://huggingface.co/spaces/raguram3398/Multimodal-RAG-Engine) |

---

## Learning Path

| Stage | What I built | Key skill |
|---|---|---|
| [01 · Python Foundations](01-python-foundations/) | 6 command-line tools: calculator, guessing game, tip calculator, to-do list, word counter, text analyzer | Keeping the logic separate from the screen, so it can be tested |
| [02 · Production Python](02-production-python/) | Log parser, file reader, weather API client, book class | Real files, outside services, clear errors and validated data |
| [03 · LLM APIs](03-llm-apis/) | **Sales Call Intelligence** | Calling AI models safely: streaming, structured output, privacy, cost |
| [04 · RAG Foundations](04-rag-foundations/) | 5 experiments: search from scratch, chunking, embeddings, Pinecone, citations | Measuring search quality instead of guessing |
| [05 · Advanced RAG](05-advanced-rag/) | **Multimodal RAG Engine** | A full document Q&A system, gated by automatic quality tests |
<!-- next stages are added here -->

---

## Software Engineering Concepts

The practices behind every project, grouped by stage of the software lifecycle. Click a stage to open it.

<details>
<summary><b>Planning & Requirements</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Definition of done | A written checklist a project must pass before it's called finished | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Scoping and trade-offs | Every project says what was left out and why, so the gaps are decisions, not accidents | both projects, [04](04-rag-foundations/) |
| Cost estimation | Estimate what a run will cost before running it, then report the real figure | [citation tracking](04-rag-foundations/citation-tracking/), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Decision records | Each design choice is recorded with the measurement behind it, kept or turned off | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Design & Architecture</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Separation of concerns | The math and the user prompts live in different files, so the math can be tested on its own | every project in [01](01-python-foundations/) |
| Pure functions and immutable data | Functions return new results instead of changing their inputs, so behavior is predictable | [to-do list](01-python-foundations/todo-cli/), [tip calculator](01-python-foundations/tip-calculator/) |
| Layered architecture | Routes, data models, services and utilities each have their own layer | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Pipeline with typed contracts | Each stage hands the next a well-defined data type: page → passage → search hit → citation → answer | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Dependency boundaries | The live app never loads the heavy document-reading libraries it doesn't need | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Right tool for the data | A class when something has data and behavior, a dataclass for plain data, a function for a transformation | [book class](02-production-python/book-class/) |
| Validation at the boundary | Data from outside is checked against an expected shape before it's used | [weather client](02-production-python/weather-client/), [book class](02-production-python/book-class/) |
| Interfaces and dependency injection | Code depends on a small interface, so tests can plug in a fake instead of a real AI model | [chunking](04-rag-foundations/chunking-comparison/), [embeddings](04-rag-foundations/embedding-comparison/), [citations](04-rag-foundations/citation-tracking/) |
| Central configuration | All settings and limits live in one place with clear names | [04](04-rag-foundations/), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Feature flags | A behavior can be switched on or off with one setting, without changing code | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Create expensive resources once | AI models and API clients are loaded once and shared, not rebuilt for every request | [04](04-rag-foundations/), both projects |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Implementation</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Types and documented contracts | Every function states what it takes, what it returns and what can go wrong | every project |
| Input validation | Bad input gets a clear retry prompt instead of a crash | every project in [01](01-python-foundations/) |
| Typed errors | Each failure has its own named error, raised early and handled in one place | [file reader](02-production-python/file-reader/), [04](04-rag-foundations/), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Timeouts and graceful degradation | No outside call can hang forever; if a service is down, the user gets a clear message | [weather client](02-production-python/weather-client/), both projects |
| Retries | A failed or malformed AI response is retried with the error fed back | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Rate-limit handling | When the search service is busy, the app says "try again" instead of crashing | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Async and streaming | Results appear on screen as the AI writes them | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Structured logging | Every log line carries a request ID, so one request can be traced end to end | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Cost tracking | The cost of every AI call is measured and shown | both projects, [citation tracking](04-rag-foundations/citation-tracking/) |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Security & Privacy</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Secrets out of the code | API keys live in a local file that is never committed; an example file shows which keys are needed | every repo |
| Bring your own key | Visitors use their own API key, kept only for their browser session and never stored | both live demos |
| Removing personal data | Names, emails, phone and card numbers are removed before the AI sees a call and before anything is logged | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Prompt-injection guard | User input is screened for common attempts to override the AI's instructions (a simple pattern check) | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Least access | Each container gets only the keys it actually needs | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Testing & Quality</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Automated unit tests | Each piece is checked by code, including the awkward cases: zero, empty, invalid, missing | every project |
| Fakes and mocks | Tests run without internet or AI models by swapping in stand-ins | [04](04-rag-foundations/), [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Slow tests kept separate | Quick tests run all the time; tests that load real models run on request | [04](04-rag-foundations/) |
| Regression tests | A bug that was found gets a test, so it can't come back unnoticed | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Code coverage | 95% of the code is exercised by tests | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
| Linting and formatting | One code style everywhere, checked automatically (ruff, black) | every project |
| Continuous integration | Tests run automatically on every push | [Sales Call Intelligence](https://github.com/raguram-3398/Sales-Intelligence) |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Evaluating AI Systems</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Answer keys for search | Search is scored against a list of the right answers, not judged by eye | [chunking](04-rag-foundations/chunking-comparison/), [embeddings](04-rag-foundations/embedding-comparison/), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Before-and-after measurement | Every change is tested with and without it, on the same questions | [citation tracking](04-rag-foundations/citation-tracking/), [chunking](04-rag-foundations/chunking-comparison/), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| AI-graded and human-checked answers | Answers are scored by RAGAS and an AI judge, and a sample is read by a person | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Tests that can fail | A deliberately bad change was made to prove the quality test catches it | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Quality gate with a fixed baseline | A change is rejected if any score drops more than normal run-to-run variation | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Reproducibility | Each result records exactly which code and data produced it, and runs are compared on the same machine | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Held-out test set | The questions used to grade the system are never used to tune it | [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Build & Deployment</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Reproducible environments | Exact dependency versions are locked, so the project installs the same way everywhere (uv, lockfile) | every repo |
| Containers | The app is packaged with everything it needs and runs the same on any machine (Docker) | both projects |
| Local orchestration | One command starts the app locally (docker compose) | both projects |
| Cloud deployment | Both apps are live on Hugging Face Spaces, with keys stored as secrets | both projects |
| Blast radius and rollback | Before deploying: what breaks if this fails, and exactly how to undo it, for code and for data | both projects |
<!-- next stages' concepts are added here -->

</details>

<details>
<summary><b>Operations & Maintenance</b></summary>

| Concept | In plain words | Where I used it |
|---|---|---|
| Data versioning | The search index is versioned and records which AI model built it, with a written rebuild procedure | [Pinecone vector store](04-rag-foundations/pinecone-vectorstore/), [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Safe refactoring | Code is restructured without changing behavior, and the results are checked to be identical | this repo, [Multimodal RAG Engine](https://github.com/raguram-3398/Multimodal-RAG-Engine) |
| Version control | Small, clearly described commits; every change reviewed before it's committed | every repo |
| Documentation for two audiences | READMEs a non-technical reader can follow, with the technical detail further down | every repo |
| Known limitations | Each project states honestly what it can't do yet | both projects, [text analyzer](01-python-foundations/text-analyzer/) |
<!-- next stages' concepts are added here -->

</details>

---

## How Every Project Is Built

- One code style, checked automatically (ruff + black)
- Type hints and a docstring on every function
- A time limit on every call to an outside service
- Real measured numbers in every README, never vague claims
- An honest list of what was not built, and why

---

## Tech Stack

| Area | Tools |
|---|---|
| Language & tooling | Python 3.12, uv, pytest, ruff, black, Git, GitHub Actions |
| AI models | Anthropic Claude (Sonnet, Haiku), OpenAI Whisper |
| Search & embeddings | Sentence Transformers (MiniLM, BGE), cross-encoder reranking, FAISS, Pinecone, BM25, NumPy |
| Documents | pypdf, unstructured, Tesseract OCR, LangChain text splitters |
| Evaluation | RAGAS, LLM-as-judge, recall@k, NDCG |
| Apps & APIs | FastAPI, Streamlit, Pydantic, requests |
| Deployment | Docker, docker compose, Hugging Face Spaces |

---

## Repository Structure

```
AI-engineer/
├── 01-python-foundations/    # 6 command-line tools
├── 02-production-python/     # files, APIs, errors, data classes
├── 03-llm-apis/              # → Sales Call Intelligence (own repo)
├── 04-rag-foundations/       # 5 search and citation experiments
└── 05-advanced-rag/          # → Multimodal RAG Engine (own repo)
```
<!-- next stages are added to this tree -->

---

## Running Any Project

Each project folder is self-contained. With Python 3.12 and [uv](https://docs.astral.sh/uv/) installed:

```bash
cd 01-python-foundations/calculator   # or any project folder
uv sync
uv run pytest
```

Each project's README has its own run command. Projects that call an outside service (Anthropic, Pinecone) need the key in a `.env` file in that folder.
