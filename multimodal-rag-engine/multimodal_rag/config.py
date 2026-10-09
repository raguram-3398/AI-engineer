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
