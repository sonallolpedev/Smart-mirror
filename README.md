# Smart Mirror

This project now includes:

- Desktop mirror mode (camera, voice, emotion) in `backend/smart_mirror.py`
- Web dashboard mode in `backend/web_app.py`

## Quick start (web dashboard)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/web_app.py
```

Open: `http://127.0.0.1:8000`

## New web features

- Time is served in Asia/Kolkata by default.
- Indian technology news is cached and refreshed daily.
- Camera-based motion detection is shown in the dashboard.
- Browser-based emotion detection is shown in the dashboard.
- Daily schedule can be customized and saved from the UI.

## Deploy on Vercel

This repo includes Vercel config in [vercel.json](vercel.json) and a serverless entrypoint at [api/index.py](api/index.py).

### Deploy from CLI

```bash
npx vercel
npx vercel --prod
```

### Vercel environment variables

Set these in Vercel Project Settings -> Environment Variables:

- MIRROR_TIMEZONE=Asia/Kolkata
- NEWS_API_KEY=83380b7809424dda92b69d3c3be6c014
- NEWS_COUNTRY=in
- OPENWEATHER_API_KEY=9f378b08dc0f4c5abc165816261603
- MIRROR_CITY=Pune,IN

## Optional environment settings

```bash
export MIRROR_TIMEZONE="Asia/Kolkata"
export NEWS_API_KEY="your_newsapi_key"
export NEWS_COUNTRY="in"
```

## Schedule storage

- Custom schedule is persisted to `backend/data/schedule.json`.
- You can edit this file manually or use the in-app schedule editor.

## Optional weather API

Set an environment variable for live weather data:

```bash
export OPENWEATHER_API_KEY="your_api_key"
export MIRROR_CITY="Pune,IN"
```

If no API key is set, the app serves fallback weather values.

## Desktop mode

`backend/smart_mirror.py` requires additional hardware-heavy packages (face recognition, deepface, speech stack) and webcam/mic support. It may not run in all containers.
