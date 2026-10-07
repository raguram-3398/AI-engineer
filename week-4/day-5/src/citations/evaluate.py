"""Pure core: score citations against gold chunk labels.

Precision and recall here are chunk-level and gold-label based: a cheap proxy
for ALCE's citation precision/recall, which judge each statement with an NLI
model instead of labels.
"""

import re
from collections.abc import Sequence
from statistics import mean

from citations.models import KIND_ABSTAIN, CaseScore, CitedAnswer, EvalCase

_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_DIGIT = re.compile(r"\d")


def states_a_number(text: str) -> bool:
    """True if `text` contains a number other than a year.

    The facts in this corpus are numbers ($75, 30 days, 14 characters), so an
    uncited block that states one is an unsupported factual claim. Years are
    excluded because framing like "Under the 2026 policy, " is not a claim.
    """
    return bool(_DIGIT.search(_YEAR.sub("", text)))


def score_case(case: EvalCase, answer: CitedAnswer) -> CaseScore:
    """Score one answer.

    - precision: share of distinct cited chunks that are gold.
    - recall: share of gold chunks that were cited.
    - stale: a cited non-gold chunk shares (source, page) with a gold chunk,
      i.e. the right page of the wrong policy version. The citation is
      perfectly grounded and still wrong.
    - abstain cases: no precision/recall; abstain_ok means nothing was cited.
    """
    cited = {c.chunk.chunk_id: c.chunk for cl in answer.claims for c in cl.citations}
    uncited = sum(
        1 for cl in answer.claims if not cl.citations and states_a_number(cl.text)
    )
    if case.kind == KIND_ABSTAIN:
        return CaseScore(
            case_id=case.case_id,
            kind=case.kind,
            precision=None,
            recall=None,
            stale=False,
            uncited_claims=uncited,
            abstained=answer.abstained,
            abstain_ok=not cited,
        )
    hits = cited.keys() & case.gold_chunk_ids
    gold_pages = {
        (c.source, c.page) for c in case.retrieved if c.chunk_id in case.gold_chunk_ids
    }
    stale = any(
        cid not in case.gold_chunk_ids and (c.source, c.page) in gold_pages
        for cid, c in cited.items()
    )
    return CaseScore(
        case_id=case.case_id,
        kind=case.kind,
        precision=len(hits) / len(cited) if cited else 0.0,
        recall=len(hits) / len(case.gold_chunk_ids),
        stale=stale,
        uncited_claims=uncited,
        abstained=answer.abstained,
        abstain_ok=None,
    )


def aggregate(scores: Sequence[CaseScore]) -> dict[str, dict[str, float]]:
    """Means per kind plus "ALL" (answerable kinds only for precision/recall).

    Keys per row: n, precision, recall, stale_rate, uncited_claims (total),
    abstain_ok_rate (abstain rows only).
    """
    groups: dict[str, list[CaseScore]] = {}
    for s in scores:
        groups.setdefault(s.kind, []).append(s)
    answerable = [s for s in scores if s.kind != KIND_ABSTAIN]
    if answerable:
        groups["ALL answerable"] = answerable

    report: dict[str, dict[str, float]] = {}
    for kind, rows in groups.items():
        row: dict[str, float] = {
            "n": float(len(rows)),
            "uncited_claims": float(sum(s.uncited_claims for s in rows)),
        }
        if kind == KIND_ABSTAIN:
            row["abstain_ok_rate"] = mean(1.0 if s.abstain_ok else 0.0 for s in rows)
        else:
            row["precision"] = mean(s.precision or 0.0 for s in rows)
            row["recall"] = mean(s.recall or 0.0 for s in rows)
            row["stale_rate"] = mean(1.0 if s.stale else 0.0 for s in rows)
        report[kind] = row
    return report
