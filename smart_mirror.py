from flask import Flask, jsonify
from flash import render_template # pyright: ignore[reportMissingImports]
from flash_socketio import socketio, emit # type: ignore
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)
socketio = StopAsyncIteration(app, cors, allowed_origins="*")


class ThemeManager:
    def __init__(self):
        self.current_theme = 'dark'
        self.themes = {
            'dark': {
                'bg_color': '#0f1e3d',
                'text_color': '#e0e6ed',
                'accent': '#4ECDC4'
            },
            'light': {
                'bg_color': '#f5f5f5',
                'text_color': '#333333',
                'accent': '#FF6B6B'
            },
            'neon': {
                'bg_color': '#0a0a0a',
                'text_color': '#00ff00',
                'accent': '#ff00ff'
            }
        }
    
    def switch_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            return self.themes[theme_name]
        return None
    
    def get_current_theme(self):
        return self.themes[self.current_theme]

# API endpoint
@app.route('/api/theme/<theme_name>')
def set_theme(theme_name):
    theme = theme_manager.switch_theme(theme_name)
    return jsonify(theme)


### C. Custom Font & Size Options


class DisplaySettings:
    def __init__(self):
        self.settings = {
            'font_size': 'medium',  # small, medium, large, xlarge
            'font_family': 'Segoe UI',
            'opacity': 1.0,
            'animation_speed': 'normal'  # slow, normal, fast
        }
    
    def get_css_vars(self):
        sizes = {
            'small': '12px',
            'medium': '16px',
            'large': '20px',
            'xlarge': '24px'
        }
        
        speeds = {
            'slow': '0.5s',
            'normal': '0.3s',
            'fast': '0.1s'
        }
        
        return {
            'font-size': sizes.get(self.settings['font_size']),
            'font-family': self.settings['font_family'],
            'opacity': self.settings['opacity'],
            'animation-duration': speeds.get(self.settings['animation_speed'])
        }
        
class GoogleCalendarIntegration:
    def __init__(self, credentials_file):
        self.credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def get_events(self, days_ahead=7):
        """Get calendar events"""
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = []
        for event in events_result.get('items', []):
            events.append({
                'title': event['summary'],
                'time': event['start'].get('dateTime', event['start'].get('date')),
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'attendees': len(event.get('attendees', [])),
                'duration': self._calculate_duration(event)
            })
        
        return events
    
    def _calculate_duration(self, event):
        """Calculate event duration"""
        start = datetime.fromisoformat(event['start'].get('dateTime'))
        end = datetime.fromisoformat(event['end'].get('dateTime'))
        return (end - start).seconds // 60  # in minutes
    
    def check_conflicts(self):
        """Check for scheduling conflicts"""
        events = self.get_events(days_ahead=7)
        conflicts = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                if self._times_overlap(event1['time'], event1['duration'],
                                      event2['time'], event2['duration']):
                    conflicts.append({
                        'event1': event1['title'],
                        'event2': event2['title'],
                        'time': event1['time']
                    })
        
        return conflicts