import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from trend_research import collect_trends


CATEGORY_ORDER = [
    "crypto_markets",
    "ai_technology",
    "science_space_nature",
    "animals_pets",
    "weird_global",
    "major_world",
    "entertainment_culture",
    "major_sports",
]


def parse_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)

    try:
        value = str(value).strip()

        # Handles RSS-style dates like: Tue, 08 Jul 2026 18:30:00 GMT
        if "," in value and "GMT" in value:
            return parsedate_to_datetime(value).astimezone(timezone.utc)

        # Handles ISO dates
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc)

    except Exception:
        return None


def get_published_at(item):
    return (
        item.get("published_at")
        or item.get("published")
        or item.get("pubDate")
        or item.get("date")
        or item.get("created_at")
    )


def is_current(item):
    title = item.get("title", "")
    description = item.get("description", "")
    text = f"{title} {description}".lower()

    stale_terms = [
        "last month",
        "months ago",
        "weeks ago",
        "earlier this year",
        "in 2025",
        "in 2024",
        "throwback",
        "anniversary",
        "recap",
        "history of",
        "explainer",
        "what to know",
        "guide to",
        "everything you need to know",
        "ahead of",
        "next month",
        "later this year",
    ]

    for term in stale_terms:
        if term in text:
            return False, f"rejected: stale/evergreen wording detected: {term}", None

    published_raw = get_published_at(item)
    published_at = parse_datetime(published_raw)

    if not published_at:
        return False, "rejected: missing or unreadable publish date", None

    now = datetime.now(timezone.utc)
    hours_old = (now - published_at).total_seconds() / 3600

    if hours_old < 0:
        return False, "rejected: publish date appears to be in the future", hours_old

    if hours_old <= 24:
        return True, "fresh: published within 24 hours", hours_old

    if hours_old <= 48:
        return True, "acceptable: published within 48 hours", hours_old

    if hours_old <= 72:
        title_boost_terms = [
            "breaking",
            "live",
            "surge",
            "record",
            "first",
            "historic",
            "new",
            "major",
            "unexpected",
            "viral",
        ]

        if any(term in text for term in title_boost_terms):
            return True, "acceptable: within 72 hours with strong momentum wording", hours_old

        return False, "rejected: older than 48 hours without clear momentum", hours_old

    return False, "rejected: older than 72 hours", hours_old


def detect_category(item):
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()

    if any(w in text for w in ["bitcoin", "ethereum", "crypto", "etf", "xrp", "solana", "btc", "eth"]):
        return "crypto_markets"

    if any(w in text for w in ["ai", "artificial intelligence", "openai", "nvidia", "chip", "robot", "technology"]):
        return "ai_technology"

    if any(w in text for w in ["space", "nasa", "mars", "moon", "planet", "asteroid", "science", "discovery", "breakthrough"]):
        return "science_space_nature"

    if any(w in text for w in ["dog", "cat", "pet", "animal", "wildlife", "elephant", "eagle", "buffalo", "zoo"]):
        return "animals_pets"

    if any(w in text for w in ["movie", "music", "celebrity", "streaming", "internet", "tiktok", "youtube", "game", "gaming"]):
        return "entertainment_culture"

    if any(w in text for w in ["nba", "nfl", "mlb", "soccer", "world cup", "olympics", "tennis", "golf", "ufc"]):
        return "major_sports"

    if any(w in text for w in ["unusual", "strange", "weird", "viral", "mystery", "found", "rescued"]):
        return "weird_global"

    return "major_world"


def score_result(item):
    title = item.get("title", "")
    description = item.get("description", "")
    url = item.get("url", "")
    text = f"{title} {description}".lower()

    score = 0
    reasons = []

    current_ok, current_reason, hours_old = is_current(item)

    if not current_ok:
        return None, [current_reason], None, hours_old

    score += 30
    reasons.append(current_reason)

    if hours_old is not None:
        if hours_old <= 12:
            score += 12
            reasons.append("freshness boost: under 12 hours")
        elif hours_old <= 24:
            score += 9
            reasons.append("freshness boost: under 24 hours")
        elif hours_old <= 48:
            score += 5
            reasons.append("freshness boost: under 48 hours")
        elif hours_old <= 72:
            score += 2
            reasons.append("freshness boost: under 72 hours")

    bad_terms = [
        "latest news",
        "top stories",
        "home",
        "world news",
        "news today",
        "live updates",
        "opinion",
        "analysis:",
        "explained",
        "newsletter",
    ]

    strong_visual_terms = [
        "unusual",
        "strange",
        "viral",
        "rescued",
        "found",
        "mystery",
        "breakthrough",
        "record",
        "surge",
        "recovery",
        "robotic",
        "giant",
        "tiny",
        "rare",
        "first",
        "historic",
        "launch",
        "crash",
        "discovery",
    ]

    risky_terms = [
        "death",
        "war",
        "burns",
        "killed",
        "funeral",
        "disease",
        "fatal",
        "shooting",
        "attack",
        "tragedy",
        "murder",
    ]

    category = detect_category(item)

    for term in bad_terms:
        if term in text:
            score -= 10
            reasons.append(f"penalty: generic result: {term}")

    for term in risky_terms:
        if term in text:
            score -= 9
            reasons.append(f"penalty: sensitive topic: {term}")

    for term in strong_visual_terms:
        if term in text:
            score += 3
            reasons.append(f"visual hook: {term}")

    category_boosts = {
        "crypto_markets": 5,
        "ai_technology": 6,
        "science_space_nature": 6,
        "animals_pets": 4,
        "weird_global": 5,
        "major_world": 3,
        "entertainment_culture": 4,
        "major_sports": 4,
    }

    score += category_boosts.get(category, 3)
    reasons.append(f"category boost: {category}")

    if url and not url.endswith(".com/") and not url.endswith(".com"):
        score += 3
        reasons.append("specific article URL")

    if len(title) < 20:
        score -= 4
        reasons.append("penalty: title too vague")

    return score, reasons, category, hours_old


def choose_target_category():
    day_index = datetime.utcnow().timetuple().tm_yday
    return CATEGORY_ORDER[day_index % len(CATEGORY_ORDER)]


def build_concepts():
    trends = collect_trends()
    target_category = choose_target_category()
    concepts = []

    for item in trends:
        score, reasons, category, hours_old = score_result(item)

        if score is None:
            continue

        if category == target_category:
            score += 5
            reasons.append(f"daily rotation boost: {target_category}")

        if score < 25:
            continue

        title = item.get("title", "Untitled")
        description = item.get("description", "")
        published_raw = get_published_at(item)

        concepts.append({
            "score": round(score, 2),
            "freshness_hours_old": round(hours_old, 2) if hours_old is not None else None,
            "category": category,
            "target_category_today": target_category,
            "source_title": title,
            "source_url": item.get("url"),
            "source_summary": description,
            "published_at": published_raw,
            "why_current_now": reasons[0] if reasons else "",
            "why_selected": reasons[:12],
            "post_angle": f"Turn this current news event into a funny Hunk Mao visual metaphor scene: {title}",
            "hashtag_seed": [
                "#hunkmao",
                "#dailyillustration",
                "#newsart",
                "#currentnews",
                "#digitalart",
            ],
        })

    concepts.sort(
        key=lambda x: (
            x["score"],
            -x["freshness_hours_old"] if x["freshness_hours_old"] is not None else -999,
        ),
        reverse=True,
    )

    return concepts[:5]


if __name__ == "__main__":
    print(json.dumps(build_concepts(), indent=2))
