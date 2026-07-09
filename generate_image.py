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
    if len(required_text) > 3:
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
- Include only the REQUIRED TEXT phrases above.
- Do not add any other words, headlines, captions, logos, scoreboards, signs, labels, tiny background text, fake UI text, or gibberish.
- If text cannot be rendered clearly, omit it rather than misspell it.

STYLE:
cinematic anime environmental concept art, premium animated movie still, lush worldbuilding, dramatic perspective, strong foreground/midground/background storytelling, polished lighting, crisp Hunk Mao face, no border, no watermark.
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
