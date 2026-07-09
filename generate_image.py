import base64
import json
from openai import OpenAI

client = OpenAI()


def generate_image():
    with open("post_brief.json", "r", encoding="utf-8") as f:
        brief = json.load(f)
    with open("brand_profile.json", "r", encoding="utf-8") as f:
        brand = json.load(f)

    required_text = brief.get("required_text", [])
    if len(required_text) > 1:
        raise RuntimeError("Too much required image text")

    final_prompt = f"""
Use the provided Hunk Mao reference image only as the authoritative character reference.
Do not copy its scene, pose, background, costume, or composition.

HUNK MAO CHARACTER LOCK:
{json.dumps(brand, indent=2)}

CURRENT NEWS EVENT:
News angle: {brief.get('news_angle')}
Why this is news: {brief.get('why_this_is_news')}
Specific subject: {brief.get('specific_subject')}
Specific action: {brief.get('specific_action')}
Scene metaphor: {brief.get('scene_metaphor')}

IMAGE PROMPT:
{brief.get('image_prompt')}

REQUIRED TEXT ONLY:
{json.dumps(required_text)}

STRICT TEXT RULES:
- Default to NO visible text anywhere in the image.
- Only include REQUIRED TEXT if it is absolutely necessary to understand the story.
- Maximum one visible text phrase in the entire image.
- Maximum three words in that phrase.
- Never create a headline, title card, news poster, slogan, caption, billboard, scoreboard, or large typography.
- Never place headline text across the top or bottom of the image.
- Do not add logos, labels, tiny background text, fake UI text, brand names, or gibberish.
- Communicate the story through action, environment, expression, props, and visual metaphor.
- If text cannot be rendered perfectly, omit it completely.

STYLE:
- cinematic anime environmental concept art
- premium animated movie still
- lush worldbuilding and environmental storytelling
- dramatic perspective and cinematic camera placement
- strong foreground, midground, and background depth
- Hunk Mao must be actively participating in the event, not posing for a poster
- build a believable narrative moment with action happening around him
- use props, environment, lighting, expressions, and visual metaphors to communicate the news
- include subtle story-specific easter eggs and background activity
- camera should feel physically inside the scene
- prefer dynamic low-angle, over-the-shoulder, close environmental, or action perspectives when appropriate
- rich atmospheric depth, cinematic lighting, volumetric effects, reflections, particles, haze, and detailed environments when appropriate
- avoid character + headline + simple background compositions
- avoid poster layouts
- avoid centered promotional compositions
- avoid generic mascot art
- avoid large typography as a storytelling device
- the final image should look like a frame captured from Hunk Mao's adventure through a real news event
"""

    with open("hunk_mao_reference.png", "rb") as reference_image:
        response = client.images.edit(
            model="gpt-image-1",
            image=reference_image,
            prompt=final_prompt,
            size="1024x1024",
        )
    image_bytes = base64.b64decode(response.data[0].b64_json)
    with open("generated_post.png", "wb") as f:
        f.write(image_bytes)
    print("Image generated successfully: generated_post.png")


if __name__ == "__main__":
    generate_image()
