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
INDEX_NAME: str = "fda-bge-small-en-v1-5-v1"  # bump the suffix on every re-index
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
ANSWER_MAX_TOKENS: int = 2048  # 2/8 spot-check answers hit 1,024 (one needed 1,598)
PRICE_IN_PER_MTOK: float = 0.10  # Haiku 5.5, prompts <= 100k tokens (pricing page)
PRICE_OUT_PER_MTOK: float = 0.50
ABSTAIN_TEXT: str = "The documents do not contain the answer."
ABSTAIN_PERCENTILE: float = 5.0  # % of answerable non-sample queries below threshold
ABSTAIN_SCORE: float = 0.6837  # p5 top-1 of the 304 non-sample queries (Day 28)
