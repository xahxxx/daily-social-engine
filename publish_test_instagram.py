import os
import time
import requests

token = os.getenv("IG_ACCESS_TOKEN")

image_url = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba"
caption = "Test post from our daily social engine 🚀🐾 #test #socialengine"

if not token:
    raise RuntimeError("IG_ACCESS_TOKEN is missing")

# 1. Get IG user id
me = requests.get(
    "https://graph.instagram.com/me",
    params={"fields": "user_id,username", "access_token": token},
    timeout=30,
)
print(me.status_code, me.text)
me.raise_for_status()

ig_user_id = me.json()["user_id"]

# 2. Create media container
container = requests.post(
    f"https://graph.instagram.com/{ig_user_id}/media",
    data={
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    },
    timeout=30,
)
print(container.status_code, container.text)
container.raise_for_status()

creation_id = container.json()["id"]

time.sleep(10)

# 3. Publish media
publish = requests.post(
    f"https://graph.instagram.com/{ig_user_id}/media_publish",
    data={
        "creation_id": creation_id,
        "access_token": token,
    },
    timeout=30,
)
print(publish.status_code, publish.text)
publish.raise_for_status()

print("Published successfully")
