import string


def clean_text(text: str) -> str:
    """Returns the cleaned text"""
    cleaned_text = text.lower()
    for punctuation in string.punctuation:
        cleaned_text = cleaned_text.replace(punctuation, "")
    return cleaned_text


def count_words(text: str) -> dict[str, int]:
    """Returns the words and count"""
    cleaned_text = clean_text(text)
    if not cleaned_text.strip():
        return {}
    words = cleaned_text.split()
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts


def get_top_words(counts: dict[str, int], n: int) -> list[tuple[str, int]]:
    """Return the top n words"""
    sorted_words = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return sorted_words[:n]


def get_unique_word_count(counts: dict[str, int]) -> int:
    """Returns the unique word count"""
    return len(counts)


def get_total_word_count(counts: dict[str, int]) -> int:
    """Returns the total words count"""
    return sum(counts.values())
