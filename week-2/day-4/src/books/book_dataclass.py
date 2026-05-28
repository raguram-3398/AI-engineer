from dataclasses import dataclass


@dataclass
class BookData:
    """Represents validated book data using a dataclass."""

    title: str
    author: str
    pages: int
    year: int
    LONG_BOOK_THRESHOLD: int = 300

    def __post_init__(self) -> None:
        """Validate book data after dataclass initialization."""
        if self.pages <= 0:
            raise ValueError("Pages must be greater than 0")
        if self.year < 1000:
            raise ValueError("year must be realistic (>= 1000)")

    def is_long(self) -> bool:
        """Return True if the book exceeds the long-book page threshold."""
        return self.pages > self.LONG_BOOK_THRESHOLD