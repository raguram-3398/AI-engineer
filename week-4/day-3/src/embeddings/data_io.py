"""I/O edge: read JSON data files into frozen dataclasses.

Every failure (missing file, bad JSON, wrong shape, dangling reference) becomes
a DataFileError naming the file, so main can report it in one line.
"""

import json
from pathlib import Path
from typing import Any

from embeddings.exceptions import DataFileError
from embeddings.models import TRIPLET_CATEGORIES, Passage, RetrievalQuery, Triplet

_TRIPLET_KEYS: tuple[str, ...] = ("anchor", "positive", "negative", "category")
_PASSAGE_KEYS: tuple[str, ...] = ("id", "text")
_QUERY_KEYS: tuple[str, ...] = ("question", "expected_id")


def _read_records(path: Path, keys: tuple[str, ...]) -> list[dict[str, str]]:
    """Return a non-empty list of objects whose `keys` are non-empty strings."""
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise DataFileError(f"{path}: file not found") from e
    except json.JSONDecodeError as e:
        raise DataFileError(f"{path}: invalid JSON ({e.msg}, line {e.lineno})") from e
    except OSError as e:
        raise DataFileError(f"{path}: could not read ({e})") from e

    if not isinstance(raw, list) or not raw:
        raise DataFileError(f"{path}: expected a non-empty JSON list")
    records: list[dict[str, str]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise DataFileError(f"{path}: item {index} is not an object")
        for key in keys:
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                raise DataFileError(f"{path}: item {index} needs non-empty '{key}'")
        records.append({key: item[key].strip() for key in keys})
    return records


def load_triplets(path: Path) -> list[Triplet]:
    """Load hard-negative triplets. Unknown categories are rejected."""
    triplets: list[Triplet] = []
    for index, record in enumerate(_read_records(path, _TRIPLET_KEYS)):
        if record["category"] not in TRIPLET_CATEGORIES:
            raise DataFileError(
                f"{path}: item {index} has unknown category {record['category']!r}"
            )
        triplets.append(Triplet(**record))
    return triplets


def load_passages(path: Path) -> list[Passage]:
    """Load passages. Duplicate ids are rejected: ids are how retrieval is scored."""
    passages = [Passage(**record) for record in _read_records(path, _PASSAGE_KEYS)]
    seen: set[str] = set()
    for passage in passages:
        if passage.id in seen:
            raise DataFileError(f"{path}: duplicate passage id {passage.id!r}")
        seen.add(passage.id)
    return passages


def load_queries(path: Path, passage_ids: set[str]) -> list[RetrievalQuery]:
    """Load retrieval queries; every expected_id must exist among `passage_ids`.

    A dangling id would make that query unanswerable and silently drag hit@k down.
    """
    queries = [RetrievalQuery(**record) for record in _read_records(path, _QUERY_KEYS)]
    for index, query in enumerate(queries):
        if query.expected_id not in passage_ids:
            raise DataFileError(
                f"{path}: item {index} expects unknown passage {query.expected_id!r}"
            )
    return queries
