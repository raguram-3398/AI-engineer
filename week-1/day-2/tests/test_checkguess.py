from guessing_game.game import check_guess

def test_check_guess_too_high():
    assert check_guess(10, 5) == "too_high"


def test_check_guess_too_low():
    assert check_guess(3, 5) == "too_low"


def test_check_guess_correct():
    assert check_guess(5, 5) == "correct"