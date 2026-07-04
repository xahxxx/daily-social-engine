import json
from openai import OpenAI
from content_strategy import build_concepts

client = OpenAI()


def generate_post_brief():
    concepts = build_concepts()

    if not concepts:
        raise RuntimeError("No concepts found")

    top_concept = concepts[0]

    with open("brand_profile.json", "r", encoding="utf-8") as f:
        brand_profile = json.load(f)

    prompt = f"""
You are the creative director for Hunk Mao, a daily illustrated Instagram news-art account.

SELECTED NEWS CONCEPT:
{json.dumps(top_concept, indent=2)}

PERMANENT BRAND PROFILE:
{json.dumps(brand_profile, indent=2)}

Create a complete post brief.

VERY IMPORTANT:
Do NOT create a generic mascot poster.
Do NOT simply place Hunk Mao in front of charts, coins, screens, or news headlines.
Do NOT repeat large words like INFLOW or BTC everywhere.
Do NOT make the whole image a financial dashboard.

Instead, convert the news into a funny visual metaphor scene.

Examples of better scene logic:
- If ETF inflows return, show Hunk Mao operating a giant money dam, with crypto rivers flowing into treasure reservoirs.
- If Bitcoin leads recovery, show Hunk Mao driving a rescue truck pulling exhausted coins out of a swamp.
- If ETH/XRP/SOL are involved, show them as tiny side characters, tools, badges, street signs, or hidden props.
- If regulation is involved, show a silly paperwork maze, not political propaganda.

IMAGE PROMPT REQUIREMENTS:
- Hunk Mao must be the central recurring orange tabby cat character.
- Use the brand profile and reference image identity.
- Create a square Instagram illustration.
- Build a narrative scene with action, setting, and visual joke.
- Include foreground, midground, and background.
- Add many tiny easter eggs and hidden props.
- Use only short simple text labels, max 2-3 words each.
- The image should feel like a treasure hunt.
- Avoid financial advice.
- Avoid fake claims.
- Avoid real politician caricatures.
- Keep the tone playful, clever, and safe.

Return ONLY valid JSON with exactly these keys:
selected_topic
source_url
scene_metaphor
image_prompt
easter_eggs
caption
hashtags
risk_notes
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )

    brief = json.loads(response.output_text)

    with open("post_brief.json", "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)

    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    generate_post_brief()
