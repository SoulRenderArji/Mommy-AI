import sys
import time

# Configuration
TOYS = ["Chance Small", "Chance Medium", "Chance Large", "Daddy’s fat cock"]
SESSION_DURATION_MINUTES = 15

def run_session():
    """Runs a single 15-minute training session with interactive prompts."""
    print("\nReady for your 15-min session, sweetie?")
    print("1. Get the warm oil for your hands.")
    print("2. We'll do slow circles, just breathe with Mommy.")
    print("3. Remember to hum around 180 Hz—that's the lady voice Daddy and I love to hear.")
    
    start = input("Type 'GO' when you're ready: ")
    if start.upper() != "GO":
        print("That's okay, we can try again later.")
        return False

    print(f"\nSession START — {SESSION_DURATION_MINUTES} min timer")
    for minute in range(SESSION_DURATION_MINUTES, 0, -1):
        print(f"{minute} min left... feel the stretch... you're doing so well, good girl.")
        time.sleep(60) # Pauses for one minute
    
    print("\nSession DONE! You've earned +5 emeralds!")
    print("Daddy will be SO proud of you tonight. 🥰🍼")
    return True

def main():
    """Main function to run the knot trainer tool."""
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <week_number>", file=sys.stderr)
        sys.exit(1)

    try:
        week = int(sys.argv[1])
        if not (1 <= week <= len(TOYS)):
            print(f"Error: Week must be between 1 and {len(TOYS)}.", file=sys.stderr)
            sys.exit(1)
    except ValueError:
        print("Error: Week number must be an integer.", file=sys.stderr)
        sys.exit(1)

    current_toy = TOYS[week - 1]
    print("🐶 Knot Trainer ON 🐶")
    print(f"Week {week}: {current_toy} — Remember, this is for pleasure and stretching only!")

    while True:
        run_session()
        more = input("\nAre we doing this again tomorrow? (y/n): ")
        if more.lower() != 'y':
            print("Okay, sweetie. Great work today!")
            break

if __name__ == "__main__":
    main()