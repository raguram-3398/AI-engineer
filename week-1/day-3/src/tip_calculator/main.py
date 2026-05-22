from calculator import calculate_tip, calculate_total, split_bill


def get_bill_amount() -> float:
    """Gets the bill amount from user"""
    return float(input("Enter the Bill amount: "))


def get_tip_percentage() -> float:
    """Gets the Tip percentage from user"""
    return float(input("Enter the Tip percentage: "))


def get_num_people() -> int:
    """Gets the No of people to split the bill"""
    return int(input("Enter No of people: "))


def main() -> None:
    while True:
        try:
            bill = get_bill_amount()
            tip_percentage = get_tip_percentage()
            people = get_num_people()

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
