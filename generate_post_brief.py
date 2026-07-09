import json
from typing import Dict, List

from openai import OpenAI

from content_strategy import build_concepts
from hunk_utils import coerce_hashtags, load_json, path_for, save_json, unique

client = OpenAI()

CRYPTO_WORDS = {
    "bitcoin": ["#cryptocurrency", "#bitcoin", "#btc", "#crypto", "#cryptonews", "#blockchain"],
    "ethereum": ["#cryptocurrency", "#ethereum", "#eth", "#crypto", "#cryptonews", "#blockchain"],
    "solana": ["#cryptocurrency", "#solana", "#sol", "#crypto", "#cryptonews", "#blockchain"],
    "crypto": ["#cryptocurrency", "#crypto", "#cryptonews", "#blockchain"],
}

REQUIRED_KEYS = ["selected_topic", "category", "source_url", "news_angle", "scene_metaphor", "image_prompt", "easter_eggs", "caption", "hashtags", "risk_notes"]


def enforce_hashtags(brief: Dict) -> Dict:
    text = " ".join(str(brief.get(k, "")) for k in ["selected_topic", "category", "news_angle", "caption", "image_prompt"]).lower()
    tags = coerce_hashtags(brief.get("hashtags", []))
    tags.append("#hunkmao")

    is_crypto = any(w in text for w in ["bitcoin", "btc", "ethereum", "eth", "solana", "crypto", "cryptocurrency", "blockchain", "etf"])
    if is_crypto:
        tags.extend(CRYPTO_WORDS["crypto"])
        if "bitcoin" in text or "btc" in text:
            tags.extend(CRYPTO_WORDS["bitcoin"])
        if "ethereum" in text or " eth" in text:
            tags.extend(CRYPTO_WORDS["ethereum"])
        if "solana" in text or " sol" in text:
            tags.extend(CRYPTO_WORDS["solana"])
    else:
        banned = {"#cryptocurrency", "#bitcoin", "#btc", "#ethereum", "#eth", "#solana", "#sol", "#crypto", "#cryptonews", "#blockchain"}
        tags = [t for t in tags if t not in banned]

    tags = unique([t for t in tags if t])[:15]
    while len(tags) < 10:
        for fallback in ["#dailyillustration", "#digitalart", "#catart", "#instaart", "#hunkmao"]:
            if fallback not in tags:
                tags.append(fallback)
            if len(tags) >= 10:
                break
    brief["hashtags"] = tags[:15]
    if len(brief["hashtags"]) < 10:
        raise ValueError(f"Hashtag validation failed: {brief['hashtags']}")
    return brief


def validate_brief(brief: Dict) -> Dict:
    for key in REQUIRED_KEYS:
        if key not in brief:
            raise KeyError(f"Model response missing key: {key}. Got keys: {list(brief.keys())}")
    if not str(brief.get("image_prompt", "")).strip():
        raise ValueError("image_prompt is empty")
    if not str(brief.get("caption", "")).strip():
        raise ValueError("caption is empty")
    return enforce_hashtags(brief)


def build_prompt(top_concept: Dict, brand_profile: Dict) -> str:
    return f"""
You are the creative director and caption writer for Hunk Mao, a daily illustrated Instagram news-art account.

SELECTED NEWS CONCEPT:
{json.dumps(top_concept, indent=2, ensure_ascii=False)}

PERMANENT BRAND PROFILE:
{json.dumps(brand_profile, indent=2, ensure_ascii=False)}

MISSION:
Create one complete post brief grounded in the selected real-world news concept. The post must be funny, cinematic, clear, safe, and visually rich.

HUNK MAO PERSONALITY:
- Confident, funny, dramatic, clever, slightly chaotic, playful, never mean.
- A youthful athletic orange tabby internet-culture hero with expressive large eyes and a mischievous confident grin.
- He reacts like the tiny emperor of internet news, not like a boring news anchor.

NEWS GROUNDING RULES:
1. Identify the single main factual event from the selected concept.
2. Identify the central subject: company, person, animal, technology, country, sport, asset, discovery, or event.
3. Include one concrete detail from the source title/summary if available.
4. Do not invent numbers, quotes, claims, prices, names, or consequences.
5. Verify this is a specific event, announcement, result, discovery, filing, launch, ruling, record, rescue, or measurable development—not evergreen promotional copy.
6. Do not give financial advice.
7. Avoid real politician caricatures and cruel tragedy humor.

IMAGE PROMPT REQUIREMENTS:
- Square Instagram cinematic anime editorial illustration.
- Hunk Mao is the central recurring orange tabby character.
- Preserve his orange tabby identity, compact athletic build, large expressive eyes, and confident grin.
- Build a narrative scene: action + setting + visual joke.
- Include foreground, midground, background, atmospheric depth, cinematic lighting, jewel-toned accents, glossy highlights, and premium anime key-art finish.
- Dense visual storytelling: tiny props, symbolic objects, background actions, easter eggs.
- The actual news subject must be visually recognizable.
- Avoid generic dashboard/chart/coin poster scenes.
- NEVER create an advertisement, sponsorship creative, brand campaign, generic service promotion, or product-benefit poster.
- A company may appear only when it is the subject of a specific fresh event; depict the EVENT, not the company slogan or evergreen service.
- Do not plaster corporate logos across clothing, hats, walls, or screens. One necessary identifying logo at most.
- Reject concepts whose source merely describes what a company/service generally does rather than something that happened today.

TEXT INSIDE IMAGE — STRICT:
- Maximum 3 visible text phrases in the whole image.
- Each phrase maximum 3 words.
- Include a REQUIRED TEXT section listing exact phrases.
- Do not request extra small labels, fake brand names, fake headlines, gibberish, ticker clutter, or random background text.
- If text is not needed, write REQUIRED TEXT: none.

CAPTION RULES:
- Exactly 2 concise sentences.
- Sentence 1 plainly explains the actual news event and includes at least one concrete source detail when available.
- Sentence 2 is Hunk Mao’s witty reaction or punchline.
- Do not repeat the headline verbatim.
- Do not say “Today’s strange little signal from the world.”

HASHTAG RULES:
- Return 10 to 15 lowercase hashtags.
- Always include #hunkmao.
- For crypto stories, include #cryptocurrency and only include asset hashtags that are directly relevant:
  Bitcoin/BTC => #bitcoin #btc
  Ethereum/ETH => #ethereum #eth
  Solana/SOL => #solana #sol
- For non-crypto stories, do not include #cryptocurrency, #bitcoin, #btc, #ethereum, #eth, #solana, #sol, #crypto, #cryptonews, or #blockchain.

RETURN ONLY VALID JSON with exactly these keys:
selected_topic, category, source_url, news_angle, scene_metaphor, image_prompt, easter_eggs, caption, hashtags, risk_notes
"""


def generate_post_brief() -> Dict:
    concepts = build_concepts()
    top_concept = concepts[0]
    brand_profile = load_json(path_for("brand_profile.json"))

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=build_prompt(top_concept, brand_profile),
        text={"format": {"type": "json_object"}},
    )

    brief = validate_brief(json.loads(response.output_text))
    brief["source_url"] = brief.get("source_url") or top_concept.get("source_url")
    save_json(path_for("post_brief.json"), brief)
    print(json.dumps(brief, indent=2, ensure_ascii=False))
    return brief


if __name__ == "__main__":
    generate_post_brief()
