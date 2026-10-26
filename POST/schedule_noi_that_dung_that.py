# -*- coding: utf-8 -*-
"""
Schedule Runner - Chạy ngầm tự động đăng hẹn giờ cho thương hiệu "Nói Thật Dùng Thật"
Lập lịch video "cạo lông mèo.mp4" lên 4 nền tảng:
- YouTube Shorts
- Facebook Reels (+ Story)
- Instagram Reels (+ Story)
- Threads
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
    YouTubeShortsUploader,
    ThreadsAPIUploader
)

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_noi_that_dung_that.log"

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
        log("📘 Đang tạo Story cho Facebook Page...")
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
                vbytes = f.read(1024 * 1024 * 10)
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

def run_schedule():
    log("=" * 70)
    log("🐱 BẮT ĐẦU CHƯƠNG TRÌNH HẸN GIỜ ĐĂNG VIDEO: NÓI THẬT DÙNG THẬT")
    log("=" * 70)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\cạo lông mèo.mp4"

    # Metadata & SEO Chuẩn Viral
    # 1. YouTube Shorts
    yt_title = "Cứu tinh cho sen mùa mèo rụng lông: Lược chải gỡ rối bấm nút nhả lông siêu đã #Shorts"
    yt_desc = (
        "Chiếc lược chải lông thần thánh giúp gỡ rối, lấy sạch lông rụng tận chân lông cho chó mèo cực êm ái. "
        "Bấm một nút là lông rụng bay hết gọn gàng, không lo lông bay khắp nhà nữa!\n\n"
        "#Shorts #noithatdungthat #luocchailongmeo #chamsocchomeo #petcare #meo #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7V7qF61u9i",
        "Link sản phẩm: https://s.shopee.vn/3VbMawZ35y",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/4flgG9yE7y",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AKamR6j0fB",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/20vcufKj4N",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/70KIt8Gf12",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5fovFzN9fH",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/7KocT0oVfT"
    ]

    # 2. Facebook Reels (+ kèm link sản phẩm trong nội dung)
    fb_title = "Lược chải lông thú cưng bấm nút nhả lông siêu tiện lợi"
    fb_caption = (
        "Mùa rụng lông đến mà nhà lúc nào cũng ngập trong lông mèo thì sắm ngay em lược chải gỡ rối thông minh này nhé các sen! "
        "Răng lược bo tròn êm ái massage cực phê, chải tới đâu lông rụng gom gọn tới đó, bấm 1 nút là nhả sạch lông trong 1 giây 🔥\n\n"
        "👉 Link sắm lược chải lông chính hãng tại: https://s.shopee.vn/6q0se8IiKl\n\n"
        "#reels #viral #fyp #noithatdungthat #luocchailongmeo #chomeo #yeupet #reviewtienich"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6q0se8IiKl",
        "Link sản phẩm: https://s.shopee.vn/5fovFzN9hc",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AUuB0s4ktd",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/9KiDcj9CGU",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8plx1oB6HT",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2VrtUAZD8K",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1gImUdcNpF",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/qjfV6fYWA"
    ]

    # 3. Instagram Reels
    ig_caption = (
        "Sen nào nuôi mèo mà không có chiếc lược chải lông bấm nút nhả tự động này thì quá thiếu sót! "
        "Lấy lông rụng siêu sạch, gỡ rối không đau rát lại còn massage thư giãn cho boss cực thích ✨ "
        "Trải nghiệm thực tế đúng là đáng từng đồng! Link sắm lược xịn mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #noithatdungthat #catlover #chamsocmeo #luocchailong #petlifestyle #catsoftiktok"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6L4c3DKcLg",
        "Link sản phẩm: https://s.shopee.vn/5q8LSIMWMf",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/9zxuPx6euY",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/9V1dp28YvX",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8KpgQtD0IO",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2LYTHrZqTJ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1VzMIKd1AE",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/gQFIngBr9"
    ]

    # 4. Threads (< 500 ký tự)
    th_caption = (
        "Nhà nuôi chó mèo đến mùa thay lông thì nhất định phải tậu em lược chải gỡ rối này! Răng lược bọc đầu êm ru, chải gom lông cực gọn, bấm 1 phát nhả sạch tinh ✨\n\n"
        "🛒 Link sắm lược xịn cho boss nè:\n"
        "1. Lược gỡ rối lông Poodle/Mèo: https://s.shopee.vn/6VO2FWJz0j\n"
        "2. Lược chải massage giảm rụng: https://s.shopee.vn/5LC4rNOQNa\n"
        "3. Lược CLEAN bấm nút nhả lông: https://s.shopee.vn/AAHKcG61Zb\n\n"
        "#noithatdungthat #petcare #meo #luocchailong"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6VO2FWJz0j",
        "Link sản phẩm: https://s.shopee.vn/5LC4rNOQNa",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AAHKcG61Zb",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/905NE7ASwS",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8V96dCCMxR",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2BF35YaToI",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1Lfw61deVD",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/W6p6UgpC8"
    ]

    # Lập lịch: Hôm nay 19:40 (Giờ vàng tương tác buổi tối)
    now = datetime.datetime.now()
    target_dt = now.replace(hour=19, minute=40, second=0, microsecond=0)
    if target_dt <= now:
        target_dt += datetime.timedelta(days=1)
    
    target_ts = int(target_dt.timestamp())
    log(f"📅 Giờ xuất bản mục tiêu: {target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {target_ts})")

    # 1. YOUTUBE SHORTS (Native API Scheduled Publish)
    log("\n🔴 [1/4] Khởi tạo & Đặt lịch YouTube Shorts (Native API)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/noi_that_dung_that.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_target = target_dt - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "noithatdungthat", "luocchailongmeo", "chomeo", "petcare"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        log(f"✅ Kết quả YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi lên lịch YouTube Shorts: {e}\n{traceback.format_exc()}")

    # 2. FACEBOOK REELS & STORY (Native Meta API Scheduled Publish)
    log("\n🔷 [2/4] Khởi tạo & Đặt lịch Facebook Reels (Meta API Scheduled)...")
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
            scheduled_time=target_ts
        )
        log(f"✅ Kết quả Facebook Reels: {res_fb}")
        post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi lên lịch Facebook Reels: {e}\n{traceback.format_exc()}")

    # 3 & 4. INSTAGRAM REELS (+ STORY) & THREADS
    log("\n📸 [3/4] & 🧵 [4/4] Đưa Instagram Reels & Threads vào trình theo dõi đếm ngược xuất bản...")
    
    while True:
        current_time = datetime.datetime.now()
        remaining_seconds = (target_dt - current_time).total_seconds()
        
        if remaining_seconds <= 0:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ VÀNG ({target_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN INSTAGRAM REELS, STORY & THREADS...")
            
            # Instagram Reels & Story
            try:
                log("📸 Đang tải lên và xuất bản Instagram Reels...")
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
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reels: {e}\n{traceback.format_exc()}")

            # Threads
            try:
                log("🧵 Đang tải lên và xuất bản bài viết Threads...")
                th_cfg = brand_data.get("threads", {})
                th_uploader = ThreadsAPIUploader(
                    threads_user_id=th_cfg["user_id"],
                    access_token=th_cfg["access_token"]
                )
                res_th = th_uploader.upload_video_thread(
                    video_path=video_path,
                    caption=th_caption,
                    comment_link=None
                )
                log(f"✅ Kết quả Threads: {res_th}")
                
                # Tự động reply bình luận Shopee vào Thread
                if res_th and "id" in res_th:
                    thread_post_id = res_th["id"]
                    log(f"💬 Đang tự động gửi bình luận Affiliate vào Thread ID {thread_post_id}...")
                    for idx, cmt in enumerate(th_comments, 1):
                        try:
                            time.sleep(2)
                            r_c = requests.post(
                                f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads",
                                data={
                                    "media_type": "TEXT_POST",
                                    "text": cmt,
                                    "reply_to_id": thread_post_id,
                                    "access_token": th_cfg["access_token"]
                                },
                                timeout=20
                            ).json()
                            if "id" in r_c:
                                pub_c = requests.post(
                                    f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                                    data={"creation_id": r_c["id"], "access_token": th_cfg["access_token"]},
                                    timeout=20
                                ).json()
                                log(f"  ✅ Đã reply comment Threads {idx}: {cmt[:40]}...")
                        except Exception as ce:
                            log(f"  ⚠️ Lỗi reply comment Threads {idx}: {ce}")
            except Exception as e:
                log(f"❌ Lỗi xuất bản Threads: {e}\n{traceback.format_exc()}")

            log("\n🎉 HOÀN THÀNH TẤT CẢ TIẾN TRÌNH CHO NÓI THẬT DÙNG THẬT!")
            break

        if int(remaining_seconds) % 900 == 0 or remaining_seconds < 60:
            log(f"⏳ Đang chạy nền... Còn {int(remaining_seconds // 60)} phút nữa tới giờ xuất bản ({target_dt.strftime('%H:%M:%S')}).")
        time.sleep(10)

if __name__ == "__main__":
    run_schedule()
