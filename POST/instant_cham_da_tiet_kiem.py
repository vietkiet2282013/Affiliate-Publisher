# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Chăm Da Tiết Kiệm"
Video: C:\\Affiliate\\Chăm Da Tiết Kiệm\\Video_việt_hóa\\4.mp4
Sản phẩm: Dầu dưỡng tái tạo da La Mer The Renewal Oil 30ml
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_cham_da_tiet_kiem.log"

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
    return brands.get("cham_da_tiet_kiem", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Chăm Da Tiết Kiệm...")
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
        log("📸 Đang khởi tạo Story cho Instagram Business Chăm Da Tiết Kiệm...")
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
    log("🚀 BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: CHĂM DA TIẾT KIỆM (TẬP 4)")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\4.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Phục hồi da khô bong tróc đỉnh cao với dầu dưỡng tái tạo La Mer The Renewal Oil #Shorts"
    yt_desc = (
        "Trải nghiệm dầu dưỡng tái tạo phục hồi da La Mer The Renewal Oil: Da ngậm nước, căng bóng tức thì và củng cố hàng rào bảo vệ da săn chắc. "
        "Bí quyết chăm da căng mọng không tì vết!\n\n"
        "#Shorts #chamdatietkiem #lamer #therenewaloil #dauduongda #skincareroutine #phuchoida #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/1BMbzZ5KU0"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "Dầu dưỡng tái tạo phục hồi da đỉnh cao La Mer The Renewal Oil"
    fb_caption = (
        "Da treatment bong tróc, khô căng hay thiếu ẩm trầm trọng thì nhất định phải thử một giọt dầu dưỡng tái tạo da này nhé các nàng ơi! "
        "Thấm cực nhanh, không hề bí bách mà giúp da căng bóng, ẩm mượt và mờ nếp nhăn thấy rõ ✨\n\n"
        "👉 Xem và mua dầu dưỡng La Mer chính hãng giá tốt tại: https://s.shopee.vn/2BF9BP1WS6\n\n"
        "#reels #viral #fyp #chamdatietkiem #lamer #therenewaloil #dauduong #skincaretips #chonglaohoa"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/2BF9BP1WS6"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Cứu cánh cho làn da khô ráp, lão hóa và thiếu sức sống! Dầu dưỡng tái tạo da La Mer The Renewal Oil cấp ẩm tầng sâu, khóa ẩm vượt trội cho lớp nền mướt mịn tự nhiên ✨ "
        "Đúng là đắt xắt ra miếng nhưng cực kỳ đáng đầu tư! Link sắm chính hãng mình ghim ngay bên dưới comment nha 👇\n\n"
        "#reels #viral #fyp #chamdatietkiem #lamervietnam #therenewaloil #facialoil #cangbongda #beautyhacks"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20viz629n5"
    ]

    # 4. Threads
    th_caption = (
        "Mùa hanh khô hay da đang treatment thì dầu dưỡng tái tạo La Mer The Renewal Oil đúng là chân ái! Nhỏ 2-3 giọt xoa đều là da căng bóng, ngậm nước và phục hồi hàng rào ẩm siêu nhanh ✨\n\n"
        "🛒 Link sắm dầu dưỡng La Mer chính hãng:\n"
        "👉 https://s.shopee.vn/W6vCL7rpo\n\n"
        "#chamdatietkiem #lamer #skincare #dauduongda"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6vCL7rpo"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/cham_da_tiet_kiem.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "chamdatietkiem", "lamer", "therenewaloil", "dauduongda"],
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

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO CHĂM DA TIẾT KIỆM!")

if __name__ == "__main__":
    main()
