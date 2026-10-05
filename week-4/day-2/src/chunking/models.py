"""Shared constants, dataclasses, and the embedder interface for Day 23."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float32]

# --- Embedding model -------------------------------------------------------
EMBED_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# --- Chunking (same size + overlap for fixed and recursive = fair comparison)
CHUNK_SIZE: int = 800  # characters, not tokens — see the token check in main
CHUNK_OVERLAP: int = 120  # 15% of CHUNK_SIZE
SEMANTIC_BREAKPOINT_PERCENTILE: float = 95.0  # break at the top 5% of topic shifts

# --- Retrieval eval ---------------------------------------------------------
TOP_K: int = 3

# --- Network ----------------------------------------------------------------
DEFAULT_TIMEOUT: float = 10.0  # seconds; Week 2 rule — every external call
USER_AGENT: str = "ai-engineer-plan-day23/0.1 (learning project)"

# --- Display ----------------------------------------------------------------
PREVIEW_CHUNKS: int = 2
PREVIEW_CHARS: int = 160

# --- Metadata values --------------------------------------------------------
DOC_TYPE_PDF: str = "pdf"
DOC_TYPE_TEXT: str = "text"
DOC_TYPE_WEB: str = "web"
STRATEGY_FIXED: str = "fixed"
STRATEGY_RECURSIVE: str = "recursive"
STRATEGY_SEMANTIC: str = "semantic"

# A chunk whose stripped text ends with none of these is counted as mid-sentence.
SENTENCE_ENDINGS: tuple[str, ...] = (".", "!", "?", '"', "'", ")", "]")


class EmbedderProtocol(Protocol):
    """Anything that can embed text and count tokens like the real model.

    The real Embedder and the test FakeEmbedder both satisfy this, so chunkers
    and evaluators never import sentence-transformers directly.
    """

    @property
    def max_tokens(self) -> int:
        """Maximum tokens the model embeds before silently truncating."""
        ...

    def embed(self, texts: list[str]) -> FloatArray:
        """Return one unit-normalized float32 vector per input text."""
        ...

    def count_tokens(self, text: str) -> int:
        """Return the token count the model actually sees, special tokens included."""
        ...


@dataclass(frozen=True)
class ChunkStats:
    """Summary numbers for one chunking strategy — one README table row."""

    strategy: str
    count: int
    min_tokens: int
    mean_tokens: float
    max_tokens: int
    over_limit: int
    mid_sentence: int


@dataclass(frozen=True)
class EvalQuery:
    """A hand-written retrieval check: the question and a verbatim answer snippet."""

    question: str
    expected_substring: str
