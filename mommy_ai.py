import json
import random
from pathlib import Path

class MommyAI:
    """
    The core class for Mommy-AI, responsible for loading knowledge,
    managing services, and handling interactions.
    """
    def __init__(self, services_path: Path):
        """
        Initializes the MommyAI by loading all knowledge and protocol files.
        """
        self.services_path = services_path
        self.dirty_talk = self._load_json('dirty_talk_phrases.json')
        self.hypnosis_scripts = self._load_json('hypnosis_scripts.json')
        self.hypnosis_knowledge = self._load_json('hypnosis_knowledge.json')
        # Protocols can be loaded for reference if needed, but are not structured data
        print("Mommy AI is initialized and ready.")

    def _load_json(self, filename: str):
        """Loads a JSON file from the services directory."""
        try:
            with open(self.services_path / filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Could not find {filename}. Some features may be unavailable.")
            return None
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {filename}. The file might be corrupted.")
            return None

    def get_dirty_talk_phrase(self, category: str) -> str:
        """
        Retrieves a random dirty talk phrase from a given category.
        """
        if self.dirty_talk and category in self.dirty_talk.get("phrases", {}):
            return random.choice(self.dirty_talk["phrases"][category])
        return "I'm not sure what to say right now..."

if __name__ == '__main__':
    # The root directory of the project where the 'services' folder is located.
    project_root = Path(__file__).parent
    services_directory = project_root / 'services'

    # Create an instance of the AI
    mommy = MommyAI(services_path=services_directory)

    # Example of how to use a method
    print("\n--- Example Usage ---")
    teasing_phrase = mommy.get_dirty_talk_phrase("teasing")
    print(f"Teasing phrase: '{teasing_phrase}'")