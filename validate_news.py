import json
import os
from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def validate_news_candidates(candidates, max_candidates=30):
    candidates = candidates[:max_candidates]

    prompt = f"""
You are the current-news validation editor for Hunk Mao, a daily illustrated Instagram news-art account.

Your job is NOT to make stories fun.
Your job is to reject stale, old, resurfaced, evergreen, or misleading stories.

CANDIDATE SEARCH RESULTS:
{json.dumps(candidates, indent=2)}

IMPORTANT:
Search result age is NOT reliable evidence that the actual event is current.
A page can surface today while the underlying event happened weeks ago.

For each candidate, determine:
1. Is this a real news story?
2. What specifically happened?
3. Did the actual event or meaningful new development happen in the last 24-48 hours?
4. Is this old news, resurfaced content, an evergreen explainer, or a future event?
5. Is it interesting enough for a general audience Instagram news-art post?

STRICT PASS RULE:
A candidate may pass only if there is a clear answer to:
"What specifically happened in the last 24-48 hours?"

Reject if:
- The event happened weeks or months ago.
- It is merely newly indexed, resurfaced, or republished.
- It is an explainer, guide, recap, prediction, or upcoming event.
- It has no concrete new development.
- It would make users feel the account is behind the news cycle.

Prefer stories that are:
- breaking or developing now
- widely discussed today
- surprising or useful
- visually interesting
- understandable in one Instagram caption

Return ONLY valid JSON with exactly this structure:

{{
  "validated": [
    {{
      "selected_topic": "short story name",
      "category": "crypto_markets | ai_technology | science_space_nature | animals_pets | weird_global | major_world | entertainment_culture | major_sports",
      "source_title": "original title",
      "source_url": "source URL",
      "source": "source name",
      "actual_event": "what happened",
      "new_development": "what specifically happened in the last 24-48 hours",
      "why_current_now": "why this is current today",
      "freshness_score": 0,
      "trend_score": 0,
      "audience_interest_score": 0,
      "visual_score": 0,
      "overall_score": 0,
      "risk_notes": "brief notes"
    }}
  ],
  "rejected": [
    {{
      "source_title": "title",
      "reason": "why rejected"
    }}
  ]
}}

Only include candidates in validated if freshness_score is 8 or higher.
Sort validated by overall_score descending.
Return at most 5 validated candidates.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )

    data = json.loads(response.output_text)

    validated = data.get("validated", [])

    if not validated:
        print("No validated current-news candidates found.")
        print(json.dumps(data.get("rejected", []), indent=2))
        return []

    return validated[:5]
