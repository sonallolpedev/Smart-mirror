import cv2
from vision_module import SmartMirrorVision

def test_vision():
    print("Initializing Vision Module... 🎭")
    vision = SmartMirrorVision()
    cap = cv2.VideoCapture(0)
    
    print("Camera opening... 📷")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Testing if process_frame hangs
        try:
            # Note: Using the old return style or new based on your current vision_module
            processed = vision.process_frame(frame)
            cv2.imshow("Vision Test", processed[0])
        except Exception as e:
            print(f"Error during processing: {e}")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_vision()