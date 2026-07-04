import json
import os
import time
import requests

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

PUBLIC_IMAGE_URL = "https://xahxxx.github.io/daily-social-engine/published/latest.png"
PUBLIC_BRIEF_URL = "https://xahxxx.github.io/daily-social-engine/published/latest.json"

if not IG_ACCESS_TOKEN:
    raise RuntimeError("IG_ACCESS_TOKEN is missing")


def get_caption():
    response = requests.get(PUBLIC_BRIEF_URL, timeout=30)
    response.raise_for_status()
    brief = response.json()

    caption = brief.get("caption", "").strip()
    hashtags = brief.get("hashtags", [])

    hashtag_text = " ".join(hashtags)

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
    return response.json()["user_id"]


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
    return response.json()["id"]


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
    print("Caption:")
    print(caption)

    ig_user_id = get_instagram_user_id()
    creation_id = create_media_container(ig_user_id, caption)
    publish_media(ig_user_id, creation_id)

    print("Published latest Hunk Mao post successfully.")


if name == "__main__":
    main()
