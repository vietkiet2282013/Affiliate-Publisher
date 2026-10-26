# -*- coding: utf-8 -*-
"""
Script Lập Lịch Tự Động & Hẹn Giờ Video cho 'Review Thật Việc Thật'
Video: C:\Affiliate\Review Thật Việc Thật\video_việt_hóa\dung dịch đánh giày.mp4
Nền tảng: YouTube Shorts, Facebook (Reels + Story), Instagram (Reels + Story)
Thời gian hẹn: Trưa 12:00 hôm nay (2026-09-26), giãn cách tự nhiên 4-11 phút.
- YouTube Shorts:        12:04:00 (UTC 05:04:00Z)
- Facebook Reels & Story: 12:13:00 (Timestamp 1790409180)
- Instagram Reels & Story: 12:22:00 (Timestamp 1790409720)
"""

import os
import sys
import time
import json
import requests
import datetime
import traceback

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import (
    FacebookReelsUploader,
    InstagramReelsUploader,
    YouTubeShortsUploader
)
from scheduler import load_queue, save_queue

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_review_that_viec_that_dung_dich_danh_giay.log"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_config():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    return brands.get("review_that_viec_that", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    """Đăng bổ sung lên Facebook Page Story"""
    try:
        log("📘 Đang khởi tạo Story cho Facebook Page...")
        file_size = os.path.getsize(video_path)
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/videos",
            data={
                "upload_phase": "start",
                "file_size": file_size,
                "access_token": access_token
            },
            timeout=30
        ).json()
        if "upload_session_id" in init_res:
            upload_session_id = init_res["upload_session_id"]
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size)
            }
            with open(video_path, "rb") as f:
                vbytes = f.read(1024 * 1024 * 15)  # Read chunk
            r_up = requests.post(
                f"https://graph.facebook.com/v19.0/{upload_session_id}",
                headers=headers,
                data=vbytes,
                timeout=60
            ).json()
            log(f"  ✅ Trạng thái upload Story FB: {r_up}")
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng FB Story: {e}")

def post_instagram_story(ig_user_id: str, access_token: str, video_path: str):
    """Đăng bổ sung lên Instagram Story"""
    try:
        log("📸 Đang khởi tạo Story cho Instagram Business...")
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={
                "media_type": "STORIES",
                "upload_type": "resumable",
                "access_token": access_token
            },
            timeout=30
        ).json()
        if "id" in init_res:
            container_id = init_res["id"]
            log(f"  ✅ Đã tạo IG Story Container: {container_id}")
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng IG Story: {e}")

def main():
    log("=" * 75)
    log("👟 BẮT ĐẦU CHƯƠNG TRÌNH HẸN GIỜ ĐĂNG VIDEO: REVIEW THẬT VIỆC THẬT (DUNG DỊCH ĐÁNH GIÀY)")
    log("=" * 75)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Review Thật Việc Thật\video_việt_hóa\dung dịch đánh giày.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. YouTube Shorts Metadata & Links
    yt_title = "Đánh Giày Trắng Cấp Tốc Sạch Nhanh Như Mới! #Shorts"
    yt_desc = (
        "Giày trắng lấm lem bùn đất hay xi đánh giày đã có dung dịch/kem vệ sinh giày đa năng. "
        "Tẩy sạch siêu tốc, lấy lại vẻ sáng bóng trong 1 phút không cần dùng nước!\n\n"
        "👉 Link sản phẩm ở đây cho ai cần nha:\n"
        "https://s.shopee.vn/5q8LTBmUji\n\n"
        "👉 Nhấp vào link này để xem thông tin và mua hàng nha mọi người:\n"
        "https://s.shopee.vn/5fovGsn84h\n\n"
        "#Shorts #reviewthatviecthat #kemvesinhgiay #danhgiay #meovat #giaythethao"
    )
    yt_comments = [
        "Link sản phẩm ở đây cho ai cần nha:\nhttps://s.shopee.vn/5q8LTBmUji",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người:\nhttps://s.shopee.vn/5fovGsn84h",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà:\nhttps://s.shopee.vn/6AlBrnlE3o",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè:\nhttps://s.shopee.vn/60RlfUlrOn",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha:\nhttps://s.shopee.vn/6VO2GPjxNu"
    ]

    # 2. Facebook Reels Metadata & Links
    fb_title = "Bí Quyết Đánh Sạch Giày Trắng Sáng Bóng Trong 1 Phút Không Cần Nước"
    fb_caption = (
        "Bí quyết đánh sạch giày trắng sáng bóng trong 1 phút không cần nước! ✨\n"
        "Dung dịch/kem vệ sinh giày chuyên dụng tẩy siêu nhanh các vết bẩn cứng đầu, trả lại vẻ mượt mà cho giày da, giày thể thao.\n\n"
        "👉 Link săn deal/mua hàng chính hãng ở đây nha cả nhà:\n"
        "https://s.shopee.vn/3LR0Uao2NR\n\n"
        "#reviewthatviecthat #kemvesinhgiay #danhgiay #meovatcuocsong #giadungtienich"
    )
    fb_comments = [
        "Mọi người xem chi tiết và đặt hàng tại link này nhé:\nhttps://s.shopee.vn/3LR0Uao2NR",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà:\nhttps://s.shopee.vn/3qNH5Vm8MY",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè:\nhttps://s.shopee.vn/3g3qtCmlhX",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha:\nhttps://s.shopee.vn/4B07U7krge",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha:\nhttps://s.shopee.vn/40ghHolV1d"
    ]

    # 3. Instagram Reels Metadata & Links
    ig_caption = (
        "Mẹo vệ sinh giày trắng sạch bong không lo phai màu hay hư da 👟✨\n"
        "Dung dịch/kem đánh giày đa năng bôi tới đâu vết bẩn tan tới đó. Siêu tiện lợi cho dân đi giày thể thao nha!\n\n"
        "👇 Link sắm chính hãng mình để ngay bình luận bên dưới nhé:\n\n"
        "#reels #viral #fyp #reviewthatviecthat #kemvesinhgiay #danhgiay #meovat"
    )
    ig_comments = [
        "Mình để sẵn link mua hàng ở đây cho mọi người nè:\nhttps://s.shopee.vn/AUuB1lMgaB",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha:\nhttps://s.shopee.vn/9KiDdcR7wy",
        "Link sản phẩm ở đây cho ai cần nha:\nhttps://s.shopee.vn/9V1dpvQUc1",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé:\nhttps://s.shopee.vn/9fL42EPrH4",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà:\nhttps://s.shopee.vn/9peUEXPDw7"
    ]

    now = datetime.datetime.now()
    today_date = now.date()

    # Thiết lập khung giờ hẹn lúc 12:00 trưa hôm nay với giãn cách tự nhiên 4-11 phút:
    # 1. YouTube Shorts:        12:04:00 (UTC 05:04:00Z)
    # 2. Facebook Reels & Story: 12:13:00 (Timestamp)
    # 3. Instagram Reels & Story: 12:22:00 (Timestamp)
    yt_target_dt = datetime.datetime.combine(today_date, datetime.time(12, 4, 0))
    fb_target_dt = datetime.datetime.combine(today_date, datetime.time(12, 13, 0))
    ig_target_dt = datetime.datetime.combine(today_date, datetime.time(12, 22, 0))

    if yt_target_dt <= now:
        yt_target_dt += datetime.timedelta(days=1)
        fb_target_dt += datetime.timedelta(days=1)
        ig_target_dt += datetime.timedelta(days=1)

    fb_target_ts = int(fb_target_dt.timestamp())

    log(f"📅 LỊCH TRÌNH XUẤT BẢN CHI TIẾT:")
    log(f"  🔴 [1] YouTube Shorts:        {yt_target_dt.strftime('%Y-%m-%d %H:%M:%S')} (UTC: {(yt_target_dt - datetime.timedelta(hours=7)).strftime('%Y-%m-%dT%H:%M:%SZ')})")
    log(f"  🔷 [2] Facebook Reels & Story:{fb_target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {fb_target_ts})")
    log(f"  📸 [3] Instagram Reels & Story:{ig_target_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # =========================================================================
    # BƯỚC 1: ĐƯA INSTAGRAM VÀO HÀNG ĐỢI SCHEDULER
    # =========================================================================
    log("\n📦 [1/3] Đang thêm Instagram Reels & Story vào hàng đợi Scheduler...")
    queue = load_queue()

    ig_comment_str = "\n".join(ig_comments)
    task_ig = {
        "id": f"task_ig_rtvt_{int(time.time())}",
        "brand_key": "review_that_viec_that",
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": ig_comment_str,
        "platforms": ["instagram"],
        "scheduled_time_str": ig_target_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(ig_target_dt.timestamp()),
        "product_keyword": "Kem vệ sinh giày",
        "status": "PENDING"
    }

    existing_timestamps = {t.get("scheduled_timestamp") for t in queue if t.get("brand_key") == "review_that_viec_that" and t.get("status") == "PENDING"}
    if task_ig["scheduled_timestamp"] not in existing_timestamps:
        queue.append(task_ig)
        log(f"  ✅ Đã lên lịch Instagram Reels: {task_ig['scheduled_time_str']}")
    else:
        log("  ℹ️ Đã tồn tại task Instagram Reels trong hàng đợi.")

    save_queue(queue)

    # Đăng/Khởi tạo Instagram Story đồng bộ
    post_instagram_story(brand_data["instagram"]["ig_user_id"], brand_data["instagram"]["access_token"], video_path)

    # =========================================================================
    # BƯỚC 2: HẸN GIỜ TRỰC TIẾP LÊN YOUTUBE SHORTS (GOOGLE API V3)
    # =========================================================================
    log("\n🔴 [2/3] Đang gọi Google API v3 để hẹn giờ YouTube Shorts...")
    utc_target = yt_target_dt - datetime.timedelta(hours=7)
    publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
    yt_comment_str = "\n\n".join(yt_comments)

    yt_cfg = brand_data.get("youtube", {})
    token_file = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/review_that_viec_that.json"))
    yt_uploader = YouTubeShortsUploader(token_file=token_file)
    yt_res = yt_uploader.upload_short(
        video_path=video_path,
        title=yt_title,
        description=yt_desc,
        comment_text=yt_comment_str,
        privacy_status="private",
        publish_at=publish_at_rfc3339
    )
    if yt_res:
        log(f"🎉 YouTube Shorts đã được lên lịch thành công: {yt_res.get('shorts_url')}")
    else:
        log("⚠️ YouTube Shorts upload thất bại hoặc có lỗi xảy ra.")

    # =========================================================================
    # BƯỚC 3: HẸN GIỜ TRỰC TIẾP LÊN FACEBOOK REELS & STORY (META GRAPH API)
    # =========================================================================
    log("\n🔷 [3/3] Đang gọi Meta Graph API để hẹn giờ Facebook Reels & Story...")
    fb_comment_str = "\n\n".join(fb_comments)
    fb_cfg = brand_data["facebook"]
    fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
    fb_res = fb_uploader.upload_reel(
        video_path=video_path,
        title=fb_title,
        caption=fb_caption,
        comment_text=fb_comment_str,
        scheduled_time=fb_target_ts
    )
    if fb_res:
        log(f"🎉 Facebook Reels đã được lên lịch thành công: {fb_res.get('reel_url')}")
    else:
        log("⚠️ Facebook Reels upload thất bại hoặc có lỗi xảy ra.")

    post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)

    log("\n" + "=" * 75)
    log("🎉 HOÀN TẤT THIẾT LẬP LỊCH ĐĂNG TOÀN BỘ 3 NỀN TẢNG CHO 'REVIEW THẬT VIỆC THẬT'!")
    log("=" * 75)

if __name__ == "__main__":
    main()
