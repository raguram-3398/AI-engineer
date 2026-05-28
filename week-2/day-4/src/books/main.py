from books.book_class import Book
from books.book_dataclass import BookData


def main() -> None:
    """Demonstrate regular class and dataclass book implementations."""
    # Regular class instances
    b1 = Book("Dune", "Frank Herbert", 412, 1965)
    b2 = Book("1984", "George Orwell", 328, 1949)
    b3 = Book("S", "Short Book", 120, 2020)

    print(b1)
    print(b2)
    print(b3)

    print(b1.is_long(), b3.is_long())
    print(b1.get_age(2026))

    print("Total books:", Book.total_books)

    # Dataclass instances
    d1 = BookData("Dune", "Frank Herbert", 412, 1965)
    d2 = BookData("1984", "George Orwell", 328, 1949)
    d3 = BookData("S", "Short Book", 120, 2020)

    print(d1)
    print(d2)
    print(d3)

    print(d1.is_long(), d3.is_long())


if __name__ == "__main__":
    main()
