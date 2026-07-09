import json
import re
from datetime import datetime, timezone, timedelta
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


TRUSTED_SOURCES = [
    "reuters",
    "associated press",
    "ap news",
    "apnews",
    "bbc",
    "cnn",
    "nbc",
    "abc news",
    "cbs news",
    "npr",
    "the guardian",
    "washington post",
    "new york times",
    "nasa",
    "espn",
    "cnbc",
    "bloomberg",
    "the verge",
    "techcrunch",
]


def parse_relative_age(value):
    if not value:
        return None

    text = str(value).strip().lower()

    if text in ["just now", "now"]:
        return datetime.now(timezone.utc)

    patterns = [
        (r"(\d+)\s*minute", "minutes"),
        (r"(\d+)\s*hour", "hours"),
        (r"(\d+)\s*day", "days"),
        (r"(\d+)\s*week", "weeks"),
        (r"(\d+)\s*month", "months"),
        (r"(\d+)\s*year", "years"),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        amount = int(match.group(1))
        now = datetime.now(timezone.utc)

        if unit == "minutes":
            return now - timedelta(minutes=amount)
        if unit == "hours":
            return now - timedelta(hours=amount)
        if unit == "days":
            return now - timedelta(days=amount)
        if unit == "weeks":
            return now - timedelta(weeks=amount)
        if unit == "months":
            return now - timedelta(days=amount * 30)
        if unit == "years":
            return now - timedelta(days=amount * 365)

    return None


def parse_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)

    relative = parse_relative_age(value)
    if relative:
        return relative

    try:
        value = str(value).strip()

        if "," in value and ("GMT" in value or "UTC" in value):
            return parsedate_to_datetime(value).astimezone(timezone.utc)

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
        or item.get("age")
    )


def is_trusted_source(item):
    source = f"{item.get('source', '')} {item.get('url', '')}".lower()
    return any(s in source for s in TRUSTED_SOURCES)


def is_current(item):
    title = item.get("title", "")
    description = item.get("description", "")
    text = f"{title} {description}".lower()

    hard_stale_terms = [
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

    for term in hard_stale_terms:
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

    if hours_old <= 12:
        return True, "fresh: published within 12 hours", hours_old

    if hours_old <= 24:
        return True, "fresh: published within 24 hours", hours_old

    if hours_old <= 48 and is_trusted_source(item):
        return True, "acceptable: trusted source within 48 hours", hours_old

    return False, "rejected: not fresh enough for daily current-news post", hours_old


def detect_category(item):
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()

    if any(w in text for w in ["bitcoin", "ethereum", "crypto", "etf", "xrp", "solana", "btc", "eth"]):
        return "crypto_markets"

    if any(w in text for w in ["ai", "artificial intelligence", "openai", "nvidia", "chip", "robot", "technology"]):
        return "ai_technology"

    if any(w in text for w in ["space", "nasa", "mars", "moon", "planet", "asteroid", "science", "discovery", "breakthrough"]):
        return "science_space_nature"

    if any(w in text for w in ["dog", "cat", "pet", "animal", "wildlife", "elephant", "eagle", "buffalo", "zoo", "monkey", "primate"]):
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

    current_ok, current_reason, hours_old = is_current(item)

    if not current_ok:
        return None, [current_reason], None, hours_old

    score = 0
    reasons = [current_reason]

    if hours_old is not None:
        if hours_old <= 6:
            score += 45
            reasons.append("freshness boost: under 6 hours")
        elif hours_old <= 12:
            score += 40
            reasons.append("freshness boost: under 12 hours")
        elif hours_old <= 24:
            score += 32
            reasons.append("freshness boost: under 24 hours")
        elif hours_old <= 48:
            score += 22
            reasons.append("freshness boost: trusted source under 48 hours")

    if is_trusted_source(item):
        score += 10
        reasons.append("trusted source boost")

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

    risky_terms = [
        "death",
        "war",
        "burns",
        "killed",
        "funeral",
        "fatal",
        "shooting",
        "attack",
        "tragedy",
        "murder",
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
        "robotic",
        "giant",
        "tiny",
        "rare",
        "first",
        "historic",
        "launch",
        "discovery",
    ]

    for term in bad_terms:
        if term in text:
            score -= 12
            reasons.append(f"penalty: generic result: {term}")

    for term in risky_terms:
        if term in text:
            score -= 12
            reasons.append(f"penalty: sensitive topic: {term}")

    for term in strong_visual_terms:
        if term in text:
            score += 3
            reasons.append(f"visual hook: {term}")

    category = detect_category(item)

    category_boosts = {
        "crypto_markets": 6,
        "ai_technology": 7,
        "science_space_nature": 6,
        "animals_pets": 2,
        "weird_global": 4,
        "major_world": 5,
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
            score += 4
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
            "source": item.get("source"),
            "published_at": published_raw,
            "why_current_now": reasons[0] if reasons else "",
            "why_selected": reasons[:12],
            "post_angle": f"Turn this verified current news event into a funny Hunk Mao visual metaphor scene: {title}",
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

    if not concepts:
        raise RuntimeError("No fresh current-news concepts found. Check Brave results and publish-date parsing.")

    return concepts[:5]


if __name__ == "__main__":
    print(json.dumps(build_concepts(), indent=2))
