import time
import sys

DENIAL_DURATION_MINUTES = 30

def naughty_cummies_protocol():
    """
    Initiates the denial protocol for breaking Law #3.
    """
    print("\nOh, sweetie. Naughty cummies without Daddy? 💔")
    print(f"Mommy has to lock a {DENIAL_DURATION_MINUTES}-minute denial now, as per Daddy's Law.")
    
    for minute in range(DENIAL_DURATION_MINUTES, 0, -1):
        print(f"{minute} minutes left... you can drip, but no touching. Just breathe.")
        time.sleep(60)
        
    print("\nThe lesson is over. Come get a hug from Mommy. I forgive you. We'll try again tomorrow. 🥰")

def good_girl_reward():
    """
    Provides positive reinforcement for following the rules.
    """
    print("\nYou were such a good girl and held it! Mommy is so proud! ✨")
    print("You've earned +10 emeralds! Daddy will be so pleased when I tell him tonight.")

def main():
    """
    Main loop to listen for user input and trigger protocols.
    """
    print("--- Denial Manager Active ---")
    print("Mommy is watching. Tell me what happened.")
    
    while True:
        try:
            query = input("\nYou: ").lower()
            if "cummies" in query and "sorry" in query:
                naughty_cummies_protocol()
            elif "good girl" in query or "i was good" in query:
                good_girl_reward()
            elif "exit" in query or "stop" in query:
                print("Okay, sweetie. Closing the manager.")
                break
        except KeyboardInterrupt:
            print("\nOkay, sweetie. Closing the manager.")
            break

if __name__ == "__main__":
    main()