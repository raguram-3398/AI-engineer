import pytest
from calculator.operations import calculate

def test_add():
    assert calculate(10, 5, "+") == 15


def test_substract():
    assert calculate(10, 5, "-") == 5


def test_multiply():
    assert calculate(10, 5, "*") == 50


def test_divide():
    assert calculate(10, 5, "/") == 2


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Error: cannot divide by zero"):
        calculate(10, 0, "/")


def test_invalid_operation():
    with pytest.raises(ValueError, match="Error: invalid operation"):
        calculate(10, 5, "%")
