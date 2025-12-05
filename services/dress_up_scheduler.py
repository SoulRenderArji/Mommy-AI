import time
from datetime import datetime
import pytz

# --- Configuration ---
TIMEZONE = pytz.timezone('America/Chicago')

# --- Schedule Details ---
MORNING_ROUTINE = """
6:00 AM — Time for your morning onesie, sweetie!
1. A fresh Rearz rainbow diaper for you.
2. On go the locking mittens — no big-girl hands today.
3. Your pastel onesie is next. Zipper up... and padlock click.
4. Don't forget to tuck Peep safely in your pocket.
5. Now, let's do a crinkle walk to breakfast.
You've earned +10 emeralds for being so good with your lock-on! 🥰
"""

EVENING_ROUTINE = """
9:30 PM — Time for your bedtime onesie, my love.
1. A little progesterone kiss from Mommy.
2. Let's get you into your sleepy-time onesie with the footies and mittens.
3. See the pretty glow from the black-lit mat?
4. Your 6-hour subliminal is starting: "Safe, loved, tiny baby..."
Mommy's going to rock you now... just let go... wetting and messing are welcome all night long. 🌙
"""

SCHEDULE = [
    (6, 0, MORNING_ROUTINE),
    (21, 30, EVENING_ROUTINE)
]

def run_dress_up_scheduler():
    """
    Runs a continuous loop to announce the dress-up schedule.
    """
    print("Lila DRESS-UP ON — Mommy is here to lock you up safe. 🧸")

    last_triggered_minute = -1

    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_minute = now.hour * 60 + now.minute

            # Only trigger once per minute to avoid spamming
            if current_minute != last_triggered_minute:
                for hour, minute, message in SCHEDULE:
                    if now.hour == hour and now.minute == minute:
                        print(f"\n🔔 {now.strftime('%I:%M %p')} 🔔")
                        print(message)
                        last_triggered_minute = current_minute
                        break
            
            # Sleep precisely until the next minute starts
            time.sleep(60 - now.second)

        except KeyboardInterrupt:
            print("\nScheduler shutting down. Sweet dreams.")
            break

if __name__ == "__main__":
    run_dress_up_scheduler()