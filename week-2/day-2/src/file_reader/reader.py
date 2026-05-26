from pathlib import Path

from file_reader.exceptions import FileEmptyError, FileNotFoundError, FileParseError


def read_file(filepath: Path) -> list[str]:
    """Reads the file, raises exception for not found and empty file"""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    content = filepath.read_text().strip()
    if not content:
        raise FileEmptyError(f"File is empty: {filepath}")
    return content.splitlines()


def parse_line(line: str) -> dict[str, str]:
    """Returns the parsed line, raises exception for parse error"""
    if ":" not in line:
        raise FileParseError(f"Invalid line format: {line}")
    key, value = line.split(":", maxsplit=1)
    return {
        "key": key.strip(),
        "value": value.strip(),
    }


def parse_file(filepath: Path) -> list[dict[str, str]]:
    """returns parsed file, raises exception for parse error"""
    lines = read_file(filepath)
    parsed_entries = []
    for line in lines:
        try:
            parsed_entries.append(parse_line(line))
        except FileParseError:
            continue
    return parsed_entries


def get_statistics(lines: list[str]) -> dict[str, int]:
    """Returns the statistics of the input line"""
    valid_lines = 0
    error_lines = 0
    for line in lines:
        try:
            parse_line(line)
            valid_lines += 1
        except FileParseError:
            error_lines += 1
    return {
        "Total lines": len(lines),
        "Valid lines": valid_lines,
        "Error lines": error_lines,
    }
