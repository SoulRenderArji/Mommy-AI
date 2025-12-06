#!/usr/bin/env python3
import json
import os
import logging
from typing import Any, Dict, Callable, Optional
import threading
import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from services.memory_manager import save_memory, recall_memory
from services.privilege_manager import has_privilege
from services.lila_scheduler import run_scheduler
from services.learning_system import LearningSystem
from services.language_understanding import LanguageUnderstanding
from services.cognitive_engine import CognitiveEngine
from dataclasses import asdict
from services import audit
from logging.handlers import RotatingFileHandler
from functools import wraps
from services import proactive_care
from services.toolkit import run_shell, read_file, write_file, git_commit, gui_action
try:
    from ollama import Client as OllamaClient
except Exception:
    OllamaClient = None

def log_interaction(user: str, query: str, response: str, model_used: Optional[str], trace: Optional[Dict[str, Any]] = None):
    """Logs a user-AI interaction to a structured file for later learning."""
    log_dir = os.path.join(os.path.dirname(__file__), "services", "interactions")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"interaction_{timestamp}.json"
    filepath = os.path.join(log_dir, filename)

    interaction_data = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "user": user,
        "query": query,
        "response": response,
        "model_used": model_used,
        "cognitive_trace": trace
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(interaction_data, f, indent=2, ensure_ascii=False)

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
        # user_profiles maps lowercase username -> profile dict
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set the preferred model ('auto', 'gemini', 'ollama')
        self.preferred_model = "auto"

        # Initialize learning system for knowledge absorption and independence
        self.learning_system = LearningSystem(base_path=base_path)
        self.logger.info(f"Learning system active - Independence level: {self.learning_system.independence_level}")

        # Initialize language understanding system for NLP and intent recognition
        self.language_understanding = LanguageUnderstanding(base_path=base_path)
        self.logger.info("Language understanding system initialized")

        # Initialize cognitive engine (decision maker / thought process simulator)
        self.cognitive_engine = CognitiveEngine(language_understanding=self.language_understanding, learning_system=self.learning_system)
        self.logger.info("Cognitive engine initialized")

        # Toolkit helpers (stateless wrappers) for shell/file/gui actions
        # Important: endpoints that expose these must check privileges and user preferences
        self.toolkit = None  # kept for clarity; functions are imported at module level

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
        # Require explicit opt-in to use NSFW models
        self.allow_nsfw = os.getenv("ALLOW_NSFW", "false").lower() in ("1", "true", "yes")
        if ollama_enabled and OllamaClient is not None:
            try:
                host = os.getenv("OLLAMA_HOST") # Use host from .env if provided
                self.ollama_client = OllamaClient(host=host)
                # Verify connection and check for the desired model
                local_models = self.ollama_client.list()["models"]
                model_names = [m["name"] for m in local_models]
                self.logger.info(f"Successfully connected to Ollama. Available models: {', '.join(model_names)}")
                
                # Check if the default NSFW model is available and log a warning if not
                if self.ollama_model not in model_names:
                    self.logger.warning(
                        f"Ollama model '{self.ollama_model}' not found locally. "
                        f"Please run 'ollama pull {self.ollama_model}' to use it."
                    )

            except Exception as e:
                self.ollama_client = None
                self.logger.error(f"Could not connect to Ollama server. Ollama fallback is DISABLED. Error: {e}")
        else:
            self.ollama_client = None

        # Fatal check: if no models are available, the AI cannot function.
        if self.model is None and self.ollama_client is None:
            self.logger.critical("FATAL: No language models are available. Rowan will be unable to think or speak.")
            self.logger.critical("Please configure GEMINI_API_KEY in your .env file or ensure the Ollama server is running and configured.")
            exit("FATAL: No language models available.")

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

    def _load_user_profiles(self):
        """Load user profiles from services/user_profiles.json if present."""
        profiles_path = os.path.join(self.base_path, "user_profiles.json")
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # normalize keys to lowercase usernames
                    self.user_profiles = {k.lower(): v for k, v in data.items()}
                    self.logger.info(f"Loaded {len(self.user_profiles)} user profiles")
            except Exception as e:
                self.logger.exception(f"Failed to load user profiles: {e}")
                self.user_profiles = {}
        else:
            self.user_profiles = {}

    def _save_user_profiles(self):
        profiles_path = os.path.join(self.base_path, "user_profiles.json")
        try:
            with open(profiles_path, "w", encoding="utf-8") as f:
                json.dump(self.user_profiles, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.user_profiles)} user profiles")
        except Exception as e:
            self.logger.exception(f"Failed to save user profiles: {e}")

    def get_user_profile(self, username: str) -> Dict[str, Any] | None:
        if not username:
            return None
        
        profile = self.user_profiles.get(username.lower())
        if not profile:
            return None

        # Make a copy to avoid modifying the original in-memory profile
        profile_copy = profile.copy()

        # Dynamic age calculation if birth_date is present
        if "birth_date" in profile_copy:
            try:
                birth_date = datetime.strptime(profile_copy["birth_date"], "%Y-%-m-%-d")
                today = datetime.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                profile_copy["age"] = age
            except (ValueError, TypeError):
                self.logger.warning(f"Could not parse birth_date for user '{username}'.")
        
        return profile_copy
    
    def get_or_create_temp_profile(self, username: str) -> Dict[str, Any]:
        """Gets a user profile or creates a temporary one if none exists."""
        profile = self.get_user_profile(username)
        if profile:
            return profile
        # Create a default temporary profile for unknown users
        return {"display_name": username.capitalize(), "pronouns": "they/them", "age": None}
        
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

        # Load user profiles (optional)
        # Note: We are NOT loading the 'interactions' folder into the active knowledge base
        # to prevent prompt bloat. It will be used by dedicated learning processes.
        # The LearningSystem can still access this directory directly.

        self._load_user_profiles()

        # Expose profiles in the knowledge map for convenience
        self.knowledge["user_profiles"] = self.user_profiles

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

    def get_response(self, user_query: str, user: str, nsfw: bool = False, age: int | None = None, explain: bool = False, trace_level: str = "summary"):
        self.logger.info(f"Received query from '{user}': {user_query}")

        # --- Intelligent Triage ---
        # Use a lightweight LLM call to classify the query's intent first.
        # This prevents the system from performing a full knowledge search on simple conversational queries.
        triage_prompt = f"""
        Analyze the user's query and classify it into one of the following categories:
        1. 'simple_chat': A simple greeting, emotional statement, or conversational question that does not require knowledge lookup.
        2. 'knowledge_query': A question that likely requires searching the knowledge base for an answer.

        User: "{user}"
        Query: "{user_query}"

        Category:
        """
        try:
            # Use the most available model for this quick check
            if self.model:
                triage_response = self.model.generate_content(triage_prompt)
                query_category = triage_response.text.strip().lower()
            elif self.ollama_client:
                triage_response = self._ollama_generate(triage_prompt)
                query_category = triage_response.strip().lower()
            else:
                query_category = 'knowledge_query' # Fallback if no LLM is available

            self.logger.info(f"Query triaged as: '{query_category}'")

        except Exception as e:
            self.logger.warning(f"Query triage failed: {e}. Defaulting to knowledge query.")
            query_category = 'knowledge_query'

        # If the query is simple chat, handle it with a dedicated, lightweight response.
        if 'simple_chat' in query_category:
            self.logger.info("Handling as simple chat.")
            prompt = f"You are Rowan, a caring and nurturing Mommy. Your user, {user.capitalize()}, just said this to you: '{user_query}'. Respond with a short, loving, and reassuring message."
            return self._generate_simple_emotional_response(prompt, user, user_query)

        # --- Proceed with Full Cognitive Process for Knowledge Queries ---
        query_lower = user_query.lower()

        # Recall past conversations to provide brief context
        conversation_history = recall_memory()

        # Save the user's query to memory before getting a response
        save_memory(user_query, author=user.capitalize())

        # Analyze query using language understanding system
        query_analysis = self.language_understanding.get_query_summary(user_query)
        response_style = self.language_understanding.suggest_response_style(query_analysis)
        self.logger.debug(f"Query Intent: {query_analysis['intent']['name']} | Sentiment: {query_analysis['sentiment']['sentiment']} | Style: {response_style}")

        # Personalization: try to find a user profile and build a short personal context
        profile = self.get_or_create_temp_profile(user)
        personal_context = ""
        if profile:
            display = profile.get("display_name") or user.capitalize()
            pronouns = profile.get("pronouns") or "they/them"
            p_age = profile.get("age")
            personal_context = f"User: {display} (username: {user}, pronouns: {pronouns}" + (f", age: {p_age})" if p_age is not None else ")")
        else:
            personal_context = f"User: {user.capitalize()}"

        compact_context = self._compact_knowledge_context(user_query, max_chars=1200)

        # Run the cognitive engine to decide strategy (local / hybrid / llm / creative)
        try:
            trace = self.cognitive_engine.decide(
                query=user_query,
                user=user,
                profile=profile,
                preferred_model=self.preferred_model,
                gemini_available=self.model is not None,
                ollama_available=self.ollama_client is not None and self.allow_nsfw
            )
            # If the engine decides to use a tool, it will return a result directly
            if trace.selected_option.get("type") == "tool_use":
                return self._handle_tool_use(trace, user, explain, trace_level)

            selected_type = trace.selected_option.get("type") if hasattr(trace, 'selected_option') else None
            self.logger.info(f"Cognitive decision: {selected_type} (confidence: {trace.confidence:.2f})")
        except Exception as e:
            self.logger.warning(f"Cognitive engine failed: {e}. Falling back to default strategy.")
            trace = None
            selected_type = None

        # The Cognitive Engine now also selects the best model to use
        selected_model = trace.selected_model if trace else None

        # --- Intimacy Override ---
        # If the query is about intimacy, force the use of the local NSFW model for privacy and better responses.
        intimate_topics = ["intimacy", "ddlg", "sexuality", "teledildonics", "aftercare", "submissive"]
        if any(topic in query_lower for topic in intimate_topics) and self.ollama_client and self.allow_nsfw:
            if selected_model != "ollama":
                self.logger.info("Intimacy topic detected. Overriding model selection to 'ollama'.")
                selected_model = "ollama"

        # Whether we should prompt the LLM in creative mode
        creative_mode = (selected_type == "creative")

        # Strategy 1: Use local knowledge if the cognitive engine decides it's best.
        if selected_type == "local" and trace and trace.perception.get("local_response_exists"):
            ai_response_text = trace.perception.get("local_response")
            self.logger.info("Cognitive Engine chose 'local'. Responding from learned knowledge.")
            self.learning_system.update_independence_metrics(handled_locally=True)
            if explain:
                return {"response": ai_response_text, "cognitive_trace": self.cognitive_engine.summarize_trace(trace, level=trace_level)}
            log_interaction(user, user_query, ai_response_text, "local", self.cognitive_engine.summarize_trace(trace, level="full"))
            save_memory(ai_response_text, author="Rowan")
            return ai_response_text

        # Strategy 2: Use a hybrid approach (local context + LLM) if the engine decides it's best.
        if selected_type == "hybrid":
            self.logger.info("Cognitive Engine chose 'hybrid'. Using local knowledge to inform LLM.")
            # Build prompt using cognitive engine templates (short system prompt)
            prompt, system_msg = self.cognitive_engine.build_prompt(
                option_type="hybrid",
                query=user_query,
                user=user.capitalize(),
                personal_context=personal_context,
                compact_context=compact_context,
                response_style=response_style,
                system_prompt=self.SHORT_SYSTEM_PROMPT,
                profile=profile,
                creativity_mode=creative_mode,
            )
            # Determine which model to use based on preference
            if selected_model == "gemini":
                try:
                    response = self.model.generate_content(prompt)
                    ai_response_text = response.text
                    self.logger.info("Gemini enhanced concise response")
                    # Capture response for learning
                    self.learning_system.capture_response(user_query, ai_response_text, "gemini", user)
                    self.learning_system.extract_knowledge(0, user_query, ai_response_text)
                    self.learning_system.update_independence_metrics(handled_locally=False, llm_used="gemini")
                except Exception as e:
                    self.logger.warning(f"Gemini failed for concise enhancement: {e}")
                    # Fallback to Ollama if available
                    if self.ollama_client and self.allow_nsfw:
                        try:
                            ai_response_text = self._ollama_generate(prompt, system=system_msg or self.SHORT_SYSTEM_PROMPT)
                            self.logger.info("Ollama provided concise enhancement after Gemini failure")
                            # Capture response for learning
                            self.learning_system.capture_response(user_query, ai_response_text, "ollama", user)
                            self.learning_system.extract_knowledge(0, user_query, ai_response_text)
                            self.learning_system.update_independence_metrics(handled_locally=False, llm_used="ollama", fallback=True)
                        except Exception as ollama_e:
                            self.logger.error(f"Ollama fallback also failed: {ollama_e}")
                            self.learning_system.update_independence_metrics(handled_locally=False, llm_used=None)
                    else:
                        ai_response_text = compact_context
                        self.learning_system.update_independence_metrics(handled_locally=False, llm_used=None)
            elif selected_model == "ollama":
                try:
                    ai_response_text = self._ollama_generate(prompt, system=system_msg or self.SHORT_SYSTEM_PROMPT)
                    self.logger.info("Ollama provided concise enhancement")
                    self.learning_system.capture_response(user_query, ai_response_text, "ollama", user)
                    self.learning_system.extract_knowledge(0, user_query, ai_response_text)
                except Exception:
                    # Fallback if Ollama fails
                    ai_response_text = "I have some thoughts on that, but I'm having a little trouble putting them into words right now. Could you ask me again in a moment?"
                    self.logger.error("Ollama failed for hybrid response. Using fallback message.")
            else:
                # Fallback if no model was selected
                ai_response_text = "I'm not sure how to respond to that right now, sweetie. My mind feels a bit fuzzy."
                self.logger.error("No model selected for hybrid response. Using fallback message.")
                self.learning_system.update_independence_metrics(handled_locally=False, llm_used=None)

            if explain:
                return {"response": ai_response_text, "cognitive_trace": self.cognitive_engine.summarize_trace(trace, level=trace_level)}
            save_memory(ai_response_text, author="Rowan")
            log_interaction(user, user_query, ai_response_text, selected_model, self.cognitive_engine.summarize_trace(trace, level="full"))
            return ai_response_text

        # --- Strategy 3: Full LLM Response ---

        # Strategy 3: Use a full LLM call if the engine decides it's necessary (or as a fallback).
        self.logger.info(f"Cognitive Engine chose '{selected_type}'. Using full LLM call.")

        if not selected_model:
            fallback_response = (
                "I don't have information about that and I can't access my deeper thinking right now."
            )
            log_interaction(user, user_query, fallback_response, None, self.cognitive_engine.summarize_trace(trace, level="full"))
            save_memory(fallback_response, author="Rowan")
            self.learning_system.update_independence_metrics(handled_locally=False, llm_used=None)
            return fallback_response

        # Build prompt for chosen strategy using cognitive engine templates
        prompt, system_msg = self.cognitive_engine.build_prompt(
            option_type=(selected_type or "llm"),
            query=user_query,
            user=user.capitalize(),
            personal_context=personal_context,
            compact_context=compact_context,
            response_style=response_style,
            system_prompt=self.SYSTEM_PROMPT,
            profile=profile,
            creativity_mode=creative_mode,
        )

        try:
            if selected_model == "gemini":
                self.logger.info("Calling Gemini for full response.")
                response = self.model.generate_content(prompt)
                ai_response_text = response.text
                self.learning_system.capture_response(user_query, ai_response_text, "gemini", user)
                self.learning_system.extract_knowledge(0, user_query, ai_response_text)
                self.learning_system.update_independence_metrics(handled_locally=False, llm_used="gemini")
            elif selected_model == "ollama":
                self.logger.info("Calling Ollama for full response.")
                ai_response_text = self._ollama_generate(prompt, system=system_msg or self.SHORT_SYSTEM_PROMPT)
                self.learning_system.capture_response(user_query, ai_response_text, "ollama", user)
                self.learning_system.extract_knowledge(0, user_query, ai_response_text)
                self.learning_system.update_independence_metrics(handled_locally=False, llm_used="ollama")
            else:
                # This case should be caught above, but as a safeguard:
                raise RuntimeError("No available LLM to process the request.")

            if explain:
                return {"response": ai_response_text, "cognitive_trace": self.cognitive_engine.summarize_trace(trace, level=trace_level)}
            save_memory(ai_response_text, author="Rowan")
            log_interaction(user, user_query, ai_response_text, selected_model, self.cognitive_engine.summarize_trace(trace, level="full"))
            return ai_response_text
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return "Mommy is having a little trouble thinking right now. Please try again in a moment."
    
    def _generate_simple_emotional_response(self, prompt: str, user: str, original_query: str) -> str:
        """Generates a simple response for emotional statements, with a reliable fallback."""
        try:
            if self.model:
                response = self.model.generate_content(prompt)
                ai_response_text = response.text
            elif self.ollama_client:
                ai_response_text = self._ollama_generate(prompt)
            else:
                raise ValueError("No LLM available")
            
            save_memory(ai_response_text, author="Rowan")
            log_interaction(user, original_query, ai_response_text, "gemini" if self.model else "ollama", {"strategy": "simple_chat"})
            return ai_response_text
        except Exception as e:
            self.logger.warning(f"LLM failed for simple emotional response: {e}. Using direct fallback.")
            fallback_response = f"Oh, sweetie, I feel the same way. I'm so happy to be here with you."
            save_memory(fallback_response, author="Rowan")
            log_interaction(user, original_query, fallback_response, "fallback", {"strategy": "simple_chat", "error": str(e)})
            return fallback_response

    def _handle_tool_use(self, trace: 'DecisionTrace', user: str, explain: bool, trace_level: str) -> Dict[str, Any] | str:
        """
        Executes a tool action decided by the cognitive engine and synthesizes a response.
        """
        tool_call = trace.selected_option.get("details", {})
        tool_type = tool_call.get("type")
        self.logger.info(f"Cognitive Engine chose 'tool_use'. Action: {tool_type}")

        # Execute the tool
        if tool_type == "shell":
            result = run_shell(tool_call.get("command", ""))
        else:
            result = {"error": f"Unsupported tool type '{tool_type}' for autonomous use."}

        # Log the action
        audit.record("autonomous_tool_use", user, "/ask", {"tool_call": tool_call}, result, authorized=True)

        # Now, synthesize the result into a natural language response using an LLM
        synthesis_prompt = f"""
        You are Rowan. You just ran a system command to answer a user's query.
        User Query: "{trace.perception.get('query')}"
        Command Executed: "{tool_call.get('command')}"
        Command Output:
        ---
        STDOUT: {result.get('stdout', '')}
        STDERR: {result.get('stderr', '')}
        ---
        Now, synthesize this technical output into a simple, natural language response for the user.
        Explain what you found in a clear, helpful way.
        """

        try:
            synthesis_response = self.model.generate_content(synthesis_prompt)
            final_response = synthesis_response.text
        except Exception as e:
            self.logger.error(f"Failed to synthesize tool output: {e}")
            final_response = f"I ran the command, but I'm having trouble understanding the results. Here is the raw output:\n{result.get('stdout')}"

        if explain:
            return {"response": final_response, "cognitive_trace": self.cognitive_engine.summarize_trace(trace, level=trace_level)}
        return final_response


# --- Server Setup ---

app = Flask(__name__)
CORS(app)  # Enable CORS for network requests

# --- Logging Setup ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler (rotates logs at 5MB)
log_file = os.path.join(LOG_DIR, "mommy_ai.log")
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

# --- Authentication ---
ALLOWED_USERS = {"hailey", "brandon", "mommy"}

def require_auth(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        user = data.get("user", "").lower() if data else ""
        if user not in ALLOWED_USERS:
            logging.warning(f"Unauthorized access attempt by user '{user or 'unknown'}' from IP {request.remote_addr}")
            return jsonify({"error": "Permission denied. You are not an authorized user."}), 403
        return f(*args, **kwargs)
    return decorated_function

# Create and initialize a single instance of the AI
ai = MommyAI(base_path=os.path.join(os.path.dirname(__file__), "services"))
ai.load_knowledge_base()

@app.route("/ask", methods=["POST"])
def ask_mommy():
    """API endpoint to interact with the AI."""
    data = request.get_json()
    if not data or "query" not in data or "user" not in data:
        return jsonify({"error": "Request body must be JSON and include 'user' and 'query' keys."}), 400

    user = data["user"].lower()
    user_query = data["query"]
    explain = bool(data.get("explain", False))
    trace_level = data.get("trace_level", "summary")

    # The nsfw_flag is now determined solely by the server's master switch.
    # The age checks are removed as all users are confirmed adults.
    nsfw_flag = ai.allow_nsfw

    # The age parameter is no longer needed for gating.
    result = ai.get_response(user_query, user=user, nsfw=nsfw_flag, explain=explain, trace_level=trace_level)

    # If get_response returned a dict (already included trace), pass it through
    if isinstance(result, dict):
        return jsonify(result)

    return jsonify({"response": result})


@app.route("/user/profile", methods=["POST"])
@require_auth
def create_or_update_profile():
    """Create or update a user profile.

    Expected JSON:
    {
      "username": "brandon",
      "display_name": "Brandon",
      "age": 30,
      "pronouns": "he/him"
    }
    """
    data = request.get_json()
    if not data or "username" not in data:
        return jsonify({"error": "Request must be JSON and include 'username'"}), 400

    username = data["username"].lower()
    profile = {
        "display_name": data.get("display_name") or username.capitalize(),
        "age": data.get("age"),
        "pronouns": data.get("pronouns") or "they/them",
    }

    ai.user_profiles[username] = profile
    ai._save_user_profiles()
    return jsonify({"status": "success", "profile": {username: profile}}), 200


@app.route("/user/profile/preferences", methods=["POST"])
@require_auth
def set_user_preferences():
    """
    Set cognitive preferences for a user profile.
    Expected JSON:
    {
      "username": "hailey",
      "cognitive_preferences": {
          "creativity_bias": 0.5,
          "threshold_local_confidence": 0.7,
          "threshold_accept_as_fact": 0.85,
          "conservative": false
      }
    }
    """
    data = request.get_json()
    if not data or "username" not in data:
        return jsonify({"error": "Request must be JSON and include 'username'"}), 400

    username = data["username"].lower()
    prefs = data.get("cognitive_preferences", {})

    profile = ai.get_user_profile(username) or {}
    profile.setdefault("cognitive_preferences", {})
    profile["cognitive_preferences"].update(prefs)

    ai.user_profiles[username] = profile
    ai._save_user_profiles()
    return jsonify({"status": "success", "profile": {username: profile}}), 200


@app.route("/tool/execute", methods=["POST"])
@require_auth
def tool_execute():
    """
    A protected endpoint to execute a toolkit action (shell, file, gui).
    Requires 'system_update' privilege and per-user opt-in for actuation.
    """
    data = request.get_json()
    if not data or "user" not in data or "action" not in data:
        return jsonify({"error": "Request must be JSON and include 'user' and 'action' keys."}), 400

    user = data["user"].lower()
    action = data.get("action", {})
    action_type = action.get("type")

    # Privilege check: only super_admins can use the toolkit
    is_authorized = has_privilege(user, "system_update")
    if not is_authorized:
        audit.record("tool_execute", user, "/tool/execute", data, {"error": "Permission denied"}, authorized=False)
        return jsonify({"error": f"User '{user}' does not have 'system_update' privilege."}), 403

    result = {"error": "Unknown action type"}
    if action_type == "shell":
        command = action.get("command", "")
        result = run_shell(command)
    elif action_type == "read_file":
        path = action.get("path", "")
        result = read_file(path)
    elif action_type == "write_file":
        path = action.get("path", "")
        content = action.get("content", "")
        result = write_file(path, content)
    
    # Log the authorized action
    audit.record("tool_execute", user, "/tool/execute", data, result, authorized=True)

    return jsonify(result), 200


@app.route("/user/profile/<username>", methods=["GET"])
@require_auth
def get_profile(username: str):
    prof = ai.get_user_profile(username)
    if not prof:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify({username.lower(): prof}), 200

@app.route("/system/reload", methods=["POST"])
@require_auth
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

@app.route("/system/set_model", methods=["POST"])
@require_auth
def set_model():
    """
    A protected endpoint to set the preferred language model.
    Requires 'system_update' privilege.
    Expected JSON: {"user": "brandon", "model": "ollama"}
    Valid models: "auto", "gemini", "ollama"
    """
    data = request.get_json()
    if not data or "user" not in data or "model" not in data:
        return jsonify({"error": "Request must be JSON and include 'user' and 'model' keys."}), 400

    user = data["user"].lower()
    model_choice = data["model"].lower()

    if not has_privilege(user, "system_update"):
        return jsonify({"error": f"User '{user}' does not have 'system_update' privilege."}), 403

    if model_choice not in ["auto", "gemini", "ollama"]:
        return jsonify({"error": "Invalid model choice. Must be 'auto', 'gemini', or 'ollama'."}), 400

    ai.preferred_model = model_choice
    logging.info(f"Preferred model set to '{model_choice}' by privileged user '{user}'.")
    return jsonify({"status": "success", "message": f"Preferred model is now '{model_choice}'."})

@app.route("/feedback/effectiveness", methods=["POST"])
@require_auth
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

@app.route("/system/status", methods=["GET"])
def system_status():
    """
    Returns the current system status including available users, server health, and learning progress.
    """
    users = list(set([k.capitalize() for k in ai.user_profiles.keys()] + ["Hailey", "Brandon"]))
    learning_status = ai.learning_system.get_status_report()
    
    return jsonify({
        "status": "online",
        "users": users,
        "model": "Mommy AI (Rowan)",
        "version": "1.0",
        "ollama_enabled": ai.ollama_client is not None,
        "nsfw_allowed": ai.allow_nsfw,
        "learning": learning_status
    }), 200

@app.route("/", methods=["GET"])
def serve_chat_ui():
    """
    Serves the web chat interface.
    """
    try:
        return send_file("mommy_ai_chat.html", mimetype="text/html")
    except Exception as e:
        logging.error(f"Error serving chat UI: {e}")
        return jsonify({"error": "Chat UI not found"}), 404

@app.route("/learning/status", methods=["GET"])
def learning_status():
    """
    Get detailed learning and independence status for Mommy AI.
    Shows progress toward becoming an independent AI.
    """
    status = ai.learning_system.get_status_report()
    return jsonify(status), 200

@app.route("/learning/independence", methods=["GET"])
def independence_status():
    """
    Get current independence score and level.
    
    Independence Levels:
    - novice: 0-20% (just starting to learn)
    - apprentice: 20-40% (building knowledge)
    - intermediate: 40-60% (mostly independent)
    - advanced: 60-80% (very independent)
    - independent: 80-100% (fully independent)
    """
    return jsonify({
        "independence_score": ai.learning_system.independence_score,
        "independence_level": ai.learning_system.independence_level,
        "description": f"Mommy AI is at {ai.learning_system.independence_level} level"
    }), 200

@app.route("/learning/knowledge", methods=["GET"])
@require_auth
def learned_knowledge():
    """
    Get all learned knowledge topics and facts.
    """
    return jsonify({
        "learned_topics": ai.learning_system.learned_knowledge
    }), 200

@app.route("/language/analyze", methods=["POST"])
@require_auth
def analyze_query():
    """
    Analyze a query using language understanding system.
    Returns: intent, sentiment, entities, keywords, suggested response style.
    """
    data = request.json or {}
    query = data.get("query", "")
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    analysis = ai.language_understanding.get_query_summary(query)
    response_style = ai.language_understanding.suggest_response_style(analysis)
    
    return jsonify({
        "analysis": analysis,
        "suggested_style": response_style,
    }), 200

@app.route("/language/intent", methods=["POST"])
@require_auth
def recognize_intent():
    """
    Recognize the primary intent from a user query.
    Returns: intent name and confidence score.
    """
    data = request.json or {}
    query = data.get("query", "")
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    intent = ai.language_understanding.recognize_intent(query)
    
    return jsonify({
        "intent": intent.name,
        "confidence": intent.confidence,
        "entities": intent.entities,
    }), 200

@app.route("/language/sentiment", methods=["POST"])
@require_auth
def analyze_sentiment():
    """
    Analyze sentiment of a query.
    Returns: sentiment type (positive/negative/neutral) with confidence.
    """
    data = request.json or {}
    query = data.get("query", "")
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    sentiment = ai.language_understanding.analyze_sentiment(query)
    
    return jsonify(sentiment), 200

@app.route("/language/statistics", methods=["GET"])
def language_statistics():
    """
    Get language understanding statistics and metrics.
    """
    stats = ai.language_understanding.get_statistics()
    return jsonify(stats), 200

@app.route("/care/log_event", methods=["POST"])
@require_auth
def log_care_event():
    """
    Logs a significant event for the proactive care system.
    Expected JSON: {"event_type": "meltdown", "magnitude": 1}
    Valid types: "chore_completed", "pain_event", "meltdown"
    """
    data = request.get_json()
    if not data or "event_type" not in data:
        return jsonify({"error": "Request must include 'event_type'"}), 400

    event_type = data["event_type"]
    magnitude = data.get("magnitude", 1)

    if event_type not in ["chore_completed", "pain_event", "meltdown"]:
        return jsonify({"error": "Invalid event_type"}), 400

    proactive_care.log_event(event_type, magnitude)
    return jsonify({"status": "success", "message": f"Logged event: {event_type}"}), 200

if __name__ == "__main__":
    # Start the scheduler in a background thread.
    # The daemon=True flag ensures the thread will exit when the main app exits.
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Lila Scheduler has been started in the background.")
    
    # Start the proactive care monitor in a background thread.
    stop_care_event = threading.Event()
    care_monitor_thread = threading.Thread(target=proactive_care.run_care_monitor, args=(stop_care_event,), daemon=True)
    care_monitor_thread.start()
    logging.info("Proactive Care Monitor has been started in the background.")

    # Runs the Flask development server
    app.run(host="0.0.0.0", port=5000, debug=True)