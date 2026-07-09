import json
import time
from datetime import datetime, timezone
from typing import Dict, List

import requests

from hunk_utils import domain_from_url, env, normalize_text, path_for, save_json

BRAVE_API_KEY = env("BRAVE_SEARCH_API_KEY", required=True)
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

QUERIES = [
    {"category_hint": "crypto_markets", "q": "Bitcoin Ethereum Solana ETF inflows crypto regulation today Reuters Bloomberg CNBC"},
    {"category_hint": "ai_technology", "q": "AI technology breakthrough chip robot startup today Reuters AP The Verge"},
    {"category_hint": "science_space_nature", "q": "science space nature discovery today NASA NOAA AP Reuters"},
    {"category_hint": "animals_pets", "q": "viral animal pet wildlife rescue unusual today AP Reuters"},
    {"category_hint": "weird_global", "q": "unusual strange viral world news today AP Reuters"},
    {"category_hint": "major_world", "q": "major world news today Reuters AP BBC"},
    {"category_hint": "entertainment_culture", "q": "entertainment culture internet trend today Variety AP"},
    {"category_hint": "sports", "q": "major sports event today ESPN AP Reuters"},
]

PREFERRED_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "npr.org", "cnbc.com", "bloomberg.com",
    "theverge.com", "techcrunch.com", "espn.com", "nasa.gov", "noaa.gov", "variety.com"
}

BLOCKED_URL_WORDS = ["/live/", "live-updates", "tag/", "category/", "topics/", "latest", "homepage"]


def brave_search(query: str, category_hint: str, count: int = 8) -> List[Dict]:
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {
        "q": query,
        "count": count,
        "freshness": "pd",
        "text_decorations": False,
        "spellcheck": True,
    }
    response = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    results = response.json().get("web", {}).get("results", [])

    clean = []
    for item in results:
        url = item.get("url") or ""
        title = normalize_text(item.get("title"), 180)
        description = normalize_text(item.get("description"), 400)
        if not url or not title:
            continue
        if any(bad in url.lower() for bad in BLOCKED_URL_WORDS):
            continue
        clean.append({
            "category_hint": category_hint,
            "query": query,
            "title": title,
            "url": url,
            "domain": domain_from_url(url),
            "description": description,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })
    return clean


def collect_trends() -> List[Dict]:
    all_results: List[Dict] = []
    seen_urls = set()
    errors = []

    for q in QUERIES:
        try:
            results = brave_search(q["q"], q["category_hint"])
            for item in results:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    all_results.append(item)
        except Exception as exc:
            errors.append({"query": q["q"], "error": str(exc)})
        time.sleep(0.2)

    all_results.sort(key=lambda x: (x.get("domain") in PREFERRED_DOMAINS, x.get("title", "")), reverse=True)
    save_json(path_for("trend_results.json"), {"results": all_results, "errors": errors, "generated_at": datetime.now(timezone.utc).isoformat()})
    if not all_results:
        raise RuntimeError(f"No trend results collected. Errors: {errors}")
    return all_results


if __name__ == "__main__":
    print(json.dumps(collect_trends(), indent=2, ensure_ascii=False))
