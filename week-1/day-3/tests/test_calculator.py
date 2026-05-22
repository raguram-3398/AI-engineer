import pytest
from tip_calculator.calculator import calculate_tip, calculate_total, split_bill


def test_calculate_tip():
    assert calculate_tip(100, 20) == 20


def test_calculate_total():
    assert calculate_total(100, 20) == 120


def test_split_bill():
    assert split_bill(120, 5) == 24


def test_split_bill_zero_people():
    with pytest.raises(ValueError, match="Number of people must be above zero."):
        split_bill(100, 0)
