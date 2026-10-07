"""Constants, value types, and the exception hierarchy for the Pinecone store."""

from dataclasses import dataclass

# --- Embedding model (the index is only valid for vectors from THIS model) ---
MODEL_ID: str = "BAAI/bge-small-en-v1.5"
DIMENSION: int = 384
BGE_QUERY_PREFIX: str = "Represent this sentence for searching relevant passages: "

# --- Pinecone index ---
# The model id is baked into the index name: a new model means a new index.
INDEX_NAME: str = "day25-bge-small-en-v1-5"
NAMESPACE: str = "policies"
METRIC: str = "cosine"
CLOUD: str = "aws"
REGION: str = "us-east-1"  # the free Starter plan only offers aws/us-east-1

# --- Timeouts and batching ---
REQUEST_TIMEOUT_S: float = 10.0  # every single Pinecone request
INDEX_READY_TIMEOUT_S: int = 120  # create_index waits this long for "Ready"
FRESHNESS_TIMEOUT_S: float = 60.0  # wait for upserts to become queryable
FRESHNESS_POLL_S: float = 1.0
UPSERT_BATCH_SIZE: int = 100
HF_DOWNLOAD_TIMEOUT_S: int = 30
HF_ETAG_TIMEOUT_S: int = 10

# --- Retrieval ---
TOP_K: int = 3

# --- Metadata ---
DATE_DIGITS: int = 8  # dates are YYYYMMDD ints so $gte/$lte work on them
METADATA_KEYS: tuple[str, ...] = ("text", "source", "page", "date", "embedding_model")


@dataclass(frozen=True)
class Chunk:
    """One retrievable passage. `date` is the document version's effective date."""

    id: str
    text: str
    source: str
    page: int
    date: int


@dataclass(frozen=True)
class Match:
    """One search hit, rebuilt from Pinecone metadata."""

    id: str
    score: float
    text: str
    source: str
    page: int
    date: int
    embedding_model: str


@dataclass(frozen=True)
class EvalQuery:
    """A query, the filter it should run with, and the chunk that answers it.

    kind: "version" (same question asked of two policy versions), "source"
    (topic shared by two documents), or "control" (no filter needed).
    """

    id: str
    kind: str
    text: str
    expected_id: str
    source: str | None
    date_from: int | None
    date_to: int | None


class VectorStoreError(Exception):
    """Base for data and I/O errors in this package."""


class VectorStoreTimeoutError(VectorStoreError):
    """A Pinecone call, or waiting for upserts to become visible, ran out of time."""


class EmbeddingModelMismatchError(VectorStoreError):
    """The index holds vectors from a different model, or has the wrong shape."""
