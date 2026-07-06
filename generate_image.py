import base64
import json
from openai import OpenAI

client = OpenAI()


def generate_image():
    with open("post_brief.json", "r", encoding="utf-8") as f:
        brief = json.load(f)

    with open("brand_profile.json", "r", encoding="utf-8") as f:
        brand = json.load(f)

    daily_prompt = (
        brief.get("image_prompt")
        or brief.get("visual_prompt")
        or brief.get("prompt")
        or brief.get("image")
    )

    if not daily_prompt:
        raise KeyError(
            f"No image prompt found in brief. Available keys: {list(brief.keys())}"
        )

        final_prompt = f"""
Use the provided Hunk Mao reference image as the authoritative character reference.

Preserve Hunk Mao's core identity:
- same orange tabby cat character
- same bright orange tabby fur pattern
- same expressive large eyes
- same compact athletic build
- same mischievous confident personality
- same recognizable facial identity

Do NOT copy the reference image's original scene, pose, background, costume, or composition.

Create a completely new cinematic anime editorial scene based on this story direction:

{daily_prompt}

Permanent brand direction:

{json.dumps(brand, indent=2)}

NEW VISUAL DIRECTION:
Transform Hunk Mao into a recurring cinematic anime news-character.
Each image should feel like a dramatic still frame from a premium animated film, not a flat editorial cartoon.

STYLE TARGET:
- cinematic anime environmental concept art
- painterly anime realism with cinematic photoreal material rendering
- lush, immersive worldbuilding
- dramatic camera language
- high-end animated movie still
- rich atmospheric depth
- emotional visual storytelling
- magical realism mixed with current-events satire
- ultra-polished cinematic anime key art
- luxury animated film lighting
- glossy high-end finish
- intricate background painting
- premium Japanese anime film still
- rich specular highlights and glistening surfaces
- crisp subject focus with cinematic lens blur
- visually stunning enough to stop a scrolling Instagram viewer

COMPOSITION:
Create a square Instagram composition with:
- Hunk Mao clearly visible as the main recurring character
- one strong central narrative scene
- foreground, middle ground, and background storytelling
- deep layered perspective
- asymmetrical cinematic framing
- strong foreground elements partially out of focus
- environmental scale and depth
- subtle visual jokes and easter eggs
- news-related props integrated naturally into the scene
- camera feels physically inside the scene, not observing from far away
- use low-angle, over-the-shoulder, foreground-framed, or dramatic perspective shots when appropriate

LIGHTING AND COLOR:
Use:
- cinematic lighting
- dramatic contrast
- deep shadows
- glowing practical lights
- volumetric light rays
- atmospheric mist or haze when appropriate
- reflective wet surfaces when appropriate
- saturated but controlled color grading
- emerald green, sapphire blue, amber, magenta, neon cyan, or sunset-gold accents when appropriate
- soft bloom and rim lighting
- sparkling highlights on water, glass, metal, eyes, fur, and wet surfaces
- luminous edge lighting around Hunk Mao
- controlled HDR contrast
- jewel-toned color palette
- glowing particles, fireflies, embers, rain mist, dust motes, or floating light flecks when appropriate
- beautiful caustic reflections and light shimmer when water or glass is present

DETAIL RULES:
- The scene should feel dense, alive, and premium.
- Include small props, tiny signs, symbolic objects, background characters, and hidden easter eggs.
- Prefer visual storytelling over written explanation.
- Avoid empty backgrounds.
- Avoid simple centered poster compositions.
- Avoid making every scene Hunk Mao sitting behind a desk.
- Avoid generic office scenes unless the news story specifically requires it.

TEXT RULES:
- Avoid excessive written text inside the illustration.
- If text appears, keep it extremely short: ideally 1–3 words per text element.
- Never include gibberish, fake brand names, distorted lettering, or misspelled words.
- Text must be secondary to the image.

CHARACTER CONSISTENCY:
- Hunk Mao must remain clearly recognizable as the same orange tabby cat character.
- Clothing and accessories should change according to the story.
- Do not default to a black hoodie or sunglasses.
- Keep his face, fur pattern, large eyes, and personality visually consistent across posts.

NEGATIVE STYLE DIRECTION:
Do not make the image look like:
- flat vector art
- simple cartoon
- children's book illustration
- generic mascot art
- low-detail digital painting
- plain editorial comic
- centered logo/poster design
- overly clean empty scene
- daytime stock illustration
- plastic 3D render

Do not add a border or watermark.
"""

    with open("hunk_mao_reference.png", "rb") as reference_image:
        response = client.images.edit(
            model="gpt-image-1",
            image=reference_image,
            prompt=final_prompt,
            size="1024x1024",
        )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    with open("generated_post.png", "wb") as f:
        f.write(image_bytes)

    print("Image generated successfully using Hunk Mao reference.")
    print("Saved as generated_post.png")


if __name__ == "__main__":
    generate_image()
