import pytest

from books.book_class import Book
from books.book_dataclass import BookData


def test_str_format() -> None:
    b = Book("Dune", "Frank Herbert", 412, 1965)
    assert str(b) == "Dune by Frank Herbert (1965)"


def test_is_long() -> None:
    b = Book("Short", "Author", 100, 2000)
    assert b.is_long() is False


def test_get_age() -> None:
    b = Book("Dune", "Frank Herbert", 412, 1965)
    assert b.get_age(2026) == 61


def test_total_books() -> None:
    initial = Book.total_books
    Book("A", "B", 100, 2000)
    Book("C", "D", 200, 2001)
    assert Book.total_books == initial + 2


def test_dataclass_invalid_pages() -> None:
    with pytest.raises(ValueError):
        BookData("X", "Y", 0, 2000)


def test_dataclass_invalid_year() -> None:
    with pytest.raises(ValueError):
        BookData("X", "Y", 100, 900)

def test_is_long_true() -> None:
    b = Book("Dune", "Frank Herbert", 412, 1965)
    assert b.is_long() is True