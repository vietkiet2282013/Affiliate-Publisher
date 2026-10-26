# -*- coding: utf-8 -*-
import json, glob, re, os, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 80)
print("1. KIỂM TRA HÀNG ĐỢI SCHEDULER (schedule_queue.json)")
print("=" * 80)
queue_path = r"c:\Affiliate\post1\POST\config\schedule_queue.json"
if os.path.exists(queue_path):
    with open(queue_path, "r", encoding="utf-8") as f:
        queue = json.load(f)
    for t in queue:
        print(f"[{t.get('status')}] Brand: {t.get('brand_key'):<20} | Platform: {str(t.get('platforms')):<15} | Lên lịch: {t.get('scheduled_time_str')} | Xong: {t.get('completed_at')}")

print("\n" + "=" * 80)
print("2. QUÉT LINK TỪ CÁC TASK LOGS")
print("=" * 80)
log_dir = r"C:\Users\ADMIN\.gemini\antigravity-ide\brain\e822a186-ab39-4fc3-8b21-be0fa2f01696\.system_generated\tasks"
log_files = glob.glob(os.path.join(log_dir, "*.log"))
for lf in sorted(log_files, key=os.path.getmtime):
    with open(lf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    yts = re.findall(r"https?://(?:www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]+", content)
    fbs = re.findall(r"https?://(?:www\.)?facebook\.com/reel/[0-9]+", content)
    igs = re.findall(r"https?://(?:www\.)?instagram\.com/reel/[a-zA-Z0-9_-]+/?", content)
    brand_match = re.findall(r"BẮT ĐẦU [^\n]+: ([^\n]+)", content)
    bname = brand_match[0] if brand_match else os.path.basename(lf)
    if yts or fbs or igs:
        print(f"\n📂 Tệp log: {os.path.basename(lf)} | Thương hiệu: {bname}")
        for y in set(yts): print("  🔴 YouTube:", y)
        for b in set(fbs): print("  🔷 Facebook:", b)
        for i in set(igs): print("  📸 Instagram:", i)

print("\n" + "=" * 80)
print("3. TRUY VẤN MEDIA GẦN ĐÂY TỪ META GRAPH API & THREADS API")
print("=" * 80)
brands_path = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_path, "r", encoding="utf-8") as f:
    brands = json.load(f)

for bkey, bcfg in brands.items():
    bname = bcfg.get("name", bkey)
    print(f"\n--- {bname} ({bkey}) ---")
    
    # Check Instagram
    ig_cfg = bcfg.get("instagram", {})
    ig_id = ig_cfg.get("ig_user_id")
    ig_tok = ig_cfg.get("access_token")
    if ig_id and ig_tok:
        try:
            r = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}/media?fields=id,caption,permalink,timestamp,media_type&limit=2&access_token={ig_tok}", timeout=10).json()
            if "data" in r:
                for m in r["data"]:
                    print(f"  📸 IG Reel: {m.get('permalink')} (Time: {m.get('timestamp')})")
            else:
                print(f"  📸 IG Error: {r.get('error', {}).get('message')}")
        except Exception as e:
            print(f"  📸 IG Query failed: {e}")

    # Check Threads
    th_cfg = bcfg.get("threads", {})
    th_tok = th_cfg.get("access_token")
    if th_tok:
        try:
            r = requests.get(f"https://graph.threads.net/v1.0/me/threads?fields=id,text,permalink,timestamp&limit=2&access_token={th_tok}", timeout=10).json()
            if "data" in r:
                for th in r["data"]:
                    print(f"  🧵 Threads: {th.get('permalink')} (Time: {th.get('timestamp')})")
            else:
                print(f"  🧵 Threads Error: {r.get('error', {}).get('message')}")
        except Exception as e:
            print(f"  🧵 Threads Query failed: {e}")
