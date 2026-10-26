# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Tủ Đồ Mùa Mới"
Video: C:\\Affiliate\\Tủ Đồ Mùa Mới\\video_việt_hóa\\3.mp4
Sản phẩm: Áo lót nữ không gọng, Áo lót quây chống tụt, Quần lót đúc su tàng hình (Tập 3)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_tu_do_mua_moi.log"

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
    return brands.get("tu_do_mua_moi", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Tủ Đồ Mùa Mới...")
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
        log("📸 Đang khởi tạo Story cho Instagram Business Tủ Đồ Mùa Mới...")
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
    log("👙 BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: TỦ ĐỒ MÙA MỚI (TẬP 3)")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Tủ Đồ Mùa Mới\video_việt_hóa\3.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Bí quyết diện đồ trễ vai không lo lộ dây với áo lót quây chống tụt tàng hình #Shorts"
    yt_desc = (
        "Tuyển chọn những mẫu nội y chân ái cho phái đẹp: Áo lót không gọng đệm êm mềm mại, áo quây viền silicon kép chống tụt và quần lót su đúc không đường may tàng hình tôn dáng. "
        "Tự tin diện mọi outfit ôm sát hay trễ vai!\n\n"
        "#Shorts #tudomuamoi #aolotkhonggong #aolotquaychongtut #quanlotducsu #noiycaocap #reviewthoitrang #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7fR5M90m5x",
        "Link sản phẩm: https://s.shopee.vn/7KoejUv0d9",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/70KVG9a1g0",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/6V5Wy1t22K",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6L4e0yoc3u",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5fovmpx2jL",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4flhxKx2Z0",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3VbOC1v33A",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/2Vryf5w44X",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/2gBOx1s66J",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/1Lg1m9w77M"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "Áo lót quây chống tụt viền silicon diện váy trễ vai siêu tự tin"
    fb_caption = (
        "Mặc váy đầm hai dây, trễ vai hay đồ ôm sát mà sợ lộ viền hay tụt áo thì sắm ngay em áo quây viền silicon kép này nhé các nàng! "
        "Chất su đúc mềm mát, ôm chắc nịch không cấn ngực, kết hợp quần lót tàng hình không lộ viền cực đỉnh 🔥\n\n"
        "👉 Sắm ngay Áo lót không gọng chân ái tại: https://s.shopee.vn/6VO7DT98Gk\n\n"
        "#reels #viral #fyp #tudomuamoi #aolotquay #aongucnangnguc #quanlotnu #noiybasic #outfittips"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6VO7DT98Gk",
        "Link sản phẩm: https://s.shopee.vn/60Rqd4M2T5",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/5VVa1cWsq0",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5LC9pG2F9j",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/5AsjdM422j",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/4qFtylCq01",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4LJce9g73i",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/40gmEc9Lq6",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3qNM27Qk2G",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3LR5R8aWvD",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/2qUoqTcLpA"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Bí quyết diện đồ hack dáng mượt mà không lo sự cố! Áo lót không gọng êm ái nâng ngực tự nhiên cùng áo quây chống tụt viền silicon kép cực chắc ✨ "
        "Item must-have trong tủ đồ của mọi cô gái! Link sắm từng mẫu nội y xịn sò mình để chi tiết dưới comment nha 👇\n\n"
        "#reels #viral #fyp #tudomuamoi #brasolutions #straplessbra #seamlessunderwear #noiychinhhang #fashionhacks"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/8AWHvIiF05",
        "Link sản phẩm: https://s.shopee.vn/8Kpi7bhbf8",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/8V98JugyKB",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8fSYWDgKzE",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8plyiWfheH",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/905Oupf4JK",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/9AOp78eQyN",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/9KiFJRdndQ",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/9V1fVkdAIT",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/9fL5i3cWxW",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/9peVuMbtcZ"
    ]

    # 4. Threads
    th_caption = (
        "Mê mặc áo trễ vai với đầm ôm thì rinh ngay combo áo quây chống tụt viền silicon + quần lót su đúc tàng hình này nha! Nhẹ bẫng, êm ru mà không lo sự cố ✨\n\n"
        "🛒 Link sắm nội y chân ái cho chị em:\n"
        "1. Áo lót cotton không gọng: https://s.shopee.vn/70KKX9mxR5\n"
        "2. Áo lót không gọng Visecret: https://s.shopee.vn/7VGb84l3QC\n"
        "3. Áo quây chống tụt Selala: https://s.shopee.vn/8V98JuhFOU\n\n"
        "#tudomuamoi #noiy #aolotquay #chongtut"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/70KKX9mxR5",
        "Link sản phẩm: https://s.shopee.vn/7VGb84l3QC",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/7KxAvllglB",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/7ptRWgjmkI",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/7fa1KNkQ5H",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/8AWHvIiW4O",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/80Crizj9PN",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/8V98JuhFOU",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/8Kpi7bhsjT",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/8plyiWfyia",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8fSYWDgc3Z"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/tu_do_mua_moi.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "tudomuamoi", "aolotkhonggong", "aolotquaychongtut", "quanlotducsu"],
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

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO TỦ ĐỒ MÙA MỚI!")

if __name__ == "__main__":
    main()
