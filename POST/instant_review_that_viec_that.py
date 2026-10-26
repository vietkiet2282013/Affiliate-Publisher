# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Review Thật Việc Thật"
Video: C:\\Affiliate\\Review Thật Việc Thật\\video_việt_hóa\\dem lung.mp4
Sản phẩm: Đệm kê thắt lưng giảm đau cột sống, thoát vị đĩa đệm
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_review_that_viec_that.log"

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
    return brands.get("review_that_viec_that", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Review Thật Việc Thật...")
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
        log("📸 Đang khởi tạo Story cho Instagram Business Review Thật Việc Thật...")
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
    log("🛏️ BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: REVIEW THẬT VIỆC THẬT")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Review Thật Việc Thật\video_việt_hóa\dem lung.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Cứu tinh cho người đau lưng thoái hóa: Đệm kê thắt lưng cao su non nâng đỡ cột sống #Shorts"
    yt_desc = (
        "Trải nghiệm thực tế đệm kê thắt lưng cao su non định hình cột sống: Giảm áp lực thắt lưng khi nằm, nâng đỡ đường cong sinh lý và hỗ trợ giảm đau thoát vị đĩa đệm hiệu quả. "
        "Giấc ngủ êm ái, sáng dậy không lo ê ẩm!\n\n"
        "#Shorts #reviewthatviecthat #demkethatlung #thoatvidiadem #giamdaulung #chamsocsuckhoe #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7fR1jL9WqA",
        "Link sản phẩm: https://s.shopee.vn/7KocT444kQ",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/70KItBNpE5",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/6V5U5etn35",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6L4c3H1z9J",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5fovFzsQ38",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4flgGDKoYw",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/3VbMaxuW4A"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "Đệm kê thắt lưng nâng đỡ cột sống giảm đau lưng thoát vị"
    fb_caption = (
        "Dân văn phòng ngồi nhiều hay người lớn tuổi hay bị đau mỏi thắt lưng, khó ngủ thì sắm ngay chiếc đệm kê lưng cao su non này nhé! "
        "Thiết kế công thái học ôm sát hõm lưng, giải tỏa áp lực cột sống giúp ngủ sâu giấc, sáng dậy nhẹ bẫng người 🔥\n\n"
        "👉 Sắm ngay Đệm kê thắt lưng chính hãng tại: https://s.shopee.vn/3qNH5Vm46E\n\n"
        "#reels #viral #fyp #reviewthatviecthat #demkelung #giamdaulung #thoatvidiadem #suckhoedoisong #reviewthuc"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/3qNH5Vm46E",
        "Link sản phẩm: https://s.shopee.vn/3g3qtCmhRD",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2qUjtfps84",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2gBJhMqVT3",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3B7aIHobSA",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/30oA5ypEn9",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4qFoHLiG4W",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/4fwO52itPV"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Ai thường xuyên thức dậy với cái lưng ê ẩm hay đau nhức vùng thắt lưng thì đừng bỏ qua món này! "
        "Đệm kê thắt lưng cao su non công thái học nâng đỡ cột sống chuẩn y tế, nằm thử là thấy dễ chịu tức thì ✨ "
        "Đánh giá chi tiết cực kỳ xứng đáng đầu tư cho sức khỏe! Link sắm chính hãng mình ghim dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #reviewthatviecthat #demthatlung #chamsocgiadinh #healthyhabits #ergonomic #reviewgiadung"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7fZzeYbnqs",
        "Link sản phẩm: https://s.shopee.vn/7ptPqrbAVv",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/6fhSSifbsi",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/6q0sf1eyXl",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/70KIrKeLCo",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/7Adj3ddhrr",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8fSWqOXzpA",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/8plx2hXMUD"
    ]

    # 4. Threads
    th_caption = (
        "Hay bị đau thắt lưng khi ngủ hoặc nằm võng lưng ê ẩm thì thử ngay gối đệm kê lưng này nhé cả nhà! Cao su non đàn hồi tốt, nâng trọn đường cong cột sống nằm siêu êm ✨\n\n"
        "🛒 Link mua gối đệm kê lưng chính hãng:\n"
        "1. Đệm kê thắt lưng Ema: https://s.shopee.vn/9AOnRJWEJu\n"
        "2. Đệm cao su non Cecila: https://s.shopee.vn/905NF0Wret\n"
        "3. Gối hỗ trợ eo Healme: https://s.shopee.vn/80Cq3Aafgj\n\n"
        "#reviewthatviecthat #demlung #daulung #suckhoe"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/9AOnRJWEJu",
        "Link sản phẩm: https://s.shopee.vn/905NF0Wret",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/8AWGFTa2Lk",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/80Cq3Aafgj",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8V96e5Ylfq",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/8KpgRmZP0p",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2BF36RwsWe",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/20vcu8xVrd"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/review_that_viec_that.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "reviewthatviecthat", "demkethatlung", "thoatvidiadem", "giamdaulung"],
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

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO REVIEW THẬT VIỆC THẬT!")

if __name__ == "__main__":
    main()
