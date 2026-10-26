# -*- coding: utf-8 -*-
"""
Tự động đăng lại YouTube Shorts cho Quần Áo Giá Hời với video sửa lại:
C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\2-sửa-lại.mp4
kèm đầy đủ 7 comment chuẩn xác từ C:\Affiliate\Quần Áo Giá Hời\Link customed\YouTube\Tập 2.xlsx
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

VIDEO_PATH = r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\2-sửa-lại.mp4"
EXCEL_PATH = r"C:\Affiliate\Quần Áo Giá Hời\Link customed\YouTube\Tập 2.xlsx"
COMMENT_FILE = r"C:\Affiliate\post1\comment.txt"
TOKEN_FILE = r"C:\Affiliate\post1\POST\credentials\youtube_tokens\quan_ao_gia_hoi.json"

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

def main():
    log("=" * 70)
    log("🚀 BẮT ĐẦU ĐĂNG LẠI YOUTUBE SHORTS: QUẦN ÁO GIÁ HỜI (BẢN SỬA LẠI)")
    log("=" * 70)

    templates = load_template_sentences()
    correct_links = get_links_from_excel(EXCEL_PATH)
    log(f"📁 Tệp video: {VIDEO_PATH}")
    log(f"✅ Đã đọc {len(correct_links)} link từ Excel:")
    for i, l in enumerate(correct_links, 1):
        log(f"  {i}. {l}")

    comments_to_post = []
    for idx, link in enumerate(correct_links):
        prefix = templates[idx % len(templates)]
        if not prefix.endswith(" "):
            prefix += " "
        comments_to_post.append(f"{prefix}{link}")

    yt_title = "Gợi ý loạt áo khoác mùa đông cực xinh tôn dáng hack tuổi giá siêu hời #Shorts"
    yt_desc = (
        "Tổng hợp những mẫu áo khoác mùa đông xinh xắn, ấm áp từ cardigan, măng tô đến nỉ croptop trẻ trung năng động. "
        "Form dáng chuẩn chỉnh, phối đồ đi chơi đi làm cực kỳ tôn dáng và nổi bật!\n\n"
        "#Shorts #quanaogiahoi #aokhoacnu #cardigan #mangto #thoitrangnu #winteroutfit #review"
    )

    yt = YouTubeShortsUploader(token_file=TOKEN_FILE)
    if not yt.authenticate():
        log("❌ Không thể xác thực YouTube cho kênh Quần Áo Giá Hời!")
        return

    while True:
        log("⏳ Đang thử tải lên YouTube Shorts (Publish Now)...")
        try:
            res_yt = yt.upload_short(
                video_path=VIDEO_PATH,
                title=yt_title,
                description=yt_desc,
                tags=["Shorts", "quanaogiahoi", "aokhoac", "cardigan", "mangto", "thoitrangnu"],
                comment_text=comments_to_post,
                privacy_status="public",
                publish_at=None
            )
            if res_yt and res_yt.get("success"):
                log(f"🎉 ĐÃ ĐĂNG YOUTUBE SHORTS THÀNH CÔNG: {res_yt.get('shorts_url')}")
                break
            else:
                log(f"⚠️ Chưa thể tải lên: {res_yt}. Đang đợi hạn mức quota và thử lại sau 60 giây...")
                time.sleep(60)
        except Exception as e:
            log(f"⚠️ Gặp lỗi: {e}. Đang đợi quota reset để thử lại tự động...")
            time.sleep(60)

if __name__ == "__main__":
    main()
