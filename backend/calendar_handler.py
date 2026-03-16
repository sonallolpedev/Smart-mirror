import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Purana: readonly | Naya: full calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendar:
    def __init__(self):
        self.creds = None
        self.service = None
        
        # 1. token.json check karein
        if os.path.exists('token.json'):
            print("🔄 token.json mil gaya. Loading...")
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # 2. Agar token nahi hai ya invalid hai toh login karein
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("⏳ Token expire ho gaya hai, refresh kar raha hoon...")
                try:
                    self.creds.refresh(Request())
                except:
                    self.perform_login()
            else:
                self.perform_login()
            
            # Token save karein
            if self.creds:
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
                    print("✅ Naya token.json save ho gaya!")

        # 3. API Service banayein
        if self.creds:
            try:
                self.service = build('calendar', 'v3', credentials=self.creds)
                print("🚀 Google Calendar Service Ready!")
            except Exception as e:
                print(f"❌ Service Error: {e}")

    def perform_login(self):
        print("🔑 Login window open ho rahi hai...")
        if not os.path.exists('credentials.json'):
            print("❌ ERROR: 'credentials.json' file backend folder mein nahi hai!")
            return
        try:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            self.creds = flow.run_local_server(port=0)
        except Exception as e:
            print(f"❌ Login process fail: {e}")

    def get_today_events(self):
        if not self.service:
            return ["Calendar Offline"]
        try:
            # Aaj ka time (UTC)
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            print("📅 Events fetch ho rahe hain...")
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=5, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            if not events:
                return ["No events found today"]
            
            formatted = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Time format (02:30 PM)
                if 'T' in start:
                    dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_str = dt.strftime("%I:%M %p")
                else:
                    time_str = "All Day"
                
                formatted.append(f"{time_str} - {event.get('summary', 'Event')}")
            return formatted
        except Exception as e:
            print(f"❌ Sync Error: {e}")
            return ["Sync Error"]

# --- TEST CODE ---
if __name__ == "__main__":
    print("--- Testing Google Calendar ---")
    cal = GoogleCalendar()
    events = cal.get_today_events()
    print("\nTODAY'S SCHEDULE:")
    for ev in events:
        print(f"• {ev}")