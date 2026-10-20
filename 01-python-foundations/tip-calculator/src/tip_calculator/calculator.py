def calculate_tip(bill_amount: float, tip_percentage: float) -> float:
    """Returns the tip amount given a bill amount and tip percentage"""
    return bill_amount * (tip_percentage / 100)


def calculate_total(bill_amount: float, tip_amount: float) -> float:
    """Returns the total amount given a bill amount and tip amount"""
    return bill_amount + tip_amount


def split_bill(total_amount: float, num_people: int) -> float:
    """Returns the split amount given a total amount and no of people"""
    if num_people <= 0:
        raise ValueError("Number of people must be above zero.")
    return total_amount / num_people
