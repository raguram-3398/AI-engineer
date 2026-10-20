from text_analyzer.analyzer import (
    count_sentences,
    count_words,
    get_average_word_length,
    get_character_frequency,
    get_summary,
)


def test_count_sentences_basic():
    assert count_sentences("Hello. World! How are you?") == 3


def test_count_sentences_trailing_period():
    assert count_sentences("Hello.") == 1  # not 2


def test_count_sentences_empty():
    assert count_sentences("") == 0


def test_count_words_basic():
    assert count_words("hello world") == 2


def test_count_words_extra_spaces():
    assert count_words("hello   world") == 2


def test_count_words_empty():
    assert count_words("") == 0


def test_average_word_length_basic():
    assert get_average_word_length("hello world") == 5.0


def test_average_word_length_with_punctuation():
    result = get_average_word_length("hello, world.")
    assert abs(result - 5.0) < 0.01


def test_average_word_length_empty():
    assert get_average_word_length("") == 0.0


def test_character_frequency_alpha_only():
    freq = get_character_frequency("hi! 123")
    assert freq == {"h": 1, "i": 1}


def test_character_frequency_lowercase():
    freq = get_character_frequency("Hello")
    assert freq == {"h": 1, "e": 1, "l": 2, "o": 1}


def test_character_frequency_empty():
    assert get_character_frequency("") == {}


def test_summary_keys():
    summary = get_summary("Hello world.")
    assert "word_count" in summary
    assert "sentence_count" in summary
    assert "average_word_length" in summary
    assert "unique_words" in summary


def test_summary_empty():
    summary = get_summary("")
    assert summary["word_count"] == 0
    assert summary["average_word_length"] == 0.0
