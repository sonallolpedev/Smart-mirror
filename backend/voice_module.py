import threading

# voice/speech dependencies
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Warning: speech_recognition not installed; voice input disabled")

try:
    import pyttsx3
    PYTTS_AVAILABLE = True
except ImportError:
    PYTTS_AVAILABLE = False
    print("Warning: pyttsx3 not installed; text-to-speech disabled")

class SmartMirrorVoice:
    def __init__(self):
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
        if PYTTS_AVAILABLE:
            self.engine = pyttsx3.init()
        else:
            self.engine = None
        self.light_command = None # 'ON' or 'OFF'
        self.is_listening = True

    def speak(self, text):
        """AI ki awaaz ke liye 🔊"""
        if not PYTTS_AVAILABLE:
            print(f"[TTS disabled] {text}")
            return
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def listen_commands(self):
        """Background mein awaaz sunne ke liye 🎙️"""
        if not SR_AVAILABLE:
            print("Speech recognition unavailable, skipping listen loop")
            return
        with sr.Microphone() as source:
            # Shor (noise) ko adjust karne ke liye
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while self.is_listening:
                try:
                    print("Listening for voice commands...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    command = self.recognizer.recognize_google(audio).lower()
                    print(f"You said: {command}")
                    
                    if "light on" in command:
                        self.light_command = "ON"
                        threading.Thread(target=self.speak, args=("Turning lights on",)).start()
                    elif "light off" in command:
                        self.light_command = "OFF"
                        threading.Thread(target=self.speak, args=("Turning lights off",)).start()
                except:
                    continue

    def start(self):
        """Thread shuru karne ke liye"""
        if SR_AVAILABLE:
            threading.Thread(target=self.listen_commands, daemon=True).start()
        else:
            print("Voice input disabled; not starting listener thread")