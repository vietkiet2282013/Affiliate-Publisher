# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Quần Áo Giá Hời"
Video: C:\\Affiliate\\Quần Áo Giá Hời\\video_việt_hóa\\2.mp4
Sản phẩm: Áo khoác Cardigan, Mangto, Nỉ Croptop, Hoodie zip (Tập 2)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_quan_ao_gia_hoi.log"

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
    return brands.get("quan_ao_gia_hoi", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Quần Áo Giá Hời...")
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
        log("📸 Đang khởi tạo Story cho Instagram Business Quần Áo Giá Hời...")
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
    log("👗 BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: QUẦN ÁO GIÁ HỜI (TẬP 2)")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\2.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Gợi ý outfit mùa thu đông vừa xinh vừa ấm giá hời cho nàng #Shorts"
    yt_desc = (
        "Tổng hợp những mẫu áo khoác cardigan, mangto dáng dài, hoodie zip nỉ ấm áp siêu tôn dáng đón mùa thu đông. "
        "Form dáng chuẩn xịn, chất vải dày dặn mặc đi học, đi chơi hay đi làm đều xinh hết nấc!\n\n"
        "#Shorts #quanaogiahoi #outfitthudong #cardigan #mangto #thoitrangnu #hoodie #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/9V1ilbHetH",
        "Link sản phẩm: https://s.shopee.vn/1BMaqHrqom",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/1Lg12arDTv",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2qUopLlVRK",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4LJcc6fnOj",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5q8QOra5M8",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/60RqbAZS1H"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "BST Áo khoác mùa thu cực xinh giá hạt dẻ cho các nàng"
    fb_caption = (
        "Thời tiết se lạnh này mà diện cardigan dệt kim hay mangto dáng dài thì thanh lịch khỏi bàn luôn các nàng ơi! "
        "Form rộng che khuyết điểm cực đỉnh, phối cùng chân váy hay jean ống suông là có ngay outfit triệu like 🔥\n\n"
        "👉 Sắm ngay Áo khoác Cardigan dáng dài giá hời tại: https://s.shopee.vn/9AOsMzIvZ7\n\n"
        "#reels #viral #fyp #quanaogiahoi #cardigan #mangto #thoitrangnu #ootdvietnam #outfitreels"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/9AOsMzIvZ7",
        "Link sản phẩm: https://s.shopee.vn/AKapl8EUCS",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/113AdysU9l",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2VryQjmm7A",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2gBOd2m8mJ",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/4B0CPngQji",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5fp0CYaih7"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Gợi ý loạt outfit thu đông trendy đang được chị em săn đón rần rần! Cardigan dáng dài thanh lịch, mangto sang chảnh cùng hoodie zip nỉ trẻ trung năng động ✨ "
        "Toàn mẫu hot hit chất đẹp giá siêu hời! Link sắm từng item chính hãng mình ghim chi tiết dưới comment nha 👇\n\n"
        "#reels #viral #fyp #quanaogiahoi #outfitoftheday #cardiganstyle #streetstyle #fallfashion #reviewthoitrang"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/8fSbm4Kpa2",
        "Link sản phẩm: https://s.shopee.vn/AUuFxRDqrV",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/qjkRft7Uk",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2LYYEQnPS9",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3qNM1BhhPY",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/40gmDUh44h",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5VVa0FbM26"
    ]

    # 4. Threads
    th_caption = (
        "Mùa thu đông tới là không thể thiếu mấy em cardigan dệt kim hay mangto dáng dài này! Vải dày dặn, mặc lên tôn dáng mà giá siêu hời ✨\n\n"
        "🛒 Link sắm outfit chính hãng nè các nàng:\n"
        "1. Cardigan ByJane: https://s.shopee.vn/8pm1yNKCF5\n"
        "2. Cardigan dệt kim Hàn Quốc: https://s.shopee.vn/W6u33uOAa\n"
        "3. Bộ nỉ Kokonomi thu đông: https://s.shopee.vn/gQKFMtkpj\n\n"
        "#quanaogiahoi #ootd #cardigan #thoitrang"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/8pm1yNKCF5",
        "Link sản phẩm: https://s.shopee.vn/W6u33uOAa",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/gQKFMtkpj",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2BF827o2n8",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3g3vosiKkX",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5Asjbdcchw",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5LC9nwbzN5"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/quan_ao_gia_hoi.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "quanaogiahoi", "outfitthudong", "cardigan", "thoitrangnu"],
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

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO QUẦN ÁO GIÁ HỜI!")

if __name__ == "__main__":
    main()
