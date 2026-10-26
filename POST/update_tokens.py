import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

token = "EAAmD979AfWEBSvIUvuEFX2ZC39rsATmBPBsSRZC6zZAIjPYQKZAEURWEnQgTDgVWkZAZBPJ6tZAs87kpLwheOPtYk6VEHYjNtgX983Ou0XG8cU3S8Hw47bYdwo8otBOr82QXQFfWWsJ9tDZCfMOE4n6xKxiwZC9w87Chj49uTEdqTwv5qTJFAkwnwFxCzctRnRIGrgT8l4OwwXVuYXEYT8i2crgl6R8lxA7OoQ04l7Imz2MJ4rV7ZBoPijnZBJHQicXLfLN2a9ZBCZAIPGSOUP9tKfFaZA"

# 1. Lấy toàn bộ accounts và Page access token
r = requests.get(
    "https://graph.facebook.com/v19.0/me/accounts",
    params={"access_token": token, "fields": "name,id,access_token,instagram_business_account", "limit": 100}
)
accounts = r.json().get("data", [])

page_tokens = {}
for p in accounts:
    page_tokens[p["id"]] = {
        "name": p["name"],
        "page_access_token": p["access_token"],
        "ig_id": p.get("instagram_business_account", {}).get("id") if p.get("instagram_business_account") else None
    }

# 2. Update permanent_meta_tokens.json
tokens_file = r"C:\Affiliate\post1\POST\config\permanent_meta_tokens.json"
try:
    with open(tokens_file, "r", encoding="utf-8") as f:
        perm_tokens = json.load(f)
except Exception:
    perm_tokens = {}

perm_tokens["user_access_token"] = token
for pid, info in page_tokens.items():
    perm_tokens[pid] = info["page_access_token"]

with open(tokens_file, "w", encoding="utf-8") as f:
    json.dump(perm_tokens, f, indent=2, ensure_ascii=False)
print("Updated permanent_meta_tokens.json successfully!")

# 3. Update brands.json
brands_file = r"C:\Affiliate\post1\POST\config\brands.json"
with open(brands_file, "r", encoding="utf-8") as f:
    brands = json.load(f)

for brand_key, brand_cfg in brands.items():
    fb_pid = brand_cfg.get("facebook", {}).get("page_id")
    if fb_pid and fb_pid in page_tokens:
        brand_cfg["facebook"]["access_token"] = page_tokens[fb_pid]["page_access_token"]
        if page_tokens[fb_pid]["ig_id"]:
            brand_cfg["instagram"]["ig_user_id"] = page_tokens[fb_pid]["ig_id"]
        brand_cfg["instagram"]["access_token"] = page_tokens[fb_pid]["page_access_token"]
        print(f"Updated FB & IG token for: {brand_key} ({page_tokens[fb_pid]['name']})")

with open(brands_file, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=2, ensure_ascii=False)
print("Updated brands.json successfully!")
