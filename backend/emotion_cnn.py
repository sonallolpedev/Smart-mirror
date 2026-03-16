import cv2
import mediapipe as mp
import pyttsx3
import speech_recognition as sr
import threading
import time
from deepface import DeepFace

# --- 1. Settings & Voice Setup ---
light_status = "OFF"
current_mood = "Detecting..."
last_spoken_emotion = ""
is_speaking = False

# Emotion Responses 📖
emotion_responses = {
    "happy": "You look radiant! Keep that smile on.",
    "sad": "I'm here for you. Things will get better.",
    "angry": "Take a deep breath. Let's stay calm.",
    "neutral": "You look focused and ready."
}

def speak(text):
    global is_speaking
    if is_speaking: return
    is_speaking = True
    print(f"Mirror: {text}")
    try:
        new_engine = pyttsx3.init()
        new_engine.say(text)
        new_engine.runAndWait()
        new_engine.stop()
    except Exception as e:
        print(f"Voice Error: {e}")
    finally:
        is_speaking = False

# --- 2. Background Emotion Detection ---
def analyze_emotion_bg(frame_to_analyze):
    global current_mood, last_spoken_emotion
    try:
        results = DeepFace.analyze(frame_to_analyze, actions=['emotion'], enforce_detection=False)
        current_mood = results[0]['dominant_emotion']
        
        if current_mood != last_spoken_emotion:
            msg = emotion_responses.get(current_mood)
            if msg:
                threading.Thread(target=speak, args=(msg,), daemon=True).start()
            last_spoken_emotion = current_mood
    except:
        pass

# --- 3. Background Voice Command ---
def listen_voice():
    global light_status
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                command = recognizer.recognize_google(audio).lower()
                if "light on" in command:
                    light_status = "ON"
                    threading.Thread(target=speak, args=("Lights on",), daemon=True).start()
                elif "light off" in command:
                    light_status = "OFF"
                    threading.Thread(target=speak, args=("Lights off",), daemon=True).start()
            except:
                continue

threading.Thread(target=listen_voice, daemon=True).start()

# --- 4. Main Setup ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils # Landmarks drawing tool
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

last_analysis_time = time.time()

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Gesture Detection (Always running) 🖐️
    results = hands.process(rgb_frame)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            # Index finger logic for Light
            if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:
                light_status = "ON"
            else:
                light_status = "OFF"

    # Emotion Analysis (Every 3 seconds) 🎭
    if time.time() - last_analysis_time > 3:
        analysis_frame = frame.copy() 
        threading.Thread(target=analyze_emotion_bg, args=(analysis_frame,), daemon=True).start()
        last_analysis_time = time.time()

    # UI display
    color = (0, 255, 0) if light_status == "ON" else (0, 0, 255)
    cv2.putText(frame, f"LIGHT: {light_status}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.putText(frame, f"MOOD: {current_mood.upper()}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    cv2.imshow("Smart Mirror AI", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()