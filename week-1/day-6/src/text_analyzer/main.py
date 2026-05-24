from text_analyzer.analyzer import get_summary, get_top_words, get_character_frequency


def get_text_input() -> str:
    print("Enter your text (press enter twice when done): ")
    lines: list[str] = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return " ".join(lines)


def display_analysis(text: str) -> None:
    summary = get_summary(text)
    top_words = get_top_words(text, 5)
    char_freq = get_character_frequency(text)

    print("\n---   Text Analysis   ---")
    print(f"Word count: {summary['word_count']}")
    print(f"Sentence count: {summary['sentence_count']}")
    print(f"Unique words: {summary['unique_words']}")
    print(f"Average word length: {summary['average_word_length']:.2f}")

    print("\n---   Top 5 Words   ---")
    for word, count in top_words:
        print(f"   {word}: {count}")

    print("\n---   Character Frequency   ---")
    for char, count in sorted(char_freq.items()):
        print(f"   {char}: {count}")


def main() -> None:
    text = get_text_input()
    if not text.strip():
        print("No text provided")
        return
    display_analysis(text)


if __name__ == "__main__":
    main()
