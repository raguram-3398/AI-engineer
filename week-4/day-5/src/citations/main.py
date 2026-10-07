"""Edges and wiring: load cases, call Claude behind a Protocol, print the eval.

Run:  PYTHONPATH=src python -m citations.main     (needs ANTHROPIC_API_KEY)
"""

import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from citations.cite import build_request, check_budget, parse_response, worst_case_usd
from citations.evaluate import aggregate, score_case
from citations.models import (
    COUNT_TOKENS_TIMEOUT_S,
    DAILY_WARN_USD,
    KIND_ABSTAIN,
    KINDS,
    MAX_OUTPUT_TOKENS,
    MODEL_ID,
    REQUEST_TIMEOUT_S,
    SDK_MAX_RETRIES,
    CaseFileError,
    CaseScore,
    CitationError,
    CitedAnswer,
    CitedChunk,
    EvalCase,
    LLMError,
    LLMTimeoutError,
    RawResponse,
)

CASES_PATH: Path = Path(__file__).resolve().parents[2] / "data" / "cases.json"


# --- Data edge -------------------------------------------------------------


def load_cases(path: Path) -> tuple[EvalCase, ...]:
    """Read and validate the eval cases.

    Raises CaseFileError on bad JSON, missing fields, an unknown kind, gold ids
    that were not retrieved, or a gold set whose emptiness disagrees with kind.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        cases = tuple(
            EvalCase(
                case_id=c["id"],
                kind=c["kind"],
                query=c["query"],
                retrieved=tuple(CitedChunk(**r) for r in c["retrieved"]),
                gold_chunk_ids=frozenset(c["gold_chunk_ids"]),
            )
            for c in raw
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        raise CaseFileError(f"{path}: {e}") from e
    for case in cases:
        retrieved_ids = {r.chunk_id for r in case.retrieved}
        if case.kind not in KINDS:
            raise CaseFileError(f"{case.case_id}: unknown kind {case.kind!r}")
        if not case.gold_chunk_ids <= retrieved_ids:
            raise CaseFileError(f"{case.case_id}: gold chunk not in retrieved set")
        if (case.kind == KIND_ABSTAIN) != (not case.gold_chunk_ids):
            raise CaseFileError(f"{case.case_id}: gold set and kind disagree")
    return cases


# --- Claude edge -----------------------------------------------------------


class LLMClient(Protocol):
    def count_tokens(self, request: Mapping[str, object]) -> int: ...

    def create(self, request: Mapping[str, object]) -> RawResponse: ...


class AnthropicClient:
    """Adapter over the Anthropic SDK. Construct once per process.

    Every call has a timeout; SDK exceptions become LLMTimeoutError / LLMError.
    `sdk` is injectable so tests can pass a stub.
    """

    def __init__(self, api_key: str | None = None, sdk: Any = None) -> None:
        import anthropic

        self._anthropic = anthropic
        self._sdk = sdk or anthropic.Anthropic(
            api_key=api_key, max_retries=SDK_MAX_RETRIES
        )

    def _call(self, fn: Any, **kwargs: Any) -> Any:
        try:
            return fn(**kwargs)
        except self._anthropic.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._anthropic.APIError as e:
            raise LLMError(str(e)) from e

    def count_tokens(self, request: Mapping[str, object]) -> int:
        body = {k: v for k, v in request.items() if k != "max_tokens"}
        result = self._call(
            self._sdk.messages.count_tokens, timeout=COUNT_TOKENS_TIMEOUT_S, **body
        )
        return int(result.input_tokens)

    def create(self, request: Mapping[str, object]) -> RawResponse:
        resp = self._call(
            self._sdk.messages.create, timeout=REQUEST_TIMEOUT_S, **request
        )
        return RawResponse(
            blocks=tuple(b.model_dump() for b in resp.content),
            input_tokens=int(resp.usage.input_tokens),
            output_tokens=int(resp.usage.output_tokens),
        )


# --- Wiring ----------------------------------------------------------------


def answer(query: str, chunks: Sequence[CitedChunk], client: LLMClient) -> CitedAnswer:
    """Guard cost, call Claude, return a verified cited answer."""
    request = build_request(query, chunks, model=MODEL_ID, max_tokens=MAX_OUTPUT_TOKENS)
    check_budget(worst_case_usd(client.count_tokens(request), MAX_OUTPUT_TOKENS))
    return parse_response(client.create(request), chunks)


def run(
    cases: Sequence[EvalCase], client: LLMClient
) -> tuple[list[tuple[EvalCase, CitedAnswer, CaseScore]], list[str], float]:
    """Answer and score every case. Returns (results, failures, total USD).

    A failing case is recorded and the run continues; nothing is silently dropped.
    """
    results: list[tuple[EvalCase, CitedAnswer, CaseScore]] = []
    failures: list[str] = []
    spent = 0.0
    warned = False
    for case in cases:
        try:
            ans = answer(case.query, case.retrieved, client)
        except CitationError as e:
            failures.append(f"{case.case_id}: {type(e).__name__}: {e}")
            continue
        spent += ans.cost.usd
        if spent >= DAILY_WARN_USD and not warned:
            print(f"WARNING: run spend ${spent:.4f} passed ${DAILY_WARN_USD:.2f}")
            warned = True
        results.append((case, ans, score_case(case, ans)))
    return results, failures, spent


def _fmt(v: float | None) -> str:
    return "  -  " if v is None else f"{v:.2f}"


def print_report(
    results: Sequence[tuple[EvalCase, CitedAnswer, CaseScore]],
    failures: Sequence[str],
    spent: float,
) -> None:
    print(f"\nModel: {MODEL_ID}\n")
    print(f"{'case':<6}{'kind':<14}{'prec':>6}{'rec':>6}  stale  uncited  cited")
    for case, ans, s in results:
        cited = sorted({c.chunk.chunk_id for cl in ans.claims for c in cl.citations})
        flag = "YES" if s.stale else "no"
        if s.abstain_ok is not None:
            flag = "ok" if s.abstain_ok else "FAIL"
        print(
            f"{s.case_id:<6}{s.kind:<14}{_fmt(s.precision):>6}{_fmt(s.recall):>6}"
            f"  {flag:<5}  {s.uncited_claims:>7}  {', '.join(cited) or '(none)'}"
        )
    print()
    for kind, row in aggregate([s for _, _, s in results]).items():
        cells = "  ".join(f"{k}={v:.2f}" for k, v in row.items() if k != "n")
        print(f"{kind:<16} n={int(row['n']):<3} {cells}")
    for case, ans, s in results:
        if s.stale or s.abstain_ok is False or (s.recall is not None and s.recall < 1):
            print(f"\n[{case.case_id}] {case.query}\n  -> {ans.text.strip()}")
    for f in failures:
        print(f"FAILED {f}")
    print(f"\nTotal cost: ${spent:.4f} over {len(results)} calls")


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 2
    cases = load_cases(CASES_PATH)
    results, failures, spent = run(cases, AnthropicClient())
    print_report(results, failures, spent)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
