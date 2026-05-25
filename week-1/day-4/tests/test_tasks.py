import pytest
from todo.tasks import add_task, remove_task, complete_task, is_valid_index


def test_add_task():
    tasks = ["study"]
    result = add_task(tasks, "excercise")
    assert result == ["study", "excercise"]
    assert tasks == ["study"]


def test_remove_task():
    tasks = ["a", "b", "c"]
    result = remove_task(tasks, 1)
    assert result == ["a", "c"]
    assert tasks == ["a", "b", "c"]


def test_complete_task():
    tasks = ["a", "b", "c"]
    result = complete_task(tasks, 1)
    assert result == ["a", "b - DONE", "c"]
    assert tasks == ["a", "b", "c"]


def test_remove_task_invalid_index_zero():
    tasks = ["a", "b", "c"]
    with pytest.raises(ValueError):
        remove_task(tasks, 5)


def test_complete_task_invalid_index():
    tasks = ["a", "b", "c"]
    with pytest.raises(ValueError):
        complete_task(tasks, 5)


def test_is_valid_index_true():
    tasks = ["a", "b", "c"]
    assert is_valid_index(tasks, 1)
    assert is_valid_index(tasks, 2)
    assert is_valid_index(tasks, 0)


def test_is_valid_index_false():
    tasks = ["a", "b", "c"]
    assert not is_valid_index(tasks, -1)
    assert not is_valid_index(tasks, 3)
    assert not is_valid_index(tasks, 4)
