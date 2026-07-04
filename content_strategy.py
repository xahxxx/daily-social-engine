import json
from trend_research import collect_trends


def score_result(item):
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    url = item.get("url", "").lower()

    score = 0
    reasons = []

    bad_homepage_terms = [
        "latest news",
        "top stories",
        "home",
        "world news",
        "animals |",
    ]

    crypto_terms = [
        "bitcoin",
        "ethereum",
        "crypto",
        "etf",
        "inflow",
        "clarity act",
        "regulation",
        "xrp",
        "solana",
    ]

    pet_terms = [
        "dog",
        "cat",
        "pet",
        "animal",
        "elephant",
        "eagle",
        "wildlife",
    ]

    visual_terms = [
        "viral",
        "unusual",
        "rescued",
        "found",
        "mystery",
        "breakthrough",
        "record",
        "surge",
        "recovery",
        "reclaims",
        "robotic",
    ]

    risky_terms = [
        "death",
        "war",
        "burns",
        "killed",
        "funeral",
        "disease",
        "fatal",
    ]

    for term in bad_homepage_terms:
        if term in text:
            score -= 8
            reasons.append(f"generic/homepage result: {term}")

    for word in crypto_terms:
        if word in text:
            score += 3
            reasons.append(f"crypto relevance: {word}")

    for word in pet_terms:
        if word in text:
            score += 4
            reasons.append(f"pet/animal relevance: {word}")

    for word in visual_terms:
        if word in text:
            score += 2
            reasons.append(f"visual hook: {word}")

    for word in risky_terms:
        if word in text:
            score -= 5
            reasons.append(f"risky/sensitive topic: {word}")

    if url and not url.endswith(".com/") and not url.endswith(".com"):
        score += 2
        reasons.append("specific article URL")

    return score, reasons


def build_concepts():
    trends = collect_trends()
    concepts = []

    for item in trends:
        score, reasons = score_result(item)

        if score < 8:
            continue

        title = item.get("title", "Untitled")
        description = item.get("description", "")

        concept = {
            "score": score,
            "source_title": title,
            "source_url": item.get("url"),
            "source_summary": description,
            "why_selected": reasons[:8],
            "post_angle": f"Turn this event into a funny, visually dense Instagram scene: {title}",
            "image_direction": (
                "Create a detailed square social-media illustration with a charismatic pet/mascot character "
                "reacting to the news event. Add tiny background signs, props, charts, stickers, newspapers, "
                "crypto symbols if relevant, and hidden easter eggs. Keep it playful, clever, and safe."
            ),
            "caption_draft": f"Today’s strange little signal from the world: {title} 🐾",
            "hashtag_seed": [
                "#dailynews",
                "#petsofinstagram",
                "#crypto",
                "#weirdnews",
                "#digitalart",
            ],
        }

        concepts.append(concept)

    concepts.sort(key=lambda x: x["score"], reverse=True)
    return concepts[:5]


if __name__ == "__main__":
    concepts = build_concepts()
    print(json.dumps(concepts, indent=2))
