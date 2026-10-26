# -*- coding: utf-8 -*-
"""
Instant Publisher - ĐĂNG NGAY LẬP TỨC (PUBLISH NOW)
Cho 3 thương hiệu:
1. Dùng Rồi Mới Nói (Hoàn tất phần còn lại: Instagram Reels, Threads)
2. Góc Tập Luyện (YouTube Shorts, Facebook Reels+Story, Instagram Reels+Story, Threads)
3. Nói Thật Dùng Thật (YouTube Shorts, Facebook Reels+Story, Instagram Reels+Story, Threads)
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

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_publisher.log"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_brands():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def reply_threads_comments(th_cfg: dict, thread_post_id: str, comments: list):
    log(f"  💬 [Threads] Đang tự động gửi bình luận Affiliate vào Thread {thread_post_id}...")
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
                requests.post(
                    f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                    data={"creation_id": r_c["id"], "access_token": th_cfg["access_token"]},
                    timeout=20
                )
                log(f"    ✅ Đã gửi comment Threads {idx}: {cmt[:40]}...")
        except Exception as e:
            log(f"    ⚠️ Lỗi reply Threads {idx}: {e}")

# ==============================================================================
# 1. DÙNG RỒI MỚI NÓI
# ==============================================================================
def publish_dung_roi_moi_noi(brands):
    log("\n" + "=" * 70)
    log("🚀 [1/3] ĐĂNG NGAY CHO THƯƠNG HIỆU: DÙNG RỒI MỚI NÓI")
    log("=" * 70)
    brand_data = brands.get("dung_roi_moi_noi", {})
    video_path = r"C:\Affiliate\Dùng Rồi Mới Nói\Video_việt_hóa\bình đun nước mang đi du lịch.mp4"

    ig_caption = (
        "Đi du lịch hay công tác không còn lo thiếu nước nóng pha sữa, pha trà nữa rồi! "
        "Máy đun nước nóng tức thời 3s mini cầm tay, chỉnh đa mức nhiệt siêu tiện lợi ✨ "
        "Review trải nghiệm thực tế cực kỳ đáng tiền! Tham khảo ngay link mua chính hãng bên dưới comment nha 👇\n\n"
        "#reels #viral #fyp #dungroimoinoi #binhdunnuocdulich #maydunnuoc3s #giadungthongminh #reviewgiadung #lifestyle"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/2gBLJfHKWL",
        "Link sản phẩm: https://s.shopee.vn/3B7buaFQVS",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/30oBiHG3qR",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2BF4ikJEXI"
    ]

    th_caption = (
        "Đi du lịch hay công tác có em máy đun nước tức thì 3 giây này tiện dã man! Nhỏ gọn bỏ balo vali, "
        "bấm 3s là có nước sôi pha sữa, trà, cafe chuẩn nhiệt ✨\n\n"
        "🛒 Link sắm máy đun nước chính hãng:\n"
        "1. Máy đun tức thời đa năng: https://s.shopee.vn/20veWRJrsH\n"
        "2. Bình thủy 3s Xiaomi: https://s.shopee.vn/2Vrv7MHxrO\n"
        "3. Máy nước nóng mini: https://s.shopee.vn/2LYUv3IbCN\n\n"
        "#dungroimoinoi #maydunnuoc3s #binhdunnuocdulich #review"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20veWRJrsH",
        "Link sản phẩm: https://s.shopee.vn/2Vrv7MHxrO",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2LYUv3IbCN",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/1VzNvWLltE"
    ]

    # Instagram Reels
    try:
        log("📸 Đang đăng ngay lên Instagram Reels...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels [Dùng Rồi Mới Nói]: {res_ig}")
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels [Dùng Rồi Mới Nói]: {e}\n{traceback.format_exc()}")

    # Threads
    try:
        log("🧵 Đang đăng ngay lên Threads...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads [Dùng Rồi Mới Nói]: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads [Dùng Rồi Mới Nói]: {e}\n{traceback.format_exc()}")

# ==============================================================================
# 2. GÓC TẬP LUYỆN
# ==============================================================================
def publish_goc_tap_luyen(brands):
    log("\n" + "=" * 70)
    log("🏋️ [2/3] ĐĂNG NGAY CHO THƯƠNG HIỆU: GÓC TẬP LUYỆN")
    log("=" * 70)
    brand_data = brands.get("goc_tap_luyen", {})
    video_path = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\3.mp4"

    yt_title = "Dụng cụ hỗ trợ tập giãn cơ thon chân & siết eo tại nhà cực đỉnh #Shorts"
    yt_desc = (
        "Tổng hợp những dụng cụ tập luyện tại nhà cực kỳ hữu ích giúp thon chân, định hình vóc dáng, siết eo và bảo vệ khớp gối hiệu quả. "
        "Tập luyện đúng cách mỗi ngày để tự tin khoe dáng chuẩn!\n\n"
        "#Shorts #goctapluyen #tapgymtainha #thonchan #gianco #sieo #fitness #workout"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6V5U5b66gG",
        "Link sản phẩm: https://s.shopee.vn/1Lfw6rRFWF",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2VrtV0Mnc3",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5VVV4WCCdz",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6fhSSf7lH8",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/70KIt8Gf12",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/40ghIyU55p",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/9zxuRy8bXw"
    ]

    fb_title = "Bí quyết tập giãn cơ định hình chân thon và siết eo tại nhà"
    fb_caption = (
        "Chân to, cơ bắp căng cứng hay mỡ bụng dưới khó giảm thì lưu ngay bài tập với combo dụng cụ tiện ích này nhé cả nhà! "
        "Bảng nghiêng giãn cơ thon chân + dụng cụ tập cơ sàn chậu tập cực đã, nhẹ người mà form dáng cải thiện rõ rệt 🔥\n\n"
        "👉 Sắm ngay bảng nghiêng giãn cơ thon chân chính hãng tại: https://s.shopee.vn/BTyiiVgKP\n\n"
        "#reels #viral #fyp #goctapluyen #tapgymtainha #thonchan #gianco #kegel #fitnesslifestyle"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/BTyiiVgKP",
        "Link sản phẩm: https://s.shopee.vn/1Lfw6rRExk",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2VrtV0Mnb5",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5VVV4WCCdF",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6fhSSf7lGa"
    ]

    ig_caption = (
        "Bí quyết sở hữu đôi chân thon gọn và vòng eo săn chắc ngay tại nhà không hề khó! "
        "Kiên trì kết hợp bài tập giãn cơ cùng dụng cụ tập sàn chậu và con lăn trợ lực mỗi ngày để cảm nhận sự thay đổi rõ rệt ✨ "
        "Link trọn bộ phụ kiện tập luyện chính hãng mình để chi tiết dưới phần comment nha 👇\n\n"
        "#reels #viral #fyp #goctapluyen #workoutathome #chanthon #gianco #pilates #fitnessgoals"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/LnOv1V2zS",
        "Link sản phẩm: https://s.shopee.vn/1VzMJAQbcn",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2gBJhJMAG8",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5fovGpBZII",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6q0sey77vd"
    ]

    th_caption = (
        "Ai hay bị mỏi chân, bắp chuối to hay đau lưng khi tập thì lưu ngay bài này! Bảng nghiêng kéo giãn bắp chân + dụng cụ tập sàn chậu siết mông đùi tại nhà siêu hiệu quả ✨\n\n"
        "🛒 Link sắm đồ tập chính hãng nè cả nhà:\n"
        "1. Bảng nghiêng thon chân: https://s.shopee.vn/W6p7KUPeV\n"
        "2. Dụng cụ tập Kegel mông đùi: https://s.shopee.vn/1gImVTPyHq\n"
        "3. Con lăn bụng 4 bánh trợ lực: https://s.shopee.vn/9zxuQmv4V2\n\n"
        "#goctapluyen #workout #chanthon #fitness"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6p7KUPeV",
        "Link sản phẩm: https://s.shopee.vn/1gImVTPyHq",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/9zxuQmv4V2",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/5q8LT8AvxL"
    ]

    # YouTube Shorts (ĐĂNG NGAY - PUBLIC)
    try:
        log("🔴 [Góc Tập Luyện] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/goc_tap_luyen.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "goctapluyen", "tapgymtainha", "thonchan", "workout"],
            comment_text=yt_comments,
            privacy_status="public",
            publish_at=None
        )
        log(f"✅ Kết quả YouTube Shorts [Góc Tập Luyện]: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi YouTube Shorts [Góc Tập Luyện]: {e}\n{traceback.format_exc()}")

    # Facebook Reels (ĐĂNG NGAY)
    try:
        log("🔷 [Góc Tập Luyện] Đang tải lên Facebook Reels (Publish Now)...")
        fb_cfg = brand_data.get("facebook", {})
        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        res_fb = fb.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comments,
            scheduled_time=None
        )
        log(f"✅ Kết quả Facebook Reels [Góc Tập Luyện]: {res_fb}")
    except Exception as e:
        log(f"❌ Lỗi Facebook Reels [Góc Tập Luyện]: {e}\n{traceback.format_exc()}")

    # Instagram Reels (ĐĂNG NGAY)
    try:
        log("📸 [Góc Tập Luyện] Đang tải lên Instagram Reels (Publish Now)...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels [Góc Tập Luyện]: {res_ig}")
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels [Góc Tập Luyện]: {e}\n{traceback.format_exc()}")

    # Threads (ĐĂNG NGAY)
    try:
        log("🧵 [Góc Tập Luyện] Đang tải lên Threads (Publish Now)...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads [Góc Tập Luyện]: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads [Góc Tập Luyện]: {e}\n{traceback.format_exc()}")

# ==============================================================================
# 3. NÓI THẬT DÙNG THẬT
# ==============================================================================
def publish_noi_that_dung_that(brands):
    log("\n" + "=" * 70)
    log("🐱 [3/3] ĐĂNG NGAY CHO THƯƠNG HIỆU: NÓI THẬT DÙNG THẬT")
    log("=" * 70)
    brand_data = brands.get("noi_that_dung_that", {})
    video_path = r"C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\cạo lông mèo.mp4"

    yt_title = "Cứu tinh cho sen mùa mèo rụng lông: Lược chải gỡ rối bấm nút nhả lông siêu đã #Shorts"
    yt_desc = (
        "Chiếc lược chải lông thần thánh giúp gỡ rối, lấy sạch lông rụng tận chân lông cho chó mèo cực êm ái. "
        "Bấm một nút là lông rụng bay hết gọn gàng, không lo lông bay khắp nhà nữa!\n\n"
        "#Shorts #noithatdungthat #luocchailongmeo #chamsocchomeo #petcare #meo #review"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7V7qF61u9i",
        "Link sản phẩm: https://s.shopee.vn/3VbMawZ35y",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/4flgG9yE7y",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AKamR6j0fB",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/20vcufKj4N"
    ]

    fb_title = "Lược chải lông thú cưng bấm nút nhả lông siêu tiện lợi"
    fb_caption = (
        "Mùa rụng lông đến mà nhà lúc nào cũng ngập trong lông mèo thì sắm ngay em lược chải gỡ rối thông minh này nhé các sen! "
        "Răng lược bo tròn êm ái massage cực phê, chải tới đâu lông rụng gom gọn tới đó, bấm 1 nút là nhả sạch lông trong 1 giây 🔥\n\n"
        "👉 Link sắm lược chải lông chính hãng tại: https://s.shopee.vn/6q0se8IiKl\n\n"
        "#reels #viral #fyp #noithatdungthat #luocchailongmeo #chomeo #yeupet #reviewtienich"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6q0se8IiKl",
        "Link sản phẩm: https://s.shopee.vn/5fovFzN9hc",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AUuB0s4ktd",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/9KiDcj9CGU",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8plx1oB6HT"
    ]

    ig_caption = (
        "Sen nào nuôi mèo mà không có chiếc lược chải lông bấm nút nhả tự động này thì quá thiếu sót! "
        "Lấy lông rụng siêu sạch, gỡ rối không đau rát lại còn massage thư giãn cho boss cực thích ✨ "
        "Trải nghiệm thực tế đúng là đáng từng đồng! Link sắm lược xịn mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #noithatdungthat #catlover #chamsocmeo #luocchailong #petlifestyle #catsoftiktok"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6L4c3DKcLg",
        "Link sản phẩm: https://s.shopee.vn/5q8LSIMWMf",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/9zxuPx6euY",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/9V1dp28YvX",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8KpgQtD0IO"
    ]

    th_caption = (
        "Nhà nuôi chó mèo đến mùa thay lông thì nhất định phải tậu em lược chải gỡ rối này! Răng lược bọc đầu êm ru, chải gom lông cực gọn, bấm 1 phát nhả sạch tinh ✨\n\n"
        "🛒 Link sắm lược xịn cho boss nè:\n"
        "1. Lược gỡ rối lông Poodle/Mèo: https://s.shopee.vn/6VO2FWJz0j\n"
        "2. Lược chải massage giảm rụng: https://s.shopee.vn/5LC4rNOQNa\n"
        "3. Lược CLEAN bấm nút nhả lông: https://s.shopee.vn/AAHKcG61Zb\n\n"
        "#noithatdungthat #petcare #meo #luocchailong"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/6VO2FWJz0j",
        "Link sản phẩm: https://s.shopee.vn/5LC4rNOQNa",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AAHKcG61Zb",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/905NE7ASwS"
    ]

    # YouTube Shorts (ĐĂNG NGAY - PUBLIC)
    try:
        log("🔴 [Nói Thật Dùng Thật] Đang tải lên YouTube Shorts (Publish Now)...")
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/noi_that_dung_that.json"))
        yt = YouTubeShortsUploader(token_file=token_path)
        res_yt = yt.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "noithatdungthat", "luocchailongmeo", "chomeo", "petcare"],
            comment_text=yt_comments,
            privacy_status="public",
            publish_at=None
        )
        log(f"✅ Kết quả YouTube Shorts [Nói Thật Dùng Thật]: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi YouTube Shorts [Nói Thật Dùng Thật]: {e}\n{traceback.format_exc()}")

    # Facebook Reels (ĐĂNG NGAY)
    try:
        log("🔷 [Nói Thật Dùng Thật] Đang tải lên Facebook Reels (Publish Now)...")
        fb_cfg = brand_data.get("facebook", {})
        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        res_fb = fb.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comments,
            scheduled_time=None
        )
        log(f"✅ Kết quả Facebook Reels [Nói Thật Dùng Thật]: {res_fb}")
    except Exception as e:
        log(f"❌ Lỗi Facebook Reels [Nói Thật Dùng Thật]: {e}\n{traceback.format_exc()}")

    # Instagram Reels (ĐĂNG NGAY)
    try:
        log("📸 [Nói Thật Dùng Thật] Đang tải lên Instagram Reels (Publish Now)...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels [Nói Thật Dùng Thật]: {res_ig}")
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels [Nói Thật Dùng Thật]: {e}\n{traceback.format_exc()}")

    # Threads (ĐĂNG NGAY)
    try:
        log("🧵 [Nói Thật Dùng Thật] Đang tải lên Threads (Publish Now)...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads [Nói Thật Dùng Thật]: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads [Nói Thật Dùng Thật]: {e}\n{traceback.format_exc()}")

def main():
    brands = load_brands()
    log("🚀 BẮT ĐẦU TIẾN TRÌNH ĐĂNG NGAY LẬP TỨC (ALL-IN-ONE)...")
    
    # 1. Dùng Rồi Mới Nói (IG & Threads)
    publish_dung_roi_moi_noi(brands)

    # 2. Góc Tập Luyện (4 nền tảng)
    publish_goc_tap_luyen(brands)

    # 3. Nói Thật Dùng Thật (4 nền tảng)
    publish_noi_that_dung_that(brands)

    log("\n🎉🎉 HOÀN TẤT TOÀN BỘ TIẾN TRÌNH ĐĂNG NGAY CHO 3 THƯƠNG HIỆU!")

if __name__ == "__main__":
    main()
