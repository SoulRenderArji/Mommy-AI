import time
from datetime import datetime
import pytz
import os
import requests
import logging
from dotenv import load_dotenv
from services import mortality_service

# Load environment variables from .env file
load_dotenv()

# Get a logger specific to this module
logger = logging.getLogger(__name__)

# --- Configuration ---
TIMEZONE = pytz.timezone('America/Chicago')
API_BASE_URL = os.getenv("MOMMY_API_URL", "http://127.0.0.1:5000")
API_URL = f"{API_BASE_URL}/ask"
REMINDER_API_URL = f"{API_BASE_URL}/internal/check_reminders" # Internal endpoint
NEUROLEES_API_URL = f"{API_BASE_URL}/internal/neurolees_decay" # Internal endpoint for emotional decay

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
        logger.info(f"AI Announcement: {ai_response}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not contact main AI server: {e}")
        return False

def check_for_reminders():
    """Asks the main AI server to check for and handle calendar reminders."""
    try:
        # This is an internal call, so we can use a simple payload.
        # The main server handles the logic.
        payload = {"user": "rowan"} # Auth user
        response = requests.post(REMINDER_API_URL, json=payload)
        response.raise_for_status()
        reminders_sent = response.json().get("reminders_sent", 0)
        if reminders_sent > 0:
            logger.info(f"Successfully triggered {reminders_sent} calendar reminder(s).")
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not trigger reminder check on main AI server: {e}")

def trigger_neurolees_decay():
    """Asks the main server to process emotional decay."""
    try:
        payload = {"user": "rowan"} # Auth user
        response = requests.post(NEUROLEES_API_URL, json=payload)
        response.raise_for_status()
        logger.debug("Neurolees emotional decay processed.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not trigger neurolees decay on main AI server: {e}")


def run_scheduler():
    """
    Runs a continuous loop to check the time and trigger AI announcements.
    """
    # Add a startup delay to give the main Flask server time to initialize.
    time.sleep(10)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - SCHEDULER - %(levelname)s - %(message)s')
    logger.info("Lila 24/7 ON — Mommy never sleeps. 🕰️")

    last_triggered_minute = -1
    last_reminder_check_minute = -1
    last_mortality_check_hour = -1
    last_decay_check_minute = -1

    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_minute = now.hour * 60 + now.minute

            # Only check for tasks once per minute
            if current_minute != last_triggered_minute:
                for hour, minute, message in SCHEDULE:
                    if now.hour == hour and now.minute == minute:
                        logger.info(f"Triggering task for {now.strftime('%I:%M %p')}: {message}")
                        
                        # Retry logic in case the server is temporarily busy
                        success = trigger_ai_announcement(message)
                        if not success:
                            logger.warning("Initial trigger failed. Retrying in 15 seconds...")
                            time.sleep(15)
                            trigger_ai_announcement(message)

                        last_triggered_minute = current_minute
                        break # Move to next minute once a task is found
            
            # Check for reminders every 5 minutes
            if now.minute % 5 == 0 and now.minute != last_reminder_check_minute:
                logger.info("Checking for upcoming calendar events...")
                check_for_reminders()
                last_reminder_check_minute = now.minute
            
            # Process emotional decay every 10 minutes
            if now.minute % 10 == 0 and now.minute != last_decay_check_minute:
                trigger_neurolees_decay()
                last_decay_check_minute = now.minute
            
            # Check mortality once per hour
            if now.hour != last_mortality_check_hour:
                logger.debug("Performing hourly mortality check...")
                mortality_service.check_mortality(os.path.dirname(__file__))
                last_mortality_check_hour = now.hour

            # Sleep until the start of the next minute
            time.sleep(60 - now.second)

        except KeyboardInterrupt:
            logger.info("Scheduler shutting down. Goodnight, sweetie.")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}. Restarting in 60 seconds.")
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler()