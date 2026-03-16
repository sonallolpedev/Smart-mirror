import requests
from ics import Calendar
from datetime import datetime

CALENDAR_URL = "https://calendar.google.com/calendar/embed?src=dhanumeshram16%40gmail.com&ctz=UTC"

def get_today_events():
    try:
        response = requests.get(CALENDAR_URL)
        calendar = Calendar(response.text)

        today = datetime.now().date()
        events_today = []

        for event in calendar.events:
            if event.begin.date() == today:
                events_today.append(
                    f"{event.begin.strftime('%H:%M')} - {event.name}"
                )

        if not events_today:
            return ["No events today"]

        return events_today[:3]   # max 3 events

    except:
        return ["Calendar not available"]
