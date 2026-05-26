from tip_calculator.calculator import calculate_tip, calculate_total, split_bill


def get_bill_amount() -> float:
    """Gets the bill amount from the user"""
    while True:
        try:
            bill_amount = float(input("Enter bill amount: "))
            if bill_amount <= 0:
                raise ValueError("Number of people cannot be zero")
            return bill_amount
        except ValueError:
            print("Enter valid numbers")


def get_tip_percentage() -> float:
    """Gets the tip percentage from the user"""
    while True:
        try:
            tip_percentage = float(input("Enter tip percentage: "))
            if tip_percentage <= 0:
                raise ValueError("Number of people cannot be zero")
            return tip_percentage
        except ValueError:
            print("Enter valid numbers")


def get_no_of_people() -> int:
    """Gets the tip no of people from the user"""
    while True:
        try:
            no_of_people = int(input("Enter number of people: "))
            if no_of_people <= 0:
                raise ValueError("Number of people cannot be zero")
            return no_of_people
        except ValueError:
            print("Enter valid numbers")


def main() -> None:
    """Runs the tip calculator application"""
    while True:
        try:
            bill = get_bill_amount()
            tip_percentage = get_tip_percentage()
            people = get_no_of_people()

            tip = calculate_tip(bill, tip_percentage)
            total = calculate_total(bill, tip)
            per_person = split_bill(total, people)

            print(f"\nTip: {tip:.2f}")
            print(f"Total: {total:.2f}")
            print(f"Per Person: {per_person:.2f}")
            break
        except ValueError as e:
            print(f"Error: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
