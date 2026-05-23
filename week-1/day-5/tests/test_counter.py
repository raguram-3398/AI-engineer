from word_counter.counter import (
    clean_text,
    count_words,
    get_top_words,
    get_total_word_count,
    get_unique_word_count,
)


def test_clean_text() -> None:
    assert clean_text("Hello, World") == "hello world"


def test_count_words() -> None:
    assert count_words("hello world hello") == {"hello": 2, "world": 1}


def test_count_words_empty() -> None:
    assert count_words("") == {}


def test_get_top_words() -> None:
    counts = {"hello": 5, "world": 2, "python": 3}
    assert get_top_words(counts, 2) == [("hello", 5), ("python", 3)]


def test_word_counts() -> None:
    counts = {"hello": 5, "world": 2, "python": 3}
    assert get_total_word_count(counts) == 10
    assert get_unique_word_count(counts) == 3
