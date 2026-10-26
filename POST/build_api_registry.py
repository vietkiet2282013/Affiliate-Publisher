import os
import sys
import json
import glob
import re

POST_DIR = r"C:\Affiliate\post1\POST"
registry_file = os.path.join(POST_DIR, "config", "api_published_videos.json")

registry = {}
if os.path.exists(registry_file):
    try:
        with open(registry_file, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception:
        registry = {}

# 1. Seed from schedule_queue.json
q_path = os.path.join(POST_DIR, "config", "schedule_queue.json")
if os.path.exists(q_path):
    try:
        with open(q_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                tid = item.get("id")
                if tid:
                    registry[str(tid)] = {
                        "is_api": True,
                        "platform": item.get("platforms", ["unknown"])[0],
                        "brand_key": item.get("brand_key"),
                        "caption": item.get("caption", "")[:100],
                        "app": "Affiliate Scheduler Worker"
                    }
    except Exception as e:
        print("Error reading queue:", e)

# 2. Seed from summary and result files
for sf in glob.glob(os.path.join(POST_DIR, "config", "*summary*.json")) + glob.glob(os.path.join(POST_DIR, "config", "*result*.json")):
    try:
        with open(sf, "r", encoding="utf-8") as f:
            d = json.load(f)
            res = d.get("results", {})
            for p, pdata in res.items():
                if isinstance(pdata, dict):
                    vid = pdata.get("video_id")
                    url = pdata.get("shorts_url") or pdata.get("reel_url") or pdata.get("permalink")
                    for key in [vid, url]:
                        if key:
                            registry[str(key)] = {
                                "is_api": True,
                                "platform": p,
                                "app": "Meta/YouTube API Publisher"
                            }
    except Exception as e:
        print("Error reading summary:", e)

# 3. Seed from logs
for lf in glob.glob(os.path.join(POST_DIR, "config", "*.log")) + glob.glob(os.path.join(POST_DIR, "*.log")):
    try:
        content = open(lf, "r", encoding="utf-8", errors="ignore").read()
        for m in re.findall(r'shorts/([a-zA-Z0-9_-]{11})', content):
            registry[m] = {"is_api": True, "platform": "YouTube", "app": "YouTube Data API"}
        for m in re.findall(r'reel/(\d+)', content):
            registry[m] = {"is_api": True, "platform": "Facebook/Instagram", "app": "Meta Graph API"}
        for m in re.findall(r'video_id[\"\':\s]+([a-zA-Z0-9_-]+)', content):
            registry[m] = {"is_api": True, "platform": "API", "app": "System API"}
    except Exception:
        pass

# Add recently tested videos
registry["nc-5tU6fg68"] = {"is_api": True, "platform": "YouTube", "app": "YouTube Data API"}
registry["1873051327437753"] = {"is_api": True, "platform": "Facebook", "app": "My_Post"}

with open(registry_file, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

print(f"Successfully built api_published_videos.json with {len(registry)} entries!")
