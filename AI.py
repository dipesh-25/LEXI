import os
import json
import random
import datetime
import webbrowser
import pyttsx3
import pyaudio
import speech_recognition as sr
from deep_translator import GoogleTranslator
import google.generativeai as genai
from config import apikey
from vosk import Model, KaldiRecognizer

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Adjust speaking rate

chat_history = ""  # To store conversation history

# Initialize Google Translator
translator = GoogleTranslator()

# Configure the Generative AI model
genai.configure(api_key=apikey)
model = genai.GenerativeModel('gemini-1.5-flash')

def say(text):
    """Convert text to speech and speak it."""
    engine.say(text)
    engine.runAndWait()

def chat(query):
    """Generate a response based on the input query using Google Generative AI."""
    global chat_history
    chat_history += f"User: {query}\nJarvis: "

    try:
        # Translate the query to English
        query_in_english = translator.translate(query, source='auto', target='en')
        print(f"Translated Query: {query_in_english}")

        # Generate content using the Generative AI model
        response = model.generate_content(query_in_english)
        reply = response.text.strip()

        # Speak the response
        say(reply)

        # Append the reply to the chat history
        chat_history += f"{reply}\n"

        return reply
    except Exception as e:
        print(f"Error in chat function: {e}")
        say("Sorry, I couldn't process that.")
        return "Error"

# Load Vosk Model for offline recognition
vosk_model = Model("model-en-in")  # Use the Indian English model from Vosk website
recognizer = KaldiRecognizer(vosk_model, 16000)

# Initialize PyAudio for Vosk
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
stream.start_stream()

def take_command_google():
    """Use Google Speech Recognition for online speech processing."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.dynamic_energy_threshold = False  # Disable auto-adjustment
        r.energy_threshold = 300  # Set a manual threshold
        r.adjust_for_ambient_noise(source, duration=1)  # Reduce noise calibration time
        print("Listening...")
        try:
            audio = r.listen(source, phrase_time_limit=10, timeout=5)  # Increased limits
            print("Recognizing...")
            query = r.recognize_google(audio, language="hi-IN")  # Optimized for Hindi
            print(f"User said: {query}")
            return query
        except sr.WaitTimeoutError:
            print("No speech detected. Try speaking louder.")
            return ""
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition; {e}")
            return ""

def take_command_vosk():
    """Use Vosk for offline speech recognition."""
    print("Listening (Offline)...")
    while True:
        data = stream.read(4096)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            query = result.get("text", "")
            print(f"User said (Vosk): {query}")
            return query

def take_command():
    """Hybrid Function: Uses Google if online, else switches to Vosk."""
    try:
        return take_command_google()  # Try online recognition
    except Exception as e:
        print(f"Google recognition failed: {e}")
        return take_command_vosk()  # If it fails, use offline recognition

if __name__ == '__main__':
    print('Welcome to dipesh AI')
    say("Dipesh AI activated. How can I assist you today?")

    while True:
        query = take_command().lower()  # Get user input (voice)
        if query == "":
            continue

        # Command to quit Jarvis
        if "quit" in query:
            say("Goodbye!")
            break

        # Reset the chat history
        elif "reset chat" in query:
            chat_history = ""

        # Get a response from Google Generative AI for the query
        else:
            chat(query)  # Process query with Google Generative AI and speak the result

