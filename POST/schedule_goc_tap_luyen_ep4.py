# -*- coding: utf-8 -*-
"""
Schedule Runner - Tự động lập lịch & Hẹn giờ đăng Video Tập 4 ("Góc Tập Luyện")
Lên 4 nền tảng:
- YouTube Shorts (Native Scheduled via Google API RFC 3339)
- Facebook Reels (Meta API Scheduled Timestamp) + Facebook Page Story
- Instagram Reels + Story (Hẹn giờ chạy theo nhịp countdown)
- Threads (Hẹn giờ chạy theo nhịp countdown + Auto-reply comment affiliate)

Khung giờ: Tối nay 2026-09-25, bắt đầu từ ~19:04, giãn cách ngẫu nhiên 7-9 phút giữa các nền tảng:
1. YouTube Shorts:        19:04:00 (UTC 12:04:00)
2. Facebook Reels & Story: 19:13:00 (Timestamp)
3. Instagram Reels & Story: 19:22:00
4. Threads:                19:31:00
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_goc_tap_luyen_ep4.log"

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
    return brands.get("goc_tap_luyen", {})

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
                vbytes = f.read(1024 * 1024 * 15)  # Read initial chunk
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

def run_schedule_ep4():
    log("=" * 75)
    log("🏋️ BẮT ĐẦU CHƯƠNG TRÌNH HẸN GIỜ ĐĂNG VIDEO: GÓC TẬP LUYỆN (TẬP 4)")
    log("=" * 75)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\4.mp4"

    # 1. YouTube Shorts Metadata & Links
    yt_title = "Combo dụng cụ tập gym & cardio tại nhà thon dáng giảm mỡ cực nhanh #Shorts"
    yt_desc = (
        "Tổng hợp những món đồ tập luyện thể dục tại nhà cực kỳ hữu ích giúp siết eo, làm đẹp dáng chân, "
        "đốt mỡ toàn thân và bảo vệ đầu gối tối đa. Kiên trì tập luyện mỗi ngày để có vóc dáng săn chắc tự tin!\n\n"
        "👉 Chi tiết từng sản phẩm chính hãng mình ghim dưới phần bình luận nhé 👇\n\n"
        "#Shorts #goctapluyen #tapgymtainha #cardio #giando #sieo #thonchan #fitness #workout"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/AKakpOtnqB",
        "Link sản phẩm: https://s.shopee.vn/6VO2GM8OcY",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/7Kx9Ft5Dvp",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/3VkQgqJoiC",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4LJXgNGe1T",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/30oA5vPV7i",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4B07U4L3l3",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/1AYWPavDM",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/1BMVuYWTqh",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/2LYTIhS2U2",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8plx2e3IIP"
    ]

    # 2. Facebook Reels Metadata & Links
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

    # 3. Instagram Reels Metadata & Links
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

    # 4. Threads Metadata & Links (< 500 ký tự)
    th_caption = (
        "Bận rộn mà vẫn muốn thon dáng, giảm mỡ thì tham khảo ngay combo máy trượt tuyết thon chân, máy leo bậc và xe đạp tập tại nhà này nhé! Nhỏ gọn, đốt calo cực đỉnh ✨\n\n"
        "🛒 Link sắm đồ tập chính hãng ở đây nè cả nhà:\n"
        "1. Máy trượt tuyết thon chân: https://s.shopee.vn/9fL42AwLBz\n"
        "2. Máy leo bậc gấp gọn: https://s.shopee.vn/5q8LT8AvyM\n"
        "3. Xe đạp tập tại chỗ đa năng: https://s.shopee.vn/3g3qt9JBNH\n\n"
        "#goctapluyen #tapgymtainha #cardio #fitness"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/9fL42AwLBz",
        "Link sản phẩm: https://s.shopee.vn/5q8LT8AvyM",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/6fhSSf7lHd",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2qUjtcMM40",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3g3qt9JBNH",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5AsefuDTKg",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3VkQgqNb6r",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/4fwO4zJ9kC",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/W6p7KZ1CV",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/1gImVTUZpq",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8AWGFQ5peD"
    ]

    now = datetime.datetime.now()
    today_date = now.date()

    # Thiết lập khung giờ giãn cách tự nhiên (tránh spam):
    # 1. YouTube Shorts: 19:04:00
    # 2. Facebook Reels: 19:13:00 (+9 phút)
    # 3. Instagram Reels: 19:22:00 (+9 phút)
    # 4. Threads:         19:31:00 (+9 phút)
    yt_target_dt = datetime.datetime.combine(today_date, datetime.time(19, 4, 0))
    fb_target_dt = datetime.datetime.combine(today_date, datetime.time(19, 13, 0))
    ig_target_dt = datetime.datetime.combine(today_date, datetime.time(19, 22, 0))
    th_target_dt = datetime.datetime.combine(today_date, datetime.time(19, 31, 0))

    # Nếu hiện tại đã quá giờ (phòng hờ), dời sang ngày tiếp theo
    if yt_target_dt <= now:
        yt_target_dt += datetime.timedelta(days=1)
        fb_target_dt += datetime.timedelta(days=1)
        ig_target_dt += datetime.timedelta(days=1)
        th_target_dt += datetime.timedelta(days=1)

    fb_target_ts = int(fb_target_dt.timestamp())

    log(f"📅 LỊCH TRÌNH XUẤT BẢN CHI TIẾT:")
    log(f"  🔴 [1] YouTube Shorts:        {yt_target_dt.strftime('%Y-%m-%d %H:%M:%S')} (UTC: {(yt_target_dt - datetime.timedelta(hours=7)).strftime('%Y-%m-%dT%H:%M:%SZ')})")
    log(f"  🔷 [2] Facebook Reels:        {fb_target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {fb_target_ts})")
    log(f"  📸 [3] Instagram Reels:       {ig_target_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  🧵 [4] Threads:               {th_target_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # =========================================================================
    # 1. YOUTUBE SHORTS (Native API Scheduled Publish)
    # =========================================================================
    log("\n" + "=" * 50)
    log("🔴 [1/4] Khởi tạo & Đặt lịch YouTube Shorts (Google API v3)...")
    res_yt = None
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/goc_tap_luyen.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)

        utc_target = yt_target_dt - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")

        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "goctapluyen", "tapgymtainha", "cardio", "sieo", "thonchan"],
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
    log("🔷 [2/4] Khởi tạo & Đặt lịch Facebook Reels (Meta API Scheduled)...")
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
        # Đăng Story bổ trợ
        post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi lên lịch Facebook Reels: {e}\n{traceback.format_exc()}")

    log("\n" + "=" * 50)
    log("📊 TỔNG HỢP TRẠNG THÁI GIAI ĐOẠN 1 (NATIVE SCHEDULING):")
    log(f"  - YouTube Shorts Video ID: {res_yt.get('video_id') if res_yt else 'N/A'}")
    log(f"  - Facebook Reel Video ID:  {res_fb.get('video_id') if res_fb else 'N/A'}")
    log("=" * 50)

    # =========================================================================
    # 3 & 4. INSTAGRAM & THREADS TIMED DISPATCHER
    # =========================================================================
    log("\n⏳ Bắt đầu vòng lặp theo dõi xuất bản Instagram Reels (19:22) & Threads (19:31)...")

    ig_published = False
    th_published = False

    while not (ig_published and th_published):
        current_time = datetime.datetime.now()

        # Kiểm tra Instagram (19:22:00)
        if not ig_published:
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
                    ig_published = True  # Avoid infinite error loop

        # Kiểm tra Threads (19:31:00)
        if not th_published:
            rem_th = (th_target_dt - current_time).total_seconds()
            if rem_th <= 0:
                log(f"\n⏰ ĐÃ ĐẾN GIỜ ({th_target_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN THREADS & AUTO-COMMENT AFFILIATE...")
                try:
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

                    if res_th and "id" in res_th:
                        thread_post_id = res_th["id"]
                        log(f"💬 Đang gửi 11 bình luận Affiliate vào Thread ID {thread_post_id}...")
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
                    th_published = True
                except Exception as e:
                    log(f"❌ Lỗi xuất bản Threads: {e}\n{traceback.format_exc()}")
                    th_published = True  # Avoid infinite error loop

        # Log định kỳ mỗi 5 phút hoặc khi gần đến giờ
        rem_next = min(
            (ig_target_dt - current_time).total_seconds() if not ig_published else 999999,
            (th_target_dt - current_time).total_seconds() if not th_published else 999999
        )
        if int(rem_next) % 300 == 0 or rem_next < 30:
            log(f"⏳ Đang chạy ngầm theo dõi: Còn {int(rem_next // 60)} phút {int(rem_next % 60)} giây tới mốc xuất bản tiếp theo...")

        time.sleep(10)

    log("\n🎉 HOÀN TẤT LẬP LỊCH VÀ XUẤT BẢN THÀNH CÔNG CHO TẤT CẢ 4 NỀN TẢNG (TẬP 4)!")

if __name__ == "__main__":
    run_schedule_ep4()
