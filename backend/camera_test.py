import cv2

# DSHOW ki jagah MSMF try karein (Windows default)
# Index 1 humara USB camera hai
cap = cv2.VideoCapture(1, cv2.CAP_MSMF) 

if not cap.isOpened():
    print("MSMF nahi chala, bina backend ke try kar rahe hain...")
    cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("USB Camera se frame nahi aa raha. Cable check karein.")
        break

    # Full Screen ke liye
    cv2.imshow("USB Camera Output", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()