# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Setup Phòng Xinh"
Video: C:\\Affiliate\\Setup Phòng Xinh\\Video_việt_hóa\\2.mp4
Sản phẩm: Nệm Cao Su Thiên Nhiên Gummi Standard 2.0, Nệm Foam NOOZ, Giường Pallet Gỗ Heino (Tập 2)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_setup_phong_xinh.log"

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
    return brands.get("setup_phong_xinh", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Setup Phòng Xinh...")
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
        log("📸 Đang khởi tạo Story cho Instagram Business Setup Phòng Xinh...")
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
    log("✨ BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: SETUP PHÒNG XINH (TẬP 2)")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\2.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Combo giường pallet & nệm cao su thiên nhiên biến phòng ngủ thành khách sạn #Shorts"
    yt_desc = (
        "Gợi ý decor phòng ngủ chuẩn phong cách tối giản Hàn Quốc với giường pallet gỗ thông tự nhiên kết hợp nệm cao su thiên nhiên Gummi Standard êm ái nâng đỡ cột sống. "
        "Không gian thư giãn chill hết nấc sau ngày dài làm việc!\n\n"
        "#Shorts #setupphongxinh #decorphongngu #giuongpallet #nemcaosu #homedecor #phongngudep #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/60Rqd4M2T5",
        "Link sản phẩm: https://s.shopee.vn/6L4h0Xg6y2",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/5VVa1cWsq0",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/4LJce9g73i",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3LR5R8aWvD",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2VryRz8bQ4",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2gBOeLp11E",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/1Lg13iRk9W",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/1BMas140wO",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/9V1in5x6vG",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8fSbnx12fQ"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "Gợi ý combo decor giường ngủ tối giản cực chill cho phòng nhỏ"
    fb_caption = (
        "Muốn biến góc phòng ngủ nhỏ thành nơi nghỉ ngơi chuẩn Hàn Quốc thì tham khảo ngay combo giường pallet gỗ thông + nệm cao su thiên nhiên này nhé cả nhà! "
        "Vừa tiết kiệm diện tích, khung chịu lực cực tốt mà nằm êm ru nâng niu giấc ngủ sâu mỗi tối 🔥\n\n"
        "👉 Sắm ngay Nệm cao su Gummi chính hãng tại: https://s.shopee.vn/8pm1zl9LDF\n\n"
        "#reels #viral #fyp #setupphongxinh #decorphongngu #giuongpallet #nemcaosuthiennhien #noithatmini #roommakeover"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/8pm1zl9LDF",
        "Link sản phẩm: https://s.shopee.vn/8Kpl1Fj11k",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/7fS4VjH22M",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/70KNvXF3hF",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6VO7DT98Gk",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5LC9pG2F9j",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4qFtylCq01",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/40gmEc9Lq6",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3qNM27Qk2G",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/2qUoqTcLpA",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/2BF831bQ6K"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Setup phòng ngủ xinh xắn ấm cúng chỉ với giường pallet gỗ tự nhiên và nệm cao su thiên nhiên Gummi! "
        "Thiết kế tinh gọn, nâng đỡ trọn vẹn lưng không lo ê ẩm lại khiến căn phòng sáng bừng sức sống ✨ "
        "Chi tiết link nội thất và nệm chính hãng mình ghim dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #setupphongxinh #bedroomdecor #minimalism #nemcaosu #giuongpallet #roomtour"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/LnTroChD8",
        "Link sản phẩm: https://s.shopee.vn/9KiIaLeQwz",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/8AWLCCisJs",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/80CuztjZsE",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9peZBGcb9h",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/LnTroClQy",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2BF83B5miR",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3LR5RK1LLm",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/5AsjcguMdF",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/6VO7D8pHvc",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/5LC9oztjIV"
    ]

    # 4. Threads
    th_caption = (
        "Phòng ngủ nhỏ muốn gọn gàng và chill thì tậu ngay combo giường pallet gỗ thông tự nhiên + nệm cao su Gummi này nha! Nằm siêu êm, nâng đỡ cột sống cực thích ✨\n\n"
        "🛒 Link sắm nội thất phòng ngủ chính hãng:\n"
        "1. Nệm Gummi Standard: https://s.shopee.vn/W6u47C3sB\n"
        "2. Đệm Foam Nooz Hybrid: https://s.shopee.vn/905SBjflqK\n"
        "3. Giường Pallet Heino: https://s.shopee.vn/8AWLCCiwXH\n\n"
        "#setupphongxinh #decor #bedroom #giuongpallet"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6u47C3sB",
        "Link sản phẩm: https://s.shopee.vn/9peZBGcWw6",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/905SBjflqK",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8AWLCCiwXH",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9KiIaLeVAc",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/W6u47C861",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1gIrSG7gjM",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3VkVdd0i0p",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/4fwT1lwGeA",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/6L4h0ppvGb",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/7ptUnakDE0"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/setup_phong_xinh.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "setupphongxinh", "decorphongngu", "giuongpallet", "nemcaosu"],
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

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO SETUP PHÒNG XINH!")

if __name__ == "__main__":
    main()
