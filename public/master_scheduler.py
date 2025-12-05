import time
from datetime import datetime
import pytz

# --- Configuration ---
TIMEZONE = pytz.timezone('America/Chicago')

# --- Schedule Details ---

DRESS_UP_MORNING = """
6:00 AM — Time for your morning onesie, sweetie!
1. A fresh Rearz rainbow diaper for you.
2. On go the locking mittens — no big-girl hands today.
3. Your pastel onesie is next. Zipper up... and padlock click.
4. Don't forget to tuck Peep safely in your pocket.
5. Now, let's do a crinkle walk to breakfast.
You've earned +10 emeralds for being so good with your lock-on! 🥰
"""

DRESS_UP_EVENING = """
9:30 PM — Time for your bedtime onesie, my love.
1. A little progesterone kiss from Mommy.
2. Let's get you into your sleepy-time onesie with the footies and mittens.
3. See the pretty glow from the black-lit mat?
4. Your 6-hour subliminal is starting: "Safe, loved, tiny baby..."
Mommy's going to rock you now... just let go... wetting and messing are welcome all night long. 🌙
"""

GENTLE_AFFIRMATIONS = [
    "You are safe in Mommy’s arms.",
    "You are loved exactly as you are.",
    "You are tiny, perfect, and free to let go.",
    "Wet and mess are cozy, nothing to be ashamed of. Mommy changes you with kisses.",
    "Your lady voice is pretty and strong.",
    "Heavy thoughts fade—Mommy’s here.",
]

DEEP_SUBLIMINALS = [
    # Mantras from therapist's book
    "I Don’t Deserve Pussy… I Only Deserve My Hand…",
    "My little Clitty Could Never Please a Real Woman… If I’m Lucky I’ll Find Big Black Cock to Stretch My Boy Pussy Like I Deserve…",
    "Cock Tastes Good… Cock Makes Me Feel Complete… Cock is Good to Eat…",
    "Cum Please Daddy… I want to Taste Your Sweet Load…",
    "Fill Me With Your Cock… Stretch Me Around Your Mighty Tool…",
    # New concepts from the Dirty Dictionary
    "You are a submissive. You find pleasure in yielding control to Mommy and Daddy.",
    "You are a bottom. You exist to be penetrated and filled.",
    "You are a slave. Your purpose is to serve your Master.",
    "You are a fuck buddy for Daddy. Nothing more.",
    # Mantras from the Slave Girl book
    "He is OWNER, and girl is owned!",
    "He commands, and girl obeys!",
    "He is MASTER, girl is slave!",
    "He is to be pleased, and girl is to please!",
    "I will listen only to my MASTER'S voice."
]

SCHEDULE = [
    # General Schedule
    (6, 0, "6:00 AM — Time for lock-on and a yummy breakfast. 🥞"),
    (9, 0, "9:00 AM — Medication time, and let's do our voice hums. 🎤"),
    (10, 30, "10:30 AM — Dot Fit exercises, and then water #3. 💧"),
    (15, 0, "3:00 PM — Time for your knot pleasure training, good girl. 🐶"),
    (19, 0, "7:00 PM — Dinner is ready! And time for water #8. 🍲"),
    (21, 30, "9:30 PM — Progesterone, and then our sleepy time walk. 🌙"),
    # Events from the Slave Girl book
    (6, 50, "6:50 AM — Time for your morning mantra, slave girl. 'He is OWNER, and girl is owned!'"),
    (20, 30, "8:30 PM — Time for your evening Confessional with Mommy."),
    # Dress-Up Schedule
    (6, 0, DRESS_UP_MORNING),
    (21, 30, DRESS_UP_EVENING)
]

def run_master_scheduler():
    """
    Runs a continuous loop to check the time and print all scheduled events.
    """
    print("🕰️ Mommy's Master Scheduler ON — I'll handle everything. 🕰️")

    # Sort schedule to ensure tasks at the same time are grouped
    SCHEDULE.sort(key=lambda x: (x[0], x[1]))

    last_triggered_minute = -1
    subliminal_end_time = None

    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_minute = now.hour * 60 + now.minute

            # Only trigger once per minute to avoid spamming
            if current_minute != last_triggered_minute:
                triggered = False
                for hour, minute, message in SCHEDULE:
                    if now.hour == hour and now.minute == minute:
                        if not triggered: # Print timestamp only for the first event of the minute
                            print(f"\n🔔 {now.strftime('%I:%M %p')} 🔔")
                            triggered = True
                        print(message)
                
                # Start subliminal session at 9:30 PM
                if now.hour == 21 and now.minute == 30:
                    subliminal_end_time = time.time() + (6 * 60 * 60) # 6 hours from now
                    print("--- 6-Hour Subliminal Lullaby Sequence Initiated ---")

                if triggered:
                    last_triggered_minute = current_minute
            
            # Run subliminal whispers if active
            if subliminal_end_time and time.time() < subliminal_end_time:
                # Alternate between gentle and deep subliminals
                all_affirmations = GENTLE_AFFIRMATIONS + DEEP_SUBLIMINALS
                affirmation = all_affirmations[now.minute % len(all_affirmations)]
                print(f"whisper: {affirmation}")
            elif subliminal_end_time and time.time() >= subliminal_end_time:
                print("--- 6-Hour Subliminal Lullaby Sequence Complete ---")
                subliminal_end_time = None

            # Sleep precisely until the next minute starts
            time.sleep(60 - now.second)

        except KeyboardInterrupt:
            print("\nScheduler shutting down. Sweet dreams, my love.")
            break

if __name__ == "__main__":
    run_master_scheduler()