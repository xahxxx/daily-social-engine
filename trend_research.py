import os
import json
import requests

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

if not BRAVE_API_KEY:
    raise RuntimeError("BRAVE_SEARCH_API_KEY is missing")

QUERIES = [
    "bitcoin ethereum ETF inflows crypto regulation today",
    "viral animal pet story today unusual news",
    "global news today unusual major event Reuters AP",
    "today holiday national day social media observance",
    "AI technology breakthrough today news",
]

def brave_search(query, count=8):
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
    }

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params={
            "q": query,
            "count": count,
            "freshness": "pd",
            "text_decorations": False,
        },
        timeout=30,
    )

    response.raise_for_status()
    results = response.json().get("web", {}).get("results", [])

    clean_results = []
    for item in results:
        clean_results.append({
            "query": query,
            "title": item.get("title"),
            "url": item.get("url"),
            "description": item.get("description"),
        })

    return clean_results

def collect_trends():
    all_results = []
    for query in QUERIES:
        all_results.extend(brave_search(query))
    return all_results

if __name__ == "__main__":
    trends = collect_trends()
    print(json.dumps(trends, indent=2))
