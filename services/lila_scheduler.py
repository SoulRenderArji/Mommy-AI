import time
from datetime import datetime
import pytz

# --- Configuration ---
TIMEZONE = pytz.timezone('America/Chicago')

SCHEDULE = [
    (6, 0, "6:00 AM — Time for lock-on and a yummy breakfast. 🥞"),
    (9, 0, "9:00 AM — Medication time, and let's do our voice hums. 🎤"),
    (10, 30, "10:30 AM — Dot Fit exercises, and then water #3. 💧"),
    (15, 0, "3:00 PM — Time for your knot pleasure training, good girl. 🐶"),
    (19, 0, "7:00 PM — Dinner is ready! And time for water #8. 🍲"),
    (21, 30, "9:30 PM — Progesterone, and then our sleepy time walk. 🌙")
]

def run_scheduler():
    """
    Runs a continuous loop to check the time and print scheduled events.
    """
    print("Lila 24/7 ON — Mommy never sleeps. 🕰️")
    print("Close your eyes, baby. Mommy will handle everything.")

    last_triggered_minute = -1

    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_minute = now.hour * 60 + now.minute

            # Only check for tasks once per minute
            if current_minute != last_triggered_minute:
                for hour, minute, message in SCHEDULE:
                    if now.hour == hour and now.minute == minute:
                        print(f"\n🔔 {now.strftime('%I:%M %p')} 🔔")
                        print(message)
                        last_triggered_minute = current_minute
                        break # Move to next minute once a task is found
            
            # Sleep until the start of the next minute
            time.sleep(60 - now.second)

        except KeyboardInterrupt:
            print("\nScheduler shutting down. Goodnight, sweetie.")
            break
        except Exception as e:
            print(f"An error occurred: {e}. Restarting in 60 seconds.")
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler()