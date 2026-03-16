import requests

API_KEY = "a0309b42617a40459170acb406e85e0c"

def get_news():
    url = (
        "https://newsapi.org/v2/top-headlines?"
        "country=us&apiKey=" + API_KEY
    )

    response = requests.get(url)
    data = response.json()

    print("RAW NEWS DATA:", data)   # 🔴 DEBUG LINE

    headlines = []

    if "articles" in data and len(data["articles"]) > 0:
        for article in data["articles"][:5]:
            headlines.append(article["title"])

    return headlines

if __name__ == "__main__":
    news = get_news()
    print("FINAL HEADLINES:", news)
