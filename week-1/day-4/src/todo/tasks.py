def add_task(tasks: list[str], task: str) -> list[str]:
    """Returns the list of tasks adding the new task"""
    return tasks + [task]


def is_valid_index(tasks: list[str], index: int) -> bool:
    """Returns if the index is true or false"""
    return 0 <= index < len(tasks)


def remove_task(tasks: list[str], index: int) -> list[str]:
    """Returns the list of tasks removing the input task"""
    if not is_valid_index(tasks, index):
        raise ValueError("Invalid task index")
    return tasks[:index] + tasks[index + 1:]


def complete_task(tasks: list[str], index: int) -> list[str]:
    """Returns the list of tasks marking done for the completed task"""
    if not is_valid_index(tasks, index):
        raise ValueError("Invalid task index")
    updated_task = f"{tasks[index]} - DONE"
    return tasks[:index] + [updated_task] + tasks[index + 1:]
