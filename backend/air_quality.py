import requests

def get_air_quality():
    try:
        API_KEY = "aa3d129b2eb7768c3bb58fdf17f69bc5"
        CITY = "Pune"

        url = (
            f"https://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat=19.0760&lon=72.8777&appid={API_KEY}"
        )

        response = requests.get(url, timeout=5)
        data = response.json()

        # 🔥 SAFETY CHECK
        if "list" not in data:
            print("⚠️ AQI data not available:", data)
            return "Unavailable", (150, 150, 150)

        aqi = data["list"][0]["main"]["aqi"]

        if aqi == 1:
            return "Good 😊", (0, 255, 0)
        elif aqi == 2:
            return "Fair 🙂", (100, 255, 100)
        elif aqi == 3:
            return "Moderate 😐", (0, 255, 255)
        elif aqi == 4:
            return "Poor 😷", (0, 165, 255)
        else:
            return "Very Poor ☠️", (0, 0, 255)

    except Exception as e:
        print("❌ AQI Error:", e)
        return "Unavailable", (150, 150, 150)
