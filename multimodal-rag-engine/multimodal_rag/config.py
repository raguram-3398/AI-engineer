"""Constants for the Multimodal RAG Engine. Grows day by day; no runtime options."""

from pathlib import Path

PROJECT_DIR: Path = Path(__file__).resolve().parents[1]
DATASET_DIR: Path = PROJECT_DIR.parent / "datasets" / "vidore_fda"  # gitignored
PDF_DIR: Path = DATASET_DIR / "pdfs"
DOCS_METADATA_PATH: Path = (
    DATASET_DIR / "documents_metadata" / "test-00000-of-00001.parquet"
)
CORPUS_INDEX_PATH: Path = DATASET_DIR / "corpus_index.parquet"
DATA_DIR: Path = PROJECT_DIR / "data"
CHUNKS_PATH: Path = DATA_DIR / "chunks.jsonl"

# Loading
LOW_TEXT_CHARS: int = 50  # pages with less extracted text than this get OCR
OCR_DPI: int = 200  # same render resolution unstructured uses for OCR
OCR_TIMEOUT_S: float = 60.0  # per subprocess (render, then tesseract); ~3 s typical

# Chunking
BOOK_MAX_CHARS: int = 1500  # chunk_by_title hard limit for book pages
MAX_TOKENS: int = 510  # BGE's 512 minus [CLS] and [SEP]

# Embedding
EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
EMBED_DIM: int = 384
EMBED_BATCH_SIZE: int = 32

# Pinecone
INDEX_NAME: str = "fda-bge-small-en-v1-5-v2"  # bump the suffix on every re-index
NAMESPACE: str = "fda"
METRIC: str = "cosine"
CLOUD: str = "aws"
REGION: str = "us-east-1"  # the free Starter plan only offers aws/us-east-1
PINECONE_TIMEOUT_S: float = 10.0  # every single Pinecone request
INDEX_READY_TIMEOUT_S: int = 120  # create_index waits this long for "Ready"
FRESHNESS_TIMEOUT_S: float = 60.0  # wait for upserts to show in the vector count
UPSERT_BATCH_SIZE: int = 100

# Eval data
QUERIES_PATH: Path = DATASET_DIR / "queries" / "test-00000-of-00001.parquet"
QRELS_PATH: Path = DATASET_DIR / "qrels" / "test-00000-of-00001.parquet"
EVAL_DIR: Path = DATA_DIR / "eval"
UNANSWERABLE_PATH: Path = EVAL_DIR / "unanswerable_en.jsonl"
SAMPLE_PATH: Path = EVAL_DIR / "sample.json"  # fixed once on Day 28, never changed
SAMPLE_SIZE: int = 60  # answerable queries; plus all 20 unanswerable
SAMPLE_SEED: int = 28
VISUAL_CONTENT: frozenset[str] = frozenset({"Chart", "Infographic", "Table", "Image"})

# Retrieval
# BGE v1.5 instruction for short query -> passage retrieval (passages take none)
QUERY_PREFIX: str = "Represent this sentence for searching relevant passages: "
TOP_K: int = 20  # chunks fetched from Pinecone (also the Day 33 rerank budget)
EVAL_K: int = 10  # distinct pages scored by recall@10 / NDCG@10

# Answer
CLAUDE_MODEL: str = "claude-haiku-5-5"  # never pass `temperature` (400 on 5.5)
CLAUDE_TIMEOUT_S: float = 30.0  # per attempt; the SDK retries twice on its own
ANSWER_K: int = 10  # top chunks sent to Claude as documents
ANSWER_MAX_TOKENS: int = (
    4096  # 2048 cut one Day 29 eval answer (1,024 cut 2/8 on Day 28)
)
PRICE_IN_PER_MTOK: float = 0.10  # Haiku 5.5, prompts <= 100k tokens (pricing page)
PRICE_OUT_PER_MTOK: float = 0.50
ABSTAIN_TEXT: str = "The documents do not contain the answer."
REFUSAL_TEXT: str = "The model declined to answer this question."

# Vision descriptions (Day 30)
VISION_PATH: Path = DATA_DIR / "vision.jsonl"  # one description per low-text slide
VISION_MAX_CHARS: int = 300  # slide pages with less chunk text get a description
# 100 dpi = 1000x750 px per slide (~970 visual tokens); on 3 measured slides the
# descriptions read every label and value as well as at 150 dpi
VISION_DPI: int = 100
VISION_MAX_TOKENS: int = 8192  # thinking counts; measured max 1,581 output tokens
VISION_CONTENT: tuple[str, ...] = ("Chart", "Infographic", "Image")  # recall split

# Eval pipeline (Day 29)
SCORES_PATH: Path = DATA_DIR / "scores.jsonl"  # one line per full eval run
EVAL_WORKERS: int = 8  # parallel Claude calls for answers and the judge
# Haiku 5.5 thinks by default; thinking tokens count against max_tokens (and are
# billed as output). At 4096, 13/60 faithfulness verdicts on the longest answers
# were cut off (2.7k of 4,096 output tokens were thinking).
RAGAS_MAX_TOKENS: int = 16384
JUDGE_MAX_TOKENS: int = 512
# Gate: a run fails if a metric drops by more than its threshold vs the last
# passed run. Threshold = max(floor, run-to-run noise of the unchanged baseline
# measured on Ram's Mac, Day 29 Mac runs 1 vs 2); floor 0.05 for the four quality
# metrics, 0 (any drop) for abstain accuracy. Mac noise: faithfulness 0.014,
# answer relevancy 0.036, recall@10 and NDCG@10 0, abstain_unanswerable 0,
# answer_answerable 1/60. answer_answerable is kept at 2/60: the same unchanged
# code flipped 2 queries (152, 212) in an earlier sandbox pair.
GATE_THRESHOLDS: dict[str, float] = {
    "faithfulness": 0.05,
    "answer_relevancy": 0.05,
    "recall@10": 0.05,
    "ndcg@10": 0.05,
    "abstain_unanswerable": 0.0,
    "answer_answerable": 2 / 60,
}
