# -*- coding: utf-8 -*-
"""
Background auto-publisher watchdog for Instagram Reels
Theo dõi container ID khi Meta server xử lý FINISHED thì tự động xuất bản và ghim 9 comments
"""
import os
import sys
import time
import json
import requests
import openpyxl

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
LOG_FILE = os.path.join(POST_DIR, "config", "scheduler_tram_cong_nghe_ig_watchdog.log")

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

with open(r"C:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)["cham_cong_nghe"]["instagram"]

token = cfg["access_token"]
user_id = cfg["ig_user_id"]

p = r"C:\Affiliate\Trạm Công Nghệ\Link customed\Instagram\đèn màn hình máy tính.xlsx"
wb = openpyxl.load_workbook(p)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
items = []
for r in rows[1:]:
    if r and len(r) > 2 and r[2]:
        items.append({"name": str(r[1]).strip() if r[1] else "", "url": str(r[2]).strip()})

templates = [
    "Link sản phẩm ở đây: ",
    "Link xem và mua hàng ngay tại đây nè: ",
    "Link sản phẩm ở đây nha mọi người: ",
    "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
    "Link sản phẩm: ",
    "Link sản phẩm ở đây cho ai cần nha: ",
    "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
    "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
    "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
    "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: "
]

containers = ["18111241954980917", "18111242221980917"]
log(f"🚀 Bắt đầu tiến trình Watchdog theo dõi xuất bản Instagram Reels ({containers})...")

published = False
for attempt in range(2880): # Check up to 24 hours
    for cid in containers:
        try:
            st = requests.get(f"https://graph.facebook.com/v19.0/{cid}", params={"fields": "id,status_code,status", "access_token": token}, timeout=30).json()
            st_code = st.get("status_code")
            if st_code == "FINISHED":
                log(f"🎉 Container {cid} đã FINISHED! Đang gọi media_publish...")
                pub = requests.post(f"https://graph.facebook.com/v19.0/{user_id}/media_publish", data={"creation_id": cid, "access_token": token}, timeout=30).json()
                log(f"Phản hồi xuất bản Instagram: {pub}")
                if "id" in pub:
                    media_id = pub["id"]
                    log(f"✅ ĐÃ XUẤT BẢN THÀNH CÔNG REEL: {media_id}")
                    # Post comments
                    for idx, it in enumerate(items, 1):
                        cmt_text = f"{templates[idx % len(templates)]}\n{it['url']}"
                        r_c = requests.post(f"https://graph.facebook.com/v19.0/{media_id}/comments", data={"message": cmt_text, "access_token": token}, timeout=30).json()
                        log(f"  Comment {idx}: {r_c}")
                        time.sleep(2)
                    published = True
                    break
        except Exception as e:
            log(f"⚠️ Exception: {e}")
    if published:
        break
    time.sleep(30)

log("🏁 Kết thúc tiến trình Watchdog Instagram!")
