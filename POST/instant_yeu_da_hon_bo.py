# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Thương hiệu: "Yêu Da Hơn Bồ"
Video: C:\\Affiliate\\Yêu Da Hơn Bồ\\Video_việt_hóa\\2.mp4
Sản phẩm: Toner Pad cấp ẩm làm dịu Torriden, Balanceful Cica, Klairs & Mặt nạ nâng cơ thon gọn cằm V-Line (Tập 2)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_yeu_da_hon_bo.log"

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
    return brands.get("yeu_da_hon_bo", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
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
    log("💖 BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: YÊU DA HƠN BỒ (TẬP 2)")
    log("=" * 70)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\2.mp4"

    # Metadata & SEO Viral
    # 1. YouTube Shorts
    yt_title = "Combo Toner Pad hạ nhiệt da cấp tốc & Mặt nạ nâng cơ thon gọn cằm VLine #Shorts"
    yt_desc = (
        "Quy trình skincare tối giản cứu tinh cho làn da sần sùi thiếu nước và nọng cằm chảy xệ: Đắp toner pad cấp ẩm sâu, hạ nhiệt làm dịu da tức thì kết hợp đai định hình nâng cơ cằm V-line thon gọn. "
        "Da mọng nước căng bóng chuẩn Hàn!\n\n"
        "#Shorts #yeudahonbo #tonerpad #matnanangco #vline #skincareroutine #cangbongda #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20vctW7tFh",
        "Link sản phẩm: https://s.shopee.vn/1gImUu9q89",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/W6p6vBqTf",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AUuB0uXlW9",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/905NEUwh4a",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/8AWHvoW32K",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8V98Kopv8H",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/80Cq34v7xW",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/7fR1jL9WqC",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/7KocT444kS",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/6fhSSifbsk",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/6q0sf1eyXn"
    ]

    # 2. Facebook Reels (+ Story)
    fb_title = "Bí quyết đắp Toner Pad làm dịu da và đai nâng cơ thon gọn mặt"
    fb_caption = (
        "Da khô ráp, mẩn đỏ hay nọng cằm khiến mặt to tròn thì bỏ túi ngay mẹo skincare này các nàng ơi! "
        "Đắp toner pad cấp nước tầng sâu kết hợp mặt nạ định hình cằm V-line giúp cơ mặt săn chắc, cằm thon gọn thấy rõ 🔥\n\n"
        "👉 Sắm ngay Toner Pad cấp ẩm sâu chính hãng tại: https://s.shopee.vn/3LR2BK9ZgQ\n\n"
        "#reels #viral #fyp #yeudahonbo #tonerpad #nangcovline #chamsocda #thongonmat #beautytips"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/3LR2BK9ZgQ",
        "Link sản phẩm: https://s.shopee.vn/2VrtUr6ePz",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2LYTIYfGf1",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/1135i4i4c2",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9KiDdVyL5Q",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/9AOp82qjeq",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8plx2Tgzq4",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/8fSWqA3k1b",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/7ptRXasRYA",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/70KItBNpE7",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/6V5U5etn37",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/5fovFzsQ3A"
    ]

    # 3. Instagram Reels (+ Story)
    ig_caption = (
        "Bí quyết chăm da căng bóng ngậm nước và sở hữu gương mặt Vline thanh thoát! "
        "Toner pad tiện lợi làm dịu lỗ chân lông kết hợp đai định hình cơ cằm ngăn ngừa chảy xệ ✨ "
        "Quy trình dưỡng nhan cực kỳ đáng thử! Link trọn bộ skincare chính hãng mình để dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #koreanskincare #tonerpads #vlinemask #chongchayxe #skincarecommunity"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/2BF4nBE12K",
        "Link sản phẩm: https://s.shopee.vn/LnQboKzl5",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/9fL5ixlSp0",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8AWHwCrArp",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6fhU9Rwsue",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/7ptRXasRXz",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6L4dkpy9ao",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/4qFpy53rdd",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/3LR2BK9ZgS",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/9AOp82qjfb",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/AKamWBmIIw",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/6AlDYX29lF"
    ]

    # 4. Threads
    th_caption = (
        "Da thiếu ẩm sần sùi với mặt nọng thì lưu ngay combo này! Toner pad đắp 5p là da ngậm nước căng mướt, đeo thêm mặt nạ cằm Vline định hình gọn gàng ✨\n\n"
        "🛒 Link sắm skincare chính hãng cho các nàng:\n"
        "1. Toner Pad Repiel: https://s.shopee.vn/20veasEeNJ\n"
        "2. Pad đa năng Torriden: https://s.shopee.vn/qjhCjJ5kC\n"
        "3. Mặt nạ định hình cằm VLine: https://s.shopee.vn/50ZGAO3EIg\n\n"
        "#yeudahonbo #skincare #tonerpad #vline"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20veasEeNJ",
        "Link sản phẩm: https://s.shopee.vn/qjhCjJ5kC",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/9peVvGkpU3",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8Kpi8VqXWs",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6q0uLkwFZh",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5LC6Z01xcW",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6VO3x8xWFr",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/50ZGAO3EIg",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/8AWHwCuXhJ",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/9KiFKLq6Ke",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/AUuCiUlexz",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/6L4dkq1WQI"
    ]

    # 1. YOUTUBE SHORTS (ĐĂNG NGAY - PUBLIC)
    try:
        log("\n🔴 [1/4] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/yeu_da_hon_bo.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "yeudahonbo", "tonerpad", "matnanangco", "vline"],
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

    log("\n🎉🎉 HOÀN THÀNH TIẾN TRÌNH ĐĂNG NGAY CHO YÊU DA HƠN BỒ!")

if __name__ == "__main__":
    main()
