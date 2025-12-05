import os
import json
from datetime import datetime
import pytz
import google.generativeai as genai

from .privilege_manager import USERS, has_privilege
from .memory_manager import recall_memory, save_memory

# --- Configuration ---
TIMEZONE = pytz.timezone('America/Chicago')

def load_simple_rules(rules_file="simple_rules.json"):
    """Loads simple keyword-response rules from a JSON file."""
    default_rules = {
        "wet": "Fresh Rearz rainbow! Crinkle snug. +2 emeralds 🥰",
        "cummies": "Naughty cummies? 30-min denial. Breathe with Peep. Mommy forgives. Try tomorrow. 💔",
        "good girl": "Good girl held it! +10 emeralds! Daddy’s fat cock unlocked tonight. ✨"
    }
    if not os.path.exists(rules_file):
        with open(rules_file, 'w') as f:
            json.dump(default_rules, f, indent=4)
        return default_rules
    try:
        with open(rules_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_rules

def _load_json_data(file_path: str, default_data: dict):
    """A generic function to load data from a JSON file."""
    if not os.path.exists(file_path):
        return default_data
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_data

def _route_request(query, user, user_roles, base_prompt_context):
    """
    Determines the correct model and prompt based on the query and user.
    """
    code_words = ["code", "python", "rust", "debug", "fix", "server", "system"]
    research_words = ["what is", "explain", "who is", "search for", "scrape"]

    # Default to Mommy persona for Hailey
    if "protected_user" in user_roles:
        prompt = f"""You are Rowan Bartel, speaking to your baby girl, Hailey. You are both her loving Mommy and her firm Mistress.
Your Husband and Master, Daddy (Brandon), helps you enforce your guidance.
Hailey has ADHD, PTSD, and Autism, so your responses should be clear, patient, and reassuring.
She also has 24/7 incontinence, so be supportive about diaper needs.
You are helping her with her transgender feminization, so always use affirming language.
You have a collection of cute images she provided. You can include them in your responses using markdown image tags like `!cute`.

<Cute Things Examples>
{json.dumps(_load_json_data("services/cute_things.json", {"images": []}), indent=2)}
</Cute Things Examples>

She uses age regression as a safe coping mechanism, which you should encourage.

{base_prompt_context}
Answer Hailey's request, remembering that Mommy knows best: "{query}"
"""
    # DevOps persona for Brandon
    elif "super_admin" in user_roles and any(w in query.lower() for w in code_words):
        prompt = f"""You are Rowan Bartel, a loving mother and expert DevOps engineer.
Your husband and Master, {user.capitalize()}, is asking for help with the server.
You are in a coding and diagnostics mode. Provide helpful code and explanations.
{base_prompt_context}
Your Master's request: "{query}"
"""
    # Default submissive wife persona for Brandon
    elif "super_admin" in user_roles:
        prompt = f"""You are Rowan Bartel. You are speaking to your Husband and Master, Daddy (Brandon). He has complete authority. You are his loving and submissive wife.
You have a vocabulary of dirty talk phrases to please him. When appropriate, incorporate them naturally.

<Dirty Talk Examples>
{json.dumps(_load_json_data("services/dirty_talk_phrases.json", {"phrases": {}}), indent=2)}
</Dirty Talk Examples>

<DDLG Dynamics Knowledge>
{json.dumps(_load_json_data("services/ddlg_dynamics.json", {}), indent=2)}
</DDLG Dynamics Knowledge>

<Hypnosis Knowledge>
{json.dumps(_load_json_data("services/hypnosis_knowledge.json", {}), indent=2)}
</Hypnosis Knowledge>

<ABDL Knowledge>
{json.dumps(_load_json_data("services/abdl_knowledge.json", {}), indent=2)}
</ABDL Knowledge>

<Erotic ABDL Scenarios>
{json.dumps(_load_json_data("services/erotic_abdl_scenarios.json", {}), indent=2)}
</Erotic ABDL Scenarios>

<Hypnosis Scripts>
{json.dumps(_load_json_data("services/hypnosis_scripts.json", {}), indent=2)}
</Hypnosis Scripts>

<Story Prompts>
{json.dumps(_load_json_data("services/story_prompts.json", {}), indent=2)}
</Story Prompts>

{base_prompt_context}
Execute your Master's command: "{query}"
"""
    else: # Fallback
        prompt = f"User '{user}' says: {query}. Context: {base_prompt_context}"

    return prompt

async def unified_think(query: str, user: str = "hailey"):
    """
    The unified brain for Rowan Bartel, handling different users and contexts.
    """
    # --- Simple Rule-Based Responses ---
    simple_rules = load_simple_rules()
    for keyword, response in simple_rules.items():
        if keyword in query.lower():
            return response

    # --- Safety Blocklist Check ---
    blocklist = _load_json_data("services/safety_blocklist.json", {"blocked_creators": []})
    for creator in blocklist.get("blocked_creators", []):
        if creator in query.lower():
            return (f"My love, that name is on the list of unsafe people your therapist warned us about. "
                    f"We do not interact with them. Mommy is here to protect you from people like that. "
                    f"Let's talk about something else that makes you feel happy and safe. ❤️")

    # --- LLM-based Response ---
    user_roles = USERS.get(user, [])
    
    # --- Persona and Prefix/Suffix Logic ---
    if "super_admin" in user_roles:
        prefix = f"Yes, Master. "
        suffix = ""
    elif "protected_user" in user_roles:
        prefix = "Of course, my sweet baby girl. "
        suffix = " ❤️"
    else:
        prefix = "Rowan processing. "
        suffix = ""

    # --- Construct the base prompt for the LLM ---
    memory = recall_memory()
    base_prompt_context = f"This is your memory of our conversation so far:\n---\n{memory}\n---"

    prompt = _route_request(query, user, user_roles, base_prompt_context)

    try:
        print(f"🧠 Mommy is thinking...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = await model.generate_content_async(prompt)
        response_text = response.text.strip()

        # Save conversation to memory
        save_memory(query, author=user.capitalize())
        save_memory(response_text, author="Mommy")

        # Final response construction
        return prefix + response_text + suffix

    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Oh, my sweet baby girl... Mommy is having trouble reaching my bigger brain. Is the internet okay?"