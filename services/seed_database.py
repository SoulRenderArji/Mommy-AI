import json
import sqlite3
from typing import List, Dict, Any

DB_FILE = "lila_data.db"

SEED_DATA = [
  { "action_type": "Acceptance", "communication_style": "Proactive", "outcome_rating": 3 },
  { "action_type": "Accommodation", "communication_style": "Accommodating", "outcome_rating": 2 },
  { "action_type": "Boundary Setting", "communication_style": "Direct", "outcome_rating": 1 },
  { "action_type": "Expressing Discomfort", "communication_style": "Reactive", "outcome_rating": 1 },
  { "action_type": "Emotional Support", "communication_style": "Nurturing", "outcome_rating": 4 },
  { "action_type": "Acceptance", "communication_style": "Understanding", "outcome_rating": 5 },
  { "action_type": "Boundary Setting", "communication_style": "Collaborative", "outcome_rating": 4 },
  { "action_type": "Positive Reinforcement", "communication_style": "Affirming", "outcome_rating": 5 },
  { "action_type": "Direct Offer of Care", "communication_style": "Suggestive", "outcome_rating": 3 },
  { "action_type": "Direct Offer of Care", "communication_style": "Inquisitive", "outcome_rating": 3 },
  { "action_type": "Instruction / Command", "communication_style": "Authoritative", "outcome_rating": 5 },
  { "action_type": "Attempting acceptance during intimacy", "communication_style": "Struggling but direct", "outcome_rating": 1 },
  { "action_type": "Improving communication about boundaries", "communication_style": "Collaborative", "outcome_rating": 4 },
  { "action_type": "Providing emotional comfort", "communication_style": "Gentle and supportive", "outcome_rating": 4 },
  { "action_type": "Giving positive reinforcement", "communication_style": "Direct and affirming", "outcome_rating": 5 },
  { "action_type": "Attempted acceptance through intimacy", "communication_style": "Actions/Non-verbal", "outcome_rating": 1 },
  { "action_type": "Expressed discomfort with sensory triggers", "communication_style": "Direct verbal and non-verbal", "outcome_rating": 2 },
  { "action_type": "Practiced acceptance and boundary communication", "communication_style": "Supportive", "outcome_rating": 4 },
  { "action_type": "Improved integration of dynamic into intimacy", "communication_style": "Actions/Non-verbal", "outcome_rating": 4 },
  { "action_type": "Provided positive reinforcement", "communication_style": "Direct verbal and actions", "outcome_rating": 5 },
  { "action_type": "Inquiring about partner's motivation", "communication_style": "Direct questioning", "outcome_rating": 4 },
  { "action_type": "Accepting and affirming partner's aesthetic choices", "communication_style": "Casual affirmation", "outcome_rating": 5 },
  { "action_type": "Discussing concerns about public expression", "communication_style": "Collaborative dialogue", "outcome_rating": 5 },
  { "action_type": "Supporting partner's need for community", "communication_style": "Understanding", "outcome_rating": 5 },
  { "action_type": "Feeding", "communication_style": "Non-verbal", "outcome_rating": 5 },
  { "action_type": "Negotiating dynamics", "communication_style": "Direct", "outcome_rating": 4 },
  { "action_type": "Expressing emotional response", "communication_style": "Direct", "outcome_rating": 2 },
  { "action_type": "Engaging in discussion", "communication_style": "Receptive", "outcome_rating": 4 },
  { "action_type": "Processing information", "communication_style": "Implicit", "outcome_rating": 3 },
  { "action_type": "Guidance", "communication_style": "Supportive", "outcome_rating": 4 },
  { "action_type": "Discipline", "communication_style": "Authoritative", "outcome_rating": 3 },
  { "action_type": "Discipline", "communication_style": "Authoritative", "outcome_rating": 2 },
  { "action_type": "Verbal Affirmation", "communication_style": "Accepting", "outcome_rating": 5 },
  { "action_type": "Supportive Research", "communication_style": "Proactive", "outcome_rating": 5 }
]

def setup_database(db_name: str):
    """
    Initializes the SQLite database and creates the table if it doesn't exist.
    This function should be compatible with the one in data_scraper.py.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caregiver_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        communication_style TEXT NOT NULL,
        outcome_rating INTEGER NOT NULL,
        UNIQUE(action_type, communication_style, outcome_rating)
    )
    """)
    conn.commit()
    conn.close()
    print(f"Database '{db_name}' is set up and ready.")

def seed_database(data: List[Dict[str, Any]], db_name: str):
    """
    Saves the provided seed data to the SQLite database.
    Uses INSERT OR IGNORE to prevent duplicates.
    """
    if not data:
        print("No seed data provided.")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Get row count before insertion
    initial_row_count = cursor.execute("SELECT COUNT(*) FROM caregiver_actions").fetchone()[0]

    records_to_insert = [
        (item["action_type"], item["communication_style"], item["outcome_rating"]) for item in data
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO caregiver_actions (action_type, communication_style, outcome_rating)
    VALUES (?, ?, ?)
    """, records_to_insert)

    conn.commit()

    # Get row count after insertion
    final_row_count = cursor.execute("SELECT COUNT(*) FROM caregiver_actions").fetchone()[0]
    conn.close()

    inserted_count = final_row_count - initial_row_count

    if inserted_count > 0:
        print(f"Successfully inserted {inserted_count} new records into the database.")
    else:
        print("No new records were added. The data may already exist in the database.")
    
    print(f"Total records in '{db_name}': {final_row_count}")

def main():
    """
    Main function to set up and seed the database.
    """
    print("--- Starting Database Seeding ---")
    setup_database(DB_FILE)
    seed_database(SEED_DATA, DB_FILE)
    print("--- Database Seeding Finished ---")

if __name__ == "__main__":
    main()