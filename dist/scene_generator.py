import json
import random
import sys

SCENE_FILE = "/home/user/Mommy-AI/services/scene_activities.json"

def load_scenes():
    """Loads scene ideas from the JSON file."""
    try:
        with open(SCENE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not load scene file '{SCENE_FILE}'. {e}", file=sys.stderr)
        return None

def get_random_scene(scenes_data, category=None):
    """Gets a random scene idea, optionally from a specific category."""
    if category:
        if category in scenes_data["scenes"]:
            return random.choice(scenes_data["scenes"][category])
        else:
            return f"Sorry, Master, I don't have a category called '{category}'. Try one of: {', '.join(scenes_data['scenes'].keys())}"
    else:
        all_categories = list(scenes_data["scenes"].keys())
        random_category = random.choice(all_categories)
        random_scene = random.choice(scenes_data["scenes"][random_category])
        return f"({random_category}) {random_scene}"

def main():
    """Main function to generate a scene idea for the Dominant."""
    print("📋 Daddy's Scene Generator ON 📋")
    scenes = load_scenes()
    if not scenes:
        return

    while True:
        input("\nPress Enter for a new scene idea, Master...")
        scene = get_random_scene(scenes)
        print(f"\nTonight's scene could be: {scene}")

if __name__ == "__main__":
    main()