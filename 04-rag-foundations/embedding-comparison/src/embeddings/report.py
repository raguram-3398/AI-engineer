"""Pure formatting: results in, plain-text tables out. No printing here."""

from embeddings.models import (
    CATEGORY_NEGATION,
    CATEGORY_NUMBERS,
    CATEGORY_PARAPHRASE,
    CATEGORY_POLYSEMY,
    CATEGORY_ROLE_REVERSAL,
    FIRST_RANK,
    RULE_WIDTH,
    SCORE_DECIMALS,
    TRIPLET_CATEGORIES,
    RetrievalQuery,
    RetrievalResult,
    TripletSummary,
)

_SHORT_CATEGORY: dict[str, str] = {
    CATEGORY_NEGATION: "neg",
    CATEGORY_NUMBERS: "num",
    CATEGORY_ROLE_REVERSAL: "role",
    CATEGORY_PARAPHRASE: "para",
    CATEGORY_POLYSEMY: "poly",
}
_MISSING: str = "-"


def _fmt(value: float) -> str:
    """Fixed-width score."""
    return f"{value:.{SCORE_DECIMALS}f}"


def _short_model(name: str) -> str:
    """'BAAI/bge-small-en-v1.5' -> 'bge-small-en-v1.5'."""
    return name.rsplit("/", maxsplit=1)[-1]


def rule(title: str) -> str:
    """A section header line."""
    return f"\n== {title} ".ljust(RULE_WIDTH, "=")


def format_triplet_table(summaries: list[TripletSummary]) -> str:
    """One row per model: overall and per-category pass rate, margins, raw levels."""
    cats = [_SHORT_CATEGORY[c] for c in TRIPLET_CATEGORIES]
    header = (
        f"{'model':<22}{'pass':>6}"
        + "".join(f"{c:>6}" for c in cats)
        + f"{'margin':>8}{'pos':>7}{'neg':>7}{'floor':>7}"
    )
    lines = [header]
    for s in summaries:
        per_cat = "".join(
            f"{s.by_category[c]:>6.2f}" if c in s.by_category else f"{_MISSING:>6}"
            for c in TRIPLET_CATEGORIES
        )
        lines.append(
            f"{_short_model(s.model):<22}{s.pass_rate:>6.2f}{per_cat}"
            f"{_fmt(s.mean_margin):>8}{_fmt(s.mean_pos):>7}"
            f"{_fmt(s.mean_neg):>7}{_fmt(s.unrelated_floor):>7}"
        )
    return "\n".join(lines)


def format_retrieval_table(results: list[RetrievalResult]) -> str:
    """One row per (model, prefix) configuration."""
    if not results:
        return "(no retrieval results)"
    k = results[0].k
    lines = [f"{'model':<22}{'prefix':>8}{'hit@1':>8}{f'hit@{k}':>8}{'MRR':>8}"]
    for r in results:
        lines.append(
            f"{_short_model(r.model):<22}{('yes' if r.prefix_used else 'no'):>8}"
            f"{r.hit_at_1:>8.2f}{r.hit_at_k:>8.2f}{_fmt(r.mrr):>8}"
        )
    return "\n".join(lines)


def format_rank_grid(
    results: list[RetrievalResult], queries: list[RetrievalQuery]
) -> str:
    """Rank of the correct passage per query per configuration; '*' marks a miss
    at rank 1. Shows WHICH questions a change helped or hurt, not just the mean."""
    if not results:
        return "(no retrieval results)"
    labels = [
        f"{_short_model(r.model)[:9]}{'+p' if r.prefix_used else ''}" for r in results
    ]
    lines = [f"{'question':<52}" + "".join(f"{label:>13}" for label in labels)]
    for i, query in enumerate(queries):
        cells = "".join(
            f"{(str(r.ranks[i]) + ('' if r.ranks[i] == FIRST_RANK else '*')):>13}"
            for r in results
        )
        lines.append(f"{query.question[:50]:<52}{cells}")
    return "\n".join(lines)
