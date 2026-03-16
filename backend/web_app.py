from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__, static_folder="static", template_folder="templates")

TIMEZONE = os.getenv("MIRROR_TIMEZONE", "Asia/Kolkata")
NEWS_REFRESH_SECONDS = 86400
DATA_DIR = Path(__file__).parent / "data"
SCHEDULE_FILE = DATA_DIR / "schedule.json"

NEWS_TOPICS = {"technology", "sports", "business"}

_news_cache: Dict[str, Dict[str, Any]] = {}

DEFAULT_SCHEDULE: Dict[str, List[str]] = {
    "Monday": [
        "07:00 Morning workout",
        "10:30 Project standup",
        "20:00 Family time",
    ],
    "Tuesday": [
        "08:00 Plan weekly priorities",
        "12:30 Lunch break",
        "18:30 Read for 30 minutes",
    ],
    "Wednesday": [
        "07:30 Stretch and mobility",
        "11:00 Client follow-up",
        "21:00 Next-day prep",
    ],
    "Thursday": [
        "08:30 Deep work block",
        "14:00 Team sync",
        "19:00 Walk and unwind",
    ],
    "Friday": [
        "09:00 Weekly review",
        "15:30 Cleanup outstanding tasks",
        "20:30 Movie night",
    ],
    "Saturday": [
        "08:00 Personal errands",
        "12:00 Lunch with friends",
        "17:00 Hobby session",
    ],
    "Sunday": [
        "09:00 Slow morning",
        "16:00 Plan upcoming week",
        "20:00 Early rest",
    ],
}


def _weather_payload() -> Dict[str, Any]:
    city = os.getenv("MIRROR_CITY", "Pune,IN")
    api_key = os.getenv("OPENWEATHER_API_KEY", "9f378b08dc0f4c5abc165816261603")

    if not api_key:
        return {
            "city": city,
            "temp_c": 26,
            "condition": "Partly Cloudy",
            "source": "fallback",
        }

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        response = requests.get(
            url,
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "city": f"{data.get('name', city)}",
            "temp_c": round(data["main"]["temp"]),
            "condition": data["weather"][0]["description"].title(),
            "source": "openweather",
        }
    except Exception:
        return {
            "city": city,
            "temp_c": 26,
            "condition": "Unavailable",
            "source": "fallback",
        }


def _news_payload(topic: str = "technology") -> Dict[str, Any]:
    topic = topic.lower().strip()
    if topic not in NEWS_TOPICS:
        topic = "technology"

    api_key = os.getenv("NEWS_API_KEY", "83380b7809424dda92b69d3c3be6c014")
    country = os.getenv("NEWS_COUNTRY", "in")
    fallback_by_topic: Dict[str, List[str]] = {
        "technology": [
            "AI tools improve productivity in daily workflows.",
            "Cloud and edge computing adoption continues to rise.",
            "Cybersecurity investments are increasing globally.",
            "Startups focus on practical automation use-cases.",
        ],
        "sports": [
            "Major leagues announce updated season fixtures.",
            "Athletes focus on data-driven performance training.",
            "International tournaments draw strong fan turnout.",
            "Clubs continue investing in youth development.",
        ],
        "business": [
            "Markets react to fresh quarterly earnings reports.",
            "SMEs increase digital adoption for operations.",
            "Global trade discussions continue across regions.",
            "Investors track inflation and rate outlook updates.",
        ],
    }
    fallback = fallback_by_topic[topic]

    cache_entry = _news_cache.get(topic, {})

    # Serve from cache for one day; fetch from internet daily.
    now = dt.datetime.now(dt.UTC)
    cached_at = cache_entry.get("cached_at")
    if cached_at and (now - cached_at).total_seconds() < NEWS_REFRESH_SECONDS:
        return {
            "topic": topic,
            "headlines": cache_entry.get("headlines", fallback),
            "source": cache_entry.get("source", "fallback"),
            "cached": True,
            "next_refresh_in_seconds": int(NEWS_REFRESH_SECONDS - (now - cached_at).total_seconds()),
        }

    if not api_key:
        _news_cache[topic] = {
            "headlines": fallback,
            "source": "fallback",
            "cached_at": now,
        }
        return {"topic": topic, "headlines": fallback, "source": "fallback", "cached": False}

    try:
        url = "https://newsapi.org/v2/top-headlines"
        response = requests.get(
            url,
            params={
                "country": country,
                "category": topic,
                "apiKey": api_key,
                "pageSize": 6,
            },
            timeout=10,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
        headlines = [
            a.get("title", "")
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
        payload = {
            "topic": topic,
            "headlines": headlines[:6] if headlines else fallback,
            "source": "newsapi",
            "cached": False,
        }
        _news_cache[topic] = {
            "headlines": payload["headlines"],
            "source": payload["source"],
            "cached_at": now,
        }
        return payload
    except Exception:
        _news_cache[topic] = {
            "headlines": fallback,
            "source": "fallback",
            "cached_at": now,
        }
        return {"topic": topic, "headlines": fallback, "source": "fallback", "cached": False}


def _load_schedule_from_file() -> Dict[str, List[str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as handle:
            json.dump(DEFAULT_SCHEDULE, handle, indent=2)
        return dict(DEFAULT_SCHEDULE)

    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            clean: Dict[str, List[str]] = {}
            for day, items in loaded.items():
                if isinstance(day, str) and isinstance(items, list):
                    clean[day] = [str(x) for x in items]
            return clean or dict(DEFAULT_SCHEDULE)
    except Exception:
        pass
    return dict(DEFAULT_SCHEDULE)


def _save_schedule_to_file(schedule: Dict[str, List[str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as handle:
        json.dump(schedule, handle, indent=2)


def _schedule_payload() -> Dict[str, Any]:
    tz = ZoneInfo(TIMEZONE)
    today = dt.datetime.now(tz).strftime("%A")
    schedule = _load_schedule_from_file()
    daily_tasks = schedule.get(today, [])
    return {
        "day": today,
        "items": daily_tasks,
        "source": "custom-file",
        "timezone": TIMEZONE,
    }


@app.get("/")
def home() -> str:
    return render_template("index.html")


@app.get("/api/status")
def status() -> Any:
    return jsonify({
        "service": "smart-mirror-web",
        "ok": True,
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
    })


@app.get("/api/time")
def api_time() -> Any:
    tz = ZoneInfo(TIMEZONE)
    now = dt.datetime.now(tz)
    return jsonify({
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%A, %d %B %Y"),
        "timezone": TIMEZONE,
    })


@app.get("/api/weather")
def api_weather() -> Any:
    return jsonify(_weather_payload())


@app.get("/api/news")
def api_news() -> Any:
    from flask import request

    topic = request.args.get("topic", "technology")
    return jsonify(_news_payload(topic))


@app.get("/api/schedule")
def api_schedule() -> Any:
    return jsonify(_schedule_payload())


@app.get("/api/schedule/all")
def api_schedule_all() -> Any:
    return jsonify({
        "schedule": _load_schedule_from_file(),
        "timezone": TIMEZONE,
    })


@app.post("/api/schedule")
def api_schedule_update() -> Any:
    from flask import request

    payload = request.get_json(silent=True) or {}
    day = str(payload.get("day", "")).strip()
    items = payload.get("items", [])

    if not day:
        return jsonify({"ok": False, "error": "Missing day"}), 400
    if not isinstance(items, list):
        return jsonify({"ok": False, "error": "items must be a list"}), 400

    schedule = _load_schedule_from_file()
    schedule[day] = [str(x).strip() for x in items if str(x).strip()]
    _save_schedule_to_file(schedule)

    return jsonify({"ok": True, "day": day, "items": schedule[day]})


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
