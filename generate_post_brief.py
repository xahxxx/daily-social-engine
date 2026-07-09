import json
import re
from typing import Any

from openai import OpenAI
from content_strategy import ALLOWED_CATEGORIES, build_concepts

client = OpenAI()

REQUIRED_KEYS = [
    "selected_topic", "category", "source_url", "news_angle", "why_this_is_news",
    "specific_subject", "specific_action", "scene_metaphor", "image_prompt",
    "required_text", "easter_eggs", "caption", "hashtags", "risk_notes"
]

BAD_CAPTION_PHRASES = [
    "reuters highlights", "ap highlights", "major breakthrough impacting global markets",
    "major ai technology breakthrough", "latest news", "keeps fans connected",
    "anytime, anywhere", "according to espn", "live scores", "global markets"
]
CRYPTO_TAGS = {"#cryptocurrency", "#crypto", "#bitcoin", "#btc", "#ethereum", "#eth", "#solana", "#sol", "#blockchain"}


def normalize_hashtags(value: Any, category: str, text_context: str):
    if isinstance(value, str):
        raw = re.split(r"[\s,]+", value.strip())
    elif isinstance(value, list):
        raw = []
        for v in value:
            if isinstance(v, str):
                raw.extend(re.split(r"[\s,]+", v.strip()))
    else:
        raw = []

    cleaned = []
    for tag in raw:
        tag = tag.strip().lower()
        if not tag:
            continue
        tag = tag if tag.startswith("#") else "#" + tag
        tag = re.sub(r"[^#a-z0-9_]", "", tag)
        if len(tag) <= 2:
            continue
        if tag not in cleaned:
            cleaned.append(tag)

    if "#hunkmao" not in cleaned:
        cleaned.insert(0, "#hunkmao")

    context = text_context.lower()
    if category != "cryptocurrency":
        cleaned = [t for t in cleaned if t not in CRYPTO_TAGS]
    else:
        for t in ["#cryptocurrency", "#crypto"]:
            if t not in cleaned:
                cleaned.append(t)
        asset_tags = []
        if any(w in context for w in ["bitcoin", "btc"]): asset_tags += ["#bitcoin", "#btc"]
        if any(w in context for w in ["ethereum", "eth"]): asset_tags += ["#ethereum", "#eth"]
        if any(w in context for w in ["solana", "sol"]): asset_tags += ["#solana", "#sol"]
        for t in asset_tags:
            if t not in cleaned:
                cleaned.append(t)

    banned = {"#streetstyle", "#urbanstyle", "#gamingvibes", "#2026season", "#sportsnews", "#soccer", "#espn", "#footballscores"}
    cleaned = [t for t in cleaned if t not in banned]
    return cleaned[:15]


def validate_brief(brief: dict, source_concept: dict):
    errors = []
    for key in REQUIRED_KEYS:
        if key not in brief:
            errors.append(f"missing key: {key}")
    if errors:
        return errors

    category = brief.get("category")
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"category not allowed: {category}")
    if brief.get("source_url") != source_concept.get("source_url"):
        errors.append("source_url changed or invented")

    caption = str(brief.get("caption", "")).strip()
    news_angle = str(brief.get("news_angle", "")).strip()
    why_news = str(brief.get("why_this_is_news", "")).strip()
    subject = str(brief.get("specific_subject", "")).strip()
    action = str(brief.get("specific_action", "")).strip()
    combined = f"{caption} {news_angle} {why_news} {subject} {action}".lower()

    if any(p in combined for p in BAD_CAPTION_PHRASES):
        errors.append("brief uses vague/promotional banned phrase")
    if len(subject.split()) < 1 or subject.lower() in {"reuters", "ap", "bbc", "espn", "source"}:
        errors.append("specific_subject is missing or publisher-as-subject")
    if len(action.split()) < 2:
        errors.append("specific_action is too vague")
    if len(why_news.split()) < 8:
        errors.append("why_this_is_news too thin")
    if len(caption.split()) < 18:
        errors.append("caption too thin to explain actual event")

    required_text = brief.get("required_text")
    if not isinstance(required_text, list) or len(required_text) > 3:
        errors.append("required_text must be list with max 3 phrases")
    else:
        for phrase in required_text:
            if len(str(phrase).split()) > 3:
                errors.append(f"required_text phrase too long: {phrase}")

    hashtags = normalize_hashtags(brief.get("hashtags"), category, combined)
    if len(hashtags) < 8:
        errors.append("not enough valid hashtags")
    brief["hashtags"] = hashtags
    return errors


def generate_post_brief():
    concepts = build_concepts()
    top_concept = concepts[0]

    with open("brand_profile.json", "r", encoding="utf-8") as f:
        brand_profile = json.load(f)

    prompt = f"""
You are the editorial director for Hunk Mao, a daily illustrated Instagram account.

ALLOWED CATEGORIES ONLY:
{json.dumps(ALLOWED_CATEGORIES)}

SELECTED VERIFIED CANDIDATE:
{json.dumps(top_concept, indent=2)}

PERMANENT BRAND PROFILE:
{json.dumps(brand_profile, indent=2)}

NON-NEGOTIABLE EDITORIAL RULES:
- This must be a specific current event, not a generic topic.
- The publisher/source is never the subject. Never write "Reuters highlights" or "AP reports" as the story.
- Identify the actual subject and actual action/development.
- Do not invent numbers, prices, dates, claims, quotes, scoreboards, brands, or statistics beyond the candidate.
- Do not cover sports, ESPN, celebrities, generic holidays, shopping, ads, streaming pages, live scores, or evergreen service pages.
- If the candidate is too vague, return risk_notes explaining the limitation but still stay inside the supplied facts.
- The image must avoid corporate logos unless the specific company is truly the subject of the event.
- Image text must be minimal: required_text max 3 phrases, max 3 words each.
- Caption must be exactly 2 concise sentences: sentence 1 explains what happened; sentence 2 is Hunk Mao's witty reaction.
- The post should feel like visually rich cinematic anime news satire, not an advertisement.

HASHTAG RULES:
- Return hashtags as a JSON array, never a single string.
- Always include #hunkmao.
- For non-crypto stories, do not include #cryptocurrency, #crypto, #bitcoin, #btc, #ethereum, #eth, #solana, #sol, or #blockchain.
- For crypto stories, include only asset hashtags genuinely present in the story.
- Hashtags must be lowercase, relevant, searchable, and not generic filler.

Return ONLY valid JSON with exactly these keys:
{json.dumps(REQUIRED_KEYS)}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    brief = json.loads(response.output_text)
    errors = validate_brief(brief, top_concept)
    if errors:
        with open("post_brief_failed.json", "w", encoding="utf-8") as f:
            json.dump({"errors": errors, "brief": brief, "source_concept": top_concept}, f, indent=2)
        raise RuntimeError("Brief failed editorial validation: " + "; ".join(errors))

    with open("post_brief.json", "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)
    print(json.dumps(brief, indent=2))
    return brief


if __name__ == "__main__":
    generate_post_brief()
