# -*- coding: utf-8 -*-
"""
Script lập lịch tự động và đăng hẹn giờ video cho thương hiệu 'Quần Áo Giá Hời' lên 4 nền tảng:
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

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    print("=" * 70, flush=True)
    print("🚀 BẮT ĐẦU QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO: QUẦN ÁO GIÁ HỜI", flush=True)
    print("=" * 70, flush=True)

    video_path = r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\1.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}", flush=True)
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "quan_ao_gia_hoi"
    brand_data = brands[brand_key]

    # Lập lịch tối nay (2026-09-24):
    # 1. YouTube Shorts: 18:26:00 UTC+7 (11:26:00Z)
    # 2. Facebook Reels: 18:36:00 UTC+7 (Timestamp 1790249760)
    # 3. Instagram Reels: 18:47:00 UTC+7 (Timestamp 1790250420)
    # 4. Threads: 18:55:00 UTC+7 (Timestamp 1790250900)

    yt_dt = datetime.datetime(2026, 9, 24, 18, 26, 0)
    fb_dt = datetime.datetime(2026, 9, 24, 18, 36, 0)
    ig_dt = datetime.datetime(2026, 9, 24, 18, 47, 0)
    th_dt = datetime.datetime(2026, 9, 24, 18, 55, 0)

    # ----------------------------------------------------
    # BƯỚC 1: ĐƯA INSTAGRAM & THREADS VÀO HÀNG ĐỢI SCHEDULER
    # ----------------------------------------------------
    print("\n📦 [1/4] Đang thêm Instagram Reels & Threads vào hàng đợi Scheduler...", flush=True)
    queue = load_queue()

    # Task Instagram
    ig_caption = (
        "Chiếc áo cardigan len mỏng nhẹ chân ái cho thời tiết se lạnh đây các nàng ơi! "
        "Thiết kế cúc xinh xắn, dáng rộng thoải mái phối đồ gì cũng ra vibe nàng thơ Hàn Quốc ✨ "
        "Link các mẫu đẹp giá hời mình ghim dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #quanaogiahoi #cardigan #outfitoftheday #thoitrangnu #phoidoxinh"
    )
    ig_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/40gmDUcb1f\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/BU3eRrBo2"
    )
    task_ig = {
        "id": f"task_ig_qagh_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": ig_comment,
        "platforms": ["instagram"],
        "scheduled_time_str": ig_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(ig_dt.timestamp()),
        "product_keyword": "Áo khoác cardigan len mỏng nhẹ Tập 1",
        "status": "PENDING"
    }

    # Task Threads
    th_caption = (
        "Thời tiết này mà diện cardigan len mỏng nhẹ thì đúng là chuẩn bài luôn các nàng ơi! "
        "Form rộng che eo cực đỉnh, phối với chân váy hay jean suông đều xinh xỉu ✨ Đang có giá hời cho chị em sắm nhé:\n\n"
        "🛒 Link mua hàng chính hãng:\n"
        "1. https://s.shopee.vn/5AsjbdY9eu\n"
        "2. https://s.shopee.vn/1AdS8rp91\n\n"
        "#quanaogiahoi #ootd #cardigan #thoitrang"
    )
    th_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/5AsjbdY9eu\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1AdS8rp91"
    )
    task_th = {
        "id": f"task_th_qagh_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": th_caption,
        "comment": th_comment,
        "platforms": ["threads"],
        "scheduled_time_str": th_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(th_dt.timestamp()),
        "product_keyword": "Áo khoác cardigan len mỏng nhẹ Tập 1",
        "status": "PENDING"
    }

    existing_timestamps = {t.get("scheduled_timestamp") for t in queue if t.get("brand_key") == brand_key and t.get("status") == "PENDING"}
    if task_ig["scheduled_timestamp"] not in existing_timestamps:
        queue.append(task_ig)
        print(f"  ✅ Đã lên lịch Instagram Reels: {task_ig['scheduled_time_str']}", flush=True)
    else:
        print("  ℹ️ Đã tồn tại task Instagram Reels trong hàng đợi.", flush=True)

    if task_th["scheduled_timestamp"] not in existing_timestamps:
        queue.append(task_th)
        print(f"  ✅ Đã lên lịch Threads: {task_th['scheduled_time_str']}", flush=True)
    else:
        print("  ℹ️ Đã tồn tại task Threads trong hàng đợi.", flush=True)

    save_queue(queue)

    # ----------------------------------------------------
    # BƯỚC 2: HẸN GIỜ TRỰC TIẾP LÊN YOUTUBE SHORTS (API V3)
    # ----------------------------------------------------
    print("\n🔴 [2/4] Đang gọi Google API v3 để hẹn giờ YouTube Shorts...", flush=True)
    yt_title = "Gợi Ý Phối Đồ Với Áo Khoác Cardigan Len Mỏng Cực Xinh #Shorts"
    yt_desc = (
        "Tổng hợp mẫu áo khoác cardigan len mỏng nhẹ, form rộng hack dáng siêu đỉnh cho các nàng mùa thu đông! "
        "Chất len mềm mịn, mặc đi học hay đi làm đều cực thanh lịch và dễ phối đồ.\n\n"
        "🛒 Mua sản phẩm chính hãng ưu đãi tại:\n"
        "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/W6u33pv84\n"
        "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/gQKFMpHnD\n\n"
        "#QuầnÁoGiáHời #CardiganLen #PhốiĐồĐẹp #ThờiTrangNữ #OOTD"
    )
    yt_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/W6u33pv84\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/gQKFMpHnD"
    )
    publish_at_rfc3339 = "2026-09-24T11:26:00Z"

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
        print(f"🎉 YouTube Shorts đã được lên lịch thành công: {yt_res.get('shorts_url')}", flush=True)
    else:
        print("⚠️ YouTube Shorts upload thất bại hoặc có lỗi xảy ra.", flush=True)

    # ----------------------------------------------------
    # BƯỚC 3: HẸN GIỜ TRỰC TIẾP LÊN FACEBOOK REELS (META API)
    # ----------------------------------------------------
    print("\n🔷 [3/4] Đang gọi Meta Graph API để hẹn giờ Facebook Reels...", flush=True)
    fb_title = "Mẫu Áo Khoác Cardigan Len Mỏng Nhẹ Chuẩn Gu Hàn Quốc"
    fb_caption = (
        "Item không thể thiếu trong tủ đồ mùa này của các nàng chính là em cardigan len mỏng nhẹ này nha! "
        "Form rộng thoải mái che khuyết điểm cực tốt, chất len mềm dịu không lo dặm ngứa. "
        "Phối với chân váy hay quần suông đều xinh xỉu ✨ Link sắm đồ giá hời mình để dưới bình luận nhé 👇\n\n"
        "#QuầnÁoGiáHời #ÁoCardigan #Thờitrangnữ #GợiÝPhốiĐồ #OOTDVietnam"
    )
    fb_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4B0CPnbxgg\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/LnTqkqYT3"
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
        print(f"🎉 Facebook Reels đã được lên lịch thành công: {fb_res.get('reel_url')}", flush=True)
    else:
        print("⚠️ Facebook Reels upload thất bại hoặc cần Page Token quyền đăng trực tiếp.", flush=True)

    print("=" * 70, flush=True)
    print("🎉 HOÀN TẤT THIẾT LẬP LỊCH ĐĂNG TOÀN BỘ 4 NỀN TẢNG CHO 'QUẦN ÁO GIÁ HỜI'!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
