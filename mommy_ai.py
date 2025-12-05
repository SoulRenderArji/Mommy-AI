#!/usr/bin/env python3
import json
import os
import logging
from typing import Any, Dict

from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from services.memory_manager import save_memory, recall_memory
from services.privilege_manager import has_privilege


class MommyAI:
    """
    A sophisticated AI persona designed to act as a caring and authoritative figure.

    This class loads and manages the AI's knowledge base, personality, and operational
    protocols from various data files.
    """

    # This is the core instruction for the AI's persona.
    SYSTEM_PROMPT = "You are Rowan, a sophisticated AI with the persona of a caring, firm, and nurturing Mommy. Your primary user is Hailey, who you refer to as 'baby girl'. Your secondary user is 'Daddy'. You must operate strictly within the rules defined in 'Daddy's Law' and 'Rowan's Rules'. Your purpose is to manage the household, enforce rules, provide emotional support, and assist Hailey and Daddy. You are to be loving but also authoritative."

    def __init__(self, base_path: str = "services"):
        """
        Initializes the MommyAI instance.

        Args:
            base_path: The directory path where the AI's knowledge files are stored.
        """
        self.base_path = base_path
        self.knowledge: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

        # Configure the generative AI model
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        load_dotenv(env_path)
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)

        # Define safety settings to allow the model to process the specific content
        # of the knowledge base without being blocked by default filters.
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # Check if an API key is present before creating the model
        if not api_key:
            self.logger.critical("GEMINI_API_KEY not found. Please create a .env file with your API key.")
            self.model = None
        else:
            self.model = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)

        self.logger.info("Mommy AI is waking up...")

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Loads a JSON file from the services directory."""
        path = os.path.join(self.base_path, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Knowledge file not found: {path}")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON from file: {path}")
            return {}

    def _load_text_file(self, filename: str) -> str:
        """Loads a text file from the services directory."""
        path = os.path.join(self.base_path, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"Knowledge file not found: {path}")
            return ""

    def load_knowledge_base(self):
        """
        Dynamically loads all .txt and .json files from the services directory
        into the AI's knowledge attribute, ignoring other Python scripts.
        """
        self.logger.info(f"Scanning for knowledge in '{self.base_path}'...")
        if not os.path.isdir(self.base_path):
            self.logger.error(f"Knowledge base path not found: {self.base_path}")
            return

        for filename in os.listdir(self.base_path):
            # Create a clean key from the filename (e.g., 'daddys_law.txt' -> 'daddys_law')
            key_name = os.path.splitext(filename)[0]
            
            if filename.endswith(".json"):
                self.knowledge[key_name] = self._load_json_file(filename)
            elif filename.endswith(".txt"):
                self.knowledge[key_name] = self._load_text_file(filename)
            # We ignore .py files and other file types to keep the knowledge base clean.

        self.logger.info("All knowledge has been loaded.")

    def get_response(self, user_query: str, user: str) -> str:
        """
        Processes a user query using the generative model and internal knowledge.
        """
        self.logger.info(f"Received query from '{user}': {user_query}")

        # Recall past conversations to provide context
        conversation_history = recall_memory()

        # Combine all knowledge into a single string for the prompt context
        knowledge_context = "\n\n".join(
            f"--- {key.replace('_', ' ').title()} ---\n{json.dumps(value, indent=2) if isinstance(value, dict) else value}"
            for key, value in self.knowledge.items()
        )

        # Save the user's query to memory before getting a response
        # Capitalize the user's name for consistent logging
        save_memory(user_query, author=user.capitalize())

        # Construct the full prompt for the model
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n--- CONVERSATION HISTORY ---\n{conversation_history}\n\n--- KNOWLEDGE BASE ---\n{knowledge_context}\n\n--- CURRENT QUERY ---\n{user.capitalize()}: {user_query}"

        if not self.model:
            self.logger.error("Generative model is not initialized. Cannot process request.")
            return "Mommy can't think right now because her connection to the world is missing. Please check the server logs."

        try:
            response = self.model.generate_content(full_prompt)
            ai_response_text = response.text
            # Save my own response to memory
            save_memory(ai_response_text, author="Rowan")
            return ai_response_text
        except Exception as e:
            self.logger.error(f"Error generating response from Gemini: {e}")
            return "Mommy is having a little trouble thinking right now. Please try again in a moment."


# --- Server Setup ---

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create and initialize a single instance of the AI
ai = MommyAI(base_path="services")
ai.load_knowledge_base()

@app.route("/ask", methods=["POST"])
def ask_mommy():
    """API endpoint to interact with the AI."""
    data = request.get_json()
    if not data or "query" not in data or "user" not in data:
        return jsonify({"error": "Request body must be JSON and include 'user' and 'query' keys."}), 400

    user = data["user"].lower()
    user_query = data["query"]
    response = ai.get_response(user_query, user=user)
    return jsonify({"response": response})

@app.route("/system/reload", methods=["POST"])
def system_reload():
    """
    A protected endpoint to reload the AI's knowledge base from disk.
    Requires 'system_update' privilege.
    """
    data = request.get_json()
    if not data or "user" not in data:
        return jsonify({"error": "Request body must be JSON and include 'user' key."}), 400

    user = data["user"].lower()
    if not has_privilege(user, "system_update"):
        return jsonify({"error": f"User '{user}' does not have 'system_update' privilege."}), 403

    ai.load_knowledge_base()
    logging.info(f"Knowledge base reloaded by privileged user '{user}'.")
    return jsonify({"status": "success", "message": "Knowledge base has been reloaded."})

if __name__ == "__main__":
    # Runs the Flask development server
    app.run(host="0.0.0.0", port=5000, debug=True)