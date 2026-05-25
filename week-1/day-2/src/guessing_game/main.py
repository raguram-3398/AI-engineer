from guessing_game.game import is_valid_range, generate_secret_number, check_guess


def get_guess(lower: int, upper: int) -> int:
    """gets the guess from user and checks validity"""
    while True:
        raw = input(f"Enter your guess({lower}-{upper}): ")
        try:
            guess = int(raw)
            if lower <= guess <= upper:
                return guess
            print("Out of range. Try again.")
        except ValueError:
            print("Invalid input. Enter a number")


def get_range() -> tuple[int, int]:
    """gets the range from user and checks validity"""
    while True:
        raw_lower = input("Enter lower bound number: ")
        raw_upper = input("Enter upper bound number: ")
        try:
            lower = int(raw_lower)
            upper = int(raw_upper)
            if is_valid_range(lower, upper):
                return lower, upper
            print("Invalid range. Lower must be less than upper. Try again.")
        except ValueError:
            print("Invalid input. Enter numbers only.")


def play_game(lower: int, upper: int) -> None:
    """runs the guessing game"""
    secret = generate_secret_number(lower, upper)
    attempts = 0
    while True:
        guess = get_guess(lower, upper)
        attempts += 1
        result = check_guess(guess, secret)
        if result == "too_high":
            print("TOO HIGH!")
        elif result == "too_low":
            print("TOO LOW!")
        else:
            print(f"Correct! You won in {attempts} attempts.")
            break


def main() -> None:
    while True:
        lower, upper = get_range()
        play_game(lower, upper)
        again = input("Wanna Play again? (y/n): ").lower()
        if again != "y":
            break


if __name__ == "__main__":
    main()
