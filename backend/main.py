import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import numpy as np
import threading
import time
import requests
from PIL import ImageFont, ImageDraw, Image

# Modules
from vision_module import SmartMirrorVision
from voice_module import SmartMirrorVoice
from dashboard_module import MirrorDashboard

# Comment Arduino temporarily if causing issues
try:
    from light_controller import ArduinoLightController
    ARDUINO_AVAILABLE = True
except:
    ARDUINO_AVAILABLE = False


# ---------------- CONFIG ----------------
API_KEY = "aa3d129b2eb7768c3bb58fdf17f69bc5"
FONT_PATH = "C:/Windows/Fonts/arial.ttf"
GREEN_COLOR = (0, 255, 0)
FONT_SIZE = 24

CAMERA_INDEX = 1   # Your External USB Camera
# ----------------------------------------


def draw_text_green(img, text, pos, size=FONT_SIZE):
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    try:
        font = ImageFont.truetype(FONT_PATH, size)
    except:
        font = ImageFont.load_default()

    draw.text(pos, text, font=font, fill=GREEN_COLOR)
    return np.array(img_pil)


def fetch_news(api_key):
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={api_key}"
        res = requests.get(url).json()
        articles = res.get('articles', [])
        return [a['title'][:50] + "..." for a in articles[:4]]
    except:
        return ["News currently unavailable"]


def start_mirror():

    # -------- CAMERA FIRST (IMPORTANT) --------
    print("Opening External USB Camera...")

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_MSMF)

    if not cap.isOpened():
        print("MSMF failed. Trying without backend...")
        cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("USB Camera not accessible. Check connection.")
        return

    print("USB Camera Connected Successfully.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    # ------------------------------------------

    # Initialize modules AFTER camera success
    vision = SmartMirrorVision()
    voice = SmartMirrorVoice()
    dashboard = MirrorDashboard(API_KEY)

    if ARDUINO_AVAILABLE:
        try:
            light_controller = ArduinoLightController()
        except:
            light_controller = None
            print("Arduino not found. LED control disabled.")
    else:
        light_controller = None

    voice.start()

    # Fullscreen Window
    win_name = "Smart Mirror Dashboard"
    cv2.namedWindow(win_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    mood, v_light, gesture = "Detecting...", "OFF", "None"
    current_light_state = "OFF"
    frame_count = 0
    latest_news = ["Fetching news..."]
    last_news_update = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame not received from USB Camera.")
            break

        frame = cv2.flip(frame, 1)
        frame_count += 1

        # AI processing every 5 frames
        if frame_count % 5 == 0:
            try:
                res = vision.process_frame(frame)
                _, mood, v_light, trend, gesture = res

                if voice.light_command:
                    current_light_state = voice.light_command
                    if light_controller:
                        light_controller.set_led(current_light_state)
                    voice.light_command = None

            except:
                pass

        # News update every 10 minutes
        if time.time() - last_news_update > 600:
            def update_news():
                nonlocal latest_news, last_news_update
                latest_news = fetch_news(API_KEY)
                last_news_update = time.time()

            threading.Thread(target=update_news, daemon=True).start()

        # Dark overlay
        overlay = np.zeros_like(frame)
        frame = cv2.addWeighted(frame, 0.4, overlay, 0.6, 0)

        curr_date, curr_time = dashboard.get_date_time()

        # Left Panel
        frame = draw_text_green(frame, "SYSTEM: ONLINE", (50, 50))
        frame = draw_text_green(frame, f"TIME: {curr_time}", (50, 90))
        frame = draw_text_green(frame, f"DATE: {curr_date}", (50, 130))

        frame = draw_text_green(frame, f"MOOD: {mood.upper()}", (50, 220))
        frame = draw_text_green(frame, f"GESTURE: {gesture}", (50, 260))
        frame = draw_text_green(frame, f"LIGHT: {current_light_state}", (50, 300))

        # Right Panel
        x_right = 750
        frame = draw_text_green(frame, "--- LATEST NEWS ---", (x_right, 50))

        for i, news in enumerate(latest_news):
            frame = draw_text_green(frame, f"> {news}", (x_right, 100 + (i * 45)))

        cv2.imshow(win_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if light_controller:
        try:
            light_controller.close()
        except:
            pass


if __name__ == "__main__":
    start_mirror()