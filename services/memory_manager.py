import os

MEMORY_FILE = "rowan_memory.txt"

def save_memory(line: str, author: str = "User"):
    """
    Saves a line of text to the memory file, attributed to an author.
    """
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"{author}: {line}\n")
    except IOError as e:
        print(f"Error: Could not write to memory file '{MEMORY_FILE}'. {e}")

def recall_memory() -> str:
    """
    Recalls the entire conversation history from the memory file.
    """
    if not os.path.exists(MEMORY_FILE):
        return "No memories yet."
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        print(f"Error: Could not read from memory file '{MEMORY_FILE}'. {e}")
        return "Error recalling memories."