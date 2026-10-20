import re


def count_sentences(text: str) -> int:
    """Count the number of sentences in a text."""
    if not text.strip():
        return 0
    parts = re.split(r"[.!?]", text)
    return len([p for p in parts if p.strip()])


def count_words(text: str) -> int:
    """Count the number of words in a text."""
    if not text.strip():
        return 0
    return len(text.split())


def clean_words(text: str) -> list[str]:
    """Convert text into cleaned lowercase words."""
    words = text.lower().split()
    cleaned = ["".join(c for c in word if c.isalpha()) for word in words]
    return [w for w in cleaned if w]


def get_unique_word_count(text: str) -> int:
    """Count the number of unique words in a text."""
    return len(set(clean_words(text)))


def get_average_word_length(text: str) -> float:
    """Calculate the average word length."""
    words = clean_words(text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def get_character_frequency(text: str) -> dict[str, int]:
    """Count the frequency of alphabetic characters."""
    freq: dict[str, int] = {}
    for char in text.lower():
        if char.isalpha():
            freq[char] = freq.get(char, 0) + 1
    return freq


def get_top_words(text: str, n: int) -> list[tuple[str, int]]:
    """Get the most frequently used words."""
    words = clean_words(text)
    if not words:
        return []
    freq: dict[str, int] = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return sorted_words[:n]


def get_summary(text: str) -> dict[str, int | float]:
    """Generate a summary of text statistics."""
    return {
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
        "average_word_length": get_average_word_length(text),
        "unique_words": get_unique_word_count(text),
    }
