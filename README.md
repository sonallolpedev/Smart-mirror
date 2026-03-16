# Advanced Smart Mirror v2.0

Features: Face Recognition · AI Voice Assistant · Emotion Detection · Weather · News · Calendar

## Required Packages

Install the dependencies:

```bash
pip install -r requirements.txt
```

Optional (for wake-word detection):
```bash
pip install pvporcupine
```

## Setup

1. Add your API keys in the CONFIG section of `smart_mirror_advanced.py`:
   - Weather API key from OpenWeatherMap
   - News API key from NewsAPI
   - OpenAI API key for GPT voice assistant

2. Register faces: run `python smart_mirror_advanced.py --register "Your Name"`
   - Stand in front of webcam, press SPACE to capture, ESC to finish.

3. Run normally: `python smart_mirror_advanced.py`

4. Say "Hey Mirror" (or press M) to activate voice assistant.

5. Press ESC to quit.

## Configuration

Edit the CONFIG dictionary in the code to customize:
- API keys
- Location and units
- Refresh intervals
- Display settings
- Face recognition settings
- Voice assistant settings
- User profiles and greetings

## Features

- **Face Recognition**: Recognizes registered users and provides personalized greetings.
- **Emotion Detection**: Analyzes facial expressions using DeepFace.
- **Voice Assistant**: Uses Google Speech Recognition and OpenAI GPT for responses.
- **Weather**: Displays current weather from OpenWeatherMap.
- **News**: Shows top headlines from NewsAPI.
- **Calendar**: Mini calendar with upcoming events.
- **Clock**: Real-time clock with date and season.

## Troubleshooting

- If camera doesn't work, change CAMERA_INDEX in CONFIG.
- Ensure all required packages are installed.
- For voice features, microphone access is needed.
- Face recognition requires registered faces via --register.