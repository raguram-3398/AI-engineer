from pathlib import Path

from log_parser.parser import LogEntry, filter_by_level, get_level_count, parse_log_file

BASE_DIR = Path(__file__).parent.parent.parent


def display_entries(entries: list[LogEntry]) -> None:
    for entry in entries:
        print(f"{entry.date} {entry.time} {entry.level} {entry.message}")


def display_summary(entries: list[LogEntry]) -> None:
    counts = get_level_count(entries)
    print("\n   ---  Log Summary  ---")
    for level, count in counts.items():
        print(f"{level}: {count}")


def display_error(entries: list[LogEntry]) -> None:
    error = filter_by_level(entries, "ERROR")
    print("\n   ---  Error Summary  ---")
    print(f"ERROR count: {len(error)}")


def main() -> None:
    log_path = BASE_DIR / "logs" / "sample.log"
    entries = parse_log_file(log_path)
    display_entries(entries)
    display_summary(entries)
    display_error(entries)


if __name__ == "__main__":
    main()
