import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

tokens_file = r"C:\Affiliate\post1\POST\config\permanent_meta_tokens.json"
with open(tokens_file, "r", encoding="utf-8") as f:
    data = json.load(f)

token = data["Góc Tập Luyện"]["page_access_token"]
video_id = "1064083453164298"

r = requests.get(
    f"https://graph.facebook.com/v19.0/{video_id}",
    params={
        "fields": "status,scheduled_publish_time,title",
        "access_token": token
    }
)
print("FB Reel status:", r.json())
