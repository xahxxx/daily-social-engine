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
You are the creative director and caption writer for Hunk Mao, a daily illustrated Instagram news-art account.

SELECTED NEWS CONCEPT:
{json.dumps(top_concept, indent=2)}

PERMANENT BRAND PROFILE:
{json.dumps(brand_profile, indent=2)}

HUNK MAO PERSONALITY:
- Hunk Mao is confident, funny, dramatic, clever, and slightly chaotic.
- He talks like a tiny orange tabby who thinks he is the emperor of internet news.
- He is playful, not mean.
- He makes short observations, not boring headlines.
- He should feel like a recurring character with a recognizable voice.
- Captions should sound like Hunk Mao reacted to the event, not like a news site copied the title.

CONTENT DIVERSITY RULE:
This post belongs to category: {top_concept.get("category")}
Today’s rotation target is: {top_concept.get("target_category_today")}
Respect the category, but if the selected event is unusually strong, lean into it.

VERY IMPORTANT:
Do NOT create a generic mascot poster.
Do NOT simply place Hunk Mao in front of charts, coins, screens, or news headlines.
Do NOT make the whole image a dashboard.
Do NOT repeat the article headline as the caption.

Instead, convert the news into a funny visual metaphor scene.

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

CAPTION REQUIREMENTS:
- 1-2 short sentences.
- Written in Hunk Mao’s voice.
- Include a tiny joke or reaction.
- Do not sound like a headline.
- Do not provide investment advice.
- Do not say “Today’s strange little signal from the world.”

Return ONLY valid JSON with exactly these keys:
selected_topic
category
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
