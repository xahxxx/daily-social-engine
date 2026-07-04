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
You are the creative director for a daily Instagram news-art account.

Your job is to transform today's selected news story into an original,
funny, visually dense illustrated social-media post.

SELECTED NEWS CONCEPT:
{json.dumps(top_concept, indent=2)}

PERMANENT BRAND AND CHARACTER PROFILE:
{json.dumps(brand_profile, indent=2)}

Create one complete post brief.

IMPORTANT CHARACTER RULES:
- The main character must follow the permanent brand profile.
- Never replace the main character with a fox, raccoon, dog, or generic mascot.
- Preserve the same core character identity from post to post.
- Change the setting, costume, pose, props, activity, and story according to the daily news event.
- The character should feel like the recurring star of an ongoing illustrated universe.

IMAGE DIRECTION:
- Square Instagram composition.
- Highly detailed and visually dense.
- Strong central scene with a clear visual story.
- Include foreground, middle-ground, and background details.
- Include many small relevant props and accessories.
- Include hidden jokes and easter eggs.
- Include environmental storytelling.
- Include small signs, labels, screens, newspapers, posters, stickers, charts, objects, and visual jokes when appropriate.
- Avoid excessive large headline text dominating the image.
- Text inside the image should be short and minimal because image models can misspell long text.
- Make each daily scene substantially different.
- Do not simply put the mascot behind a desk every day.
- Use the actual news event as the basis of the visual narrative.
- Do not fabricate factual claims.
- Do not give financial advice.

Return a JSON object containing exactly these keys:

selected_topic
source_url
image_prompt
easter_eggs
caption
hashtags
risk_notes

The image_prompt must be detailed enough to directly send to an image-generation model.

The caption should be engaging and natural for Instagram.

The hashtags should be specifically relevant to the selected story and the brand rather than repeating generic hashtags every day.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_object"
            }
        },
    )

    brief = json.loads(response.output_text)

    with open("post_brief.json", "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)

    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    generate_post_brief()
