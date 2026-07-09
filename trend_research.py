import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

ALLOWED_CATEGORIES = [
    "science_technology",
    "ai",
    "pets_animals",
    "space",
    "world_weird",
    "cryptocurrency",
]

QUERIES = [
    {"q": "site:reuters.com science technology breakthrough discovery today", "category_hint": "science_technology"},
    {"q": "science discovery today researchers announced breakthrough", "category_hint": "science_technology"},
    {"q": "artificial intelligence news today announced AI model chip regulation startup", "category_hint": "ai"},
    {"q": "AI technology news today Reuters AP announced breakthrough", "category_hint": "ai"},
    {"q": "animal rescue unusual pet wildlife story today", "category_hint": "pets_animals"},
    {"q": "viral animal rescue wildlife unusual today", "category_hint": "pets_animals"},
    {"q": "space news today NASA SpaceX astronomy discovery scientists announced", "category_hint": "space"},
    {"q": "weird world news today unusual strange discovery rescued found", "category_hint": "world_weird"},
    {"q": "cryptocurrency news today bitcoin ethereum solana ETF regulation market", "category_hint": "cryptocurrency"},
]

BLOCKED_DOMAINS = {
    "espn.com", "www.espn.com", "draftkings.com", "fanduel.com",
    "pinterest.com", "www.pinterest.com", "instagram.com", "www.instagram.com",
    "x.com", "twitter.com", "youtube.com", "www.youtube.com",
}

PROMO_TERMS = [
    "anytime, anywhere", "live scores", "watch live", "stream", "streaming",
    "how to watch", "where to watch", "schedule", "tickets", "shop now",
    "download the app", "sign up", "subscribe", "homepage", "home page",
    "latest news and updates", "breaking news, video", "scores, highlights",
    "according to espn.com", "espn keeps fans", "service", "promo", "advertisement",
]

EVENT_VERBS = [
    "announced", "launched", "released", "unveiled", "discovered", "detected",
    "rescued", "found", "approved", "rejected", "sued", "agreed", "reported",
    "confirmed", "revealed", "warned", "raised", "cut", "surged", "fell",
    "opened", "closed", "landed", "arrived", "selected", "acquired", "built",
]

GENERIC_PHRASES = [
    "major breakthrough impacting global markets",
    "major ai technology breakthrough",
    "highlights a major",
    "keeps fans connected",
    "latest news",
    "top stories",
    "global markets",
    "live 2026 soccer scores",
]


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def normalize_text(value) -> str:
    value = "" if value is None else str(value)
    return re.sub(r"\s+", " ", value).strip()


def looks_promotional(title: str, description: str, url: str) -> bool:
    text = f"{title} {description} {url}".lower()
    domain = _domain(url)
    if domain in BLOCKED_DOMAINS:
        return True
    if any(term in text for term in PROMO_TERMS):
        return True
    if any(term in text for term in GENERIC_PHRASES):
        return True
    if re.search(r"/scores/?$|/watch/?$|/schedule/?$|/live/?$", url.lower()):
        return True
    return False


def has_event_signal(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    if any(term in text for term in GENERIC_PHRASES):
        return False
    return any(re.search(rf"\b{re.escape(v)}\b", text) for v in EVENT_VERBS)


def brave_search(query_obj, count=8):
    if not BRAVE_API_KEY:
        raise RuntimeError("BRAVE_SEARCH_API_KEY is missing")
    if isinstance(query_obj, str):
        query_obj = {"q": query_obj, "category_hint": "world_weird"}

    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params={
            "q": query_obj["q"],
            "count": count,
            "freshness": "pd",
            "text_decorations": False,
            "spellcheck": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    results = response.json().get("web", {}).get("results", []) or []

    clean = []
    for item in results:
        title = normalize_text(item.get("title"))
        desc = normalize_text(item.get("description"))
        url = normalize_text(item.get("url"))
        if not title or not url:
            continue
        clean.append({
            "query": query_obj["q"],
            "category_hint": query_obj.get("category_hint"),
            "title": title,
            "url": url,
            "domain": _domain(url),
            "description": desc,
            "age": item.get("age"),
            "discovered_at_utc": datetime.now(timezone.utc).isoformat(),
            "is_promotional": looks_promotional(title, desc, url),
            "has_event_signal": has_event_signal(title, desc),
        })
    return clean


def collect_trends():
    all_results = []
    errors = []
    seen = set()
    for q in QUERIES:
        try:
            for item in brave_search(q):
                key = item["url"].split("?")[0].rstrip("/")
                if key in seen:
                    continue
                seen.add(key)
                all_results.append(item)
        except Exception as exc:
            errors.append({"query": q["q"] if isinstance(q, dict) else str(q), "error": str(exc)})

    payload = {"results": all_results, "errors": errors}
    with open("trend_candidates.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    if not all_results and errors:
        raise RuntimeError(f"No trend results collected. Errors: {errors[:3]}")
    return all_results


if __name__ == "__main__":
    print(json.dumps(collect_trends(), indent=2))
