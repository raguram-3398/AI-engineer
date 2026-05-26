from dataclasses import dataclass
from pathlib import Path


@dataclass
class LogEntry:
    date: str
    time: str
    level: str
    message: str


def parse_line(line: str) -> LogEntry | None:
    parts = line.strip().split(maxsplit=3)
    if len(parts) != 4:
        return None
    date, time, level, message = parts
    if "-" not in date:
        return None
    if ":" not in time:
        return None
    return LogEntry(date, time, level, message)


def parse_log_file(filepath: Path) -> list[LogEntry]:
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    entries: list[LogEntry] = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            entry = parse_line(stripped_line)
            if entry is not None:
                entries.append(entry)
    return entries


def filter_by_level(entries: list[LogEntry], level: str) -> list[LogEntry]:
    return [entry for entry in entries if entry.level == level]


def get_level_count(entries: list[LogEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.level] = counts.get(entry.level, 0) + 1
    return counts
