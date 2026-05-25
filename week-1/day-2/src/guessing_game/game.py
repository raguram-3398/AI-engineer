import random


def is_valid_range(lower: int, upper: int) -> bool:
    """checks if lower is lower than upper"""
    return lower < upper


def generate_secret_number(lower: int, upper: int) -> int:
    """generate a random number between lower and upper"""
    return random.randint(lower, upper)


def check_guess(guess: int, secret: int) -> str:
    """checks if the guess is high, correct or low"""
    if guess > secret:
        return "too_high"
    elif guess < secret:
        return "too_low"
    else:
        return "correct"
