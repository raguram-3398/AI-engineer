"""Constants, frozen dataclasses, and the embedder interface for Day 24.

Everything other modules agree on lives here: model names, the BGE query
instruction, eval parameters, and the shapes of inputs and results.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float32]

# --- Models under comparison -------------------------------------------------
MINILM_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
BGE_NAME: str = "BAAI/bge-small-en-v1.5"

# BGE v1.5 retrieval instruction. Goes on QUERIES ONLY, never on passages.
# The trailing space matters: it separates the instruction from the query text.
BGE_QUERY_PREFIX: str = "Represent this sentence for searching relevant passages: "
NO_PREFIX: str = ""

# --- Network -----------------------------------------------------------------
# Model weights come from the Hugging Face Hub on first load. huggingface_hub
# parses these env vars with int(), so they MUST be whole seconds: "30.0" crashes
# the import. Once cached locally, loading makes no download.
HF_DOWNLOAD_TIMEOUT_S: int = 30
HF_ETAG_TIMEOUT_S: int = 10
HF_DOWNLOAD_TIMEOUT_ENV: str = "HF_HUB_DOWNLOAD_TIMEOUT"
HF_ETAG_TIMEOUT_ENV: str = "HF_HUB_ETAG_TIMEOUT"

# --- Evaluation --------------------------------------------------------------
TOP_K: int = 3
COSINE_TOLERANCE: float = 1e-5  # float32 rounding between manual and matrix cosine
TEXTS_PER_TRIPLET: int = 3  # anchor, positive, negative
MIN_FLOOR_TEXTS: int = 2  # an off-diagonal mean needs at least two texts
FIRST_RANK: int = 1  # ranks are 1-based: rank 1 = top result

# --- Triplet categories (a typo in the data file is a DataFileError) ----------
CATEGORY_NEGATION: str = "negation"
CATEGORY_NUMBERS: str = "numbers"
CATEGORY_ROLE_REVERSAL: str = "role_reversal"
CATEGORY_PARAPHRASE: str = "paraphrase_no_overlap"
CATEGORY_POLYSEMY: str = "lexical_overlap_different_meaning"
TRIPLET_CATEGORIES: tuple[str, ...] = (
    CATEGORY_NEGATION,
    CATEGORY_NUMBERS,
    CATEGORY_ROLE_REVERSAL,
    CATEGORY_PARAPHRASE,
    CATEGORY_POLYSEMY,
)

# --- Data files --------------------------------------------------------------
TRIPLETS_FILE: str = "triplets.json"
PASSAGES_FILE: str = "passages.json"
QUERIES_FILE: str = "queries.json"
DATA_DIR_NAME: str = "data"
PROJECT_ROOT_DEPTH: int = 2  # src/embeddings/main.py -> parents[2] = project root

# --- Display -----------------------------------------------------------------
SCORE_DECIMALS: int = 3
RULE_WIDTH: int = 78


class EmbedderProtocol(Protocol):
    """Anything that turns text into unit vectors and counts tokens like the model.

    The real SentenceTransformerEmbedder and the test FakeEmbedder both satisfy
    this, so evaluation code never imports sentence-transformers.
    Implementations must NOT add any prefix themselves; prefixing is the
    caller's decision (see similarity.with_query_prefix).
    """

    @property
    def model_name(self) -> str:
        """Hub id of the model that produced the vectors (goes in index metadata)."""
        ...

    @property
    def dimension(self) -> int:
        """Length of every vector returned by embed()."""
        ...

    @property
    def max_tokens(self) -> int:
        """Tokens beyond this are silently truncated before embedding."""
        ...

    def embed(self, texts: list[str]) -> FloatArray:
        """Return a (len(texts), dimension) float32 array of unit-norm rows."""
        ...

    def count_tokens(self, text: str) -> int:
        """Return the token count the model actually sees, special tokens included."""
        ...


@dataclass(frozen=True)
class ModelSpec:
    """A model to evaluate and the query instruction its authors recommend."""

    name: str
    query_prefix: str


@dataclass(frozen=True)
class Triplet:
    """One hard-negative check.

    `positive` means the same as `anchor` in different words; `negative` shares
    many words with `anchor` but means something different.
    """

    anchor: str
    positive: str
    negative: str
    category: str


@dataclass(frozen=True)
class TripletResult:
    """Scores for one triplet under one model."""

    triplet: Triplet
    pos_score: float
    neg_score: float

    @property
    def margin(self) -> float:
        """Positive score minus negative score. Scale-free across models in sign."""
        return self.pos_score - self.neg_score

    @property
    def passed(self) -> bool:
        """True only if the paraphrase strictly beats the hard negative. Ties fail."""
        return self.margin > 0.0


@dataclass(frozen=True)
class TripletSummary:
    """One README row: how a model handles hard negatives."""

    model: str
    pass_rate: float
    by_category: dict[str, float]
    mean_margin: float
    mean_pos: float
    mean_neg: float
    unrelated_floor: float


@dataclass(frozen=True)
class Passage:
    """A retrievable unit with a stable id (stands in for a chunk)."""

    id: str
    text: str


@dataclass(frozen=True)
class RetrievalQuery:
    """A user question and the id of the passage that answers it."""

    question: str
    expected_id: str


@dataclass(frozen=True)
class RetrievalResult:
    """Retrieval quality for one (model, prefix) configuration.

    `ranks[i]` is the 1-based rank of the expected passage for query i.
    """

    model: str
    prefix_used: bool
    hit_at_1: float
    hit_at_k: float
    mrr: float
    k: int
    ranks: tuple[int, ...]
