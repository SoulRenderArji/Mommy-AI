import sys
sys.path.append('.') # Adds the project root to the Python path

import asyncio
import pyttsx3
import speech_recognition as sr
import requests
import shlex

CURRENT_USER = "hailey"  # Default user
API_URL = "http://127.0.0.1:5000/ask"

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
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "Mommy heard you, but her thoughts are a bit jumbled.")
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

            response = await asyncio.to_thread(ask_mommy_api, query, CURRENT_USER)
            print(f"\nMommy says: {response}") # Print spoken response for the log
            speak(tts_engine, response)

        except KeyboardInterrupt:
            print("\nOkay, sweetie. I'll be here if you need me.")
            break

if __name__ == "__main__":
    asyncio.run(main())