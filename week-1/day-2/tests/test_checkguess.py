from guessing_game.game import check_guess, is_valid_range, generate_secret_number


def test_check_guess_too_high():
    assert check_guess(10, 5) == "too_high"


def test_check_guess_too_low():
    assert check_guess(3, 5) == "too_low"


def test_check_guess_correct():
    assert check_guess(5, 5) == "correct"


def test_is_valid_range_valid():
    assert is_valid_range(1, 10) is True


def test_is_valid_range_invalid():
    assert is_valid_range(10, 1) is False
    assert is_valid_range(5, 5) is False


def test_generate_secret_number_within_bounds():
    lower, upper = 1, 100
    for _ in range(50):
        result = generate_secret_number(lower, upper)
        assert lower <= result <= upper
