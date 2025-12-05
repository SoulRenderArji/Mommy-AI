#!/usr/bin/env python3
import json
import os
import logging
from typing import Any, Dict
import threading
import sqlite3

from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from services.memory_manager import save_memory, recall_memory
from services.privilege_manager import has_privilege
from services.lila_scheduler import run_scheduler


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

    def _load_db_data(self, db_filename: str) -> list[dict[str, Any]]:
        """Loads caregiver action data from the SQLite database."""
        db_path = os.path.join(self.base_path, db_filename)
        if not os.path.exists(db_path):
            self.logger.warning(f"Database file not found: {db_path}. Skipping.")
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT action_type, communication_style, outcome_rating FROM caregiver_actions ORDER BY outcome_rating DESC")
            rows = cursor.fetchall()
            conn.close()
            # Convert sqlite3.Row objects to standard dictionaries for JSON serialization
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            self.logger.error(f"Error reading from database {db_path}: {e}")
            return []

    def update_effectiveness(self, action_type: str, communication_style: str, feedback_delta: int, db_filename: str = "lila_data.db") -> bool:
        """
        Updates the effectiveness rating of a caregiver action based on feedback.
        
        Args:
            action_type: Type of action (e.g., "Emotional Support", "Discipline")
            communication_style: Communication style used (e.g., "Nurturing", "Authoritative")
            feedback_delta: Change in rating (-2 to +2 recommended, though no limits)
            db_filename: Name of the database file to update
        
        Returns:
            True if update was successful, False otherwise
        """
        db_path = os.path.join(self.base_path, db_filename)
        if not os.path.exists(db_path):
            self.logger.error(f"Database file not found: {db_path}. Cannot update effectiveness.")
            return False
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Update the outcome_rating for the matching action
            cursor.execute(
                "UPDATE caregiver_actions SET outcome_rating = outcome_rating + ? WHERE action_type = ? AND communication_style = ?",
                (feedback_delta, action_type, communication_style)
            )
            
            if cursor.rowcount == 0:
                self.logger.warning(f"No matching action found: {action_type} / {communication_style}")
                conn.close()
                return False
            
            conn.commit()
            conn.close()
            self.logger.info(f"Updated effectiveness: {action_type} ({communication_style}) by {feedback_delta:+d}")
            
            # Reload the knowledge base to reflect the changes
            self.load_knowledge_base()
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error updating database {db_path}: {e}")
            return False

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
            elif filename.endswith(".db"):
                self.knowledge[key_name] = self._load_db_data(filename)
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

@app.route("/feedback/effectiveness", methods=["POST"])
def update_effectiveness():
    """
    API endpoint for Mommy AI to learn from outcomes and adjust her strategies.
    Updates the effectiveness rating of caregiver actions based on feedback.
    
    Expected JSON payload:
    {
        "user": "hailey",
        "action_type": "Emotional Support",
        "communication_style": "Nurturing",
        "feedback": 1  # Positive feedback (1 or 2) or negative (-1 or -2)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    
    required_fields = ["user", "action_type", "communication_style", "feedback"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Request must include: {', '.join(required_fields)}"}), 400
    
    user = data["user"].lower()
    action_type = data["action_type"]
    communication_style = data["communication_style"]
    feedback_delta = data["feedback"]
    
    # Validate feedback is in a reasonable range
    if not isinstance(feedback_delta, int) or feedback_delta == 0:
        return jsonify({"error": "Feedback must be a non-zero integer"}), 400
    
    # Update the effectiveness rating
    success = ai.update_effectiveness(action_type, communication_style, feedback_delta)
    
    if success:
        message = f"Mommy remembers: {action_type} with {communication_style} was {'more' if feedback_delta > 0 else 'less'} effective. Learning from you, baby girl. 💕"
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": f"Could not find or update action: {action_type} / {communication_style}"}), 404

if __name__ == "__main__":
    # Start the scheduler in a background thread.
    # The daemon=True flag ensures the thread will exit when the main app exits.
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Lila Scheduler has been started in the background.")

    # Runs the Flask development server
    app.run(host="0.0.0.0", port=5000, debug=True)