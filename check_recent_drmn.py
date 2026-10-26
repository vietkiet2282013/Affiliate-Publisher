import requests
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

ig_cfg = brands["dung_roi_moi_noi"]["instagram"]
th_cfg = brands["dung_roi_moi_noi"]["threads"]

print("--- INSTAGRAM RECENT MEDIA ---")
r_ig = requests.get(
    f"https://graph.facebook.com/v19.0/{ig_cfg['ig_user_id']}/media",
    params={"fields": "id,caption,permalink", "access_token": ig_cfg["access_token"], "limit": 2}
).json()
print(json.dumps(r_ig, indent=2, ensure_ascii=False))

print("\n--- THREADS RECENT MEDIA ---")
r_th = requests.get(
    f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads",
    params={"fields": "id,text,permalink", "access_token": th_cfg["access_token"], "limit": 2}
).json()
print(json.dumps(r_th, indent=2, ensure_ascii=False))
