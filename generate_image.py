import base64
import json
from pathlib import Path
from typing import Dict

from openai import OpenAI

from hunk_utils import load_json, path_for

client = OpenAI()


def find_reference_image() -> Path:
    candidates = [
        path_for("hunk_mao_reference.png"),
        path_for("hunk_mao_reference(1).png"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Missing Hunk Mao reference image. Save it as hunk_mao_reference.png in this folder.")


def final_image_prompt(brief: Dict, brand: Dict) -> str:
    daily_prompt = brief.get("image_prompt") or brief.get("visual_prompt") or brief.get("prompt") or brief.get("image")
    if not daily_prompt:
        raise KeyError(f"No image prompt found in brief. Available keys: {list(brief.keys())}")

    return f"""
Use the provided Hunk Mao reference image only as the authoritative character identity reference.

PRESERVE HUNK MAO:
- same recurring orange tabby cat identity
- youthful compact athletic build, not obese or babyish
- sharp orange tabby markings and fluffy cheek fur
- expressive large lively eyes
- mischievous confident grin and playful chaotic hero energy

DO NOT COPY FROM REFERENCE:
- do not copy the old pose, background, coaster/amusement scene, costume, sunglasses, layout, signs, or composition unless today's prompt specifically asks for them
- create a new scene from the news brief

TODAY'S APPROVED BRIEF:
{daily_prompt}

CAPTION CONTEXT:
{brief.get('caption', '')}

BRAND PROFILE:
{json.dumps(brand, indent=2, ensure_ascii=False)}

STYLE TARGET:
- premium cinematic anime environmental concept art
- painterly anime realism with cinematic photoreal material rendering
- high-end animated movie still
- rich atmospheric depth, foreground/midground/background storytelling
- dramatic perspective, physically inside the scene
- glossy high-end finish, crisp subject focus, cinematic lens blur
- jewel-toned controlled color palette, soft bloom, rim light, volumetric rays
- rich specular highlights on eyes, fur, metal, glass, water, wet streets, screens when relevant
- visually stunning enough to stop an Instagram scroll

COMPOSITION RULES:
- square Instagram composition
- Hunk Mao must be clearly visible as the main recurring character
- one strong central narrative scene, not a poster collage
- deep layered perspective, environmental scale, visual jokes and easter eggs
- news-related props integrated naturally
- avoid empty backgrounds and simple centered logo/poster compositions

TEXT RULES:
- obey the REQUIRED TEXT section from the brief exactly
- maximum 3 visible text phrases total
- no extra random signs, fake brand names, labels, headlines, tickers, gibberish, watermark, or border
- text must be large, simple, readable, and secondary to the image

NEGATIVE STYLE DIRECTION:
Avoid flat vector art, simple cartoon, children's book style, generic mascot art, low-detail digital painting, plain editorial comic, plastic 3D render, stock daytime illustration, empty sterile background, and dashboard-only scenes.
"""


def generate_image() -> Path:
    brief = load_json(path_for("post_brief.json"))
    brand = load_json(path_for("brand_profile.json"))
    reference_path = find_reference_image()

    with reference_path.open("rb") as reference_image:
        response = client.images.edit(
            model="gpt-image-1",
            image=reference_image,
            prompt=final_image_prompt(brief, brand),
            size="1024x1024",
        )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)
    output_path = path_for("generated_post.png")
    output_path.write_bytes(image_bytes)
    print(f"Image generated successfully: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_image()
