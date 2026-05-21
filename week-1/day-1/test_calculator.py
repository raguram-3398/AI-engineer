from calculator import calculate

def test_add():
    assert calculate(10, 5, '+') == 15

def test_substract():
    assert calculate(10, 5, '-') == 5

def test_multiply():
    assert calculate(10, 5, '*') == 50

def test_divide():
    assert calculate(10, 5, '/') == 2

def test_divide_by_zero():
    assert calculate(10, 0, '/') == "Error: cannot divide by zero"

def test_invalid_operation():
    assert calculate(10, 5, '%') == "Error: invalid operation"