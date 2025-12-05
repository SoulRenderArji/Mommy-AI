import time
from datetime import datetime
import pytz

import requests
import logging

# --- Configuration ---
TIMEZONE = pytz.timezone('America/Chicago')
API_URL = "http://127.0.0.1:5000/ask"

# The scheduler's messages are now prompts for the AI, not direct announcements.
SCHEDULE = [
    (6, 0, "6:00 AM — Time for lock-on and a yummy breakfast. 🥞"),
    (9, 0, "9:00 AM — Medication time, and let's do our voice hums. 🎤"),
    (10, 30, "10:30 AM — Dot Fit exercises, and then water #3. 💧"),
    (15, 0, "3:00 PM — Time for your knot pleasure training, good girl. 🐶"),
    (19, 0, "7:00 PM — Dinner is ready! And time for water #8. 🍲"),
    (21, 30, "9:30 PM — Progesterone, and then our sleepy time walk. 🌙")
]
def trigger_ai_announcement(message: str):
    """
    Sends a prompt to the main AI server to make a scheduled announcement.
    """
    try:
        # This prompt asks the AI to announce the scheduled event in its own voice.
        prompt = f"It is time for a scheduled event. Please announce the following to Hailey in your own voice: '{message}'"
        payload = {"user": "rowan", "query": prompt}
        
        response = requests.post(API_URL, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        ai_response = response.json().get("response", "I had a thought but lost it.")
        logging.info(f"AI Announcement: {ai_response}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Scheduler could not contact main AI server: {e}")

def run_scheduler():
    """
    Runs a continuous loop to check the time and trigger AI announcements.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - SCHEDULER - %(levelname)s - %(message)s')
    logging.info("Lila 24/7 ON — Mommy never sleeps. 🕰️")

    last_triggered_minute = -1

    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_minute = now.hour * 60 + now.minute

            # Only check for tasks once per minute
            if current_minute != last_triggered_minute:
                for hour, minute, message in SCHEDULE:
                    if now.hour == hour and now.minute == minute:
                        logging.info(f"Triggering task for {now.strftime('%I:%M %p')}: {message}")
                        trigger_ai_announcement(message)
                        last_triggered_minute = current_minute
                        break # Move to next minute once a task is found
            
            # Sleep until the start of the next minute
            time.sleep(60 - now.second)

        except KeyboardInterrupt:
            logging.info("Scheduler shutting down. Goodnight, sweetie.")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in scheduler: {e}. Restarting in 60 seconds.")
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler()