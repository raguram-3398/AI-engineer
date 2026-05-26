from word_counter.counter import (
    count_words,
    get_top_words,
    get_unique_word_count,
    get_total_word_count,
)


def get_text_input() -> str:
    """Returns input text"""
    while True:
        text = input("Enter Text: ").strip()
        if text:
            return text
        print("Text cannot be empty")


def display_results(counts: dict[str, int], top_n: int) -> None:
    """Displays the results"""
    if not counts:
        print("No words found.")
        return
    print(f"Total words: {get_total_word_count(counts)}")
    print(f"Unique words: {get_unique_word_count(counts)}")
    print("\nTop Words:")
    for word, count in get_top_words(counts, top_n):
        print(f"{word}: {count}")


def main() -> None:
    """Runs the Word_counter application"""
    text = get_text_input()
    counts = count_words(text)
    display_results(counts, top_n=5)


if __name__ == "__main__":
    main()
