class FileReaderError(Exception):
    """Base exception for all file reader errors."""


class FileNotFoundError(FileReaderError):
    """Raised when the requested file does not exist."""


class FileEmptyError(FileReaderError):
    """Raised when the file exists but contains no content."""


class FileParseError(FileReaderError):
    """Raised when a line cannot be parsed into the expected format."""
