"""Pure core: chunk ids, record shape, filters, and parsing results. No I/O."""

from collections.abc import Mapping, Sequence

from vectorstore.models import (
    DATE_DIGITS,
    DIMENSION,
    METADATA_KEYS,
    Chunk,
    EmbeddingModelMismatchError,
    Match,
    VectorStoreError,
)


def chunk_id(source: str, date: int, page: int) -> str:
    """Deterministic id: same source + version + page always gives the same id.

    Upsert overwrites on id, so re-running ingestion replaces records instead
    of duplicating them.
    """
    return f"{source}@{date}#p{page}"


def _check_date(name: str, value: int) -> None:
    """Raise ValueError unless value looks like a YYYYMMDD int."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an int like 20260301, got {value!r}")
    if len(str(value)) != DATE_DIGITS:
        raise ValueError(f"{name} must be YYYYMMDD, got {value}")


def to_record(
    chunk: Chunk, vector: Sequence[float], model_id: str
) -> dict[str, object]:
    """Build the Pinecone record for one chunk.

    The chunk text is stored in metadata so a hit can be cited without a
    second lookup. The model id is stored on EVERY record so a reader can
    verify the vectors match its query model.
    """
    if len(vector) != DIMENSION:
        raise ValueError(f"vector has {len(vector)} dims, index expects {DIMENSION}")
    _check_date("chunk.date", chunk.date)
    return {
        "id": chunk.id,
        "values": [float(x) for x in vector],
        "metadata": {
            "text": chunk.text,
            "source": chunk.source,
            "page": chunk.page,
            "date": chunk.date,
            "embedding_model": model_id,
        },
    }


def build_filter(
    source: str | None = None,
    date_from: int | None = None,
    date_to: int | None = None,
) -> dict[str, object] | None:
    """Translate optional constraints into a Pinecone filter, or None for no filter.

    Top-level keys are ANDed by Pinecone. Both date bounds are inclusive.
    """
    flt: dict[str, object] = {}
    if source is not None:
        flt["source"] = {"$eq": source}

    date_range: dict[str, int] = {}
    if date_from is not None:
        _check_date("date_from", date_from)
        date_range["$gte"] = date_from
    if date_to is not None:
        _check_date("date_to", date_to)
        date_range["$lte"] = date_to
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError(f"date_from {date_from} is after date_to {date_to}")
    if date_range:
        flt["date"] = date_range

    return flt or None


def parse_matches(raw: Sequence[Mapping[str, object]]) -> list[Match]:
    """Turn raw hits ({id, score, metadata}) into Matches.

    Raises VectorStoreError if a hit lacks required metadata (e.g. a record
    written by older code), instead of failing later with a KeyError.
    """
    matches: list[Match] = []
    for hit in raw:
        metadata = hit.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise VectorStoreError(f"hit {hit.get('id')!r} has non-dict metadata")
        missing = [key for key in METADATA_KEYS if key not in metadata]
        if missing:
            raise VectorStoreError(f"hit {hit.get('id')!r} is missing {missing}")
        matches.append(
            Match(
                id=str(hit["id"]),
                score=float(hit["score"]),  # type: ignore[arg-type]
                text=str(metadata["text"]),
                source=str(metadata["source"]),
                page=int(metadata["page"]),  # Pinecone returns numbers as floats
                date=int(metadata["date"]),
                embedding_model=str(metadata["embedding_model"]),
            )
        )
    return matches


def check_model(matches: Sequence[Match], expected_model: str) -> None:
    """Raise EmbeddingModelMismatchError if any hit came from another model.

    Comparing a query vector against vectors from a different model gives
    scores that look normal and mean nothing, so this must fail loudly.
    """
    wrong = sorted({m.embedding_model for m in matches} - {expected_model})
    if wrong:
        raise EmbeddingModelMismatchError(
            f"index returned vectors from {wrong}, query model is {expected_model!r}"
        )
