# -*- coding: utf-8 -*-
"""
Tự động thêm comment YouTube chuẩn bị thiếu khi quota hồi phục:
- Quần Áo Giá Hời: https://youtube.com/shorts/Q9LU6Qw5x48 (7 comments)
- Tủ Đồ Mùa Mới: https://youtube.com/shorts/s3TPE5XKdss (6 comments còn lại)
- Góc Tập Luyện: https://youtube.com/shorts/IPf_o74lJXc (10 comments)
"""
import os
import sys
import time
import openpyxl
import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import YouTubeShortsUploader

COMMENT_FILE = r"C:\Affiliate\post1\comment.txt"

TASKS = [
    {
        "channel": "Quần Áo Giá Hời",
        "video_id": "Q9LU6Qw5x48",
        "excel_path": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\YouTube\Tập 2.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\quan_ao_gia_hoi.json",
        "start_idx": 0
    },
    {
        "channel": "Tủ Đồ Mùa Mới",
        "video_id": "s3TPE5XKdss",
        "excel_path": r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\YouTube\Tập 3.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\tu_do_mua_moi.json",
        "start_idx": 5 # đã đăng được 5 comment trước đó
    },
    {
        "channel": "Góc Tập Luyện",
        "video_id": "IPf_o74lJXc",
        "excel_path": r"C:\Affiliate\Góc Tập Luyện\Link customed\YouTube\Tập 2.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\goc_tap_luyen.json",
        "start_idx": 0
    }
]

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def load_template_sentences():
    with open(COMMENT_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def get_links_from_excel(path):
    wb = openpyxl.load_workbook(path)
    sheet = wb.active
    links = []
    for row in list(sheet.iter_rows(values_only=True))[1:]:
        if row and len(row) >= 3 and row[2]:
            l = str(row[2]).strip()
            if l.startswith("http"):
                links.append(l)
    return links

def run_comments():
    templates = load_template_sentences()
    
    for task in TASKS:
        channel = task["channel"]
        video_id = task["video_id"]
        token_file = task["token_file"]
        links = get_links_from_excel(task["excel_path"])
        start_idx = task["start_idx"]
        
        log(f"\n🚀 Đang xử lý kênh: {channel} (Video ID: {video_id})")
        yt = YouTubeShortsUploader(token_file=token_file)
        if not yt.authenticate():
            log(f"❌ Không thể xác thực cho {channel}")
            continue

        for idx in range(start_idx, len(links)):
            link = links[idx]
            prefix = templates[idx % len(templates)]
            if not prefix.endswith(" "):
                prefix += " "
            comment_body = f"{prefix}{link}"
            
            posted = False
            while not posted:
                try:
                    yt.youtube.commentThreads().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "videoId": video_id,
                                "topLevelComment": {
                                    "snippet": {
                                        "textOriginal": comment_body
                                    }
                                }
                            }
                        }
                    ).execute()
                    log(f"  ✅ Đã đăng comment {idx+1}/{len(links)}: {comment_body[:55]}...")
                    posted = True
                    time.sleep(3)
                except Exception as e:
                    if "quotaExceeded" in str(e):
                        log(f"  ⏳ Chạm trần quota YouTube API. Đợi 120 giây thử lại...")
                        time.sleep(120)
                    else:
                        log(f"  ❌ Lỗi đăng comment: {e}")
                        break

    log("🎉 ĐÃ HOÀN TẤT TẤT CẢ COMMENT YOUTUBE!")

if __name__ == "__main__":
    run_comments()
