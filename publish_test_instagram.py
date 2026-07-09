import json
import os
import re
import time
import requests

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
POST_STAMP = os.environ.get("POST_STAMP")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes"}
BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://xahxxx.github.io/daily-social-engine/published")

if POST_STAMP:
    PUBLIC_IMAGE_URL = f"{BASE_URL}/hunk-mao-{POST_STAMP}.png"
    PUBLIC_BRIEF_URL = f"{BASE_URL}/hunk-mao-{POST_STAMP}.json"
else:
    PUBLIC_IMAGE_URL = f"{BASE_URL}/latest.png"
    PUBLIC_BRIEF_URL = f"{BASE_URL}/latest.json"


def normalize_hashtags(tags):
    if isinstance(tags, str):
        raw = re.split(r"[\s,]+", tags.strip())
    elif isinstance(tags, list):
        raw = []
        for t in tags:
            raw.extend(re.split(r"[\s,]+", str(t).strip()))
    else:
        raise RuntimeError("hashtags must be a list or string")
    cleaned = []
    for tag in raw:
        tag = tag.strip().lower()
        if not tag:
            continue
        tag = tag if tag.startswith("#") else "#" + tag
        tag = re.sub(r"[^#a-z0-9_]", "", tag)
        if len(tag) <= 2:
            continue
        if tag not in cleaned:
            cleaned.append(tag)
    if "#hunkmao" not in cleaned:
        cleaned.insert(0, "#hunkmao")
    if len(cleaned) < 8:
        raise RuntimeError(f"Too few valid hashtags: {cleaned}")
    return cleaned[:15]


def get_caption():
    response = requests.get(PUBLIC_BRIEF_URL, timeout=30)
    response.raise_for_status()
    brief = response.json()
    caption = str(brief.get("caption", "")).strip()
    if len(caption.split()) < 12:
        raise RuntimeError("Caption is too short / not explanatory enough")
    hashtags = normalize_hashtags(brief.get("hashtags", []))
    return f"{caption}\n\n{' '.join(hashtags)}".strip()


def get_instagram_user_id():
    if not IG_ACCESS_TOKEN:
        raise RuntimeError("IG_ACCESS_TOKEN is missing")
    response = requests.get(
        "https://graph.instagram.com/me",
        params={"fields": "user_id,username", "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    print(response.status_code, response.text)
    response.raise_for_status()
    return response.json()["user_id"]


def create_media_container(ig_user_id, caption):
    response = requests.post(
        f"https://graph.instagram.com/{ig_user_id}/media",
        data={"image_url": PUBLIC_IMAGE_URL, "caption": caption, "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    print(response.status_code, response.text)
    response.raise_for_status()
    return response.json()["id"]


def publish_media(ig_user_id, creation_id):
    time.sleep(20)
    response = requests.post(
        f"https://graph.instagram.com/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        timeout=30,
    )
    print(response.status_code, response.text)
    response.raise_for_status()


def main():
    caption = get_caption()
    print("Caption prepared:\n", caption)
    if DRY_RUN:
        print("DRY_RUN=true, not publishing to Instagram.")
        return
    ig_user_id = get_instagram_user_id()
    creation_id = create_media_container(ig_user_id, caption)
    publish_media(ig_user_id, creation_id)
    print("Published latest Hunk Mao post successfully.")


if __name__ == "__main__":
    main()
