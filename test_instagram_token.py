import os
import requests

token = os.getenv("IG_ACCESS_TOKEN")
if not token:
    raise RuntimeError("IG_ACCESS_TOKEN is missing")
response = requests.get(
    "https://graph.instagram.com/me",
    params={"fields": "user_id,username,account_type", "access_token": token},
    timeout=30,
)
print(response.status_code)
print(response.text)
response.raise_for_status()
