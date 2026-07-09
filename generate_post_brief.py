import json
import re
from typing import Any, Dict, List, Tuple

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
    "anytime, anywhere", "according to espn", "live scores", "global markets",
    "major breakthrough", "major event", "new development"
]

PUBLISHER_SUBJECTS = {
    "reuters", "ap", "associated press", "bbc", "cnn", "espn", "source",
    "news outlet", "article", "report", "website"
}

CRYPTO_TAGS = {
    "#cryptocurrency", "#crypto", "#bitcoin", "#btc", "#ethereum", "#eth",
    "#solana", "#sol", "#blockchain"
}

BANNED_TAGS = {
    "#streetstyle", "#urbanstyle", "#gamingvibes", "#2026season", "#sportsnews",
    "#soccer", "#espn", "#footballscores", "#celebrity", "#shopping", "#ad"
}

CATEGORY_BASE_TAGS = {
    "science_technology": [
        "#hunkmao", "#science", "#technology", "#sciencenews", "#technews",
        "#innovation", "#research", "#discovery", "#futuretech", "#digitalart"
    ],
    "ai": [
        "#hunkmao", "#ai", "#artificialintelligence", "#ainews", "#technology",
        "#machinelearning", "#innovation", "#futuretech", "#digitalart", "#animeart"
    ],
    "pets_animals": [
        "#hunkmao", "#animals", "#pets", "#animalnews", "#wildlife",
        "#animalrescue", "#catsofinstagram", "#petsofinstagram", "#digitalart", "#animeart"
    ],
    "space": [
        "#hunkmao", "#space", "#spacenews", "#nasa", "#astronomy",
        "#spaceexploration", "#science", "#cosmos", "#digitalart", "#animeart"
    ],
    "world_weird": [
        "#hunkmao", "#weirdnews", "#worldnews", "#strangenews", "#oddlyinteresting",
        "#unusualnews", "#todaynews", "#digitalart", "#animeart", "#catart"
    ],
    "cryptocurrency": [
        "#hunkmao", "#cryptocurrency", "#crypto", "#cryptonews", "#blockchain",
        "#web3", "#digitalassets", "#markets", "#digitalart", "#animeart"
    ],
}

ASSET_TAGS = {
    "bitcoin": ["#bitcoin", "#btc"],
    "btc": ["#bitcoin", "#btc"],
    "ethereum": ["#ethereum", "#eth"],
    "eth": ["#ethereum", "#eth"],
    "solana": ["#solana", "#sol"],
    " sol ": ["#solana", "#sol"],
}


def _clean_tag(tag: str) -> str:
    tag = str(tag).strip().lower()
    if not tag:
        return ""
    tag = tag if tag.startswith("#") else "#" + tag
    tag = re.sub(r"[^#a-z0-9_]", "", tag)
    if len(tag) <= 2 or tag == "#":
        return ""
    return tag


def normalize_hashtags(value: Any, category: str, text_context: str) -> List[str]:
    """Accepts model hashtags as array OR string, removes bad tags, and pads with safe category tags."""
    raw: List[str] = []
    if isinstance(value, str):
        raw = re.split(r"[\s,]+", value.strip())
    elif isinstance(value, list):
        for v in value:
            if isinstance(v, str):
                raw.extend(re.split(r"[\s,]+", v.strip()))

    cleaned: List[str] = []
    for tag in raw:
        t = _clean_tag(tag)
        if t and t not in BANNED_TAGS and t not in cleaned:
            cleaned.append(t)

    if category != "cryptocurrency":
        cleaned = [t for t in cleaned if t not in CRYPTO_TAGS]
    else:
        # Always include base crypto tags, then only asset tags that are actually present.
        context = f" {text_context.lower()} "
        for t in ["#cryptocurrency", "#crypto", "#cryptonews", "#blockchain"]:
            if t not in cleaned:
                cleaned.append(t)
        for word, tags in ASSET_TAGS.items():
            if word in context:
                for t in tags:
                    if t not in cleaned:
                        cleaned.append(t)

    # Add deterministic safe tags if model gave too few or gave bad ones.
    for t in CATEGORY_BASE_TAGS.get(category, CATEGORY_BASE_TAGS["world_weird"]):
        if category != "cryptocurrency" and t in CRYPTO_TAGS:
            continue
        if t not in cleaned:
            cleaned.append(t)

    if "#hunkmao" in cleaned:
        cleaned.remove("#hunkmao")
    cleaned.insert(0, "#hunkmao")

    return cleaned[:15]


def repair_brief(brief: Dict[str, Any], source_concept: Dict[str, Any]) -> Dict[str, Any]:
    """Repair safe, mechanical issues only. Does not invent factual claims."""
    category = brief.get("category") or source_concept.get("category") or "world_weird"
    if category not in ALLOWED_CATEGORIES:
        category = source_concept.get("category") if source_concept.get("category") in ALLOWED_CATEGORIES else "world_weird"
    brief["category"] = category
    brief["source_url"] = source_concept.get("source_url")

    combined = " ".join(str(brief.get(k, "")) for k in [
        "selected_topic", "news_angle", "why_this_is_news", "specific_subject", "specific_action", "caption"
    ])
    combined += " " + str(source_concept.get("source_title", "")) + " " + str(source_concept.get("source_summary", ""))
    brief["hashtags"] = normalize_hashtags(brief.get("hashtags"), category, combined)

    required_text = brief.get("required_text")
    if not isinstance(required_text, list):
        required_text = []
    safe_text = []
    for phrase in required_text:
        phrase = str(phrase).strip()
        if phrase and len(phrase.split()) <= 3:
            safe_text.append(phrase)
    brief["required_text"] = safe_text[:3]

    for key in REQUIRED_KEYS:
        brief.setdefault(key, "" if key not in {"hashtags", "required_text", "easter_eggs"} else [])
    return brief


def validate_brief(brief: Dict[str, Any], source_concept: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
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
    if len(subject.split()) < 1 or subject.lower() in PUBLISHER_SUBJECTS:
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

    hashtags = normalize_hashtags(brief.get("hashtags"), str(category), combined)
    brief["hashtags"] = hashtags
    if len(hashtags) < 8:
        errors.append("not enough valid hashtags")
    return errors


def _prompt_for_concept(top_concept: Dict[str, Any], brand_profile: Dict[str, Any]) -> str:
    return f"""
You are the editorial director for Hunk Mao, a daily illustrated Instagram account.

ALLOWED CATEGORIES ONLY:
{json.dumps(ALLOWED_CATEGORIES)}

SELECTED VERIFIED CANDIDATE:
{json.dumps(top_concept, indent=2)}

PERMANENT BRAND PROFILE:
{json.dumps(brand_profile, indent=2)}

NON-NEGOTIABLE EDITORIAL RULES:
- This must be a specific current event, not a generic topic.
- The publisher/source is never the subject. Never write "Reuters highlights", "AP reports", or source-as-story wording.
- Identify the actual subject and actual action/development from the candidate.
- Do not invent numbers, prices, dates, claims, quotes, scoreboards, brands, or statistics beyond the candidate.
- Do not cover sports, ESPN, celebrities, generic holidays, shopping, ads, streaming pages, live scores, or evergreen service pages.
- If the candidate is too vague, do not make it sound more specific than the supplied facts.
- The image must avoid corporate logos unless the specific company is truly the subject of the event.
- Image text must be minimal: required_text max 3 phrases, max 3 words each.
- Caption must be exactly 2 concise sentences: sentence 1 explains what happened; sentence 2 is Hunk Mao's witty reaction.
- The post should feel like visually rich cinematic anime news satire, not an advertisement.

HASHTAG RULES:
- Return hashtags as a JSON array, never a single string.
- Return 10 to 15 hashtags.
- Always include #hunkmao.
- For non-crypto stories, do not include #cryptocurrency, #crypto, #bitcoin, #btc, #ethereum, #eth, #solana, #sol, or #blockchain.
- For crypto stories, include only asset hashtags genuinely present in the story.
- Hashtags must be lowercase, relevant, searchable, and not generic filler.

Return ONLY valid JSON with exactly these keys:
{json.dumps(REQUIRED_KEYS)}
"""


def _call_model(prompt: str) -> Dict[str, Any]:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    return json.loads(response.output_text)


def generate_post_brief(max_candidates: int = 5, attempts_per_candidate: int = 2) -> Dict[str, Any]:
    concepts = build_concepts(max_concepts=max_candidates)

    with open("brand_profile.json", "r", encoding="utf-8") as f:
        brand_profile = json.load(f)

    failures: List[Dict[str, Any]] = []

    for concept_index, top_concept in enumerate(concepts[:max_candidates], start=1):
        for attempt in range(1, attempts_per_candidate + 1):
            try:
                prompt = _prompt_for_concept(top_concept, brand_profile)
                if attempt > 1:
                    prompt += "\nPrevious attempt failed validation. Be more specific, avoid vague source-as-story wording, and return 10-15 valid hashtags as an array.\n"

                brief = _call_model(prompt)
                brief = repair_brief(brief, top_concept)
                errors = validate_brief(brief, top_concept)

                # If ONLY hashtags failed, repair_brief should have fixed it; validate once more.
                if errors == ["not enough valid hashtags"]:
                    brief["hashtags"] = normalize_hashtags([], brief["category"], json.dumps(brief) + json.dumps(top_concept))
                    errors = validate_brief(brief, top_concept)

                if not errors:
                    with open("post_brief.json", "w", encoding="utf-8") as f:
                        json.dump(brief, f, indent=2)
                    with open("post_brief_attempts.json", "w", encoding="utf-8") as f:
                        json.dump({"success_candidate": concept_index, "failures": failures}, f, indent=2)
                    print(json.dumps(brief, indent=2))
                    return brief

                failures.append({
                    "candidate_index": concept_index,
                    "attempt": attempt,
                    "errors": errors,
                    "brief": brief,
                    "source_concept": top_concept,
                })

            except Exception as exc:
                failures.append({
                    "candidate_index": concept_index,
                    "attempt": attempt,
                    "errors": [str(exc)],
                    "source_concept": top_concept,
                })

    with open("post_brief_failed.json", "w", encoding="utf-8") as f:
        json.dump({"failures": failures, "concepts_tried": concepts[:max_candidates]}, f, indent=2)

    last_errors = failures[-1]["errors"] if failures else ["unknown failure"]
    raise RuntimeError("Brief failed editorial validation after retries: " + "; ".join(last_errors))


if __name__ == "__main__":
    generate_post_brief()
generate_post_brief_FIXED.py
Displaying generate_post_brief_FIXED.py.
