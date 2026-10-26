# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Trạm Công Nghệ"
Video: C:\\Affiliate\\Trạm Công Nghệ\\video_việt_hóa\\cam máy tính tracking.mp4
Sản phẩm: Webcam máy tính AI tracking theo dõi khuôn mặt, chống ồn Insta360 Link 2 Pro
Đăng lên 4 nền tảng:
- YouTube Shorts (Public ngay)
- Facebook Reels (+ Story)
- Instagram Reels (+ Story)
- Threads (Kèm auto comment link Shopee)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_tram_cong_nghe.log"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_brand_config():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    return brands.get("cham_cong_nghe", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Trạm Công Nghệ...")
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
    try:
        log("📸 Đang khởi tạo Story cho Instagram Business Trạm Công Nghệ...")
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
                log(f"  ✅ Đã gửi reply comment Threads {idx}: {cmt[:40]}...")
        except Exception as e:
            log(f"  ⚠️ Lỗi reply Threads {idx}: {e}")

def main():
    log("=" * 70)
    log("💻 BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: TRẠM CÔNG NGHỆ")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\cam máy tính tracking.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Webcam AI tự động xoay tracking theo dõi khuôn mặt cực xịn cho streamer #Shorts"
    yt_desc = (
        "Chiếc webcam AI thông minh tự động xoay PTZ bám sát chuyển động khuôn mặt cực mượt, độ phân giải sắc nét tích hợp mic lọc ồn AI. "
        "Thiết bị đỉnh cao cho hội họp trực tuyến và livestream chuyên nghiệp!\n\n"
        "#Shorts #tramcongnghe #webcam #aitracking #insta360link #webcamlivestream #thietbithongminh #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7fR1j1nQ2v",
        "Link sản phẩm: https://s.shopee.vn/7KocSmfXF9",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/70KIt1Aupx",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/6V5U5UF69K",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6L4c2xZc1z",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5fovFqD94U",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4flgG42H44",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3VbMaonlMv",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/AKamR6j0fB"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "Webcam AI thông minh tự động theo dõi chuyển động khuôn mặt cực mượt"
    fb_caption = (
        "Làm việc online hay livestream mà có chiếc webcam AI tracking này thì góc hình luôn chuẩn tâm điểm! "
        "Gimbal xoay êm ái bám sát từng cử chỉ, tự lấy nét cực nhanh kèm chống ồn chuyên nghiệp 🔥\n\n"
        "👉 Sắm ngay Webcam AI Tracking chính hãng tại: https://s.shopee.vn/20vctlXKbb\n\n"
        "#reels #viral #fyp #tramcongnghe #webcam #cammaytinh #aitracking #streamer #techlifestyle #reviewdochoi"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20vctlXKbb",
        "Link sản phẩm: https://s.shopee.vn/qjfVcblyU",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AAHKcm2F2P",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8fSWq17x5E",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8V96di8aQJ",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/3qNH58QHbZ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2LYTINVzeO",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/BTyiOeF35",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/9V1dpY4i70"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Nâng tầm góc livestream & hội họp với webcam AI Tracking đỉnh chóp! "
        "Tự động nhận diện khuôn mặt xoay theo người dùng, hình ảnh sắc nét không vỡ hạt và mic thu âm siêu trong ✨ "
        "Review trải nghiệm thực tế công nghệ này quá đỉnh! Link săn chính hãng mình ghim dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #tramcongnghe #webcamai #techgear #desksetup #insta360 #congnghe #gadgetlover"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/1qcChSXxwa",
        "Link sản phẩm: https://s.shopee.vn/gQFJJcPJT",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AKakp51bhS",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8plx2K7JkH",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/7Kx9FZD1n6",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/3LR0UDSBcU",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2VrtUgVMJR",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/1135hvb4MG",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/9KiDdF5LRz"
    ]

    # 4. Threads
    th_caption = (
        "Chiếc webcam AI tracking này làm việc hay livestream đỉnh thực sự! Di chuyển tới đâu cam xoay bám theo tới đó, mic lọc ồn AI cực xịn sò ✨\n\n"
        "🛒 Link sắm webcam AI chính hãng:\n"
        "1. Webcam Full HD có mic: https://s.shopee.vn/1gImV9YbHZ\n"
        "2. Webcam 2K USB: https://s.shopee.vn/W6p70d2eS\n"
        "3. Insta360 Link 2 Pro AI PTZ: https://s.shopee.vn/1BMVuEaR1J\n\n"
        "#tramcongnghe #webcam #aitracking #setup"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/1gImV9YbHZ",
        "Link sản phẩm: https://s.shopee.vn/W6p70d2eS",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AUuB1O0yMV",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/905NEd6gPK",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/30oA5bTSIK",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/3VkQgWRYHX",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/20vctlXGKM",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/1BMVuEaR1J",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/AUuB1O0u5E"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/cham_cong_nghe.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "tramcongnghe", "webcam", "aitracking", "insta360link"],
            comment_text=yt_comments,
            privacy_status="public",
            publish_at=None
        )
        log(f"✅ Kết quả YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi YouTube Shorts: {e}\n{traceback.format_exc()}")

    # 2. FACEBOOK REELS & STORY (ĐĂNG NGAY)
    try:
        log("\n🔷 [2/4] Đang tải lên Facebook Reels (Publish Now)...")
        fb_cfg = brand_data.get("facebook", {})
        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        res_fb = fb.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comments,
            scheduled_time=None
        )
        log(f"✅ Kết quả Facebook Reels: {res_fb}")
        post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi Facebook Reels: {e}\n{traceback.format_exc()}")

    # 3. INSTAGRAM REELS & STORY (ĐĂNG NGAY)
    try:
        log("\n📸 [3/4] Đang tải lên Instagram Reels (Publish Now)...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels: {res_ig}")
        post_instagram_story(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels: {e}\n{traceback.format_exc()}")

    # 4. THREADS (ĐĂNG NGAY)
    try:
        log("\n🧵 [4/4] Đang tải lên Threads (Publish Now)...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads: {e}\n{traceback.format_exc()}")

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO TRẠM CÔNG NGHỆ!")

if __name__ == "__main__":
    main()
