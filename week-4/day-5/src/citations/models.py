"""Constants, value types, and the exception hierarchy for citation tracking."""

from dataclasses import dataclass

# --- Claude model and pricing (USD per million tokens, Claude Sonnet 5.5) ---
MODEL_ID: str = "claude-sonnet-5-5"
INPUT_USD_PER_MTOK: float = 2.0
OUTPUT_USD_PER_MTOK: float = 10.0
TOKENS_PER_MTOK: int = 1_000_000

# --- Generation and guardrails ---
MAX_OUTPUT_TOKENS: int = 400  # also the output ceiling in the pre-call cost check
MAX_USD_PER_CALL: float = 0.02  # refuse the call if the worst case exceeds this
DAILY_WARN_USD: float = 0.50  # warn once a run has spent this much
REQUEST_TIMEOUT_S: float = 30.0  # messages.create
COUNT_TOKENS_TIMEOUT_S: float = 10.0  # messages.count_tokens
SDK_MAX_RETRIES: int = 2  # the SDK retries 429/5xx/connection errors itself

# --- Prompt ---
AS_OF_DATE: str = "2026-10-07"  # "today" for deciding which policy version applies
ABSTAIN_TEXT: str = "NOT_IN_DOCUMENTS"

# --- Eval case kinds ---
KIND_VERSION: str = "version"  # two versions retrieved, only one is right
KIND_MULTI: str = "multi_source"  # answer needs two different documents
KIND_CONTROL: str = "control"  # single-version document, easy
KIND_ABSTAIN: str = "abstain"  # retrieved chunks do not answer the question
KINDS: frozenset[str] = frozenset(
    {KIND_VERSION, KIND_MULTI, KIND_CONTROL, KIND_ABSTAIN}
)


@dataclass(frozen=True)
class CitedChunk:
    """One retrieved passage, as Day 25's Pinecone hit would return it.

    `date` is the policy version's effective date (YYYYMMDD) and `score` the
    retrieval similarity. Neither is citable; both travel as metadata.
    """

    chunk_id: str
    source: str
    page: int
    date: int
    text: str
    score: float


@dataclass(frozen=True)
class Citation:
    """A verified pointer: `cited_text` is chunk.text[start_char:end_char]."""

    chunk: CitedChunk
    cited_text: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class Claim:
    """One text block of the answer and the citations that support it (may be none)."""

    text: str
    citations: tuple[Citation, ...]


@dataclass(frozen=True)
class CostRecord:
    """Actual cost of one call, from the response's `usage`."""

    input_tokens: int
    output_tokens: int
    usd: float


@dataclass(frozen=True)
class CitedAnswer:
    claims: tuple[Claim, ...]
    abstained: bool
    cost: CostRecord

    @property
    def text(self) -> str:
        return "".join(c.text for c in self.claims)


@dataclass(frozen=True)
class RawResponse:
    """Response content blocks as plain dicts plus token usage (SDK-independent)."""

    blocks: tuple[dict[str, object], ...]
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class EvalCase:
    """A query, the chunks retrieval returned for it (frozen), and the gold chunks.

    `gold_chunk_ids` is empty for abstain cases.
    """

    case_id: str
    kind: str
    query: str
    retrieved: tuple[CitedChunk, ...]
    gold_chunk_ids: frozenset[str]


@dataclass(frozen=True)
class CaseScore:
    """Per-case citation scores. precision/recall are None for abstain cases."""

    case_id: str
    kind: str
    precision: float | None
    recall: float | None
    stale: bool
    uncited_claims: int
    abstained: bool
    abstain_ok: bool | None


class CitationError(Exception):
    """Base for data and I/O errors in this package."""


class CaseFileError(CitationError):
    """The eval case file is missing fields or inconsistent."""


class CitationIntegrityError(CitationError):
    """A citation points outside the documents or its text does not match."""


class CostLimitError(CitationError):
    """The worst-case cost of a call exceeds MAX_USD_PER_CALL."""


class LLMTimeoutError(CitationError):
    """A Claude API call ran out of time."""


class LLMError(CitationError):
    """Any other Claude API failure."""
