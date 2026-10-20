import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import anthropic
import pytest
from fakes import cite, raw, text

from citations.main import CASES_PATH, AnthropicClient, answer, load_cases, run
from citations.models import (
    COUNT_TOKENS_TIMEOUT_S,
    REQUEST_TIMEOUT_S,
    CaseFileError,
    CostLimitError,
    LLMError,
    LLMTimeoutError,
)

try:
    import httpx2 as _http
except ImportError:  # older SDKs use httpx
    import httpx as _http  # type: ignore[no-redef]

from fakes import FakeClient


def test_real_case_file_loads() -> None:
    cases = load_cases(CASES_PATH)
    assert {c.kind for c in cases} == {"version", "multi_source", "control", "abstain"}


def test_gold_not_in_retrieved_is_rejected(tmp_path: Path) -> None:
    case = json.loads(CASES_PATH.read_text())[0]
    case["gold_chunk_ids"] = ["nope"]
    p = tmp_path / "c.json"
    p.write_text(json.dumps([case]))
    with pytest.raises(CaseFileError):
        load_cases(p)


def test_budget_blocks_call_before_create() -> None:
    case = load_cases(CASES_PATH)[0]
    client = FakeClient(lambda r: raw(text("x")), input_tokens=50_000)
    with pytest.raises(CostLimitError):
        answer(case.query, case.retrieved, client)
    assert client.created == []


def test_run_reports_stale_and_records_failures() -> None:
    cases = load_cases(CASES_PATH)
    v1 = next(c for c in cases if c.case_id == "v1")
    stale_idx = [r.chunk_id for r in v1.retrieved].index("expense-2024-p2")
    client = FakeClient(lambda r: raw(text("$60", cite(v1.retrieved, stale_idx))))
    results, failures, spent = run([v1], client)
    assert results[0][2].stale and failures == [] and spent > 0

    broken = FakeClient(
        lambda r: raw(text("x", {**cite(v1.retrieved, 0), "cited_text": "made up"}))
    )
    results, failures, _ = run([v1], broken)
    assert results == [] and "CitationIntegrityError" in failures[0]


class _StubMessages:
    def __init__(self, exc: Exception | None = None) -> None:
        self.exc = exc
        self.kwargs: list[dict[str, Any]] = []

    def _go(self, **kwargs: Any) -> Any:
        self.kwargs.append(kwargs)
        if self.exc:
            raise self.exc
        return SimpleNamespace(
            input_tokens=10,
            content=[
                SimpleNamespace(model_dump=lambda: {"type": "text", "text": "hi"})
            ],
            usage=SimpleNamespace(input_tokens=10, output_tokens=2),
        )

    count_tokens = create = _go


def _client(exc: Exception | None = None) -> tuple[AnthropicClient, _StubMessages]:
    msgs = _StubMessages(exc)
    return AnthropicClient(sdk=SimpleNamespace(messages=msgs)), msgs


def test_adapter_passes_timeouts_and_strips_max_tokens_for_count() -> None:
    client, msgs = _client()
    req = {"model": "m", "max_tokens": 5, "messages": []}
    client.count_tokens(req)
    client.create(req)
    assert msgs.kwargs[0]["timeout"] == COUNT_TOKENS_TIMEOUT_S
    assert "max_tokens" not in msgs.kwargs[0]
    assert msgs.kwargs[1]["timeout"] == REQUEST_TIMEOUT_S


def test_adapter_translates_timeout_and_api_errors() -> None:
    request = _http.Request("POST", "https://api.anthropic.com/v1/messages")
    client, _ = _client(anthropic.APITimeoutError(request=request))
    with pytest.raises(LLMTimeoutError):
        client.create({"model": "m"})
    client, _ = _client(anthropic.APIConnectionError(request=request))
    with pytest.raises(LLMError):
        client.count_tokens({"model": "m"})
