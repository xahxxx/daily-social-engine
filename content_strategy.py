import json
import random
import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from hunk_utils import load_json, path_for, save_json
from trend_research import collect_trends

CATEGORY_ORDER = [
    "science_technology",
    "ai",
    "cryptocurrency",
    "pets_animals",
    "space",
    "world_weird",
    
]

CATEGORY_TERMS = {
    "animals_pets": ["dog", "cat", "pet", "animal", "wildlife", "zoo", "eagle", "bear", "whale", "shark", "rescue"],
    "crypto_markets": ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "etf", "solana", "xrp", "token", "blockchain"],
    "ai_technology": ["ai", "artificial intelligence", "chip", "robot", "semiconductor", "technology", "openai", "nvidia", "startup"],
    "science_space_nature": ["nasa", "space", "mars", "moon", "planet", "science", "discovery", "climate", "volcano", "earthquake", "ocean"],
    "sports": ["nba", "nfl", "mlb", "nhl", "soccer", "world cup", "olympic", "tennis", "golf", "sports", "final"],
    "entertainment_culture": ["movie", "music", "celebrity", "festival", "culture", "internet", "streaming", "box office"],
    "weird_global": ["unusual", "strange", "weird", "viral", "mystery", "found", "rescued", "rare"],
}

GENERIC_TERMS = ["latest news", "top stories", "home", "live updates", "news today", "breaking news"]
SENSITIVE_TERMS = ["death", "killed", "fatal", "shooting", "attack", "war", "funeral", "massacre", "abuse"]
VISUAL_TERMS = ["rare", "first", "record", "historic", "giant", "tiny", "rescued", "mystery", "breakthrough", "surge", "robot", "discovery"]
TRUSTED_DOMAINS = {"reuters.com", "apnews.com", "bbc.com", "npr.org", "cnbc.com", "bloomberg.com", "nasa.gov", "noaa.gov", "espn.com"}


def detect_category(item: Dict) -> str:
    text = f"{item.get('category_hint', '')} {item.get('title', '')} {item.get('description', '')}".lower()
    for category, terms in CATEGORY_TERMS.items():
        if any(term in text for term in terms):
            return category
    return item.get("category_hint") or "major_world"


def score_result(item: Dict, target_category: str, last_category: str = "") -> Tuple[int, List[str], str]:
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    domain = item.get("domain", "")
    category = detect_category(item)
    score = 0
    reasons = []

    if domain in TRUSTED_DOMAINS:
        score += 8
        reasons.append(f"trusted source: {domain}")
    elif domain:
        score += 2
        reasons.append(f"source: {domain}")

    if category == target_category:
        score += 8
        reasons.append(f"daily rotation boost: {target_category}")
    if category == last_category:
        score -= 7
        reasons.append(f"repeat category penalty: {last_category}")

    category_boosts = {
        "animals_pets": 10,
        "weird_global": 9,
        "ai_technology": 8,
        "science_space_nature": 8,
        "crypto_markets": 7,
        "sports": 6,
        "entertainment_culture": 5,
        "major_world": 4,
    }
    score += category_boosts.get(category, 4)
    reasons.append(f"category: {category}")

    for term in VISUAL_TERMS:
        if term in text:
            score += 3
            reasons.append(f"visual hook: {term}")

    for term in GENERIC_TERMS:
        if term in text:
            score -= 9
            reasons.append(f"generic result: {term}")

    for term in SENSITIVE_TERMS:
        if term in text:
            score -= 8
            reasons.append(f"sensitive topic: {term}")

    if re.search(r"\b\d+(?:\.\d+)?%|\$\d+|\b\d{3,}\b", text):
        score += 2
        reasons.append("contains concrete detail")

    return score, reasons[:12], category


def choose_target_category() -> str:
    state = load_json(path_for("hunk_mao_state.json"), default={})
    last_category = state.get("last_category", "")
    day_index = datetime.now(timezone.utc).timetuple().tm_yday
    ordered = CATEGORY_ORDER[day_index % len(CATEGORY_ORDER):] + CATEGORY_ORDER[:day_index % len(CATEGORY_ORDER)]
    for category in ordered:
        if category != last_category:
            return category
    return ordered[0]


def build_concepts(limit: int = 6) -> List[Dict]:
    trends = collect_trends()
    state = load_json(path_for("hunk_mao_state.json"), default={})
    target_category = choose_target_category()
    last_category = state.get("last_category", "")
    concepts = []

    for item in trends:
        score, reasons, category = score_result(item, target_category, last_category)
        if score < 8:
            continue
        title = item.get("title", "Untitled")
        description = item.get("description", "")
        concepts.append({
            "score": score,
            "category": category,
            "target_category_today": target_category,
            "last_category": last_category,
            "source_title": title,
            "source_url": item.get("url"),
            "source_domain": item.get("domain"),
            "source_summary": description,
            "collected_at": item.get("collected_at"),
            "why_selected": reasons,
            "post_angle": f"Turn this real news item into a funny cinematic Hunk Mao visual metaphor: {title}",
        })

    concepts.sort(key=lambda x: x["score"], reverse=True)
    # Deterministic: never randomly replace the strongest verified story with a weaker candidate.
    final = concepts[:limit]
    save_json(path_for("selected_concepts.json"), final)
    if not final:
        raise RuntimeError("No usable concepts survived scoring. Check trend_results.json for raw results.")
    return final


if __name__ == "__main__":
    print(json.dumps(build_concepts(), indent=2, ensure_ascii=False))
