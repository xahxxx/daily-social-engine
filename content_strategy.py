import json
from trend_research import collect_trends
from validate_news import validate_news_candidates


def build_concepts():
    raw_candidates = collect_trends()

    if not raw_candidates:
        raise RuntimeError("No search candidates found from trend_research.py")

    validated = validate_news_candidates(raw_candidates)

    if not validated:
        raise RuntimeError("No validated current-news concepts found.")

    concepts = []

    for item in validated:
        score = item.get("overall_score", 0)

        concepts.append({
            "score": score,
            "category": item.get("category"),
            "target_category_today": item.get("category"),
            "selected_topic": item.get("selected_topic"),
            "source_title": item.get("source_title"),
            "source_url": item.get("source_url"),
            "source": item.get("source"),
            "actual_event": item.get("actual_event"),
            "new_development": item.get("new_development"),
            "why_current_now": item.get("why_current_now"),
            "source_summary": item.get("actual_event"),
            "why_selected": [
                f"freshness_score: {item.get('freshness_score')}",
                f"trend_score: {item.get('trend_score')}",
                f"audience_interest_score: {item.get('audience_interest_score')}",
                f"visual_score: {item.get('visual_score')}",
                item.get("why_current_now", ""),
            ],
            "post_angle": f"Turn this verified current news event into a funny Hunk Mao visual metaphor scene: {item.get('actual_event')}",
            "hashtag_seed": [
                "#hunkmao",
                "#dailyillustration",
                "#newsart",
                "#currentnews",
                "#digitalart",
            ],
            "risk_notes": item.get("risk_notes", ""),
        })

    concepts.sort(key=lambda x: x.get("score", 0), reverse=True)

    return concepts[:5]


if __name__ == "__main__":
    print(json.dumps(build_concepts(), indent=2))
