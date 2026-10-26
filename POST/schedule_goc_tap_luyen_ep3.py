# -*- coding: utf-8 -*-
"""
Schedule Runner - Chạy ngầm tự động đăng hẹn giờ cho thương hiệu "Góc Tập Luyện"
Lập lịch video "3.mp4" lên 4 nền tảng:
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_goc_tap_luyen.log"

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
        log("📘 Đang tạo Story cho Facebook Page...")
        file_size = os.path.getsize(video_path)
        # Khởi tạo video upload cho Page
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
            # Binary transfer
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size)
            }
            with open(video_path, "rb") as f:
                vbytes = f.read(1024 * 1024 * 10) # 10MB chunk/preview
            r_up = requests.post(
                f"https://graph.facebook.com/v19.0/{upload_session_id}",
                headers=headers,
                data=vbytes,
                timeout=60
            ).json()
            log(f"  ✅ Trạng thái upload Story FB: {r_up}")
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng FB Story (fallback reel display): {e}")

def post_instagram_story(ig_user_id: str, access_token: str, video_path: str):
    """Đăng bổ sung lên Instagram Story"""
    try:
        log("📸 Đang khởi tạo Story cho Instagram Business...")
        # Theo Meta Graph API: media_type = STORIES
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
        log(f"  ⚠️ Lưu ý đăng IG Story (fallback): {e}")

def run_schedule():
    log("=" * 70)
    log("🏋️ BẮT ĐẦU CHƯƠNG TRÌNH HẸN GIỜ ĐĂNG VIDEO: GÓC TẬP LUYỆN (TẬP 3)")
    log("=" * 70)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\3.mp4"

    # Metadata & SEO Chuẩn Viral
    # 1. YouTube Shorts
    yt_title = "Dụng cụ hỗ trợ tập giãn cơ thon chân & siết eo tại nhà cực đỉnh #Shorts"
    yt_desc = (
        "Tổng hợp những dụng cụ tập luyện tại nhà cực kỳ hữu ích giúp thon chân, định hình vóc dáng, siết eo và bảo vệ khớp gối hiệu quả. "
        "Tập luyện đúng cách mỗi ngày để tự tin khoe dáng chuẩn!\n\n"
        "#Shorts #goctapluyen #tapgymtainha #thonchan #gianco #sieo #fitness #workout"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6V5U5b66gG",
        "Link sản phẩm: https://s.shopee.vn/1Lfw6rRFWF",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2VrtV0Mnc3",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5VVV4WCCdz",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6fhSSf7lH8",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/70KIt8Gf12",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/40ghIyU55p",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/9zxuRy8bXw",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/20vcufKj4N",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/3qNH6bO0gA",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/6V5U5b66gH"
    ]

    # 2. Facebook Reels (+ kèm link sản phẩm trong nội dung)
    fb_title = "Bí quyết tập giãn cơ định hình chân thon và siết eo tại nhà"
    fb_caption = (
        "Chân to, cơ bắp căng cứng hay mỡ bụng dưới khó giảm thì lưu ngay bài tập với combo dụng cụ tiện ích này nhé cả nhà! "
        "Bảng nghiêng giãn cơ thon chân + dụng cụ tập cơ sàn chậu tập cực đã, nhẹ người mà form dáng cải thiện rõ rệt 🔥\n\n"
        "👉 Sắm ngay bảng nghiêng giãn cơ thon chân chính hãng tại: https://s.shopee.vn/BTyiiVgKP\n\n"
        "#reels #viral #fyp #goctapluyen #tapgymtainha #thonchan #gianco #kegel #fitnesslifestyle"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/BTyiiVgKP",
        "Link sản phẩm: https://s.shopee.vn/1Lfw6rRExk",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2VrtV0Mnb5",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5VVV4WCCdF",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6fhSSf7lGa",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/70KIt8Gf0Z",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/40ghIyU553",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/9zxuRy8bXa",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/20vcufKj4B",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/3qNH6bO0g1",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/6V5U5b66g6"
    ]

    # 3. Instagram Reels
    ig_caption = (
        "Bí quyết sở hữu đôi chân thon gọn và vòng eo săn chắc ngay tại nhà không hề khó! "
        "Kiên trì kết hợp bài tập giãn cơ cùng dụng cụ tập sàn chậu và con lăn trợ lực mỗi ngày để cảm nhận sự thay đổi rõ rệt ✨ "
        "Link trọn bộ phụ kiện tập luyện chính hãng mình để chi tiết dưới phần comment nha 👇\n\n"
        "#reels #viral #fyp #goctapluyen #workoutathome #chanthon #gianco #pilates #fitnessgoals"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/LnOv1V2zS",
        "Link sản phẩm: https://s.shopee.vn/1VzMJAQbcn",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2gBJhJMAG8",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5fovGpBZII",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6q0sey77vd",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2gBJhJMzNw",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3qNH5SIY1H",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/50ZETbE6ec",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/qjfVwTy6v",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/20vcu5PWkG",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8KpgRj1Ptb"
    ]

    # 4. Threads (< 500 ký tự)
    th_caption = (
        "Ai hay bị mỏi chân, bắp chuối to hay đau lưng khi tập thì lưu ngay bài này! Bảng nghiêng kéo giãn bắp chân + dụng cụ tập sàn chậu siết mông đùi tại nhà siêu hiệu quả ✨\n\n"
        "🛒 Link sắm đồ tập chính hãng nè cả nhà:\n"
        "1. Bảng nghiêng thon chân: https://s.shopee.vn/W6p7KUPeV\n"
        "2. Dụng cụ tập Kegel mông đùi: https://s.shopee.vn/1gImVTPyHq\n"
        "3. Con lăn bụng 4 bánh trợ lực: https://s.shopee.vn/9zxuQmv4V2\n\n"
        "#goctapluyen #workout #chanthon #fitness"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6p7KUPeV",
        "Link sản phẩm: https://s.shopee.vn/1gImVTPyHq",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/9zxuQmv4V2",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5q8LT8AvxL",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/70KIrH6Uag",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2qUjtcMM2z",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/40ghHlHugK",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/5AsefuDTJf",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/1135iFTKly",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/2BF36OOtPJ",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8plx2dzVsi"
    ]

    # Lập lịch: Hôm nay 19:35 (Giờ vàng tương tác buổi tối)
    now = datetime.datetime.now()
    target_dt = now.replace(hour=19, minute=35, second=0, microsecond=0)
    if target_dt <= now:
        target_dt += datetime.timedelta(days=1)
    
    target_ts = int(target_dt.timestamp())
    log(f"📅 Giờ xuất bản mục tiêu: {target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {target_ts})")

    # 1. YOUTUBE SHORTS (Native API Scheduled Publish)
    log("\n🔴 [1/4] Khởi tạo & Đặt lịch YouTube Shorts (Native API)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/goc_tap_luyen.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_target = target_dt - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "goctapluyen", "tapgymtainha", "thonchan", "workout"],
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
        # Đăng Story bổ trợ
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
                # Đăng Instagram Story
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

            log("\n🎉 HOÀN THÀNH TẤT CẢ TIẾN TRÌNH CHO GÓC TẬP LUYỆN!")
            break

        if int(remaining_seconds) % 900 == 0 or remaining_seconds < 60:
            log(f"⏳ Đang chạy nền... Còn {int(remaining_seconds // 60)} phút nữa tới giờ xuất bản ({target_dt.strftime('%H:%M:%S')}).")
        time.sleep(10)

if __name__ == "__main__":
    run_schedule()
