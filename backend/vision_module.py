import cv2
import numpy as np
from deepface import DeepFace
import mediapipe as mp

class SmartMirrorVision:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8)
        # DeepFace models load hone mein time lete hain, isliye hum pre-load ka logic use kar sakte hain
        
    def process_frame(self, frame):
        mood = "Neutral"
        gesture = "None"

        # --- 1. ENHANCED EMOTION DETECTION ---
        try:
            # Hum 'enforce_detection=False' rakhenge taaki door se bhi detect ho
            # detector_backend='opencv' fast hai, 'retinaface' slow par accurate hai
            # Agar accuracy badhani hai toh 'opencv' ko badal kar 'retinaface' kar sakte hain
            results = DeepFace.analyze(
                img_path = frame, 
                actions = ['emotion'], 
                enforce_detection = False, 
                detector_backend = 'opencv', 
                silent = True
            )
            
            emotions = results[0]['emotion']
            # Angry emotion ki sensitivity badhane ke liye:
            # Agar angry ka score 10% se upar hai, toh use priority dein
            if emotions['angry'] > 15: 
                mood = "Angry"
            else:
                mood = results[0]['dominant_emotion'].capitalize()
                
        except Exception as e:
            mood = "Neutral"

        # --- 2. FLEXIBLE GESTURE DETECTION ---
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)
        
        if result.multi_hand_landmarks:
            landmarks = result.multi_hand_landmarks[0].landmark
            
            # Index (8) aur Middle (12) finger tips ko check kar rahe hain
            # Flexibility ke liye distance logic:
            if landmarks[8].y < landmarks[5].y: # Index finger up
                gesture = "Palm"
            else:
                gesture = "Fist"
        
        return True, mood, "OFF", "Stable", gesture