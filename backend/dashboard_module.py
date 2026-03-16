import requests
import datetime
import feedparser

class MirrorDashboard:
    
    def __init__(self, weather_api_key, news_api_key=None):
        self.weather_api_key = weather_api_key
        self.news_api_key = news_api_key or weather_api_key
        
        # Default values
        self.location = "Pune"
        self.lat = None
        self.lon = None

        # Initial fetch
        self.update_location()

    def update_location(self):
        """IP-based real-time location detection"""
        try:
            # timeout ko 10s rakha hai taaki network slow hone par crash na ho
            r = requests.get("http://ip-api.com/json", timeout=10).json()
            if r.get("status") == "success":
                self.location = r.get("city")
                self.lat = r.get("lat")
                self.lon = r.get("lon")
                print(f"📍 Real-time Location: {self.location}")
                return True
        except Exception as e:
            print(f"Location Error: {e}")
        return False

    def get_season(self):
        month = datetime.datetime.now().month
        if month in [12, 1, 2]: return "Winter ❄️"
        elif month in [3, 4, 5, 6]: return "Summer ☀️"
        elif month in [7, 8, 9]: return "Monsoon 🌧️"
        else: return "Autumn 🍂"

    def get_weather_and_aqi(self):
        """Weather aur AQI dono fetch karta hai coordinates use karke"""
        try:
            # 1. Weather Fetch
            if self.lat and self.lon:
                w_url = f"http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.weather_api_key}&units=metric"
            else:
                w_url = f"http://api.openweathermap.org/data/2.5/weather?q={self.location}&appid={self.weather_api_key}&units=metric"
            
            w_res = requests.get(w_url, timeout=5).json()
            
            if w_res.get("cod") != 200: 
                return None

            temp = round(w_res['main']['temp'])
            desc = w_res['weather'][0]['description'].title()
            
            # 2. AQI Fetch (Coordinates se accurate milta hai)
            lat, lon = w_res['coord']['lat'], w_res['coord']['lon']
            aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={self.weather_api_key}"
            aqi_res = requests.get(aqi_url, timeout=5).json()
            aqi_num = aqi_res['list'][0]['main']['aqi'] 

            aqi_map = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
            
            return {
                "location": self.location,
                "temp": f"{temp}°C", 
                "desc": desc, 
                "aqi": aqi_map.get(aqi_num, "Unknown"),
                "season": self.get_season()
            }
        except Exception as e:
            print(f"Weather Error: {e}")
            return None

    def get_news_headlines(self):
        """Google News RSS Feed (Fast and No-Key)"""
        try:
            url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(url)
            headlines = []
            for entry in feed.entries[:5]:
                # "Title - Source" se source hatana
                title = entry.title.split(' - ')[0] 
                headlines.append(title)
            return headlines
        except:
            return ["Unable to fetch news"]

    def get_calendar_events(self):
        """Google Calendar Handler se connect karke events lata hai"""
        try:
            from calendar_handler import GoogleCalendar
            cal = GoogleCalendar()
            events = cal.get_today_events() # Yeh list of strings return karega
            
            if not events:
                return ["No events today"]
                
            # Agar list mein pehla element error message hai
            if events[0] in ["Calendar Error", "Sync Error", "Auth Pending..."]:
                return events

            return events[:4] # Top 4 events return karein
        except Exception as e:
            print(f"Dashboard Calendar Error: {e}")
            return ["Calendar Sync Error"]