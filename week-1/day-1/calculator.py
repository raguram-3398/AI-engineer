def get_operation() -> str:
    while True:
        op = input("Enter the operation (+ , - , *, /): ")
        if op in ["+", "-", "*", "/"]:
            return op
        print("Error: Enter valid operator")
    return op


def get_numbers() -> tuple[int, int]:
    try:
        a = int(input("Enter first number: "))
        b = int(input("Enter second number: "))
        return a, b
    except ValueError:
        print("Error: Enter valid numbers")
        return get_numbers()


def calculate(a: int, b: int, op: str):
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        if b == 0:
            return "Error: cannot divide by zero"
        return a / b
    else:
        return "Error: invalid operation"


def main():
    a, b = get_numbers()
    op = get_operation()

    result = calculate(a, b, op)

    print("Result:", result)


if __name__ == "__main__":
    main()
