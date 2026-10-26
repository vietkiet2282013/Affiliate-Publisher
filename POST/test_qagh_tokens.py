import json
import os
import requests

with open(r"C:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)["quan_ao_gia_hoi"]

fb_token = cfg["facebook"]["access_token"]
page_id = cfg["facebook"]["page_id"]
ig_user_id = cfg["instagram"]["ig_user_id"]
th_user_id = cfg["threads"]["user_id"]
th_token = cfg["threads"]["access_token"]

# Check FB
r1 = requests.get(f"https://graph.facebook.com/v19.0/{page_id}", params={"access_token": fb_token, "fields": "id,name"}).json()
print("Facebook:", r1)

# Check IG
r2 = requests.get(f"https://graph.facebook.com/v19.0/{ig_user_id}", params={"access_token": fb_token, "fields": "id,username"}).json()
print("Instagram:", r2)

# Check Threads
r3 = requests.get(f"https://graph.threads.net/v1.0/{th_user_id}", params={"access_token": th_token, "fields": "id,username"}).json()
print("Threads:", r3)

yt_path = os.path.join(r"C:\Affiliate\post1\POST", cfg["youtube"]["token_file"])
print("YouTube token file exists:", os.path.exists(yt_path))
