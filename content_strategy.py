import json
import random
from datetime import datetime
from trend_research import collect_trends


CATEGORY_ORDER = [
    "animals_pets",
    "crypto_markets",
    "ai_technology",
    "holidays_seasonal",
    "weird_global",
    "major_world",
]


def detect_category(item):
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()

    if any(w in text for w in ["dog", "cat", "pet", "animal", "wildlife", "elephant", "eagle"]):
        return "animals_pets"

    if any(w in text for w in ["bitcoin", "ethereum", "crypto", "etf", "xrp", "solana", "btc"]):
        return "crypto_markets"

    if any(w in text for w in ["ai", "artificial intelligence", "technology", "science", "breakthrough", "robot"]):
        return "ai_technology"

    if any(w in text for w in ["holiday", "national day", "observance", "season", "july", "christmas", "halloween"]):
        return "holidays_seasonal"

    if any(w in text for w in ["unusual", "strange", "weird", "viral", "mystery", "found", "rescued"]):
        return "weird_global"

    return "major_world"


def score_result(item):
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    url = item.get("url", "").lower()

    score = 0
    reasons = []

    bad_terms = [
        "latest news",
        "top stories",
        "home",
        "world news",
        "animals |",
        "news today",
        "live updates",
    ]

    strong_visual_terms = [
        "unusual", "strange", "viral", "rescued", "found", "mystery",
        "breakthrough", "record", "surge", "recovery", "robotic",
        "giant", "tiny", "rare", "first", "historic"
    ]

    risky_terms = [
        "death", "war", "burns", "killed", "funeral", "disease",
        "fatal", "shooting", "attack", "tragedy"
    ]

    category = detect_category(item)

    for term in bad_terms:
        if term in text:
            score -= 8
            reasons.append(f"generic result: {term}")

    for term in strong_visual_terms:
        if term in text:
            score += 3
            reasons.append(f"visual hook: {term}")

    for term in risky_terms:
        if term in text:
            score -= 7
            reasons.append(f"sensitive topic: {term}")

    if category == "animals_pets":
        score += 10
        reasons.append("category boost: animals/pets")
    elif category == "crypto_markets":
        score += 7
        reasons.append("category boost: crypto/markets")
    elif category == "ai_technology":
        score += 8
        reasons.append("category boost: AI/tech")
    elif category == "holidays_seasonal":
        score += 6
        reasons.append("category boost: holiday/seasonal")
    elif category == "weird_global":
        score += 9
        reasons.append("category boost: weird/global")
    else:
        score += 4
        reasons.append("category boost: major world")

    if url and not url.endswith(".com/") and not url.endswith(".com"):
        score += 3
        reasons.append("specific article URL")

    return score, reasons, category


def choose_target_category():
    day_index = datetime.utcnow().timetuple().tm_yday
    return CATEGORY_ORDER[day_index % len(CATEGORY_ORDER)]


def build_concepts():
    trends = collect_trends()
    target_category = choose_target_category()
    concepts = []

    for item in trends:
        score, reasons, category = score_result(item)

        if category == target_category:
            score += 8
            reasons.append(f"daily rotation boost: {target_category}")

        if score < 8:
            continue

        title = item.get("title", "Untitled")
        description = item.get("description", "")

        concepts.append({
            "score": score,
            "category": category,
            "target_category_today": target_category,
            "source_title": title,
            "source_url": item.get("url"),
            "source_summary": description,
            "why_selected": reasons[:10],
            "post_angle": f"Turn this event into a funny Hunk Mao visual metaphor scene: {title}",
            "hashtag_seed": [
                "#hunkmao",
                "#dailyillustration",
                "#petsofinstagram",
                "#weirdnews",
                "#digitalart",
            ],
        })

    concepts.sort(key=lambda x: x["score"], reverse=True)

    # Small shuffle among top 3 to reduce repetitive behavior
    top = concepts[:3]
    if len(top) > 1:
        random.shuffle(top)

    return top + concepts[3:5]


if __name__ == "__main__":
    print(json.dumps(build_concepts(), indent=2))
