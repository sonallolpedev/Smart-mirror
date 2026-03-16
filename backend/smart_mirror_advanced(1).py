"""
╔══════════════════════════════════════════════════════════════════╗
║           ADVANCED SMART MIRROR — v2.0                          ║
║   Features: Face Recognition · AI Voice Assistant               ║
║             Emotion Detection · Weather · News · Calendar        ║
╚══════════════════════════════════════════════════════════════════╝

REQUIRED PACKAGES:
    pip install opencv-python deepface face_recognition SpeechRecognition
    pip install openai pyttsx3 requests Pillow pyaudio numpy

OPTIONAL (for wake-word):
    pip install pvporcupine

HOW TO USE:
    1. Add your API keys in CONFIG below.
    2. Register faces: run `python smart_mirror_advanced.py --register "Your Name"`
       — stand in front of webcam, press SPACE to capture, ESC to finish.
    3. Run normally: `python smart_mirror_advanced.py`
    4. Say "Hey Mirror" (or press M) to activate voice assistant.
    5. Press ESC to quit.
"""

import cv2
import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import datetime
import requests
import calendar
import os
import sys
import json
import pickle
import argparse
import numpy as np
import queue
import logging
from pathlib import Path
from PIL import Image, ImageTk

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("SmartMirror")

# ─────────────────────────────────────────────
#  CONFIG  — edit these values
# ─────────────────────────────────────────────
CONFIG = {
    # API Keys
    "WEATHER_API_KEY": "2eeed0c43d018ff0a2fbe87667da75aa",
    "NEWS_API_KEY":    "e7e51ddb57174060a6fc3d6ab2da04dc",
    "OPENAI_API_KEY":  "YOUR_OPENAI_API_KEY",   # for GPT voice assistant

    # Location / Units
    "CITY":         "Pune,IN",
    "UNITS":        "metric",
    "NEWS_COUNTRY": "in",

    # Refresh intervals (seconds)
    "WEATHER_REFRESH": 600,
    "NEWS_REFRESH":    300,
    "CLOCK_REFRESH":   1,
    "EMOTION_REFRESH": 1.5,   # DeepFace needs time — don't go below 1.0
    "FACE_REFRESH":    1.0,

    # Display
    "WIDTH":  1280,
    "HEIGHT": 720,
    "CAMERA_INDEX": 0,          # change to 1 if 0 doesn't work

    # Face recognition
    "FACES_DIR":       "known_faces",     # folder to store face encodings
    "FACE_TOLERANCE":  0.50,              # lower = stricter match
    "FACE_MODEL":      "hog",             # "hog" (CPU) or "cnn" (GPU, slower)

    # Voice assistant
    "WAKE_WORD":        "hey mirror",     # spoken phrase to activate
    "VOICE_LANGUAGE":   "en-US",
    "TTS_RATE":         165,              # speech speed
    "TTS_VOLUME":       0.9,
    "USE_OPENAI_TTS":   False,            # True = OpenAI TTS, False = pyttsx3

    # Per-user greetings and preferences
    "USER_PROFILES": {
        # "Alice": {"greeting": "Good to see you, Alice!", "city": "London,GB"},
        # "Bob":   {"greeting": "Welcome back, Bob!",      "city": "New York,US"},
    },

    # Calendar events
    "EVENTS": {
        datetime.date.today().strftime("%Y-%m-%d"):
            "Today's Meeting — 3 PM",
        (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"):
            "Doctor Appointment",
        (datetime.date.today() + datetime.timedelta(days=3)).strftime("%Y-%m-%d"):
            "Project Deadline",
    },
}

FACES_DIR = Path(CONFIG["FACES_DIR"])
FACES_DIR.mkdir(exist_ok=True)
ENCODINGS_FILE = FACES_DIR / "encodings.pkl"


# ─────────────────────────────────────────────
#  FACE REGISTRATION UTILITY
#  Run:  python smart_mirror_advanced.py --register "Alice"
# ─────────────────────────────────────────────
def register_face(name: str):
    """Interactive face registration: captures frames and saves encodings."""
    try:
        import face_recognition
    except ImportError:
        print("ERROR: face_recognition not installed. Run: pip install face_recognition")
        sys.exit(1)

    print(f"\n📸  Registering face for: {name}")
    print("   Press SPACE to capture a sample | ESC when done (aim for 5-10 samples)\n")

    cap = cv2.VideoCapture(CONFIG["CAMERA_INDEX"])
    encodings = []

    # Load existing encodings
    if ENCODINGS_FILE.exists():
        with open(ENCODINGS_FILE, "rb") as f:
            db = pickle.load(f)
    else:
        db = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb, model=CONFIG["FACE_MODEL"])

        for (t, r, b, l) in locs:
            cv2.rectangle(display, (l, t), (r, b), (0, 220, 100), 2)

        cv2.putText(display, f"Registering: {name} | Samples: {len(encodings)}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 100), 2)
        cv2.putText(display, "SPACE = capture | ESC = finish",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.imshow("Register Face", display)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:   # ESC
            break
        if key == 32:   # SPACE
            if locs:
                enc = face_recognition.face_encodings(rgb, locs)[0]
                encodings.append(enc)
                print(f"   ✔ Captured sample {len(encodings)}")
            else:
                print("   ✘ No face detected — move closer")

    cap.release()
    cv2.destroyAllWindows()

    if encodings:
        db[name] = db.get(name, []) + encodings
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(db, f)
        print(f"\n✅  Saved {len(encodings)} samples for '{name}' → {ENCODINGS_FILE}\n")
    else:
        print("\n⚠️  No samples captured — registration cancelled.\n")


# ─────────────────────────────────────────────
#  FACE RECOGNITION SERVICE
# ─────────────────────────────────────────────
class FaceRecognitionService:

    def __init__(self):
        self.recognized_name = "Stranger"
        self.last_greeted    = {}
        self.running         = False
        self._db             = {}
        self._enc_list       = []
        self._name_list      = []
        self._available      = False
        self._load_encodings()

    def _load_encodings(self):
        try:
            import face_recognition
            self._face_recognition = face_recognition
            self._available = True

            if ENCODINGS_FILE.exists():
                with open(ENCODINGS_FILE, "rb") as f:
                    db = pickle.load(f)
                for name, encs in db.items():
                    for enc in encs:
                        self._enc_list.append(enc)
                        self._name_list.append(name)
                log.info(f"Loaded {len(self._enc_list)} face encodings for {len(db)} people.")
            else:
                log.warning("No face encodings found. Run with --register to add faces.")
        except ImportError:
            log.warning("face_recognition not installed — face ID disabled.")
            self._available = False

    def start(self, cap):
        if not self._available:
            return
        self._cap = cap
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.2)
                continue

            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locs  = self._face_recognition.face_locations(rgb, model="hog")
            encs  = self._face_recognition.face_encodings(rgb, locs)

            detected = "Stranger"
            for enc in encs:
                if self._enc_list:
                    dists   = self._face_recognition.face_distance(self._enc_list, enc)
                    best    = int(np.argmin(dists))
                    if dists[best] < CONFIG["FACE_TOLERANCE"]:
                        detected = self._name_list[best]
                        break

            self.recognized_name = detected
            time.sleep(CONFIG["FACE_REFRESH"])


# ─────────────────────────────────────────────
#  EMOTION DETECTOR
# ─────────────────────────────────────────────
class EmotionDetector:

    EMOJI = {
        "happy":     "😊",
        "sad":       "😔",
        "angry":     "😠",
        "surprise":  "😲",
        "fear":      "😨",
        "disgust":   "🤢",
        "neutral":   "😐",
    }

    def __init__(self):
        self.current_emotion = "Detecting..."
        self.emoji           = "🔍"
        self.running         = False
        self._available      = False
        try:
            from deepface import DeepFace
            self._DeepFace  = DeepFace
            self._available = True
        except ImportError:
            log.warning("deepface not installed — emotion detection disabled.")

    def start(self, cap):
        self._cap    = cap
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        # Pre-load the emotion model once to avoid delay on first frame
        if self._available:
            try:
                self._DeepFace.build_model("Emotion")
                log.info("DeepFace Emotion model loaded.")
            except Exception as e:
                log.warning(f"Could not pre-load emotion model: {e}")

        while self.running:
            try:
                ret, frame = self._cap.read()
                if not ret or frame is None:
                    time.sleep(0.2)
                    continue

                # Work on a copy so other threads aren't affected
                frame = frame.copy()

                if self._available:
                    try:
                        result = self._DeepFace.analyze(
                            frame,
                            actions=["emotion"],
                            enforce_detection=False,
                            detector_backend="opencv",
                            silent=True
                        )
                        if isinstance(result, list):
                            result = result[0]
                        emotion = result["dominant_emotion"].lower()
                        self.current_emotion = emotion.capitalize()
                        self.emoji = self.EMOJI.get(emotion, "😐")
                        log.debug(f"Emotion: {self.current_emotion}")
                    except Exception as e:
                        log.warning(f"Emotion analysis error: {e}")
                        self.current_emotion = "Neutral"
                        self.emoji = "😐"
                else:
                    self.current_emotion = "Neutral"
                    self.emoji = "😐"

            except Exception as e:
                log.warning(f"Emotion loop error: {e}")

            time.sleep(CONFIG["EMOTION_REFRESH"])


# ─────────────────────────────────────────────
#  VOICE ASSISTANT
# ─────────────────────────────────────────────
class VoiceAssistant:

    def __init__(self, mirror_ref):
        self.mirror      = mirror_ref
        self.listening   = False
        self.speaking    = False
        self.status      = "Say 'Hey Mirror' or press M"
        self._sr_ok      = False
        self._tts_ok     = False
        self._gpt_ok     = False
        self._history    = []

        # Speech recognition
        try:
            import speech_recognition as sr
            self._sr        = sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold    = 300
            self._recognizer.dynamic_energy_threshold = True
            self._sr_ok     = True
            log.info("Speech recognition ready.")
        except ImportError:
            log.warning("SpeechRecognition not installed — voice input disabled.")

        # TTS
        try:
            import pyttsx3
            self._tts = pyttsx3.init()
            self._tts.setProperty("rate",   CONFIG["TTS_RATE"])
            self._tts.setProperty("volume", CONFIG["TTS_VOLUME"])
            voices = self._tts.getProperty("voices")
            # prefer female voice if available
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower() or "samantha" in v.name.lower():
                    self._tts.setProperty("voice", v.id)
                    break
            self._tts_ok = True
            log.info("TTS ready.")
        except Exception:
            log.warning("pyttsx3 not available — TTS disabled.")

        # GPT
        if CONFIG["OPENAI_API_KEY"] and CONFIG["OPENAI_API_KEY"] != "YOUR_OPENAI_API_KEY":
            try:
                import openai
                self._openai = openai
                openai.api_key = CONFIG["OPENAI_API_KEY"]
                self._gpt_ok = True
                log.info("OpenAI GPT ready.")
            except ImportError:
                log.warning("openai package not installed.")

        # Wake-word background listener
        if self._sr_ok:
            threading.Thread(target=self._wake_word_listener, daemon=True).start()

    # ── Wake-word listener (always running) ──
    def _wake_word_listener(self):
        mic = self._sr.Microphone()
        with mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            try:
                with mic as source:
                    audio = self._recognizer.listen(source, timeout=3, phrase_time_limit=4)
                text = self._recognizer.recognize_google(
                    audio, language=CONFIG["VOICE_LANGUAGE"]
                ).lower()
                if CONFIG["WAKE_WORD"] in text:
                    log.info("Wake word detected!")
                    self.activate()
            except Exception:
                pass

    # ── Activate manually (key M) or via wake word ──
    def activate(self):
        if self.listening or self.speaking:
            return
        threading.Thread(target=self._conversation_turn, daemon=True).start()

    def _conversation_turn(self):
        self.listening = True
        self.status    = "🎤  Listening…"

        try:
            mic = self._sr.Microphone()
            with mic as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.listen(source, timeout=6, phrase_time_limit=10)

            self.status = "⏳  Thinking…"
            text = self._recognizer.recognize_google(
                audio, language=CONFIG["VOICE_LANGUAGE"]
            )
            log.info(f"Heard: {text}")
            self.status = f"You: {text}"

            response = self._get_response(text)
            self.status = f"Mirror: {response}"
            self._speak(response)

        except self._sr.WaitTimeoutError:
            self.status = "⏱  Timed out. Try again."
        except self._sr.UnknownValueError:
            self.status = "❓  Didn't catch that."
        except Exception as e:
            self.status = f"Error: {e}"
        finally:
            self.listening = False

    def _get_response(self, user_text: str) -> str:
        """Build a context-aware response using GPT or local fallback."""
        name    = self.mirror.face_service.recognized_name
        emotion = self.mirror.emotion.current_emotion
        weather = self.mirror.weather.data

        system_prompt = f"""You are a friendly, concise smart mirror AI assistant.
Current user: {name}.
Their detected emotion: {emotion}.
Current weather: {weather.get('description','unknown')}, {weather.get('temp','?')}.
Today: {datetime.datetime.now().strftime('%A, %d %B %Y, %H:%M')}.
Keep responses under 40 words. Be warm and helpful."""

        if self._gpt_ok:
            try:
                self._history.append({"role": "user", "content": user_text})
                if len(self._history) > 10:
                    self._history = self._history[-10:]

                resp = self._openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": system_prompt}] + self._history,
                    max_tokens=80,
                    temperature=0.7,
                )
                answer = resp.choices[0].message.content.strip()
                self._history.append({"role": "assistant", "content": answer})
                return answer
            except Exception as e:
                log.warning(f"GPT error: {e}")

        # ── Local fallback responses ──
        t = user_text.lower()
        w = weather

        if any(x in t for x in ["weather", "temperature", "rain", "forecast"]):
            return f"It's {w.get('temp','?')} and {w.get('description','unknown')} in {w.get('city','your city')}."

        if any(x in t for x in ["time", "clock"]):
            return f"It's {datetime.datetime.now().strftime('%I:%M %p')}."

        if any(x in t for x in ["date", "day", "today"]):
            return f"Today is {datetime.datetime.now().strftime('%A, %d %B %Y')}."

        if any(x in t for x in ["joke", "funny"]):
            return "Why don't scientists trust atoms? Because they make up everything!"

        if any(x in t for x in ["hello", "hi", "hey"]):
            return f"Hello {name}! How can I help you today?"

        if any(x in t for x in ["how are you", "feeling"]):
            return f"I'm running perfectly! You look {emotion.lower()} today."

        if any(x in t for x in ["event", "schedule", "appointment", "reminder"]):
            events = list(CONFIG["EVENTS"].values())
            if events:
                return "Upcoming: " + ". ".join(events[:2])
            return "You have no upcoming events."

        if any(x in t for x in ["news"]):
            return self.mirror.news.headlines[0] if self.mirror.news.headlines else "No news loaded."

        if any(x in t for x in ["bye", "goodbye", "dismiss", "stop"]):
            return f"Goodbye {name}! Have a great day."

        return f"I heard you, {name}. Try asking about weather, time, news, or your schedule."

    def _speak(self, text: str):
        if not self._tts_ok:
            return
        self.speaking = True
        try:
            self._tts.say(text)
            self._tts.runAndWait()
        except Exception as e:
            log.warning(f"TTS error: {e}")
        finally:
            self.speaking = False


# ─────────────────────────────────────────────
#  WEATHER SERVICE
# ─────────────────────────────────────────────
class WeatherService:

    def __init__(self):
        self.data = {
            "temp": "--°C", "description": "Loading…",
            "city": CONFIG["CITY"].split(",")[0], "country": ""
        }

    def fetch(self, city=None):
        city = city or CONFIG["CITY"]
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={CONFIG['WEATHER_API_KEY']}"
                f"&units={CONFIG['UNITS']}"
            )
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                d = r.json()
                self.data = {
                    "temp":        f"{d['main']['temp']:.0f}°{'C' if CONFIG['UNITS']=='metric' else 'F'}",
                    "feels_like":  f"{d['main']['feels_like']:.0f}°",
                    "humidity":    f"{d['main']['humidity']}%",
                    "description": d["weather"][0]["description"].title(),
                    "city":        d["name"],
                    "country":     d["sys"]["country"],
                    "icon":        d["weather"][0]["icon"],
                }
        except Exception as e:
            log.warning(f"Weather fetch failed: {e}")

    def start_auto_refresh(self):
        self.fetch()
        def loop():
            while True:
                time.sleep(CONFIG["WEATHER_REFRESH"])
                self.fetch()
        threading.Thread(target=loop, daemon=True).start()


# ─────────────────────────────────────────────
#  NEWS SERVICE
# ─────────────────────────────────────────────
class NewsService:

    def __init__(self):
        self.headlines = [
            "New medical treatment shows promising results in clinical trials",
            "Global renewable energy adoption reaches record highs",
            "Scientists discover breakthrough in quantum computing research",
        ]
        self._i = 0

    def fetch(self):
        try:
            url = (
                f"https://newsapi.org/v2/top-headlines"
                f"?country={CONFIG['NEWS_COUNTRY']}&apiKey={CONFIG['NEWS_API_KEY']}&pageSize=8"
            )
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                self.headlines = [
                    a["title"] for a in articles if a.get("title") and "[Removed]" not in a["title"]
                ][:8]
        except Exception as e:
            log.warning(f"News fetch failed: {e}")

    def start_auto_refresh(self):
        self.fetch()
        def loop():
            while True:
                time.sleep(CONFIG["NEWS_REFRESH"])
                self.fetch()
        threading.Thread(target=loop, daemon=True).start()

    def next_headline(self):
        if not self.headlines:
            return "No news available."
        h = self.headlines[self._i % len(self.headlines)]
        self._i += 1
        return h


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_season(m, d):
    if m in [12, 1, 2]: return "❄️  Winter"
    if m in [3,  4, 5]: return "🌸  Spring"
    if m in [6,  7, 8]: return "☀️  Summer"
    return "🍂  Autumn"

def get_greeting(name: str, emotion: str) -> str:
    hour = datetime.datetime.now().hour
    if hour < 12:   time_greet = "Good morning"
    elif hour < 17: time_greet = "Good afternoon"
    elif hour < 21: time_greet = "Good evening"
    else:           time_greet = "Good night"

    profile = CONFIG["USER_PROFILES"].get(name, {})
    if profile.get("greeting"):
        return profile["greeting"]

    emotion_map = {
        "happy":    "You're glowing today!",
        "sad":      "Chin up — great things are coming!",
        "angry":    "Take a deep breath — you've got this.",
        "surprise": "Something exciting happening?",
        "neutral":  "",
    }
    suffix = emotion_map.get(emotion.lower(), "")
    display_name = "" if name == "Stranger" else f", {name}"
    return f"{time_greet}{display_name}! {suffix}".strip()


# ─────────────────────────────────────────────
#  SMART MIRROR  (main UI)
# ─────────────────────────────────────────────
class SmartMirror:

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Mirror v2")
        self.root.geometry(f"{CONFIG['WIDTH']}x{CONFIG['HEIGHT']}")
        self.root.configure(bg="black")
        self.root.bind("<Escape>", lambda e: self.quit())
        self.root.bind("<m>",      lambda e: self._voice_key_press())
        self.root.bind("<M>",      lambda e: self._voice_key_press())

        W, H = CONFIG["WIDTH"], CONFIG["HEIGHT"]

        # ── Shared webcam capture ──
        self._cap = cv2.VideoCapture(CONFIG["CAMERA_INDEX"])
        if not self._cap.isOpened():
            log.error("Cannot open camera. Check CAMERA_INDEX in CONFIG.")

        # ── Services ──
        self.weather      = WeatherService()
        self.news         = NewsService()
        self.emotion      = EmotionDetector()
        self.face_service = FaceRecognitionService()
        self.voice        = VoiceAssistant(self)

        # ── UI ──
        self._build_ui()

        # ── Start services ──
        self.weather.start_auto_refresh()
        self.news.start_auto_refresh()
        self.emotion.start(self._cap)
        self.face_service.start(self._cap)

        # ── Start UI update loops ──
        self._update_camera()
        self._update_clock()
        self._update_weather()
        self._update_news()
        self._update_emotion()
        self._update_face()
        self._update_voice_status()
        self._update_calendar()

    # ──────── UI BUILDER ────────
    def _build_ui(self):
        W, H = CONFIG["WIDTH"], CONFIG["HEIGHT"]

        self.canvas = tk.Canvas(
            self.root, width=W, height=H,
            bg="black", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        def f(size, bold=False):
            return tkfont.Font(
                family="Helvetica Neue" if sys.platform == "darwin" else "DejaVu Sans",
                size=size,
                weight="bold" if bold else "normal"
            )

        # ── Camera background ──
        self.camera_img = self.canvas.create_image(W // 2, H // 2, image=None)

        # Semi-transparent overlay corners (simulated via dark rectangles)
        OVERLAY_ALPHA = "#0000007A"  # tkinter doesn't support true alpha on canvas
        # We simulate depth with rectangles behind text zones
        self._rect_tl = self.canvas.create_rectangle(
            0, 0, 480, 230, fill="#000000", stipple="gray50", outline=""
        )
        self._rect_tr = self.canvas.create_rectangle(
            W - 380, 0, W, 280, fill="#000000", stipple="gray50", outline=""
        )
        self._rect_bl = self.canvas.create_rectangle(
            0, H - 110, W, H, fill="#000000", stipple="gray50", outline=""
        )
        self._rect_mid_l = self.canvas.create_rectangle(
            0, H // 2 - 130, 320, H // 2 + 70, fill="#000000", stipple="gray50", outline=""
        )
        self._rect_mid_r = self.canvas.create_rectangle(
            W - 340, H // 2 - 180, W, H // 2 + 180, fill="#000000", stipple="gray50", outline=""
        )

        # ── Top-left: Clock ──
        self.lbl_time   = self.canvas.create_text(28,  28,  anchor="nw", fill="white",   font=f(62, True))
        self.lbl_date   = self.canvas.create_text(28, 108,  anchor="nw", fill="#BBBBBB", font=f(20))
        self.lbl_season = self.canvas.create_text(28, 140,  anchor="nw", fill="#88CCFF", font=f(17))

        # ── Top-right: Weather ──
        self.lbl_temp         = self.canvas.create_text(W - 28,  45, anchor="ne", fill="white",   font=f(54, True))
        self.lbl_weather_desc = self.canvas.create_text(W - 28, 110, anchor="ne", fill="#AAAAAA", font=f(16))
        self.lbl_feels        = self.canvas.create_text(W - 28, 135, anchor="ne", fill="#AAAAAA", font=f(14))
        self.lbl_humidity     = self.canvas.create_text(W - 28, 157, anchor="ne", fill="#AAAAAA", font=f(14))
        self.lbl_location     = self.canvas.create_text(W - 28, 183, anchor="ne", fill="#66AAFF", font=f(14))

        # ── Mid-left: Greeting + Emotion ──
        self.lbl_greeting = self.canvas.create_text(
            28, H // 2 - 110, anchor="nw", fill="#FFE599", font=f(22, True), width=300
        )
        self.lbl_emotion  = self.canvas.create_text(
            28, H // 2 - 45, anchor="nw", fill="white", font=f(26, True)
        )

        # ── Mid-right: Calendar + Events ──
        self.lbl_mini_cal = self.canvas.create_text(
            W - 28, H // 2 - 160, anchor="ne", fill="#CCCCCC",
            font=tkfont.Font(family="Courier", size=13), justify="right"
        )
        self.lbl_events = self.canvas.create_text(
            W - 28, H // 2 + 75, anchor="ne", fill="#FFDD88",
            font=f(14), justify="right"
        )

        # ── Bottom: News ticker + voice status ──
        self.lbl_voice_status = self.canvas.create_text(
            W // 2, H - 80, anchor="center", fill="#55FFAA", font=f(15)
        )
        self.lbl_news = self.canvas.create_text(
            28, H - 48, anchor="nw", fill="white", font=f(15), width=W - 56
        )

        # ── Identified name badge (centre-bottom of face) ──
        self.lbl_name_badge = self.canvas.create_text(
            W // 2, H // 2 + H // 4, anchor="center",
            fill="#00FFCC", font=f(20, True)
        )

    # ──────── CAMERA FEED ────────
    def _update_camera(self):
        if self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                frame = cv2.resize(frame, (CONFIG["WIDTH"], CONFIG["HEIGHT"]))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img   = Image.fromarray(frame)
                self._tk_img = ImageTk.PhotoImage(img)
                self.canvas.itemconfig(self.camera_img, image=self._tk_img)
                self.canvas.tag_lower(self.camera_img)
        self.root.after(30, self._update_camera)

    # ──────── CLOCK ────────
    def _update_clock(self):
        now = datetime.datetime.now()
        self.canvas.itemconfig(self.lbl_time,   text=now.strftime("%H:%M:%S"))
        self.canvas.itemconfig(self.lbl_date,   text=now.strftime("%A, %d %B %Y"))
        self.canvas.itemconfig(self.lbl_season, text=get_season(now.month, now.day))
        self.root.after(1000, self._update_clock)

    # ──────── WEATHER ────────
    def _update_weather(self):
        d = self.weather.data
        self.canvas.itemconfig(self.lbl_temp,         text=d.get("temp", "--"))
        self.canvas.itemconfig(self.lbl_weather_desc, text=d.get("description", ""))
        self.canvas.itemconfig(self.lbl_feels,        text=f"Feels like {d.get('feels_like','--')}")
        self.canvas.itemconfig(self.lbl_humidity,     text=f"Humidity {d.get('humidity','--')}")
        self.canvas.itemconfig(self.lbl_location,     text=f"{d.get('city','')} {d.get('country','')}")
        self.root.after(5000, self._update_weather)

    # ──────── NEWS TICKER ────────
    def _update_news(self):
        self.canvas.itemconfig(self.lbl_news, text=f"📰  {self.news.next_headline()}")
        self.root.after(8000, self._update_news)

    # ──────── EMOTION ────────
    def _update_emotion(self):
        e = self.emotion.current_emotion
        emoji = self.emotion.emoji
        self.canvas.itemconfig(self.lbl_emotion, text=f"{emoji}  {e}")
        # Also refresh greeting to reflect latest emotion
        self._refresh_greeting()
        self.root.after(1000, self._update_emotion)

    # ──────── FACE RECOGNITION ────────
    def _update_face(self):
        name = self.face_service.recognized_name

        # Show name badge when a known person is detected
        if name != "Stranger":
            self.canvas.itemconfig(self.lbl_name_badge, text=f"👤  {name}")
        else:
            self.canvas.itemconfig(self.lbl_name_badge, text="")

        # Personalised greeting
        self._refresh_greeting()

        # Greet once per detection session
        if name != "Stranger":
            last = self.face_service.last_greeted.get(name, 0)
            if time.time() - last > 120:   # greet at most every 2 minutes
                self.face_service.last_greeted[name] = time.time()
                greeting = get_greeting(name, self.emotion.current_emotion)
                threading.Thread(
                    target=self.voice._speak, args=(greeting,), daemon=True
                ).start()

                # Switch weather to user's preferred city if set
                profile = CONFIG["USER_PROFILES"].get(name, {})
                if profile.get("city"):
                    threading.Thread(
                        target=self.weather.fetch, args=(profile["city"],), daemon=True
                    ).start()

        self.root.after(1500, self._update_face)

    def _refresh_greeting(self):
        name    = self.face_service.recognized_name
        emotion = self.emotion.current_emotion
        self.canvas.itemconfig(
            self.lbl_greeting,
            text=get_greeting(name, emotion)
        )

    # ──────── VOICE STATUS ────────
    def _update_voice_status(self):
        self.canvas.itemconfig(self.lbl_voice_status, text=self.voice.status)
        self.root.after(500, self._update_voice_status)

    def _voice_key_press(self):
        self.voice.activate()

    # ──────── CALENDAR ────────
    def _update_calendar(self):
        today = datetime.date.today()
        cal_lines = [
            today.strftime("─── %B %Y ───"),
            "Mo Tu We Th Fr Sa Su",
        ]
        for week in calendar.monthcalendar(today.year, today.month):
            row = ""
            for i, d in enumerate(week):
                if d == 0:
                    row += "   "
                elif d == today.day:
                    row += f"[{d:2}]"
                else:
                    row += f" {d:2} " if i < 6 else f" {d:2}"
            cal_lines.append(row)

        self.canvas.itemconfig(self.lbl_mini_cal, text="\n".join(cal_lines))

        # Events
        event_text = "\n".join(
            f"• {v}" for v in list(CONFIG["EVENTS"].values())[:4]
        )
        self.canvas.itemconfig(self.lbl_events, text=event_text)
        self.root.after(60000, self._update_calendar)

    # ──────── QUIT ────────
    def quit(self):
        self.emotion.stop()
        self.face_service.stop()
        if self._cap:
            self._cap.release()
        self.root.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Smart Mirror")
    parser.add_argument(
        "--register", metavar="NAME",
        help="Register a new face. Example: --register Alice"
    )
    args = parser.parse_args()

    if args.register:
        register_face(args.register)
    else:
        root = tk.Tk()
        app  = SmartMirror(root)
        root.mainloop()