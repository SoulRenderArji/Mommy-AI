import sys
sys.path.append('.') # Adds the project root to the Python path

import asyncio
import pyttsx3
import speech_recognition as sr
import requests
import shlex

CURRENT_USER = "hailey"  # Default user
API_URL = "http://127.0.0.1:5000/ask"
NSFW_SESSION = {
    "active": False,
    "age": None
}

def initialize_tts():
    """Initializes the text-to-speech engine."""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    # Attempt to find a female voice
    for voice in voices:
        if voice.gender == 'female':
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 175) # Adjust speech rate
    return engine

def speak(engine, text):
    """Speaks the given text using the TTS engine."""
    engine.say(text)
    engine.runAndWait()

def listen_for_command():
    """Listens for a spoken command from the user."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nMommy is listening... 🤫")
        r.pause_threshold = 1.0 # seconds of non-speaking audio before a phrase is considered complete
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return "Mommy couldn't quite hear you, sweetie. Can you say that again?"
    except sr.RequestError:
        return "Mommy's ears are having trouble connecting. Let's try typing for now."

def ask_mommy_api(query: str, user: str) -> str:
    """Sends a query to the MommyAI server and gets a response."""
    try:
        payload = {"user": user, "query": query}        
        # If the NSFW session is active, automatically add the required flags
        if NSFW_SESSION["active"]:
            payload["nsfw"] = True
            payload["age"] = NSFW_SESSION["age"]

        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "Mommy heard you, but her thoughts are a bit jumbled.")
    except requests.exceptions.RequestException as e:
        print(f"\nError connecting to Mommy AI server: {e}")
        return "I can't seem to reach Mommy right now, sweetie. Is her server running?"
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return "Something went very wrong. Please check the console."


def send_feedback_api(user: str, action: str, style: str, rating: int) -> str:
    """Sends effectiveness feedback to the MommyAI server."""
    feedback_url = "http://127.0.0.1:5000/feedback/effectiveness"
    try:
        payload = {
            "user": user,
            "action_type": action,
            "communication_style": style,
            "feedback": rating
        }
        response = requests.post(feedback_url, json=payload)
        response.raise_for_status()
        return response.json().get("message", "Feedback received, thank you.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return "Mommy couldn't find that specific action/style combination to update."
        else:
            error_detail = e.response.json().get('error', 'An unknown error occurred.')
            return f"Mommy had a problem processing that feedback: {error_detail}"
    except requests.exceptions.RequestException as e:
        print(f"\nError connecting to Mommy AI server: {e}")
        return "I can't seem to reach Mommy right now, sweetie. Is her server running?"
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return "Something went very wrong. Please check the console."

async def main():
    """
    Main loop for an interactive chat session that uses persistent memory.
    """
    global CURRENT_USER
    tts_engine = initialize_tts()
    print("--- Mommy's Listening (Unified Core) ---")
    speak(tts_engine, "I'm here, sweetie. Tell Mommy anything.")
    print("You can switch users by typing 'login <name>' (e.g., 'login brandon').")
    print("\n[System Notice: All parties represented or interacting with this system are over the age of 21. This system does not involve or condone interaction with actual minors.]")

    while True:
        try:
            # Ask user if they want to type or speak
            choice = await asyncio.to_thread(input, f"\n{CURRENT_USER.capitalize()}: (Press Enter to speak, or type your message) ")
            if choice:
                query = choice
            else:
                query = await asyncio.to_thread(listen_for_command)
                print(f"You said: {query}")

            query = query.strip()

            if query.lower() == "exit":
                print("Okay, sweetie. I'll be here if you need me.")
                break
            
            if query.lower().startswith("login "):
                new_user = query.split(" ", 1)[1].lower()
                CURRENT_USER = new_user
                print(f"Mommy sees you, {CURRENT_USER.capitalize()}!")
                continue

            if query.lower().startswith("/nsfw-on "):
                try:
                    age_str = query.split(" ", 1)[1]
                    age = int(age_str)
                    if age >= 21:
                        NSFW_SESSION["active"] = True
                        NSFW_SESSION["age"] = age
                        print("\nSystem: NSFW session is now active. Mature topics are enabled.")
                    else:
                        print("\nSystem: You must be 21 or older to enable this mode.")
                except (ValueError, IndexError):
                    print("\nUsage: /nsfw-on <your_age>")
                continue
            elif query.lower() == "/nsfw-off":
                NSFW_SESSION["active"] = False
                print("\nSystem: NSFW session is now disabled.")
                continue
            
            if query.lower().startswith("/feedback "):
                try:
                    # Use shlex to safely parse the command
                    parts = shlex.split(query)
                    if len(parts) != 4:
                        print("\nUsage: /feedback \"<action_type>\" \"<style>\" <rating>")
                        continue
                    _, action_type, style, rating_str = parts
                    rating = int(rating_str)
                    feedback_response = await asyncio.to_thread(send_feedback_api, CURRENT_USER, action_type, style, rating)
                    print(f"\nSystem: {feedback_response}")
                except (ValueError, IndexError):
                    print("\nInvalid feedback format. Usage: /feedback \"<action_type>\" \"<style>\" <rating>")
                continue

            response = await asyncio.to_thread(ask_mommy_api, query, CURRENT_USER)
            print(f"\nMommy says: {response}") # Print spoken response for the log
            speak(tts_engine, response)

        except KeyboardInterrupt:
            print("\nOkay, sweetie. I'll be here if you need me.")
            break

if __name__ == "__main__":
    asyncio.run(main())