import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"C:\Affiliate\post1\POST\config\permanent_meta_tokens.json", "r", encoding="utf-8") as f:
    tokens = json.load(f)

token = tokens.get("Góc Tập Luyện", {}).get("page_access_token")
page_id = "1211541072052658"
r = requests.get(f"https://graph.facebook.com/v19.0/{page_id}", params={"fields": "name,id", "access_token": token})
print("FB:", r.json())

ig_id = "17841438553537040"
r_ig = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}", params={"fields": "username,id", "access_token": token})
print("IG:", r_ig.json())

with open(r"C:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

th = brands.get("goc_tap_luyen", {}).get("threads", {})
r_th = requests.get(f"https://graph.threads.net/v1.0/{th.get('user_id')}", params={"fields": "username,id", "access_token": th.get("access_token")})
print("Threads:", r_th.json())
