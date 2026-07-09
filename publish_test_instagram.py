import json
import os
import time
import requests

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
POST_STAMP = os.environ.get("POST_STAMP")

if POST_STAMP:
    PUBLIC_IMAGE_URL = f"https://xahxxx.github.io/daily-social-engine/published/hunk-mao-{POST_STAMP}.png"
    PUBLIC_BRIEF_URL = f"https://xahxxx.github.io/daily-social-engine/published/hunk-mao-{POST_STAMP}.json"
else:
    PUBLIC_IMAGE_URL = "https://xahxxx.github.io/daily-social-engine/published/latest.png"
    PUBLIC_BRIEF_URL = "https://xahxxx.github.io/daily-social-engine/published/latest.json"

if not IG_ACCESS_TOKEN:
    raise RuntimeError("IG_ACCESS_TOKEN is missing")

if not IG_USER_ID:
    raise RuntimeError("IG_USER_ID is missing")


def get_caption():
    print(f"Waiting for brief URL: {PUBLIC_BRIEF_URL}")

    max_attempts = 12
    wait_seconds = 15

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                PUBLIC_BRIEF_URL,
                timeout=30,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )

            if response.status_code == 200:
                brief = response.json()

                caption = brief.get("caption", "").strip()
                hashtags = brief.get("hashtags", [])

                clean_hashtags = []

                for tag in hashtags:
                    tag = str(tag).strip()

                    if not tag:
                        continue

                    if not tag.startswith("#"):
                        tag = f"#{tag}"

                    clean_hashtags.append(tag)

                hashtag_text = " ".join(clean_hashtags)

                if caption and hashtag_text:
                    return f"{caption}\n\n{hashtag_text}"

                if caption:
                    return caption

                raise RuntimeError("Brief JSON exists but caption is empty")

            print(
                f"Brief not ready yet "
                f"(attempt {attempt}/{max_attempts}, "
                f"status {response.status_code})."
            )

        except requests.RequestException as e:
            print(
                f"Brief request failed "
                f"(attempt {attempt}/{max_attempts}): {e}"
            )

        if attempt < max_attempts:
            time.sleep(wait_seconds)

    raise RuntimeError(
        f"Brief did not become available after "
        f"{max_attempts * wait_seconds} seconds: "
        f"{PUBLIC_BRIEF_URL}"
    )


def wait_for_image_url():
    print(f"Waiting for image URL: {PUBLIC_IMAGE_URL}")

    max_attempts = 12
    wait_seconds = 15

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                PUBLIC_IMAGE_URL,
                timeout=30,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )

            if response.status_code == 200:
                print("Image URL is available.")
                return

            print(
                f"Image not ready yet "
                f"(attempt {attempt}/{max_attempts}, "
                f"status {response.status_code})."
            )

        except requests.RequestException as e:
            print(
                f"Image request failed "
                f"(attempt {attempt}/{max_attempts}): {e}"
            )

        if attempt < max_attempts:
            time.sleep(wait_seconds)

    raise RuntimeError(
        f"Image did not become available after "
        f"{max_attempts * wait_seconds} seconds: "
        f"{PUBLIC_IMAGE_URL}"
    )


def create_media_container(caption):
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"

    payload = {
        "image_url": PUBLIC_IMAGE_URL,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    creation_id = data.get("id")

    if not creation_id:
        raise RuntimeError(f"No creation ID returned: {json.dumps(data, indent=2)}")

    print(f"Created media container: {creation_id}")
    return creation_id


def publish_media(creation_id):
    url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }

    response = requests.post(url, data=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    media_id = data.get("id")

    if not media_id:
        raise RuntimeError(f"No media ID returned: {json.dumps(data, indent=2)}")

    print(f"Published Instagram media: {media_id}")
    return media_id


def main():
    print(f"POST_STAMP: {POST_STAMP}")
    print(f"PUBLIC_IMAGE_URL: {PUBLIC_IMAGE_URL}")
    print(f"PUBLIC_BRIEF_URL: {PUBLIC_BRIEF_URL}")

    wait_for_image_url()
    caption = get_caption()

    print("Final caption:")
    print(caption)

    creation_id = create_media_container(caption)

    # Instagram sometimes needs a moment after container creation.
    time.sleep(10)

    publish_media(creation_id)


if __name__ == "__main__":
    main()
