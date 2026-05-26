from pathlib import Path

import pytest

from log_parser.parser import (
    LogEntry,
    filter_by_level,
    get_level_count,
    parse_line,
    parse_log_file,
)


def test_parse_line_valid():
    line = "2026-05-20 10:23:01 INFO Server started"

    result = parse_line(line)

    assert result is not None
    assert isinstance(result, LogEntry)
    assert result.date == "2026-05-20"
    assert result.time == "10:23:01"
    assert result.level == "INFO"
    assert result.message == "Server started"


def test_parse_line_invalid():
    line = "bad line without enough parts"

    result = parse_line(line)

    assert result is None


def test_filter_by_level():
    entries = [
        LogEntry("2026-05-20", "10:00:00", "INFO", "A"),
        LogEntry("2026-05-20", "10:01:00", "ERROR", "B"),
        LogEntry("2026-05-20", "10:02:00", "INFO", "C"),
    ]

    filtered = filter_by_level(entries, "INFO")

    assert len(filtered) == 2
    assert all(e.level == "INFO" for e in filtered)


def test_get_level_count():
    entries = [
        LogEntry("2026-05-20", "10:00:00", "INFO", "A"),
        LogEntry("2026-05-20", "10:01:00", "ERROR", "B"),
        LogEntry("2026-05-20", "10:02:00", "INFO", "C"),
    ]

    counts = get_level_count(entries)

    assert counts == {
        "INFO": 2,
        "ERROR": 1,
    }


def test_parse_log_file_missing_file():
    fake_path = Path("this_file_does_not_exist.log")

    with pytest.raises(FileNotFoundError):
        parse_log_file(fake_path)


def test_parse_log_file_valid(tmp_path):
    log_file = tmp_path / "sample.log"

    log_file.write_text(
        "2026-05-20 10:00:00 INFO A\n"
        "2026-05-20 10:01:00 ERROR B\n"
        "bad malformed line\n"
        "2026-05-20 10:02:00 INFO C\n",
        encoding="utf-8",
    )

    entries = parse_log_file(log_file)

    # malformed line should be skipped
    assert len(entries) == 3

    assert entries[0].level == "INFO"
    assert entries[1].level == "ERROR"
    assert entries[2].message == "C"


def test_parse_log_file_empty(tmp_path: Path) -> None:
    """Empty file should return empty list, not raise."""
    log_file = tmp_path / "empty.log"
    log_file.write_text("", encoding="utf-8")
    entries = parse_log_file(log_file)
    assert entries == []
