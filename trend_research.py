import os
import requests

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

if not BRAVE_API_KEY:
    raise RuntimeError("BRAVE_SEARCH_API_KEY is missing")

queries = [
    "breaking global news today specific event site:reuters.com OR site:apnews.com",
    "bitcoin ethereum crypto regulation ETF today news",
    "viral animal pet story today unusual news",
    "today holiday observance national day social media",
    "technology AI science breakthrough today news",
]

headers = {
    "Accept": "application/json",
    "X-Subscription-Token": BRAVE_API_KEY,
}

for query in queries:
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params={
            "q": query,
            "count": 8,
            "freshness": "pd",
            "text_decorations": False,
        },
        timeout=30,
    )

    print("Status:", response.status_code)
    response.raise_for_status()

    results = response.json().get("web", {}).get("results", [])

    for i, item in enumerate(results, start=1):
        print(f"\n{i}. {item.get('title')}")
        print(item.get("url"))
        print(item.get("description"))
