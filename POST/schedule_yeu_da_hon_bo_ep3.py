# -*- coding: utf-8 -*-
"""
Schedule Runner - Đăng hẹn giờ video Tập 3 cho thương hiệu "Yêu Da Hơn Bồ"
Lập lịch video "3.mp4" cho 4 nền tảng (YouTube Shorts, Facebook Reels/Story, Instagram Reels/Story, Threads) vào 12:00 ngày 26/09/2026:
1. YouTube Shorts: Hẹn giờ trực tiếp server-side qua Google API v3 (12:00:00 UTC+7 / 05:00:00 UTC)
2. Facebook Reels (+ Story): Hẹn giờ Reels server-side qua Meta Graph API (12:08:00 UTC+7)
3. Instagram Reels (+ Story): Trình chạy nền máy tính xuất bản tự động đúng 12:16:00 UTC+7
4. Threads: Trình chạy nền máy tính xuất bản tự động đúng 12:24:00 UTC+7 (gửi kèm link affiliate comment)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_yeu_da_hon_bo_ep3.log"

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
    return brands.get("yeu_da_hon_bo", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    """Đăng bổ sung lên Facebook Page Story"""
    try:
        log("📘 Đang tạo Story cho Facebook Page Yêu Da Hơn Bồ...")
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
        log("📸 Đang khởi tạo Story cho Instagram Business Yêu Da Hơn Bồ...")
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

def reply_threads_comments(th_cfg: dict, thread_post_id: str, comments: list):
    """Gửi các câu comment link affiliate vào bài viết Threads"""
    log(f"💬 [Threads] Đang tự động gửi bình luận Affiliate vào Thread ID {thread_post_id}...")
    for idx, cmt in enumerate(comments, 1):
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
                log(f"  ✅ Đã gửi reply comment Threads {idx}: {cmt[:45]}...")
        except Exception as e:
            log(f"  ⚠️ Lỗi reply Threads {idx}: {e}")

def run_schedule():
    log("=" * 70)
    log("💖 BẮT ĐẦU QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO 12:00 (26/09/2026): YÊU DA HƠN BỒ (TẬP 3)")
    log("=" * 70)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\3.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # Metadata & SEO Chuẩn Viral từng nền tảng
    # 1. YouTube Shorts (12:00:00)
    yt_title = "Mặt nạ V-Line nâng cơ thon gọn cằm & Mặt nạ mắt chống quầng thâm #Shorts"
    yt_desc = (
        "Quy trình dưỡng da & định hình gương mặt cực phẩm: Đai đeo định hình cằm V-line kết hợp cùng mặt nạ mắt dưỡng ẩm sâu mờ quầng thâm. "
        "Cho gương mặt thon gọn thanh thoát và đôi mắt tươi trẻ rạng rỡ!\n\n"
        "#Shorts #yeudahonbo #matnanangco #matnavline #matnamat #chamsocda #skincare"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/2qUlaPEqWn",
        "Link sản phẩm: https://s.shopee.vn/40giyYAPA8",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/5AsgMh5xnT",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/1137P2LpFm",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2BF4nBHNt7",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/8plyjQs0MW",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/9fL5ixopfn",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/5q8N9v3QSA",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/6fhU9S0FlR",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/2qUlaPEqXo",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/4B09ArAJui"
    ]

    # 2. Facebook Reels & Story (12:08:00)
    fb_title = "Bí quyết định hình cằm V-Line thon gọn và giảm quầng thâm mắt"
    fb_caption = (
        "Nọng cằm và quầng thâm mắt khiến bạn trông mệt mỏi già trước tuổi? "
        "Đắp ngay mặt nạ định hình cằm V-line kết hợp mặt nạ mắt collagen giúp cơ mặt săn chắc, giảm nếp nhăn và quầng thâm rõ rệt ✨\n\n"
        "👉 Sắm ngay Mặt nạ nâng cơ V-Line chính hãng tại: https://s.shopee.vn/7AdkkMyLjX\n\n"
        "#reels #viral #fyp #yeudahonbo #nangcovline #matnamat #chamsocda #lamdep"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7AdkkMyLjX",
        "Link sản phẩm: https://s.shopee.vn/30oBmiEDBq",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/4B09Ar9lpB",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/1AaDCPdHU",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1BMXbLLBup",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2LYUzUGkYA",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8fSYX7sdhV",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/AAHMJsmveu",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/5fowxc43n9",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/7AdkkMyLkY",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/2gBLO6FTsn"
    ]

    # 3. Instagram Reels & Story (12:16:00)
    ig_caption = (
        "Bí quyết sở hữu gương mặt V-line thon gọn chuẩn Hàn và đôi mắt mịn màng căng mướt! "
        "Mặt nạ nâng cơ định hình cằm kết hợp mặt nạ mắt dưỡng ẩm sâu giảm quầng thâm cực đỉnh ✨ "
        "Link trọn bộ skincare chính hãng mình để dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #vlinemask #eyemask #skincareroutine #beautytips"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7KxAwfxiOa",
        "Link sản phẩm: https://s.shopee.vn/3B7bz1DZqt",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/4LJZNA98UE",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/BU0PVOzwX",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1LfxneKYZs",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2VrvBnG7DD",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/9AOp82qjgc",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/9zxw7ZnYzt",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/6AlDYX29mG",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/70KKY3yz5X",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/3B7bz1DZru"
    ]

    # 4. Threads (12:24:00)
    th_caption = (
        "Ai bị nọng cằm với quầng thâm mắt mệt mỏi thì tham khảo ngay bộ đôi này! Mặt nạ định hình cằm V-line đeo 30p là cằm thon gọn thấy rõ, thêm mặt nạ mắt collagen mờ nhăn dưỡng ẩm sâu ✨\n\n"
        "🛒 Link sắm đồ dưỡng da chính hãng nè cả nhà:\n"
        "1. Mặt nạ V-Line thon gọn cằm: https://s.shopee.vn/7VGb8yx53d\n"
        "2. Mặt nạ mắt Lanbena Collagen: https://s.shopee.vn/AUuCiUlez0\n\n"
        "#yeudahonbo #skincare #vlinemask #eyecare"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7VGb8yx53d",
        "Link sản phẩm: https://s.shopee.vn/3LR2BKCwVw",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/4VczZT8V9H",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/LnQboOMba",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1VzNzxJvEv",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/8AWHwCuXiK",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/905OvjrN1b",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/AUuCiUlez0",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/60RnME2n7F",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/7VGb8yx54e",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/30oBmiEDCt"
    ]

    # Thiết lập mốc thời gian xuất bản mục tiêu: trưa nay 26/09/2026
    today = datetime.date(2026, 9, 26)
    yt_dt = datetime.datetime.combine(today, datetime.time(12, 0, 0))
    fb_dt = datetime.datetime.combine(today, datetime.time(12, 8, 0))
    ig_dt = datetime.datetime.combine(today, datetime.time(12, 16, 0))
    th_dt = datetime.datetime.combine(today, datetime.time(12, 24, 0))

    log(f"📅 YouTube Shorts xuất bản lúc: {yt_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 Facebook Reels (+Story) xuất bản lúc: {fb_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 Instagram Reels (+Story) xuất bản lúc: {ig_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 Threads xuất bản lúc: {th_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. YOUTUBE SHORTS (Hẹn giờ qua Native Google API v3)
    log("\n🔴 [1/4] Khởi tạo & Lập lịch YouTube Shorts (Google API v3)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/yeu_da_hon_bo.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_target = yt_dt - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "yeudahonbo", "matnanangco", "matnavline", "matnamat"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        log(f"✅ Kết quả YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi lên lịch YouTube Shorts: {e}\n{traceback.format_exc()}")

    # 2. FACEBOOK REELS & STORY (Hẹn giờ qua Native Meta Graph API)
    log("\n🔷 [2/4] Khởi tạo & Lập lịch Facebook Reels (Meta API Scheduled)...")
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
            scheduled_time=int(fb_dt.timestamp())
        )
        log(f"✅ Kết quả Facebook Reels: {res_fb}")
        post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi lên lịch Facebook Reels: {e}\n{traceback.format_exc()}")

    # 3 & 4. INSTAGRAM REELS (+ STORY) & THREADS (Chạy đếm ngược xuất bản tự động trên máy)
    log("\n📸 [3/4] & 🧵 [4/4] Đang đưa Instagram & Threads vào trình theo dõi đếm ngược xuất bản máy tính...")
    
    ig_done = False
    th_done = False

    while True:
        current_time = datetime.datetime.now()

        # Xuất bản Instagram Reels + Story
        if not ig_done and current_time >= ig_dt:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ VÀNG INSTAGRAM ({ig_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN INSTAGRAM REELS & STORY...")
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
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reels: {e}\n{traceback.format_exc()}")
            ig_done = True

        # Xuất bản Threads
        if not th_done and current_time >= th_dt:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ VÀNG THREADS ({th_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN THREADS...")
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
                    reply_threads_comments(th_cfg, res_th["id"], th_comments)
            except Exception as e:
                log(f"❌ Lỗi xuất bản Threads: {e}\n{traceback.format_exc()}")
            th_done = True

        if ig_done and th_done:
            log("\n🎉 HOÀN THÀNH TẤT CẢ TIẾN TRÌNH HẸN GIỜ CHO YÊU DA HƠN BỒ TẬP 3 (YOUTUBE, FACEBOOK, INSTAGRAM, THREADS)!")
            break

        time.sleep(10)

if __name__ == "__main__":
    run_schedule()
