import os
import json
import requests
from datetime import datetime, timezone


BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

if not BRAVE_API_KEY:
    raise RuntimeError("BRAVE_SEARCH_API_KEY is missing")


QUERIES = [
    "breaking news today Reuters AP",
    "trending news today Reuters AP",
    "major news happening now Reuters AP",
    "AI technology breaking news today",
    "crypto market news today bitcoin ethereum solana",
    "science space discovery today NASA Reuters",
    "unusual news today Reuters AP",
    "sports breaking news today ESPN AP",
    "entertainment culture trending news today AP",
]


def brave_search(query, count=10):
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
    data = response.json()
    results = data.get("web", {}).get("results", [])

    clean_results = []

    for item in results:
        clean_results.append({
            "query": query,
            "title": item.get("title") or "",
            "url": item.get("url") or "",
            "description": item.get("description") or "",
            "published_at": item.get("age") or "",
            "source": item.get("profile", {}).get("name") or "",
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })

    return clean_results


def dedupe_results(results):
    seen_urls = set()
    deduped = []

    for item in results:
        url = item.get("url")

        if not url:
            continue

        clean_url = url.split("?")[0].rstrip("/")

        if clean_url in seen_urls:
            continue

        seen_urls.add(clean_url)
        deduped.append(item)

    return deduped


def collect_trends():
    all_results = []

    for query in QUERIES:
        try:
            all_results.extend(brave_search(query))
        except Exception as e:
            print(f"Warning: Brave search failed for query '{query}': {e}")

    return dedupe_results(all_results)


if __name__ == "__main__":
    trends = collect_trends()
    print(json.dumps(trends, indent=2))
