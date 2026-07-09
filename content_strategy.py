import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from trend_research import collect_trends, has_event_signal, looks_promotional

ALLOWED_CATEGORIES = [
    "science_technology",
    "ai",
    "pets_animals",
    "space",
    "world_weird",
    "cryptocurrency",
]

CATEGORY_KEYWORDS = {
    "cryptocurrency": ["bitcoin", "btc", "ethereum", "eth", "solana", "crypto", "blockchain", "token", "etf", "stablecoin"],
    "ai": ["artificial intelligence", " ai ", "openai", "anthropic", "deepmind", "nvidia", "chip", "llm", "robot", "model"],
    "space": ["space", "nasa", "spacex", "rocket", "mars", "moon", "asteroid", "satellite", "astronomy", "planet"],
    "pets_animals": ["dog", "cat", "pet", "animal", "wildlife", "zoo", "rescue", "rescued", "bear", "whale", "eagle", "turtle"],
    "science_technology": ["science", "scientists", "researchers", "study", "discovery", "breakthrough", "technology", "quantum", "battery", "fusion", "medical device"],
    "world_weird": ["weird", "strange", "unusual", "mystery", "found", "rescued", "rare", "record", "bizarre"],
}

BLOCKED_SUBJECTS = ["espn", "sports fan", "live scores", "streaming", "watch live", "celebrity", "horoscope"]
PUBLISHER_NAMES = ["reuters", "ap", "associated press", "bbc", "cnn", "cnbc", "the verge", "techcrunch", "yahoo"]
VAGUE_TERMS = ["major breakthrough", "impacting global markets", "latest news", "top stories", "keeps fans connected"]

VISUAL_TERMS = ["rare", "first", "record", "rescued", "discovered", "unveiled", "launched", "detected", "mystery", "surge"]


def _text(item):
    return f"{item.get('title','')} {item.get('description','')}".lower()


def detect_category(item):
    if item.get("category_hint") in ALLOWED_CATEGORIES:
        return item["category_hint"]
    text = f" {_text(item)} "
    scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "world_weird"


def validate_candidate(item):
    title = item.get("title", "")
    desc = item.get("description", "")
    url = item.get("url", "")
    text = f"{title} {desc}".lower()
    reasons = []

    if not url.startswith("http"):
        return False, ["missing valid url"]
    if looks_promotional(title, desc, url):
        return False, ["promotional/evergreen/service page"]
    if any(b in text for b in BLOCKED_SUBJECTS):
        return False, ["blocked subject/service content"]
    if any(v in text for v in VAGUE_TERMS):
        return False, ["vague non-specific news language"]
    if not has_event_signal(title, desc):
        return False, ["no concrete event verb/action"]
    if len(title.split()) < 5:
        return False, ["title too thin"]
    if len(desc.split()) < 10:
        reasons.append("thin snippet")

    # Publisher can be source, but not the story subject.
    first_words = " ".join(title.lower().split()[:3])
    if any(first_words.startswith(p) for p in PUBLISHER_NAMES):
        return False, ["publisher treated as story subject"]
    return True, reasons or ["passes event gate"]


def score_result(item):
    valid, gate_reasons = validate_candidate(item)
    category = detect_category(item)
    if not valid:
        return -999, gate_reasons, category

    text = _text(item)
    score = 20
    reasons = list(gate_reasons)
    for term in VISUAL_TERMS:
        if term in text:
            score += 4
            reasons.append(f"visual/event hook: {term}")
    if item.get("age"):
        score += 5
        reasons.append("fresh result age present")
    if item.get("domain") in {"reuters.com", "apnews.com", "nasa.gov", "science.nasa.gov"}:
        score += 5
        reasons.append("reputable source boost")
    if category in ALLOWED_CATEGORIES:
        score += 6
        reasons.append(f"allowed category: {category}")
    return score, reasons[:12], category


def build_concepts(max_concepts=8):
    trends = collect_trends()
    concepts = []
    rejects = []
    for item in trends:
        score, reasons, category = score_result(item)
        if score < 20:
            rejects.append({"title": item.get("title"), "url": item.get("url"), "score": score, "reasons": reasons})
            continue
        concepts.append({
            "score": score,
            "category": category,
            "source_title": item.get("title"),
            "source_url": item.get("url"),
            "source_domain": item.get("domain"),
            "source_summary": item.get("description"),
            "source_age": item.get("age"),
            "why_selected": reasons,
            "news_event_gate": "PASSED: specific recent event/action detected; not promotional evergreen content",
        })
    concepts.sort(key=lambda c: c["score"], reverse=True)
    with open("concept_selection_debug.json", "w", encoding="utf-8") as f:
        json.dump({"selected": concepts[:max_concepts], "rejected_sample": rejects[:30]}, f, indent=2)
    if not concepts:
        raise RuntimeError("No valid news-event concepts found. Check concept_selection_debug.json for rejected candidates.")
    return concepts[:max_concepts]


if __name__ == "__main__":
    print(json.dumps(build_concepts(), indent=2))
