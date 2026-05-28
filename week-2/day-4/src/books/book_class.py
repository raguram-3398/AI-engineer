from __future__ import annotations


class Book:
    """Represents a book with state and behavior."""

    total_books: int = 0
    LONG_BOOK_THRESHOLD: int = 300

    def __init__(self, title: str, author: str, pages: int, year: int) -> None:
        """Initialize a Book instance with title, author, pages, and publication year."""
        self.title = title
        self.author = author
        self.pages = pages
        self.year = year
        Book.total_books += 1

    def __str__(self) -> str:
        """Return a human-readable string representation of the book."""
        return f"{self.title} by {self.author} ({self.year})"

    def is_long(self) -> bool:
        """Return True if the book exceeds the long-book page threshold."""
        return self.pages > Book.LONG_BOOK_THRESHOLD

    def get_age(self, current_year: int) -> int:
        """Return the age of the book based on the provided current year."""
        return current_year - self.year

    def summary(self) -> str:
        """Return a formatted summary containing all book details."""
        return f"{self.title} | {self.author} | {self.pages} pages | {self.year}"
