# -*- coding: utf-8 -*-
"""
Schedule Runner - Tự động lập lịch & Hẹn giờ đăng Video "Đồng Hồ Báo Thức"
Cho thương hiệu: Nói Thật Dùng Thật
Lên 3 nền tảng (Bỏ Threads theo yêu cầu mới):
- YouTube Shorts (Native Scheduled via Google API RFC 3339)
- Facebook Reels (Meta API Scheduled Timestamp) + Facebook Page Story
- Instagram Reels + Story (Chạy ngầm đếm ngược đến mốc giờ)

Khung giờ: 12:00:00 trưa nay (2026-09-26), giãn cách nhẹ giữa các nền tảng:
- YouTube Shorts: 12:00:00 (UTC 05:00:00)
- Facebook Reels & Story: 12:05:00 (Timestamp)
- Instagram Reels & Story: 12:10:00
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_noi_that_dung_that_dong_ho.log"

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
    return brands.get("noi_that_dung_that", {})

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
                vbytes = f.read()
            r_up = requests.post(
                f"https://graph.facebook.com/v19.0/{upload_session_id}",
                headers=headers,
                data=vbytes,
                timeout=120
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

def run_schedule():
    log("=" * 75)
    log("⏰ BẮT ĐẦU HẸN GIỜ ĐĂNG VIDEO: NÓI THẬT DÙNG THẬT - ĐỒNG HỒ BÁO THỨC / HẸN GIỜ")
    log("=" * 75)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\đồng hồ báo thức.mp4"

    # 1. YouTube Shorts Metadata & Links
    yt_title = "Bí quyết tập trung học bài & làm việc không trì hoãn với đồng hồ hẹn giờ thông minh #Shorts"
    yt_desc = (
        "Tổng hợp các mẫu đồng hồ hẹn giờ đếm ngược Pomodoro, đồng hồ báo thức học sinh thông minh giúp bạn rèn luyện kỷ luật, "
        "quản lý thời gian hiệu quả và tăng 200% năng suất làm việc mỗi ngày!\n\n"
        "👉 Chi tiết từng sản phẩm chính hãng mình ghim dưới phần bình luận nhé 👇\n\n"
        "#Shorts #noithatdungthat #donghobaothuc #donghohengio #pomodoro #meovat #hocsinh #desksetup"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7VGZRMGrbH",
        "Link sản phẩm: https://s.shopee.vn/3g3qsJVSNc",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/3B7aHOXMOb",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/4fwO49ReLy",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4B07TETYMx",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/LnOuBi99I",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2VrtUAZtkn",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/1Lfw61eL7e",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/8fSWpVCQF9"
    ]

    # 2. Facebook Reels Metadata & Links
    fb_title = "Đồng hồ hẹn giờ Pomodoro & báo thức thông minh giúp rèn kỷ luật học tập"
    fb_caption = (
        "Ai hay bị mất tập trung khi học bài hay làm việc thì sắm ngay một em đồng hồ đếm ngược trực quan này nha! "
        "Giúp phân chia thời gian chuẩn phương pháp Pomodoro, rèn thói quen tập trung và bứt phá hiệu suất 🔥\n\n"
        "👉 Mua ngay Đồng hồ LED đếm ngược Deli chính hãng tại: https://s.shopee.vn/5VVV3gOTep\n\n"
        "#reels #viral #fyp #noithatdungthat #donghobaothuc #donghohengio #pomodoro #meovathocxong"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/5VVV3gOTep",
        "Link sản phẩm: https://s.shopee.vn/70KIqRIlcC",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/3qNH4cUp2f",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2gBJgTZGPW",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4qFoGSR111",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/1135hPfbnM",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/W6p6UhVoL",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/20vctFbnli",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/1VzMIKdhmh"
    ]

    # 3. Instagram Reels Metadata & Links
    ig_caption = (
        "Rèn thói quen tập trung đỉnh cao với bộ sưu tập đồng hồ hẹn giờ đếm ngược & báo thức siêu xinh! "
        "Dùng cho góc học tập hay bàn làm việc đều cực xịn ✨ "
        "Link trọn bộ đồng hồ chính hãng mình ghim chi tiết dưới phần comment nha 👇\n\n"
        "#reels #viral #fyp #noithatdungthat #donghohengio #pomodoro #studywithme #deskdecor"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7fZzdfGEGG",
        "Link sản phẩm: https://s.shopee.vn/7Adj2kI8HF",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/3LR0ThWj3a",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2qUjsmYd4Z",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4LJXfXSv1w",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/1BMVtieySP",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1AYVZjPpG",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/2BF35YbAQl",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/9AOnQQAWEC"
    ]

    now = datetime.datetime.now()
    today_date = now.date()

    # Thiết lập mốc giờ 12:00 trưa hôm nay (2026-09-26)
    yt_target_dt = datetime.datetime.combine(today_date, datetime.time(12, 0, 0))
    fb_target_dt = datetime.datetime.combine(today_date, datetime.time(12, 5, 0))
    ig_target_dt = datetime.datetime.combine(today_date, datetime.time(12, 10, 0))

    if yt_target_dt <= now:
        log("⚠️ Thời gian 12:00 trưa hôm nay đã qua, đặt mốc hẹn giờ cho 12:00 trưa ngày mai!")
        yt_target_dt += datetime.timedelta(days=1)
        fb_target_dt += datetime.timedelta(days=1)
        ig_target_dt += datetime.timedelta(days=1)

    fb_target_ts = int(fb_target_dt.timestamp())

    log(f"📅 LỊCH TRÌNH XUẤT BẢN CHI TIẾT (12:00 TRƯA):")
    log(f"  🔴 [1] YouTube Shorts:        {yt_target_dt.strftime('%Y-%m-%d %H:%M:%S')} (UTC: {(yt_target_dt - datetime.timedelta(hours=7)).strftime('%Y-%m-%dT%H:%M:%SZ')})")
    log(f"  🔷 [2] Facebook Reels:        {fb_target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {fb_target_ts})")
    log(f"  📸 [3] Instagram Reels:       {ig_target_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # =========================================================================
    # 1. YOUTUBE SHORTS (Native API Scheduled Publish)
    # =========================================================================
    log("\n" + "=" * 50)
    log("🔴 [1/3] Khởi tạo & Đặt lịch YouTube Shorts (Google API v3)...")
    res_yt = None
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/noi_that_dung_that.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)

        utc_target = yt_target_dt - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")

        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "noithatdungthat", "donghobaothuc", "donghohengio", "pomodoro", "meovat"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        log(f"✅ Kết quả YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi lên lịch YouTube Shorts: {e}\n{traceback.format_exc()}")

    # =========================================================================
    # 2. FACEBOOK REELS & STORY (Native Meta API Scheduled Publish)
    # =========================================================================
    log("\n" + "=" * 50)
    log("🔷 [2/3] Khởi tạo & Đặt lịch Facebook Reels (Meta API Scheduled)...")
    res_fb = None
    try:
        fb_cfg = brand_data.get("facebook", {})
        fb_uploader = FacebookReelsUploader(
            page_id=fb_cfg["page_id"],
            access_token=fb_cfg["access_token"]
        )
        res_fb = fb_uploader.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comments,
            scheduled_time=fb_target_ts
        )
        log(f"✅ Kết quả Facebook Reels: {res_fb}")
        post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi lên lịch Facebook Reels: {e}\n{traceback.format_exc()}")

    log("\n" + "=" * 50)
    log("📊 TỔNG HỢP TRẠNG THÁI GIAI ĐOẠN 1 (NATIVE SCHEDULING):")
    log(f"  - YouTube Shorts Video ID: {res_yt.get('video_id') if res_yt else 'N/A'}")
    log(f"  - Facebook Reel Video ID:  {res_fb.get('video_id') if res_fb else 'N/A'}")
    log("=" * 50)

    # =========================================================================
    # 3. INSTAGRAM TIMED DISPATCHER
    # =========================================================================
    log("\n⏳ Bắt đầu vòng lặp theo dõi xuất bản Instagram Reels (12:10:00)...")

    ig_published = False

    while not ig_published:
        current_time = datetime.datetime.now()
        rem_ig = (ig_target_dt - current_time).total_seconds()
        if rem_ig <= 0:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ ({ig_target_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN INSTAGRAM REELS & STORY...")
            try:
                ig_cfg = brand_data.get("instagram", {})
                ig_uploader = InstagramReelsUploader(
                    ig_user_id=ig_cfg["ig_user_id"],
                    access_token=ig_cfg["access_token"]
                )
                res_ig = ig_uploader.upload_reel(
                    video_path=video_path,
                    caption=ig_caption,
                    comment_text=ig_comments
                )
                log(f"✅ Kết quả Instagram Reels: {res_ig}")
                post_instagram_story(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
                ig_published = True
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reels: {e}\n{traceback.format_exc()}")
                ig_published = True

        if int(rem_ig) % 300 == 0 or rem_ig < 30:
            log(f"⏳ Đang chạy ngầm theo dõi IG: Còn {int(rem_ig // 60)} phút {int(rem_ig % 60)} giây tới mốc xuất bản...")

        time.sleep(10)

    log("\n🎉 HOÀN TẤT LẬP LỊCH VÀ XUẤT BẢN THÀNH CÔNG CHO CẢ 3 NỀN TẢNG (YOUTUBE, FACEBOOK, INSTAGRAM) VÀO MỐC 12:00 TRƯA!")

if __name__ == "__main__":
    run_schedule()
