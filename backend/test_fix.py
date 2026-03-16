import mediapipe as mp
try:
    print(f"Mediapipe Version: {mp.__version__}")
    # Check if solutions exists
    if hasattr(mp, 'solutions'):
        print("Success! 'solutions' attribute mil gaya. ✅")
    else:
        print("Abhi bhi 'solutions' nahi mil raha hai. ❌")
except Exception as e:
    print(f"Error: {e}")