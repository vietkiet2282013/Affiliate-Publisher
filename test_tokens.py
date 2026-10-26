import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"c:\Affiliate\post1\POST"
with open(os.path.join(POST_DIR, "config", "brands.json"), encoding="utf-8") as f:
    brands = json.load(f)

# Kiểm tra Facebook token của brand đầu tiên hoặc tìm brand có token còn sống
print(f"Tổng số brands: {len(brands)}")
for k, v in brands.items():
    fb_tok = v.get("facebook", {}).get("access_token", "")
    page_id = v.get("facebook", {}).get("page_id", "")
    r = requests.get(f"https://graph.facebook.com/v19.0/{page_id}?fields=id,name&access_token={fb_tok}")
    print(f"Brand {k}: FB status {r.status_code}")
    if r.status_code == 200:
        print("  -> Page info:", r.json())
        # Thử lấy videos
        rv = requests.get(f"https://graph.facebook.com/v19.0/{page_id}/videos?fields=id,title,description,created_time,views,likes.summary(true),comments.summary(true)&access_token={fb_tok}&limit=3")
        print("  -> Videos rv status:", rv.status_code)
        if rv.status_code == 200:
            print("  -> Videos sample:", json.dumps(rv.json(), ensure_ascii=False)[:300])
        break
