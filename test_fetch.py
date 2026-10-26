import requests
import json
import os
import sys

POST_DIR = r"c:\Affiliate\post1\POST"
with open(os.path.join(POST_DIR, "config", "brands.json"), encoding="utf-8") as f:
    brands = json.load(f)

b = brands.get("cham_da_tiet_kiem", {})

print("--- TESTING FB ---")
fb = b.get("facebook", {})
fb_url = f"https://graph.facebook.com/v19.0/{fb.get('page_id')}/videos"
r = requests.get(fb_url, params={
    "fields": "id,title,description,created_time,views,likes.summary(true),comments.summary(true)",
    "access_token": fb.get("access_token"),
    "limit": 5
})
print("FB Videos status:", r.status_code)
print("FB Videos data:", r.json())

print("\n--- TESTING IG ---")
ig = b.get("instagram", {})
ig_url = f"https://graph.facebook.com/v19.0/{ig.get('ig_user_id')}/media"
r_ig = requests.get(ig_url, params={
    "fields": "id,caption,media_type,like_count,comments_count,timestamp,permalink",
    "access_token": ig.get("access_token"),
    "limit": 5
})
print("IG Media status:", r_ig.status_code)
print("IG Media data:", r_ig.json())

print("\n--- TESTING THREADS ---")
th = b.get("threads", {})
th_url = f"https://graph.threads.net/v1.0/{th.get('user_id')}/threads"
r_th = requests.get(th_url, params={
    "fields": "id,media_product_type,media_type,text,permalink,timestamp",
    "access_token": th.get("access_token"),
    "limit": 5
})
print("Threads status:", r_th.status_code)
print("Threads data:", r_th.json())
