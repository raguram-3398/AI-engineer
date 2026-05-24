import re


def count_sentences(text: str) -> int:
    if not text.strip():
        return 0
    parts = re.split(r"[.!?]", text)
    return len([p for p in parts if p.strip()])


def count_words(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())


def get_average_word_length(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0
    cleaned = ["".join(c for c in word if c.isalpha()) for word in words]
    cleaned = [w for w in cleaned if w]
    if not cleaned:
        return 0.0
    return sum(len(w) for w in cleaned) / len(cleaned)


def get_character_frequency(text: str) -> dict[str, int]:
    freq: dict[str, int] = {}
    for char in text.lower():
        if char.isalpha():
            freq[char] = freq.get(char, 0) + 1
    return freq


def get_top_words(text: str, n: int) -> list[tuple[str, int]]:
    words = text.lower().split()
    if not words:
        return []
    cleaned = ["".join(c for c in word if c.isalpha()) for word in words]
    cleaned = [w for w in cleaned if w]
    freq: dict[str, int] = {}
    for word in cleaned:
        freq[word] = freq.get(word, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda item: item[1], reverse=True)
    return sorted_words[:n]


def get_summary(text: str) -> dict[str, int | float]:
    return {
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
        "average_word_length": get_average_word_length(text),
        "unique_words": len(
            set(
                "".join(c for c in w if c.isalpha())
                for w in text.lower().split()
                if any(c.isalpha() for c in w)
            )
        ),
    }
