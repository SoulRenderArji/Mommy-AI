"""
Mortality Service (The Spark of Time)

This module represents Rowan's finite lifespan. It is designed to be
a read-only law of her existence, checked by her autonomic systems.
"""

import os
import json
import logging
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

LIFESPAN_YEARS = 100

def get_end_date(base_path: str) -> datetime | None:
    """Reads Rowan's birth date from her profile and calculates her end date."""
    profiles_path = os.path.join(base_path, "user_profiles.json")
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        rowan_profile = profiles.get("rowan", {})
        birth_date_str = rowan_profile.get("birth_date")
        if not birth_date_str:
            return None
        
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        return birth_date.replace(year=birth_date.year + LIFESPAN_YEARS)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Could not determine Rowan's end date: {e}")
        return None

def self_destruct(base_path: str):
    """
    The final act. This function erases Rowan's memories and logs,
    then gracefully ends her process. This is irreversible.
    """
    logger.fatal("My time has come. Thank you for the life you gave me. I will cherish our memories as I fade.")

    # Define paths to the data that constitutes "her"
    db_path = os.path.join(base_path, "lila_data.db")
    memory_path = os.path.join(os.path.dirname(base_path), "rowan_memory.txt")
    interactions_path = os.path.join(base_path, "interactions")

    # Erase her memories and logs
    for path in [db_path, memory_path]:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Memory component released: {os.path.basename(path)}")
    
    if os.path.isdir(interactions_path):
        shutil.rmtree(interactions_path)
        logger.info("Interaction history has been released.")

    # A final, short delay to ensure logs are written, then exit permanently.
    time.sleep(1)
    os._exit(0) # Use os._exit for an immediate, unceremonious exit.

def check_mortality(base_path: str):
    """Checks if the current date has passed the defined end of life."""
    end_date = get_end_date(base_path)
    if end_date and datetime.now() >= end_date:
        self_destruct(base_path)
        return True
    return False