import cv2
import mediapipe as mp

# Mediapipe Hands setup 🛠️
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,         # Ek waqt mein ek hi haath track karenge
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Camera start 📷
cap = cv2.VideoCapture(0)

print("Hand Tracking Shuru ho raha hai... 'q' dabaye band karne ke liye.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Mirror effect ke liye flip 🪞
    frame = cv2.flip(frame, 1)
    
    # BGR se RGB mein convert (Mediapipe ke liye) 🎨
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # 1. Haath ki side pehchanna (Left/Right)
            label = results.multi_handedness[idx].classification[0].label
            
            # 2. Landmarks ko list mein convert karna taaki points access kar sakein
            landmarks = hand_landmarks.landmark
            
            # 3. Finger Counting Logic (Sabse important!) 🖐️
            fingers_open = []
            
            # Index, Middle, Ring, aur Pinky fingers ke tips (8, 12, 16, 20)
            tip_ids = [8, 12, 16, 20]
            for tip in tip_ids:
                # Agar Tip ki Y value niche wale joint se kam hai (matlab screen par upar hai)
                if landmarks[tip].y < landmarks[tip - 2].y:
                    fingers_open.append(1)
                else:
                    fingers_open.append(0)

            # Thumb logic (X-axis use karte hain kyunki wo side mein move hota hai)
            if label == "Right":
                if landmarks[4].x < landmarks[3].x: fingers_open.append(1)
            else:
                if landmarks[4].x > landmarks[3].x: fingers_open.append(1)

            total_fingers = sum(fingers_open)

            # 4. Final Control Logic 💡
            # Right Hand + Open Palm (Hey) -> ON
            if label == "Right" and total_fingers >= 4:
                status_text = "HEY! LIGHT ON 💡"
                color = (0, 255, 0)
            # Left Hand -> OFF
            elif label == "Left":
                status_text = "BYE! LIGHT OFF 🌑"
                color = (0, 0, 255)
            else:
                status_text = f"Waiting... ({label})"
                color = (255, 255, 255)

            # Drawing Landmarks and Text
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            cv2.putText(frame, status_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
    cv2.imshow("Smart Mirror - Gesture Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()