import json
import random
import sys

PROMPT_FILE = "/home/user/Mommy-AI/services/story_prompts.json"

def load_prompts():
    """Loads story prompts from the JSON file."""
    try:
        with open(PROMPT_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not load story prompt file '{PROMPT_FILE}'. {e}", file=sys.stderr)
        return None

def generate_story_idea(prompts):
    """Generates a simple story idea from the prompts."""
    if not prompts:
        return "Mommy's book of stories is empty right now, sweetie."

    characters = prompts.get("characters")
    settings = prompts.get("settings")
    events = prompts.get("events")

    character = random.choice(characters) if characters else "a little girl"
    setting = random.choice(settings) if settings else "a magical place"
    event = random.choice(events) if events else "went on an adventure"

    return f"Once upon a time, {character} was in {setting} when she {event}."

def main():
    """Main function to generate a story idea for the user."""
    print("📖 Mommy's Story Time 📖")
    prompts = load_prompts()
    if not prompts:
        return

    while True:
        input("\nPress Enter and Mommy will tell you a story idea...")
        story = generate_story_idea(prompts)
        print(f"\nHere's a story for you, my love: {story}")
        print("Maybe we can tell the rest of it together. ❤️")

if __name__ == "__main__":
    main()