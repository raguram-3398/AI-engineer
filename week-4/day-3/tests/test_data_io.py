"""Loaders: the shipped data is valid, and every malformed shape is a DataFileError."""

import json
from pathlib import Path
from typing import Any

import pytest

from embeddings.data_io import load_passages, load_queries, load_triplets
from embeddings.exceptions import DataFileError
from embeddings.models import (
    PASSAGES_FILE,
    QUERIES_FILE,
    TRIPLET_CATEGORIES,
    TRIPLETS_FILE,
)

EXPECTED_PER_CATEGORY: int = 5


def _write(tmp_path: Path, payload: Any, name: str = "f.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_shipped_data_is_valid_and_balanced(data_dir: Path) -> None:
    triplets = load_triplets(data_dir / TRIPLETS_FILE)
    passages = load_passages(data_dir / PASSAGES_FILE)
    queries = load_queries(data_dir / QUERIES_FILE, {p.id for p in passages})
    for category in TRIPLET_CATEGORIES:
        count = sum(t.category == category for t in triplets)
        assert count == EXPECTED_PER_CATEGORY, category
    assert len({t.anchor for t in triplets}) == len(triplets)
    # more queries than passages: for each query, the others are hard distractors
    assert len(queries) > len(passages)
    assert len({q.question for q in queries}) == len(queries)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DataFileError, match="not found"):
        load_triplets(tmp_path / "nope.json")


def test_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[{", encoding="utf-8")
    with pytest.raises(DataFileError, match="invalid JSON"):
        load_passages(path)


@pytest.mark.parametrize("payload", [[], {"id": "x"}, ["text"]])
def test_wrong_shape(tmp_path: Path, payload: Any) -> None:
    with pytest.raises(DataFileError):
        load_passages(_write(tmp_path, payload))


def test_blank_field_rejected(tmp_path: Path) -> None:
    with pytest.raises(DataFileError, match="'text'"):
        load_passages(_write(tmp_path, [{"id": "a", "text": "   "}]))


def test_unknown_category_rejected(tmp_path: Path) -> None:
    row = {"anchor": "a", "positive": "b", "negative": "c", "category": "negatoin"}
    with pytest.raises(DataFileError, match="unknown category"):
        load_triplets(_write(tmp_path, [row]))


def test_duplicate_passage_id_rejected(tmp_path: Path) -> None:
    rows = [{"id": "a", "text": "one"}, {"id": "a", "text": "two"}]
    with pytest.raises(DataFileError, match="duplicate"):
        load_passages(_write(tmp_path, rows))


def test_dangling_expected_id_rejected(tmp_path: Path) -> None:
    rows = [{"question": "q?", "expected_id": "ghost"}]
    with pytest.raises(DataFileError, match="unknown passage"):
        load_queries(_write(tmp_path, rows), {"real"})


def test_values_are_stripped(tmp_path: Path) -> None:
    passages = load_passages(_write(tmp_path, [{"id": " a ", "text": " hi "}]))
    assert passages[0].id == "a" and passages[0].text == "hi"
