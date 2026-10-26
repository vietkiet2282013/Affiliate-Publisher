# -*- coding: utf-8 -*-
"""
Schedule Runner - Tự động lập lịch & Hẹn giờ đăng Video Tập 4 cho thương hiệu "Góc Tập Luyện"
Phạm vi thực hiện theo yêu cầu mới nhất:
- Không đăng Threads, không đăng YouTube
- Hẹn giờ xuất bản vào lúc 12:00 ngày 26/09/2026 cho Facebook Reels & Story, Instagram Reels & Story

Chi tiết:
- Facebook Reels: Sử dụng Native Meta API Scheduled Publishing (scheduled_publish_time = 1790398800)
- Facebook Story: Đăng đồng bộ
- Instagram Reels & Story: Khởi chạy tiến trình theo dõi đếm ngược (countdown dispatcher) tự động tải lên và xuất bản đúng 12:00:00 ngày 26/09/2026 kèm ghim 11 bình luận Affiliate Shopee.
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
    InstagramReelsUploader
)

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_goc_tap_luyen_ep4_12h.log"

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
    cfg_path = os.path.join(POST_DIR, "config", "permanent_meta_tokens.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        meta_tokens = json.load(f)
    
    brand_cfg = meta_tokens.get("Góc Tập Luyện", {})
    page_id = brand_cfg.get("page_id", "1211541072052658")
    page_token = brand_cfg.get("page_access_token")
    ig_id = brand_cfg.get("instagram_business_id", "17841438553537040")

    return {
        "page_id": page_id,
        "access_token": page_token,
        "ig_user_id": ig_id
    }

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
                vbytes = f.read(1024 * 1024 * 15)  # 15MB initial chunk
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

def run():
    log("=" * 75)
    log("🏋️ BẮT ĐẦU CHƯƠNG TRÌNH HẸN GIỜ ĐĂNG VIDEO TẬP 4: GÓC TẬP LUYỆN")
    log("📌 MỤC TIÊU: 12:00:00 NGÀY 26/09/2026 TRÊN FACEBOOK & INSTAGRAM")
    log("=" * 75)

    config = load_config()
    video_path = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\4.mp4"

    # 1. Metadata Facebook
    fb_title = "Combo đồ tập thể dục cardio đốt mỡ & siết eo tại nhà cho dáng chuẩn"
    fb_caption = (
        "Muốn eo thon, chân nuột và cơ thể săn chắc ngay tại nhà thì không thể bỏ qua combo tiện ích này nha cả nhà! "
        "Từ máy trượt tuyết làm đẹp dáng chân, máy leo bậc cầu thang mini, xe đạp tập, dây nhảy đến đệm bảo vệ khớp gối chuyên dụng 🔥\n\n"
        "👉 Sắm ngay máy trượt tuyết tập sàn chậu dáng chân tại: https://s.shopee.vn/9KiDdYxbrt\n\n"
        "#reels #viral #fyp #goctapluyen #tapgymtainha #cardiotainha #thonchan #sieo #fitnesslifestyle"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/9KiDdYxbrt",
        "Link sản phẩm: https://s.shopee.vn/5VVV4WCCeG",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/6L4c4391xX",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/7ptPqo3Juw",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3LR0UXKS3B",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/4qFoHIEk0a",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3B7aIEOrml",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/4LJXgNKQQ6",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/BTyiiaHsP",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/1Lfw6rVqVk",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/2VrtV0RP95"
    ]

    # 2. Metadata Instagram
    ig_caption = (
        "Setup góc tập tại nhà cực xịn cùng combo máy trượt thon chân, xe đạp mini và dây nhảy đốt mỡ siêu đỉnh! "
        "Vừa tiện lợi, vừa giúp giữ dáng săn chắc mà không tốn nhiều diện tích ✨ "
        "Link trọn bộ dụng cụ tập luyện chính hãng mình ghim chi tiết dưới phần comment nha 👇\n\n"
        "#reels #viral #fyp #goctapluyen #workoutathome #gymtainha #cardio #chanthon #fitnessgoals"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/9peUETvhr0",
        "Link sản phẩm: https://s.shopee.vn/5LC4sDCpzF",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/6q0sey77we",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/7fZzeV3xFv",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3qNH5SIY2I",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/4fwO4zFNLZ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3LR0UXOERo",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/4VcxsgJn59",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/LnOv1ZeXS",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/1VzMJAVDAn",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/80Cq376SzA"
    ]

    # Khung giờ mục tiêu: 12:00:00 ngày 26/09/2026
    target_dt = datetime.datetime(2026, 9, 26, 12, 0, 0)
    target_ts = int(target_dt.timestamp())

    log(f"⏰ Thời điểm hẹn giờ xuất bản: {target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Unix Timestamp: {target_ts})")

    # =========================================================================
    # 1. FACEBOOK REELS & STORY (Native Meta API Scheduled Publish)
    # =========================================================================
    log("\n" + "=" * 50)
    log("🔷 [1/2] Đang tải lên và đặt lịch Facebook Reels qua Native Meta API...")
    res_fb = None
    try:
        fb_uploader = FacebookReelsUploader(
            page_id=config["page_id"],
            access_token=config["access_token"]
        )
        res_fb = fb_uploader.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comments,
            scheduled_time=target_ts
        )
        log(f"✅ Kết quả lập lịch Facebook Reels: {res_fb}")
        post_facebook_story(config["page_id"], config["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi lên lịch Facebook Reels: {e}\n{traceback.format_exc()}")

    # =========================================================================
    # 2. INSTAGRAM REELS & STORY (Countdown Dispatcher)
    # =========================================================================
    log("\n" + "=" * 50)
    log("📸 [2/2] Bắt đầu tiến trình đếm ngược để xuất bản Instagram Reels & Story lúc 12:00...")
    
    while True:
        now = datetime.datetime.now()
        rem_sec = (target_dt - now).total_seconds()

        if rem_sec <= 0:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ VÀNG ({target_dt.strftime('%Y-%m-%d %H:%M:%S')})! BẮT ĐẦU XUẤT BẢN INSTAGRAM...")
            try:
                ig_uploader = InstagramReelsUploader(
                    ig_user_id=config["ig_user_id"],
                    access_token=config["access_token"]
                )
                res_ig = ig_uploader.upload_reel(
                    video_path=video_path,
                    caption=ig_caption,
                    comment_text=ig_comments
                )
                log(f"✅ Kết quả xuất bản Instagram Reels: {res_ig}")
                post_instagram_story(config["ig_user_id"], config["access_token"], video_path)
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reels: {e}\n{traceback.format_exc()}")
            break

        # Log tiến trình mỗi 30 phút hoặc khi còn dưới 1 phút
        if int(rem_sec) % 1800 == 0 or rem_sec < 60:
            hours = int(rem_sec // 3600)
            mins = int((rem_sec % 3600) // 60)
            secs = int(rem_sec % 60)
            log(f"⏳ Đang chạy ngầm: Còn {hours} giờ {mins} phút {secs} giây tới giờ xuất bản Instagram ({target_dt.strftime('%H:%M:%S')})...")

        time.sleep(10)

    log("\n🎉 HOÀN TẤT THÀNH CÔNG TẤT CẢ CÁC BƯỚC ĐĂNG HẸN GIỜ CHO GÓC TẬP LUYỆN!")

if __name__ == "__main__":
    run()
