import base64
import json
from openai import OpenAI

client = OpenAI()


def generate_image():
    with open("post_brief.json", "r", encoding="utf-8") as f:
        brief = json.load(f)

    image_prompt = brief["image_prompt"]

    response = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        size="1024x1024",
    )

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    with open("generated_post.png", "wb") as f:
        f.write(image_bytes)

    print("Image generated: generated_post.png")


if __name__ == "__main__":
    generate_image()
