import json
import os
import time
from typing import Dict, List

import requests

from hunk_utils import clean_hashtag, env, unique

IG_ACCESS_TOKEN = env("IG_ACCESS_TOKEN", required=True)
POST_STAMP = os.getenv("POST_STAMP", "").strip()
GITHUB_PAGES_BASE = os.getenv("GITHUB_PAGES_BASE", "https://xahxxx.github.io/daily-social-engine/published").rstrip("/")

if POST_STAMP:
    PUBLIC_IMAGE_URL = f"{GITHUB_PAGES_BASE}/hunk-mao-{POST_STAMP}.png"
    PUBLIC_BRIEF_URL = f"{GITHUB_PAGES_BASE}/hunk-mao-{POST_STAMP}.json"
else:
    PUBLIC_IMAGE_URL = f"{GITHUB_PAGES_BASE}/latest.png"
    PUBLIC_BRIEF_URL = f"{GITHUB_PAGES_BASE}/latest.json"


def request_json(method: str, url: str, **kwargs) -> Dict:
    for attempt in range(3):
        response = requests.request(method, url, timeout=45, **kwargs)
        print(response.status_code, response.text[:1000])
        if response.status_code < 500:
            response.raise_for_status()
            return response.json() if response.text else {}
        time.sleep(5 * (attempt + 1))
    response.raise_for_status()
    return {}


def get_caption() -> str:
    brief = request_json("GET", PUBLIC_BRIEF_URL)
    caption = str(brief.get("caption", "")).strip()
    hashtags = unique([clean_hashtag(t) for t in brief.get("hashtags", [])])
    hashtags = [t for t in hashtags if t]
    if not caption:
        raise RuntimeError("Caption is empty in published brief JSON")
    return f"{caption}\n\n{' '.join(hashtags)}".strip()


def get_instagram_user_id() -> str:
    data = request_json(
        "GET",
        "https://graph.instagram.com/me",
        params={"fields": "user_id,username,account_type", "access_token": IG_ACCESS_TOKEN},
    )
    return data["user_id"]


def create_media_container(ig_user_id: str, caption: str) -> str:
    data = request_json(
        "POST",
        f"https://graph.instagram.com/{ig_user_id}/media",
        data={"image_url": PUBLIC_IMAGE_URL, "caption": caption, "access_token": IG_ACCESS_TOKEN},
    )
    return data["id"]


def wait_for_container(creation_id: str, max_wait: int = 90) -> None:
    deadline = time.time() + max_wait
    while time.time() < deadline:
        data = request_json(
            "GET",
            f"https://graph.instagram.com/{creation_id}",
            params={"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN},
        )
        status = data.get("status_code")
        print("Container status:", status, data.get("status"))
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram media container failed: {data}")
        time.sleep(10)
    raise TimeoutError("Instagram media container did not finish in time")


def publish_media(ig_user_id: str, creation_id: str) -> Dict:
    wait_for_container(creation_id)
    return request_json(
        "POST",
        f"https://graph.instagram.com/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
    )


def main() -> None:
    caption = get_caption()
    print("Caption:\n", caption)
    print("Image URL:", PUBLIC_IMAGE_URL)
    ig_user_id = get_instagram_user_id()
    creation_id = create_media_container(ig_user_id, caption)
    result = publish_media(ig_user_id, creation_id)
    print("Published latest Hunk Mao post successfully.")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
