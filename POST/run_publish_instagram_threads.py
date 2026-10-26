# -*- coding: utf-8 -*-
"""
Execution Task: Đăng video Tập 4 lên Instagram (Reels + Story) và Threads
Được kích hoạt bởi Windows Task Scheduler vào đúng 12:00:00 ngày 26/09/2026.
Thương hiệu: Góc Tập Luyện
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
    InstagramReelsUploader,
    ThreadsAPIUploader
)

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_instagram_threads_12h.log"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_credentials():
    meta_path = os.path.join(POST_DIR, "config", "permanent_meta_tokens.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_tokens = json.load(f)
    
    brand_meta = meta_tokens.get("Góc Tập Luyện", {})
    ig_access_token = brand_meta.get("page_access_token")
    ig_user_id = brand_meta.get("instagram_business_id", "17841438553537040")

    brands_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(brands_path, "r", encoding="utf-8") as f:
        brands_data = json.load(f)
    th_cfg = brands_data.get("goc_tap_luyen", {}).get("threads", {})

    return {
        "ig_user_id": ig_user_id,
        "ig_access_token": ig_access_token,
        "threads_user_id": th_cfg.get("user_id", "27890678400603793"),
        "threads_access_token": th_cfg.get("access_token")
    }

def post_instagram_story(ig_user_id: str, access_token: str, video_path: str):
    """Đăng Story bổ trợ cho Instagram Business"""
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
    log("🚀 [TASK RUNNER] BẮT ĐẦU ĐĂNG BÀI LÊN INSTAGRAM & THREADS (12H00 NGÀY 26/09/2026)")
    log("=" * 75)

    creds = load_credentials()
    video_path = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\4.mp4"

    # 1. Instagram Metadata
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

    # 2. Threads Metadata
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
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/4fwO4zJ9kC",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/1gImVTUZpq",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8AWGFQ5peD"
    ]

    # --- Bước 1: Instagram Reels & Story ---
    log("📸 [1/2] Đang tải lên và xuất bản Instagram Reels...")
    try:
        ig_uploader = InstagramReelsUploader(
            ig_user_id=creds["ig_user_id"],
            access_token=creds["ig_access_token"]
        )
        res_ig = ig_uploader.upload_reel(
            video_path=video_path,
            caption=ig_caption,
            comment_text=ig_comments
        )
        log(f"✅ Kết quả Instagram Reels: {res_ig}")
        post_instagram_story(creds["ig_user_id"], creds["ig_access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi đăng Instagram Reels: {e}\n{traceback.format_exc()}")

    # Nghỉ giãn cách tự nhiên 30 giây giữa 2 nền tảng
    log("⏳ Nghỉ 30 giây trước khi đăng Threads...")
    time.sleep(30)

    # --- Bước 2: Threads Video & Comments ---
    log("🧵 [2/2] Đang tải lên và xuất bản bài viết Threads...")
    try:
        th_uploader = ThreadsAPIUploader(
            threads_user_id=creds["threads_user_id"],
            access_token=creds["threads_access_token"]
        )
        res_th = th_uploader.upload_video_thread(
            video_path=video_path,
            caption=th_caption,
            comment_link=None
        )
        log(f"✅ Kết quả Threads: {res_th}")

        if res_th and "id" in res_th:
            thread_post_id = res_th["id"]
            log(f"💬 Đang tự động gửi bình luận Affiliate vào Thread ID {thread_post_id}...")
            for idx, cmt in enumerate(th_comments, 1):
                try:
                    time.sleep(2)
                    r_c = requests.post(
                        f"https://graph.threads.net/v1.0/{creds['threads_user_id']}/threads",
                        data={
                            "media_type": "TEXT_POST",
                            "text": cmt,
                            "reply_to_id": thread_post_id,
                            "access_token": creds["threads_access_token"]
                        },
                        timeout=20
                    ).json()
                    if "id" in r_c:
                        pub_c = requests.post(
                            f"https://graph.threads.net/v1.0/{creds['threads_user_id']}/threads_publish",
                            data={"creation_id": r_c["id"], "access_token": creds["threads_access_token"]},
                            timeout=20
                        ).json()
                        log(f"  ✅ Đã reply comment Threads {idx}: {cmt[:40]}...")
                except Exception as ce:
                    log(f"  ⚠️ Lỗi reply comment Threads {idx}: {ce}")
    except Exception as e:
        log(f"❌ Lỗi đăng Threads: {e}\n{traceback.format_exc()}")

    log("\n🎉 HOÀN TẤT ĐĂNG LÊN CẢ INSTAGRAM VÀ THREADS!")

if __name__ == "__main__":
    main()
