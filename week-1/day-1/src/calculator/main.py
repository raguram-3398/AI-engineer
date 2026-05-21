from operations import calculate


def get_operation() -> str:
    """Returns a valid mathematical operator from the user."""
    while True:
        op = input("Enter the operation (+ , - , *, /): ")
        if op in ["+", "-", "*", "/"]:
            return op
        print("Error: Enter valid operator")


def get_numbers() -> tuple[float, float]:
    """Returns two valid numbers from the user."""
    while True:
        try:
            a = float(input("Enter first number: "))
            b = float(input("Enter second number: "))
            return a, b
        except ValueError:
            print("Error: Enter valid numbers")


def main() -> None:
    """Runs the calculator application."""
    a, b = get_numbers()
    op = get_operation()

    try:
        result = calculate(a, b, op)
        print("Result:", result)

    except ValueError as error:
        print("Error:", error)


if __name__ == "__main__":
    main()
