# -*- coding: utf-8 -*-
"""
Script lập lịch tự động và đăng hẹn giờ video cho thương hiệu 'Chăm Da Tiết Kiệm' lên 4 nền tảng:
1. YouTube Shorts: Server-side schedule qua Google API v3 (status.publishAt & privacyStatus: private)
2. Facebook Reels: Server-side schedule qua Meta Graph API (scheduled_publish_time & video_state: SCHEDULED)
3. Instagram Reels: Local Queue scheduler.py chạy nền
4. Threads: Local Queue scheduler.py chạy nền
"""

import os
import sys
import time
import json
import datetime
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import (
    FacebookReelsUploader,
    YouTubeShortsUploader,
    InstagramReelsUploader,
    ThreadsAPIUploader
)
from scheduler import load_queue, save_queue

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO: CHĂM DA TIẾT KIỆM")
    print("=" * 70)

    video_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\3.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "cham_da_tiet_kiem"
    brand_data = brands[brand_key]

    # Thông tin lịch trình tối nay (2026-09-24)
    # 1. YouTube Shorts: 18:05:00 UTC+7 (11:05:00Z)
    # 2. Facebook Reels: 18:14:00 UTC+7 (Timestamp 1790248440)
    # 3. Instagram Reels: 18:22:00 UTC+7 (Timestamp 1790248920)
    # 4. Threads: 18:31:00 UTC+7 (Timestamp 1790249460)

    yt_dt = datetime.datetime(2026, 9, 24, 18, 5, 0)
    fb_dt = datetime.datetime(2026, 9, 24, 18, 14, 0)
    ig_dt = datetime.datetime(2026, 9, 24, 18, 22, 0)
    th_dt = datetime.datetime(2026, 9, 24, 18, 31, 0)

    # ----------------------------------------------------
    # BƯỚC 1: ĐƯA INSTAGRAM & THREADS VÀO HÀNG ĐỢI SCHEDULER
    # ----------------------------------------------------
    print("\n📦 [1/4] Đang thêm Instagram Reels & Threads vào hàng đợi Scheduler...")
    queue = load_queue()

    # Task Instagram
    ig_caption = (
        "Cấp ẩm căng bóng da tại nhà cực dễ với Biodance Bubble Pack Booster & Mặt nạ Collagen phục hồi sâu ✨ "
        "Da mịn màng, ẩm mượt không lo khô ráp mùa này! Link mua chính hãng mình ghim bên dưới comment nha 👇\n\n"
        "#reels #viral #fyp #skincareroutine #biodance #chamdatietkiem #collagen #beautyhacks"
    )
    ig_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9zxzHFOeaQ\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5VVWZlvEIy"
    )
    task_ig = {
        "id": f"task_ig_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": ig_comment,
        "platforms": ["instagram"],
        "scheduled_time_str": ig_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(ig_dt.timestamp()),
        "product_keyword": "Biodance Bubble Booster & Mặt nạ Collagen",
        "status": "PENDING"
    }

    # Task Threads
    th_caption = (
        "Da khô sần, thiếu sức sống thì thử ngay combo Biodance Bubble Pack Booster sủi bọt căng bóng + Mặt nạ Collagen cấp ẩm sâu này nha cả nhà! "
        "Cấp nước tầng sâu, da ngậm nước mọng mướt tức thì mà cực kỳ tiết kiệm ✨\n\n"
        "🛒 Link mua hàng chính hãng:\n"
        "1. Biodance Booster: https://s.shopee.vn/AAHPTYO1FT\n"
        "2. Mặt nạ Collagen: https://s.shopee.vn/4qFpmXxlg5\n\n"
        "#chamdatietkiem #skincare #biodance #review"
    )
    th_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/AAHPTYO1FT\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4qFpmXxlg5"
    )
    task_th = {
        "id": f"task_th_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": th_caption,
        "comment": th_comment,
        "platforms": ["threads"],
        "scheduled_time_str": th_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(th_dt.timestamp()),
        "product_keyword": "Biodance Bubble Booster & Mặt nạ Collagen",
        "status": "PENDING"
    }

    # Check avoid duplicate
    existing_timestamps = {t.get("scheduled_timestamp") for t in queue if t.get("brand_key") == brand_key and t.get("status") == "PENDING"}
    if task_ig["scheduled_timestamp"] not in existing_timestamps:
        queue.append(task_ig)
        print(f"  ✅ Đã lên lịch Instagram Reels: {task_ig['scheduled_time_str']}")
    else:
        print("  ℹ️ Đã tồn tại task Instagram Reels cùng khung giờ trong hàng đợi.")

    if task_th["scheduled_timestamp"] not in existing_timestamps:
        queue.append(task_th)
        print(f"  ✅ Đã lên lịch Threads: {task_th['scheduled_time_str']}")
    else:
        print("  ℹ️ Đã tồn tại task Threads cùng khung giờ trong hàng đợi.")

    save_queue(queue)

    # ----------------------------------------------------
    # BƯỚC 2: HẸN GIỜ TRỰC TIẾP LÊN YOUTUBE SHORTS (API V3)
    # ----------------------------------------------------
    print("\n🔴 [2/4] Đang gọi Google API v3 để hẹn giờ YouTube Shorts...")
    yt_title = "Bí Quyết Da Căng Bóng Với Biodance Bubble Booster #Shorts"
    yt_desc = (
        "Tinh chất sủi bọt Biodance Liposome Bubble Pack Booster giúp da ngậm nước căng bóng tức thì, "
        "kết hợp cùng mặt nạ Collagen cấp ẩm sâu cho làn da rạng rỡ chuẩn Hàn!\n\n"
        "#ChămDaTiếtKiệm #Biodance #BubbleBooster #CollagenMask #SkincareTips"
    )
    yt_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9V1igKQYbP\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8AWHkfkwQm"
    )
    publish_at_rfc3339 = "2026-09-24T11:05:00Z"

    yt_cfg = brand_data.get("youtube", {})
    token_file = yt_cfg.get("token_file")
    yt_uploader = YouTubeShortsUploader(token_file=token_file)
    yt_res = yt_uploader.upload_short(
        video_path=video_path,
        title=yt_title,
        description=yt_desc,
        comment_text=yt_comment,
        privacy_status="private",
        publish_at=publish_at_rfc3339
    )
    if yt_res:
        print(f"🎉 YouTube Shorts đã được lên lịch thành công: {yt_res.get('shorts_url')}")
    else:
        print("⚠️ YouTube Shorts upload thất bại hoặc có lỗi xảy ra.")

    # ----------------------------------------------------
    # BƯỚC 3: HẸN GIỜ TRỰC TIẾP LÊN FACEBOOK REELS (META API)
    # ----------------------------------------------------
    print("\n🔷 [3/4] Đang gọi Meta Graph API để hẹn giờ Facebook Reels...")
    fb_title = "Bí Quyết Da Căng Mịn Tiết Kiệm Tại Nhà"
    fb_caption = (
        "Không cần đi spa tốn kém, em sủi bọt Biodance Bubble Booster kết hợp mặt nạ Collagen này giúp da căng mướt, cấp ẩm sâu cả ngày dài! Chị em thử ngay nha ✨\n\n"
        "#ChămDaTiếtKiệm #Biodance #SkincareHànQuốc #PhụcHồiDa #DưỡngẨmDa"
    )
    fb_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/AUuFsAMkZV\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2Vrv0G6vRe"
    )
    fb_cfg = brand_data["facebook"]
    fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
    fb_res = fb_uploader.upload_reel(
        video_path=video_path,
        title=fb_title,
        caption=fb_caption,
        comment_text=fb_comment,
        scheduled_time=int(fb_dt.timestamp())
    )
    if fb_res:
        print(f"🎉 Facebook Reels đã được lên lịch thành công: {fb_res.get('reel_url')}")
    else:
        print("⚠️ Facebook Reels upload thất bại hoặc có lỗi xảy ra.")

    # ----------------------------------------------------
    # BƯỚC 4: ĐẢM BẢO SCHEDULER WORKER CHẠY NỀN
    # ----------------------------------------------------
    print("\n⚙️ [4/4] Kiểm tra Scheduler Background Worker...")
    python_exe = os.path.join(os.path.dirname(BASE_DIR), ".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    scheduler_script = os.path.join(BASE_DIR, "scheduler.py")
    log_file = os.path.join(BASE_DIR, "config", "scheduler.log")
    with open(log_file, "a", encoding="utf-8") as out:
        subprocess.Popen(
            [python_exe, scheduler_script, "--worker"],
            stdout=out,
            stderr=out,
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
    print(f"✅ Scheduler Worker đã sẵn sàng chạy nền để xuất bản Instagram (18:22) và Threads (18:31)!")
    print("=" * 70)
    print("🎉 HOÀN TẤT THIẾT LẬP LỊCH ĐĂNG TOÀN BỘ 4 NỀN TẢNG CHO 'CHĂM DA TIẾT KIỆM'!")
    print("=" * 70)

if __name__ == "__main__":
    main()
