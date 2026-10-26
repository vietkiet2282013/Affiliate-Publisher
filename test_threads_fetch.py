import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"c:\Affiliate\post1\POST"
with open(os.path.join(POST_DIR, "config", "brands.json"), encoding="utf-8") as f:
    brands = json.load(f)

for b_key, b_val in brands.items():
    th = b_val.get("threads", {})
    uid = th.get("user_id")
    tok = th.get("access_token")
    if not tok:
        continue
    r = requests.get(f"https://graph.threads.net/v1.0/{uid}/threads", params={
        "fields": "id,media_product_type,media_type,text,permalink,timestamp",
        "access_token": tok,
        "limit": 3
    })
    print(f"[{b_key}] Threads status: {r.status_code}")
    if r.status_code == 200:
        data = r.json().get("data", [])
        print(f"  -> Total posts returned: {len(data)}")
        for item in data:
            post_id = item["id"]
            # Thử lấy insights của bài viết nếu có
            r_ins = requests.get(f"https://graph.threads.net/v1.0/{post_id}/insights", params={
                "metric": "views,likes,replies,reposts,quotes",
                "access_token": tok
            })
            ins_data = r_ins.json() if r_ins.status_code == 200 else {}
            print(f"    📝 Post ID: {post_id} | Text: {item.get('text', '')[:30]}... | Date: {item.get('timestamp')}")
            print(f"       Insights: {ins_data}")
        break
