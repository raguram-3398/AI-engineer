from pathlib import Path

import pytest

from file_reader.exceptions import FileEmptyError
from file_reader.exceptions import FileNotFoundError
from file_reader.exceptions import FileParseError
from file_reader.reader import get_statistics
from file_reader.reader import parse_line
from file_reader.reader import read_file


def test_read_file_raises_for_missing_file(
    tmp_path: Path,
) -> None:
    filepath = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        read_file(filepath)


def test_read_file_raises_for_empty_file(
    tmp_path: Path,
) -> None:
    filepath = tmp_path / "empty.txt"

    filepath.write_text("")

    with pytest.raises(FileEmptyError):
        read_file(filepath)


def test_parse_line_parses_valid_line() -> None:
    result = parse_line("name: Alice")

    assert result == {
        "key": "name",
        "value": "Alice",
    }


def test_parse_line_raises_for_invalid_line() -> None:
    with pytest.raises(FileParseError):
        parse_line("invalid line")


def test_get_statistics_returns_correct_counts() -> None:
    lines = [
        "name: Alice",
        "invalid line",
        "city: Austin",
    ]

    result = get_statistics(lines)

    assert result == {
        "Total lines": 3,
        "Valid lines": 2,
        "Error lines": 1,
    }