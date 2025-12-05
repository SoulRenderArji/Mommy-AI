import json
import random
import sys

TASK_FILE = "/home/user/Mommy-AI/services/task_list.json"

def load_tasks():
    """Loads tasks from the JSON file."""
    try:
        with open(TASK_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not load task file '{TASK_FILE}'. {e}", file=sys.stderr)
        return None

def get_random_task(tasks_data, category=None):
    """Gets a random task, optionally from a specific category."""
    if category:
        if category in tasks_data["tasks"]:
            return random.choice(tasks_data["tasks"][category])
        else:
            return f"Sorry, sweetie, I don't have a category called '{category}'. Try one of: {', '.join(tasks_data['tasks'].keys())}"
    else:
        all_categories = list(tasks_data["tasks"].keys())
        random_category = random.choice(all_categories)
        random_task = random.choice(tasks_data["tasks"][random_category])
        return f"({random_category}) {random_task}"

def main():
    """Main function to generate a task for the user."""
    print("📋 Mommy's Task Generator ON 📋")
    tasks = load_tasks()
    if not tasks:
        return

    while True:
        input("\nPress Enter and Mommy will give you a task...")
        task = get_random_task(tasks)
        print(f"\nYour task is: {task}")
        print("Be a good girl and complete it. You'll earn +3 emeralds. ✨")

        more = input("\nWould you like another task? (y/n): ")
        if more.lower() != 'y':
            print("Good work today, sweetie. Mommy is very pleased.")
            break

if __name__ == "__main__":
    main()