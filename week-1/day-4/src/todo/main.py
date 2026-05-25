from todo.tasks import is_valid_index, add_task, remove_task, complete_task


def display_tasks(tasks: list[str]) -> None:
    """Returns the list of tasks"""
    if not tasks:
        print("No tasks available.")
        return
    for index, task in enumerate(tasks, start=1):
        print(f"{index}: {task}")


def get_menu_choice() -> str:
    """Returns the menu choice"""
    return input("\nchoose an option: ")


def get_task_input() -> str:
    """Returns validated non-empty task input"""
    while True:
        task = input("Enter task: ").strip()
        if task:
            return task
        print("Task cannot be empty.")


def get_index_input(tasks: list[str]) -> int:
    """Returns the validated input index number"""
    while True:
        try:
            user_index = int(input("Enter task index: "))
            index = user_index - 1
            if is_valid_index(tasks, index):
                return index
            print("Invalid index.")
        except ValueError:
            print("Enter a valid number: ")


def main() -> None:
    """Runs the todo application"""
    tasks: list[str] = []
    while True:
        print("\nTodo app Menu")
        print("1 - View Tasks")
        print("2 - Add Task")
        print("3 - Complete Task")
        print("4 - Remove Task")
        print("5 - Exit")
        choice = get_menu_choice()
        if choice == "1":
            display_tasks(tasks)
        elif choice == "2":
            task = get_task_input()
            tasks = add_task(tasks, task)
        elif choice == "3":
            try:
                index = get_index_input(tasks)
                tasks = complete_task(tasks, index)
            except ValueError as error:
                print(error)
        elif choice == "4":
            index = get_index_input(tasks)
            tasks = remove_task(tasks, index)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid Choice")


if __name__ == "__main__":
    main()
