# Smart Mirror Application - Setup & Usage Guide

## Overview
A Python-based smart mirror application that displays time, date, weather, calendar events, and AI-generated reflections. Perfect for home automation and personal dashboards.

## Features

✨ **Real-Time Display**
- Live clock with hour:minute format
- Current date and day of week
- Auto-updating every second

🌤️ **Weather Integration**
- Current temperature and weather conditions
- Location-based forecasting
- Emoji weather indicators
- Humidity, wind speed, and "feels like" data

📅 **Calendar Integration**
- Daily schedule display
- Event time and duration
- Event categorization (personal, work, etc.)
- Support for Google Calendar (with setup)

🤖 **AI Reflections**
- Claude-powered daily reflections
- Inspirational and motivational quotes
- Contextual wisdom based on time of day
- Cached reflections for efficiency

📍 **Location Services**
- Current location display
- Searchable location updates
- Weather tied to location
- Support for latitude/longitude coordinates

## Installation

### 1. Clone/Setup
```bash
cd smart-mirror
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:

```env
# Required for AI Reflections
ANTHROPIC_API_KEY=sk-ant-...

# Optional for Weather API (uses demo data if not provided)
OPENWEATHER_API_KEY=your_api_key_here

# Optional for Google Calendar Integration
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
```

### 4. Get API Keys

**Anthropic API Key:**
- Visit https://console.anthropic.com
- Create a new API key
- Add to `.env` file

**OpenWeather API Key (Optional):**
- Visit https://openweathermap.org/api
- Sign up for free tier
- Create API key
- Add to `.env` file

**Google Calendar (Optional Setup):**
- Enable Google Calendar API in Google Cloud Console
- Create service account credentials
- Download credentials JSON
- Place in project directory

## Running the Application

```bash
python smart_mirror.py
```

The application will start on `http://localhost:5000`

## API Endpoints

- `GET /` - Main smart mirror interface
- `GET /api/data` - All dashboard data
- `GET /api/time` - Current time and date
- `GET /api/weather` - Weather information
- `GET /api/calendar` - Calendar events
- `GET /api/reflection` - Daily reflection
- `POST /api/location` - Update location

## Project Structure

```
smart-mirror/
├── smart_mirror.py          # Main Flask application
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── credentials.json          # Google Calendar (optional)
└── README.md                # This file
```

## Customization

### Change Default Location
Edit in `smart_mirror.py`:
```python
DEFAULT_LOCATION = {
    'lat': 18.5204,
    'lon': 73.8567,
    'city': 'Pune',
    'country': 'India'
}
```

### Change Timezone
Edit in `smart_mirror.py`:
```python
TIMEZONE = 'Asia/Kolkata'
```

### Modify Calendar Events
In `SmartMirror.get_calendar_events()`:
```python
demo_events = [
    {
        'title': 'Your Event',
        'time': 'HH:MM',
        'duration': minutes,
        'type': 'work' or 'personal'
    }
]
```

### Custom Reflections
Modify the `generate_reflection()` method to customize AI prompts.

## Advanced Features

### Google Calendar Integration
Uncomment the calendar integration code in `get_calendar_events()`:
```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
```

### Real Weather Data
Uncomment the weather API call in `get_weather()` and ensure `OPENWEATHER_API_KEY` is set.

### Database Integration
Extend `SmartMirror` class to connect to databases for persistent event logging.

### Camera Integration
Add OpenCV/PyCamera for motion detection and face recognition.

## Troubleshooting

**Port Already in Use:**
```bash
python smart_mirror.py --port 5001
```

**API Connection Errors:**
- Check internet connection
- Verify API keys in `.env`
- Check API rate limits

**Missing Dependencies:**
```bash
pip install -r requirements.txt --upgrade
```

**Module Not Found:**
- Ensure virtual environment is activated
- Reinstall with `pip install -r requirements.txt`

## Performance Tips

1. Adjust refresh intervals (default 5 minutes):
   - Edit `setInterval(fetchDashboardData, 300000)` in HTML

2. Limit calendar events:
   - Adjust `days_ahead` parameter in `get_calendar_events()`

3. Cache weather data:
   - Implement Redis for distributed caching

4. Optimize UI:
   - Run in production mode: Remove `debug=True`

## Future Enhancements

- 🎥 Camera feed with face recognition
- 🔔 Notification system
- 🎵 Music player integration
- 📊 Health/Fitness data
- 🌙 Night mode with low brightness
- 🔐 Authentication and multi-user support
- 📱 Mobile companion app
- 💬 Voice control integration

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation
3. Check application logs
4. Verify environment variables

---

**Happy Mirroring! 🪞✨**
