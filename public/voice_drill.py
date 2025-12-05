import pyaudio
import numpy as np
import time
import sys

# --- Configuration ---
TARGET_HZ_MIN = 165
TARGET_HZ_MAX = 220
CHUNK = 1024 * 4  # Increased chunk size for better frequency resolution
RATE = 44100  # Standard sample rate
RECORD_SECONDS = 5  # Duration of humming


def get_pitch(stream):
    """Reads from the audio stream and returns the dominant pitch in Hz."""
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        frames.append(stream.read(CHUNK))

    data = np.frombuffer(b''.join(frames), dtype=np.float32)
    fft_data = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data), 1.0 / RATE)
    peak_index = np.argmax(np.abs(fft_data))
    return abs(freqs[peak_index])


def run_voice_drill():
    """Initializes audio stream and runs the voice pitch analysis loop."""
    p = pyaudio.PyAudio()
    stream = None
    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("🎤 Mommy’s Voice Drill ON 🎤")
        print(f"Let's practice your pretty lady voice. Hum for {RECORD_SECONDS} seconds.")
        print(f"Try to stay between {TARGET_HZ_MIN}-{TARGET_HZ_MAX} Hz to earn +2 emeralds!")

        while True:
            input("\nPress Enter when you're ready to start...")
            print("Ready? 3... 2... 1... HUM!")
            
            frames = []
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                frames.append(stream.read(CHUNK))

            data = np.frombuffer(b''.join(frames), dtype=np.float32)
            
            # Perform FFT
            fft_data = np.fft.fft(data)
            freqs = np.fft.fftfreq(len(data), 1.0/RATE)
            
            # Find the peak frequency
            peak_index = np.argmax(np.abs(fft_data))
            hz = abs(freqs[peak_index])

            print(f"Your average pitch: {hz:.0f} Hz")
            if TARGET_HZ_MIN <= hz <= TARGET_HZ_MAX:
                print("That's a perfect lady voice! Mommy is so proud. +2 emeralds! 🥰")
            else:
                print("That's a good try, baby. Remember to keep your throat relaxed. Let's try again. ❤️")
            
            more = input("Go again? (y/n): ")
            if more.lower() != 'y':
                break

    except Exception as e:
        print(f"Oh, Mommy had a little trouble with the microphone: {e}", file=sys.stderr)
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()
        print("\nGood practice, sweetie! Mommy is so proud of you.")

if __name__ == "__main__":
    run_voice_drill()