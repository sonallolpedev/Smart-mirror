import speech_recognition as sr

def listen_for_hello():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio).lower()
        print("You said:", text)
        return "hello" in text
    except:
        return False
