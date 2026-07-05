import base64
import json
from openai import OpenAI

client = OpenAI()


def generate_image():
    with open("post_brief.json", "r", encoding="utf-8") as f:
        brief = json.load(f)

    with open("brand_profile.json", "r", encoding="utf-8") as f:
        brand = json.load(f)

    daily_prompt = brief["image_prompt"]

    final_prompt = f"""
Use the provided Hunk Mao reference image as the authoritative
character reference.

Preserve Hunk Mao's core identity:
- same species
- same orange tabby appearance
- same facial identity
- same recognizable proportions
- same general visual personality
- same core illustration aesthetic

Do NOT copy the reference image's original scene, pose, background,
costume, or composition.

Create a completely new daily editorial illustration based on this
story direction:

{daily_prompt}

Permanent brand direction:

{json.dumps(brand, indent=2)}

IMPORTANT:
Hunk Mao must remain clearly recognizable as the same recurring
character from the reference image.

The daily scene should be visually ambitious and substantially
different each day.

VISUAL CONSISTENCY RULES:
- Hunk Mao must always be recognizable as the same orange tabby cat character.
- He has bright orange tabby fur, expressive large eyes, and a compact athletic build.
- Clothing and accessories should vary according to the story. Do not default to a black hoodie or sunglasses.
- Keep Hunk Mao's core facial appearance and fur pattern visually consistent across posts.
- Avoid excessive written text inside the illustration.
- If text appears inside the artwork, keep it extremely short: ideally 1–3 words per text element.
- Never intentionally include misspelled words, gibberish, distorted lettering, or fake brand names.
- Prefer visual symbols, signs, objects, and environmental storytelling over large amounts of text.

Create a square Instagram composition with:
- one strong central narrative scene
- foreground, middle ground, and background storytelling
- dense environmental details
- numerous small props
- visual jokes
- hidden easter eggs
- tiny signs and stickers
- news-related objects
- clever background characters when appropriate
- cinematic lighting
- polished professional illustration quality

Avoid turning every scene into a character sitting behind a desk.

Avoid excessive text. Any text visible in the image should be short,
simple, and secondary to the visual storytelling.

Do not add a border or watermark.
"""

    with open("hunk_mao_reference.png", "rb") as reference_image:
        response = client.images.edit(
            model="gpt-image-1",
            image=reference_image,
            prompt=final_prompt,
            size="1024x1024"
        )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    with open("generated_post.png", "wb") as f:
        f.write(image_bytes)

    print("Image generated successfully using Hunk Mao reference.")
    print("Saved as generated_post.png")


if __name__ == "__main__":
    generate_image()
