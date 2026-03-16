import cv2

# MSMF backend try kar rahe hain
for i in range(3):
    print(f"Testing Index {i} with MSMF...")
    cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
    if cap.isOpened():
        print(f"✅ CAMERA FOUND AT INDEX {i}!")
        cap.release()
        break
    else:
        print(f"❌ Index {i} failed.")