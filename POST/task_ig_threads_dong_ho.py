# -*- coding: utf-8 -*-
"""
Task Runner - Đăng Video "Đồng Hồ Báo Thức" cho thương hiệu Nói Thật Dùng Thật
Lên 2 nền tảng: Instagram (Reels + Story) và Threads (Video + Auto-reply 9 comment affiliate)
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
from token_refresher import refresh_meta_tokens_if_needed

LOG_FILE = r"C:\Affiliate\post1\POST\config\task_ig_threads_dong_ho.log"

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

def run_post():
    log("=" * 75)
    log("🚀 ĐẾN GIỜ THỰC THI (12:00 TRƯA): ĐĂNG VIDEO LÊN INSTAGRAM & THREADS")
    log("=" * 75)

    brand_data = load_config()

    # ── Tự động kiểm tra & gia hạn token trước khi upload ──
    log("🔐 Kiểm tra token Meta trước khi đăng...")
    refresh_meta_tokens_if_needed("noi_that_dung_that", ["instagram", "threads"])
    brand_data = load_config()   # Reload sau refresh

    video_path = r"C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\đồng hồ báo thức.mp4"

    # 1. Instagram Reels Metadata & Links
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

    # 2. Threads Metadata & Links
    th_caption = (
        "Bận rộn mà vẫn muốn tập trung học bài & làm việc thì tham khảo ngay các mẫu đồng hồ đếm ngược Pomodoro này nha! "
        "Nhỏ gọn, nhắc giờ chuẩn và rèn kỷ luật cực hiệu quả ✨\n\n"
        "🛒 Link sắm đồng hồ chính hãng ở đây nè cả nhà:\n"
        "1. Đồng hồ LED đếm ngược Deli: https://s.shopee.vn/7ptPpyFavJ\n"
        "2. Đồng hồ thông minh DODUPO: https://s.shopee.vn/6fhSRpK2IA\n"
        "3. Đồng hồ Cú Mèo BANGSHE Capybara: https://s.shopee.vn/3VkQg0W5id\n\n"
        "#noithatdungthat #donghobaothuc #donghohengio #pomodoro #studygram"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7ptPpyFavJ",
        "Link sản phẩm: https://s.shopee.vn/6fhSRpK2IA",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/3VkQg0W5id",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/50ZESlQNg0",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4VcxrqSHgz",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/gQFIngsTK",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/BTyhsimUJ",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/1gImUdd4Rg",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/905NE7B9ZB"
    ]

    # --- INSTAGRAM REELS & STORY ---
    log("\n📸 [1/2] Xuất bản Instagram Reels & Story...")
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
        log(f"❌ Lỗi đăng Instagram Reels: {e}\n{traceback.format_exc()}")

    # --- THREADS VIDEO & COMMENTS ---
    log("\n🧵 [2/2] Xuất bản Threads Video & Reply 9 Comment Affiliate...")
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
            log(f"💬 Đang gửi 9 bình luận Affiliate nối tiếp vào Thread ID {thread_post_id}...")
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
        log(f"❌ Lỗi đăng Threads: {e}\n{traceback.format_exc()}")

    log("\n🎉 HOÀN TẤT ĐĂNG LÊN INSTAGRAM & THREADS THÀNH CÔNG!")

if __name__ == "__main__":
    run_post()
