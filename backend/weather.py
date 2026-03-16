import requests
from location import get_city

API_KEY = "aa3d129b2eb7768c3bb58fdf17f69bc5"

def get_weather():
    city = get_city()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    temp = data["main"]["temp"]
    condition = data["weather"][0]["description"]

    return city, temp, condition

if __name__ == "__main__":
    city, t, c = get_weather()
    print("City:", city)
    print("Temperature:", t)
    print("Condition:", c)
