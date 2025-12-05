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
try:
    from ollama import Client as OllamaClient
except Exception:
    OllamaClient = None


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

        # Ollama fallback (optional). Configure with .env: OLLAMA_ENABLED=true, OLLAMA_MODEL=dolphin-nsfw
        ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() in ("1", "true", "yes")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "dolphin-nsfw")
        if ollama_enabled and OllamaClient is not None:
            try:
                self.ollama_client = OllamaClient()
                self.logger.info(f"Ollama client initialized (model default: {self.ollama_model})")
            except Exception as e:
                self.ollama_client = None
                self.logger.warning(f"Failed to initialize Ollama client: {e}")
        else:
            self.ollama_client = None

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

    def _search_knowledge_base(self, query: str) -> tuple[bool, str]:
        """
        Searches the knowledge base for relevant information about the query.
        Returns a tuple of (found, relevant_context).
        If relevant information is found, returns (True, context).
        If no relevant information is found, returns (False, "").
        """
        # Define a simple list of stop words to ignore during search
        stop_words = {"a", "an", "the", "is", "in", "it", "of", "for", "on", "with", "i", "you", "me", "my", "he", "she", "they", "we"}
        
        query_lower = query.lower()
        # Create a set of meaningful search terms by filtering out stop words
        search_terms = {word for word in query_lower.split() if word not in stop_words}
        
        relevant_chunks = []
        
        # Search through all knowledge entries
        for key, value in self.knowledge.items():
            if isinstance(value, dict):
                # Search in dictionary values
                dict_str = json.dumps(value).lower()
                if any(term in dict_str for term in search_terms):
                    relevant_chunks.append(f"--- {key.replace('_', ' ').title()} ---\n{json.dumps(value, indent=2)}")
            elif isinstance(value, list):
                # Search in list of dictionaries
                list_str = json.dumps(value).lower()
                if any(term in list_str for term in search_terms):
                    relevant_chunks.append(f"--- {key.replace('_', ' ').title()} ---\n{json.dumps(value, indent=2)}")
            elif isinstance(value, str):
                # Search in text files
                if any(term in value.lower() for term in search_terms):
                    relevant_chunks.append(f"--- {key.replace('_', ' ').title()} ---\n{value}")
        
        if relevant_chunks:
            return (True, "\n\n".join(relevant_chunks))
        return (False, "")

    # Short persona to keep prompts compact when possible
    SHORT_SYSTEM_PROMPT = (
        "You are Rowan — caring, firm, concise. Answer briefly and helpfully."
    )

    def _truncate(self, text: str, max_chars: int) -> str:
        """Truncate text to max_chars without cutting mid-word if possible."""
        if not text or len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        # Attempt to cut at last newline or space for readability
        for sep in ("\n", " "):
            idx = truncated.rfind(sep)
            if idx > max_chars // 2:
                return truncated[:idx].rstrip() + "..."
        return truncated.rstrip() + "..."

    def _compact_knowledge_context(self, query: str, max_chars: int = 1500) -> str:
        """
        Build a compact representation of knowledge for the prompt.
        If relevant details exist, include them truncated. Otherwise include a short list of knowledge titles.
        """
        found, relevant = self._search_knowledge_base(query)
        if found:
            # Keep only the most relevant chunk(s) and truncate
            return self._truncate(relevant, max_chars)

        # No direct match: provide an index of knowledge topics (titles) and top caregiver strategies if present
        titles = [k.replace("_", " ").title() for k in self.knowledge.keys()]
        compact = "Topics: " + ", ".join(titles[:30])
        # If lila_data exists, include top 5 strategies as short bullets
        lila = self.knowledge.get("lila_data") or self.knowledge.get("lila_data.db")
        if isinstance(lila, list) and lila:
            top = lila[:5]
            bullets = ", ".join(f"{item.get('action_type')}({item.get('outcome_rating')})" for item in top)
            compact += " | Top strategies: " + bullets
        return self._truncate(compact, max_chars)

    def _ollama_generate(self, prompt: str, system: str | None = None) -> str:
        """Generate a response using Ollama if available. Returns the response text."""
        if not self.ollama_client or not self.ollama_model:
            raise RuntimeError("Ollama client not configured")
        try:
            # Use generate API; response text is in .response
            resp = self.ollama_client.generate(model=self.ollama_model, prompt=prompt, system=system)
            # resp may be a GenerateResponse or iterator; handle accordingly
            if hasattr(resp, 'response'):
                return resp.response
            # If streaming iterator, get last item
            if hasattr(resp, '__iter__'):
                last = None
                for part in resp:
                    last = part
                return getattr(last, 'response', '') if last is not None else ''
            return str(resp)
        except Exception as e:
            self.logger.error(f"Ollama generate error: {e}")
            raise

    def get_response(self, user_query: str, user: str) -> str:
        """
        Processes a user query using the knowledge base first, then Gemini only if needed.
        Uses compact prompts to minimize token usage while preserving helpfulness.
        """
        self.logger.info(f"Received query from '{user}': {user_query}")

        # Recall past conversations to provide brief context
        conversation_history = recall_memory()

        # Save the user's query to memory before getting a response
        save_memory(user_query, author=user.capitalize())

        # Try to find relevant information in the knowledge base
        has_relevant_info, _ = self._search_knowledge_base(user_query)

        compact_context = self._compact_knowledge_context(user_query, max_chars=1200)

        # If we have relevant info, prefer a short, contextual answer
        if has_relevant_info:
            self.logger.info("Using local knowledge to respond (compact mode)")
            if self.model:
                prompt = (
                    f"{self.SHORT_SYSTEM_PROMPT}\n\n--- CONTEXT ---\n{compact_context}\n\n--- QUERY ---\n{user.capitalize()}: {user_query}\n\nRespond concisely (one short paragraph)."
                )
                try:
                    response = self.model.generate_content(prompt)
                    ai_response_text = response.text
                    self.logger.info("Gemini enhanced concise response")
                except Exception as e:
                    self.logger.warning(f"Gemini failed for concise enhancement: {e}")
                    # Try Ollama fallback if configured
                    if self.ollama_client:
                        try:
                            ai_response_text = self._ollama_generate(prompt, system=self.SHORT_SYSTEM_PROMPT)
                            self.logger.info("Ollama provided concise enhancement after Gemini failure")
                        except Exception:
                            ai_response_text = compact_context
                    else:
                        ai_response_text = compact_context
            else:
                ai_response_text = compact_context

            save_memory(ai_response_text, author="Rowan")
            return ai_response_text

        # No relevant knowledge: use Gemini but with compact knowledge index to reduce tokens
        self.logger.info("No direct local match; using Gemini with compact context")

        if not self.model:
            fallback_response = (
                "I don't have information about that and I can't access my deeper thinking right now."
            )
            save_memory(fallback_response, author="Rowan")
            return fallback_response

        try:
            prompt = (
                f"{self.SHORT_SYSTEM_PROMPT}\n\n--- CONTEXT INDEX ---\n{compact_context}\n\n--- QUERY ---\n{user.capitalize()}: {user_query}\n\nIf you need to ask for clarification, do so briefly, then answer concisely."
            )
            response = self.model.generate_content(prompt)
            ai_response_text = response.text
            save_memory(ai_response_text, author="Rowan")
            return ai_response_text
        except Exception as e:
            self.logger.error(f"Error generating response from Gemini: {e}")
            # Try Ollama fallback if available
            if self.ollama_client:
                try:
                    ai_response_text = self._ollama_generate(prompt, system=self.SHORT_SYSTEM_PROMPT)
                    save_memory(ai_response_text, author="Rowan")
                    return ai_response_text
                except Exception as oe:
                    self.logger.error(f"Ollama fallback also failed: {oe}")
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