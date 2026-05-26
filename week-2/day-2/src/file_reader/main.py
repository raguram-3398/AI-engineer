from pathlib import Path

from file_reader.exceptions import FileReaderError
from file_reader.reader import get_statistics, parse_file, read_file

BASE_DIR = Path(__file__).parent.parent.parent

def display_statistics(stats: dict[str, int]) -> None:
    """Displays the statistics"""
    print("\n---   File Statistics   ---")
    for key, value in stats.items():
        print(f"{key}: {value}")


def display_parsed(entries: list[dict[str, str]]) -> None:
    """Displays the Parsed entries"""
    print("\n---   Parsed entries   ---")
    for entry in entries:
        print(f"{entry['key']}: {entry['value']}")


def main() -> None:
    """Runs the file reader application"""
    filepath = BASE_DIR / "data" / "sample.txt"
    try:
        lines = read_file(filepath)
        stats = get_statistics(lines)
        parsed_entries = parse_file(filepath)
        display_statistics(stats)
        display_parsed(parsed_entries)
    except FileReaderError as error:
        print(f"File read error: {error}")
    finally:
        print("File reading completed")


if __name__ == "__main__":
    main()
