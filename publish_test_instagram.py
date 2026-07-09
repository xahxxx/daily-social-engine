import json
import os
import time
import requests


IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

POST_STAMP = os.environ.get("POST_STAMP")

if POST_STAMP:
    PUBLIC_IMAGE_URL = f"https://xahxxx.github.io/daily-social-engine/published/hunk-mao-{POST_STAMP}.png"
    PUBLIC_BRIEF_URL = f"https://xahxxx.github.io/daily-social-engine/published/hunk-mao-{POST_STAMP}.json"
else:
    PUBLIC_IMAGE_URL = "https://xahxxx.github.io/daily-social-engine/published/latest.png"
    PUBLIC_BRIEF_URL = "https://xahxxx.github.io/daily-social-engine/published/latest.json"

if not IG_ACCESS_TOKEN:
    raise RuntimeError("IG_ACCESS_TOKEN is missing")


def get_caption():
    response = requests.get(PUBLIC_BRIEF_URL, timeout=30)
    response.raise_for_status()
    brief = response.json()

    if brief.get("selected_topic") == "NO_VALID_CURRENT_STORY":
        raise RuntimeError("No valid current news story selected. Skipping Instagram publish.")

    caption = brief.get("caption", "").strip()
    hashtags = brief.get("hashtags", [])

    if not caption:
        raise RuntimeError("Brief is missing caption. Skipping Instagram publish.")

    if not hashtags:
        raise RuntimeError("Brief is missing hashtags. Skipping Instagram publish.")

    clean_hashtags = []
    seen = set()

    for tag in hashtags:
        tag = str(tag).strip().lower()
        tag = tag.replace(" ", "")

        if not tag:
            continue

        if not tag.startswith("#"):
            tag = "#" + tag

        if tag not in seen:
            clean_hashtags.append(tag)
            seen.add(tag)

    if not clean_hashtags:
        raise RuntimeError("No valid hashtags after cleaning. Skipping Instagram publish.")

    hashtag_text = " ".join(clean_hashtags)

    return f"{caption}\n\n{hashtag_text}".strip()


def get_instagram_user_id():
    response = requests.get(
        "https://graph.instagram.com/me",
        params={
            "fields": "user_id,username",
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )

    print(response.status_code, response.text)
    response.raise_for_status()

    data = response.json()

    if "user_id" not in data:
        raise RuntimeError(f"Instagram user_id missing from response: {data}")

    return data["user_id"]


def create_media_container(ig_user_id, caption):
    response = requests.post(
        f"https://graph.instagram.com/{ig_user_id}/media",
        data={
            "image_url": PUBLIC_IMAGE_URL,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )

    print(response.status_code, response.text)
    response.raise_for_status()

    data = response.json()

    if "id" not in data:
        raise RuntimeError(f"Instagram media container id missing from response: {data}")

    return data["id"]


def publish_media(ig_user_id, creation_id):
    time.sleep(15)

    response = requests.post(
        f"https://graph.instagram.com/{ig_user_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )

    print(response.status_code, response.text)
    response.raise_for_status()


def main():
    caption = get_caption()

    print("Image URL:")
    print(PUBLIC_IMAGE_URL)

    print("Brief URL:")
    print(PUBLIC_BRIEF_URL)

    print("Caption:")
    print(caption)

    ig_user_id = get_instagram_user_id()
    creation_id = create_media_container(ig_user_id, caption)
    publish_media(ig_user_id, creation_id)

    print("Published latest Hunk Mao post successfully.")


if __name__ == "__main__":
    main()
