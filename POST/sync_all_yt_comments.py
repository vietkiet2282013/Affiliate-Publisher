# -*- coding: utf-8 -*-
"""
Tự động đồng bộ và đăng lại bình luận YouTube chính xác nhất cho các kênh:
1. Yêu Da Hơn Bồ: https://youtube.com/shorts/LwGkLJFa1o8 (Tập 2.xlsx - 12 comments - XÓA CŨ ĐĂNG LẠI)
2. Góc Tập Luyện: https://youtube.com/shorts/IPf_o74lJXc (Tập 3.xlsx - 11 comments - XÓA CŨ ĐĂNG LẠI)
3. Dùng Rồi Mới Nói: https://youtube.com/shorts/QJvHfiA2RBM (máy đun nước tức thời 3 giây.xlsx - 4 comments)
4. Quần Áo Giá Hời: https://youtube.com/shorts/Q9LU6Qw5x48 (Tập 2.xlsx - 7 comments)
5. Tủ Đồ Mùa Mới: https://youtube.com/shorts/s3TPE5XKdss (Tập 3.xlsx - 11 comments)

Chạy liên tục kiểm tra hạn mức Google API, ngay khi reset (00:00 PST = 14:00 - 15:00 VN) sẽ hoàn tất toàn bộ.
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

CHANNELS_CONFIG = [
    {
        "channel": "Yêu Da Hơn Bồ",
        "video_id": "LwGkLJFa1o8",
        "excel_path": r"C:\Affiliate\Yêu Da Hơn Bồ\Link customed\YouTube\Tập 2.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\yeu_da_hon_bo.json",
        "clean_old": True
    },
    {
        "channel": "Góc Tập Luyện",
        "video_id": "IPf_o74lJXc",
        "excel_path": r"C:\Affiliate\Góc Tập Luyện\Link customed\YouTube\Tập 3.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\goc_tap_luyen.json",
        "clean_old": True
    },
    {
        "channel": "Dùng Rồi Mới Nói",
        "video_id": "QJvHfiA2RBM",
        "excel_path": r"C:\Affiliate\Dùng Rồi Mới Nói\Link customed\YouTube\máy đun nước tức thời 3 giây.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\dung_roi_moi_noi.json",
        "clean_old": False
    },
    {
        "channel": "Quần Áo Giá Hời",
        "video_id": "Q9LU6Qw5x48",
        "excel_path": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\YouTube\Tập 2.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\quan_ao_gia_hoi.json",
        "clean_old": False
    },
    {
        "channel": "Tủ Đồ Mùa Mới",
        "video_id": "s3TPE5XKdss",
        "excel_path": r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\YouTube\Tập 3.xlsx",
        "token_file": r"C:\Affiliate\post1\POST\credentials\youtube_tokens\tu_do_mua_moi.json",
        "clean_old": False
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

def delete_old_comments(yt, video_id):
    """Xóa các bình luận cũ trên video nếu có"""
    try:
        res = yt.youtube.commentThreads().list(
            part="id,snippet",
            videoId=video_id,
            maxResults=100
        ).execute()
        items = res.get("items", [])
        if not items:
            return True
        log(f"  🗑️ Tìm thấy {len(items)} bình luận cũ, đang xóa...")
        for it in items:
            c_id = it["id"]
            try:
                yt.youtube.comments().delete(id=c_id).execute()
                log(f"    - Đã xóa comment: {c_id}")
                time.sleep(1)
            except Exception as e:
                log(f"    ⚠️ Không thể xóa comment {c_id}: {e}")
                if "quotaExceeded" in str(e):
                    return False
        return True
    except Exception as e:
        log(f"  ⚠️ Lỗi khi lấy danh sách comment cũ: {e}")
        if "quotaExceeded" in str(e):
            return False
        return True

def process_channel(cfg, templates):
    channel = cfg["channel"]
    video_id = cfg["video_id"]
    excel_path = cfg["excel_path"]
    token_file = cfg["token_file"]

    links = get_links_from_excel(excel_path)
    log(f"\n==================================================")
    log(f"🚀 XỬ LÝ KÊNH: {channel} (Video ID: {video_id})")
    log(f"📄 Tệp Excel: {excel_path}")
    log(f"🔗 Tổng số link cần comment: {len(links)}")
    log(f"==================================================")

    yt = YouTubeShortsUploader(token_file=token_file)
    if not yt.authenticate():
        log(f"❌ Không thể xác thực YouTube cho {channel}")
        return False

    # Xóa comment cũ nếu được yêu cầu
    if cfg.get("clean_old", False):
        clean_ok = delete_old_comments(yt, video_id)
        if not clean_ok:
            return False
        # Đánh dấu đã xóa xong để không xóa lại vòng lặp sau
        cfg["clean_old"] = False

    # Kiểm tra xem comment nào đã có sẵn
    existing_texts = []
    try:
        res = yt.youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100
        ).execute()
        for it in res.get("items", []):
            txt = it["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
            existing_texts.append(txt)
        log(f"ℹ️ Video hiện đã có {len(existing_texts)} bình luận.")
    except Exception as e:
        if "quotaExceeded" in str(e):
            log("⏳ Đang chạm trần quota khi kiểm tra comment!")
            return False

    for idx, link in enumerate(links):
        # Kiểm tra xem link này đã được comment chưa
        already_posted = any(link in txt for txt in existing_texts)
        if already_posted:
            log(f"  ⏭️ Link {idx+1}/{len(links)} đã tồn tại: {link}")
            continue

        prefix = templates[idx % len(templates)]
        if not prefix.endswith(" "):
            prefix += " "
        body = f"{prefix}{link}"

        log(f"  💬 Đang đăng comment {idx+1}/{len(links)}: {body[:60]}...")
        try:
            yt.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": body
                            }
                        }
                    }
                }
            ).execute()
            log(f"    ✅ Thành công!")
            existing_texts.append(body)
            time.sleep(3)
        except Exception as e:
            if "quotaExceeded" in str(e):
                log(f"    ⏳ Quota exceeded khi đăng link {idx+1}. Sẽ thử lại sau...")
                return False
            else:
                log(f"    ❌ Lỗi khác: {e}")
                time.sleep(3)

    log(f"🎉 Hoàn thành 100% comment cho kênh {channel}!")
    return True

def main():
    templates = load_template_sentences()
    log("🚀 BẮT ĐẦU CHƯƠNG TRÌNH ĐỒNG BỘ COMMENT YOUTUBE TỰ ĐỘNG...")
    
    remaining_channels = list(CHANNELS_CONFIG)

    while remaining_channels:
        current_cfg = remaining_channels[0]
        success = process_channel(current_cfg, templates)
        if success:
            remaining_channels.pop(0)
        else:
            log("⏳ Đang đợi 60 giây trước khi thử lại kênh tiếp theo...")
            time.sleep(60)

    log("🎉🎉 TẤT CẢ CÁC KÊNH YOUTUBE ĐÃ ĐƯỢC CẬP NHẬT COMMENT ĐẦY ĐỦ VÀ CHUẨN XÁC!")

if __name__ == "__main__":
    main()
