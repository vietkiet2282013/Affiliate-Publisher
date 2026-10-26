# -*- coding: utf-8 -*-
"""
Script lập lịch tự động và đăng hẹn giờ video cho thương hiệu 'Góc Tập Luyện' lên 4 nền tảng:
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
    print("🚀 BẮT ĐẦU QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO: GÓC TẬP LUYỆN", flush=True)
    print("=" * 70, flush=True)

    video_path = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\2.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}", flush=True)
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "goc_tap_luyen"
    brand_data = brands[brand_key]

    # Lập lịch tối nay:
    # 1. YouTube Shorts: 18:11:00 UTC+7 (11:11:00Z)
    # 2. Facebook Reels: 18:19:00 UTC+7 (Timestamp 1790248740)
    # 3. Instagram Reels: 18:28:00 UTC+7 (Timestamp 1790249280)
    # 4. Threads: 18:39:00 UTC+7 (Timestamp 1790249940)

    yt_dt = datetime.datetime(2026, 9, 24, 18, 11, 0)
    fb_dt = datetime.datetime(2026, 9, 24, 18, 19, 0)
    ig_dt = datetime.datetime(2026, 9, 24, 18, 28, 0)
    th_dt = datetime.datetime(2026, 9, 24, 18, 39, 0)

    # ----------------------------------------------------
    # BƯỚC 1: ĐƯA INSTAGRAM & THREADS VÀO HÀNG ĐỢI SCHEDULER
    # ----------------------------------------------------
    print("\n📦 [1/4] Đang thêm Instagram Reels & Threads vào hàng đợi Scheduler...", flush=True)
    queue = load_queue()

    # Task Instagram
    ig_caption = (
        "Bí quyết siết cơ bụng tại nhà không đau lưng cho anh chị em đây! "
        "Con lăn 4 bánh trợ lực thông minh Habana Sport hồi chuyển cực êm, giữ thăng bằng tốt cho cả người mới bắt đầu ✨ "
        "Mỗi ngày chỉ cần 15 phút là cơ bụng săn chắc thấy rõ! Link mua chính hãng mình để dưới comment nha 👇\n\n"
        "#reels #viral #fyp #goctapluyen #conlantapbung #gymtainha #giammobung #workoutmotivation"
    )
    ig_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1qcChmPKvq\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2gBJhJMAF7"
    )
    task_ig = {
        "id": f"task_ig_gtl_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": ig_comment,
        "platforms": ["instagram"],
        "scheduled_time_str": ig_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(ig_dt.timestamp()),
        "product_keyword": "Con lăn tập cơ bụng 4 bánh trợ lực",
        "status": "PENDING"
    }

    # Task Threads
    th_caption = (
        "Gập bụng truyền thống dễ đau cổ đau lưng, đổi qua con lăn tập bụng 4 bánh có trợ lực này tập sướng hơn hẳn! "
        "Lò xo hồi lực êm ái, bám sàn tốt, siết toàn bộ cơ bụng trên dưới liên sườn cực đã ✨\n\n"
        "🛒 Link mua hàng chính hãng nè:\n"
        "1. Con lăn bụng Habana Sport 4 bánh: https://s.shopee.vn/1gImVTPyGp\n"
        "2. Con lăn tập bụng Welike: https://s.shopee.vn/3B7aIEKGEE\n\n"
        "#goctapluyen #workout #gym #fitness"
    )
    th_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1gImVTPyGp\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3B7aIEKGEE"
    )
    task_th = {
        "id": f"task_th_gtl_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": th_caption,
        "comment": th_comment,
        "platforms": ["threads"],
        "scheduled_time_str": th_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(th_dt.timestamp()),
        "product_keyword": "Con lăn tập cơ bụng 4 bánh trợ lực",
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
    yt_title = "Siết Cơ Bụng Cực Đỉnh Với Con Lăn 4 Bánh Trợ Lực #Shorts"
    yt_desc = (
        "Tập bụng tại nhà cực nhàn mà hiệu quả siết cơ gấp đôi nhờ con lăn 4 bánh có trợ lực Habana Sport! "
        "Có lò xo trợ lực đẩy kéo êm ái, chống trượt an toàn, người mới bắt đầu cũng tập ngon ơ.\n\n"
        "🛒 Mua sản phẩm chính hãng tại:\n"
        "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2LYTIhNQv1\n"
        "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3qNH5SHisQ\n\n"
        "#GócTậpLuyện #TậpBụngTạiNhà #ConLănTậpBụng #GymTạiNhà #FitnessMotivation"
    )
    yt_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2LYTIhNQv1\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3qNH5SHisQ"
    )
    publish_at_rfc3339 = "2026-09-24T11:11:00Z"

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
    fb_title = "Con Lăn Tập Bụng 4 Bánh Trợ Lực Siết Cơ Tại Nhà"
    fb_caption = (
        "Muốn bụng phẳng eo thon mà ngại gập bụng đau lưng thì thử ngay con lăn 4 bánh trợ lực này nhé! "
        "Thiết kế bánh đôi trợ lực hồi chuyển thông minh, tập êm không lo chấn thương. Bác nào đang tập gym tại nhà lưu lại ngay nha ✨\n\n"
        "#GócTậpLuyện #ConLănTậpBụng #GiảmMỡBụng #FitnessTạiNhà #GymMotivation"
    )
    fb_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1Lfw6rREwj\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2qUjtcLWu8"
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
        print("⚠️ Facebook Reels upload thất bại hoặc có lỗi xảy ra.", flush=True)

    print("=" * 70, flush=True)
    print("🎉 HOÀN TẤT THIẾT LẬP LỊCH ĐĂNG TOÀN BỘ 4 NỀN TẢNG CHO 'GÓC TẬP LUYỆN'!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
