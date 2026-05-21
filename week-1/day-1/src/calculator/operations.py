def calculate(a: float, b: float, op: str) -> float:
    """Performs mathematical operation on two numbers."""
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        if b == 0:
            raise ValueError("Error: cannot divide by zero")
        return a / b
    else:
        raise ValueError("Error: invalid operation")
