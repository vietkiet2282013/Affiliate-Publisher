# -*- coding: utf-8 -*-
"""
Script lập lịch tự động và đăng hẹn giờ video cho thương hiệu 'Review Thật Việc Thật' lên 4 nền tảng:
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
    print("🚀 BẮT ĐẦU QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO: REVIEW THẬT VIỆC THẬT", flush=True)
    print("=" * 70, flush=True)

    video_path = r"C:\Affiliate\Review Thật Việc Thật\video_việt_hóa\cọ khe nhà vệ sinh.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}", flush=True)
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "review_that_viec_that"
    brand_data = brands[brand_key]

    # Lập lịch tối nay (2026-09-24):
    # 1. YouTube Shorts: 18:16:00 UTC+7 (11:16:00Z)
    # 2. Facebook Reels: 18:24:00 UTC+7 (Timestamp 1790249040)
    # 3. Instagram Reels: 18:33:00 UTC+7 (Timestamp 1790249580)
    # 4. Threads: 18:44:00 UTC+7 (Timestamp 1790250240)

    yt_dt = datetime.datetime(2026, 9, 24, 18, 16, 0)
    fb_dt = datetime.datetime(2026, 9, 24, 18, 24, 0)
    ig_dt = datetime.datetime(2026, 9, 24, 18, 33, 0)
    th_dt = datetime.datetime(2026, 9, 24, 18, 44, 0)

    # ----------------------------------------------------
    # BƯỚC 1: ĐƯA INSTAGRAM & THREADS VÀO HÀNG ĐỢI SCHEDULER
    # ----------------------------------------------------
    print("\n📦 [1/4] Đang thêm Instagram Reels & Threads vào hàng đợi Scheduler...", flush=True)
    queue = load_queue()

    # Task Instagram
    ig_caption = (
        "Cứu tinh cho những góc chết khó cọ rửa nhất trong nhà tắm đây rồi! "
        "Cây chổi cọ chữ L cán dài này lách vào tận khe bồn cầu, viền gạch cọ tới đâu sáng bóng tới đó mà không cần khom lưng mỏi người ✨ "
        "Link sản phẩm chính hãng mình để dưới phần bình luận nhé 👇\n\n"
        "#reels #viral #fyp #reviewthatviecthat #choiconhavesinh #donnhathongminh #meovatcuocsong #giadungtienich"
    )
    ig_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1Lfw6uvaBB\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1qcChptgAI"
    )
    task_ig = {
        "id": f"task_ig_rtvt_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": ig_comment,
        "platforms": ["instagram"],
        "scheduled_time_str": ig_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(ig_dt.timestamp()),
        "product_keyword": "Chổi cọ góc chữ L nhà vệ sinh",
        "status": "PENDING"
    }

    # Task Threads
    th_caption = (
        "Chân ái dọn nhà tắm là đây! Mấy cái góc kẹt chân bồn cầu hay khe kính trước giờ cọ mãi không tới, "
        "dùng cây chổi cọ chữ L này luồn vào một phát là sạch bong ✨ Cán dài đứng chà thẳng lưng không lo mỏi. "
        "Review thật việc thật cho mọi người nhé!\n\n"
        "🛒 Link mua hàng chính hãng:\n"
        "1. https://s.shopee.vn/2BF36Rwk1J\n"
        "2. https://s.shopee.vn/2LYTIkw6gM\n\n"
        "#reviewthatviecthat #meovat #giadung"
    )
    th_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2BF36Rwk1J\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2LYTIkw6gM"
    )
    task_th = {
        "id": f"task_th_rtvt_{int(time.time())}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": th_caption,
        "comment": th_comment,
        "platforms": ["threads"],
        "scheduled_time_str": th_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": int(th_dt.timestamp()),
        "product_keyword": "Chổi cọ góc chữ L nhà vệ sinh",
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
    yt_title = "Chổi Cọ Khe Chữ L Vệ Sinh Góc Chết Siêu Sạch #Shorts"
    yt_desc = (
        "Review thật cây chổi cọ nhà vệ sinh góc chữ L cán dài: len lỏi tận chân bồn cầu, khe gạch, "
        "góc chết tường phòng tắm cọ tới đâu sạch bong tới đó! Không còn phải cúi gập lưng hay dùng tay kỳ cọ vất vả nữa nha mọi người.\n\n"
        "🛒 Mua sản phẩm chính hãng tại:\n"
        "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8plx2hb4e4\n"
        "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8fSWqObhz3\n\n"
        "#ReviewThậtViệcThật #ChổiCọNhàVệSinh #CọGócChữL #MẹoVặtGiaĐình #ĐồGiaDụngThôngMinh"
    )
    yt_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8plx2hb4e4\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/8fSWqObhz3"
    )
    publish_at_rfc3339 = "2026-09-24T11:16:00Z"

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
    fb_title = "Chổi Cọ Góc Chữ L Cán Dài Đánh Bay Mọi Khe Kẽ Nhà Tắm"
    fb_caption = (
        "Ai hay dọn nhà vệ sinh mà ngán nhất mấy góc chết với khe chân bồn cầu thì sắm ngay cây chổi cọ chữ L này nha! "
        "Đầu chổi bẻ cong 90 độ, lông cọ cứng cáp luồn lách mọi ngóc ngách, cán dài đứng cọ thẳng lưng siêu khỏe. "
        "Trải nghiệm dùng thực tế quá ưng ý! Link mua chính hãng mình ghim dưới cmt nhé 👇\n\n"
        "#ReviewThậtViệcThật #ChổiCọChữL #VệSinhNhàCửa #ĐồGiaDụngThôngMinh #MẹoDọnNhà"
    )
    fb_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6L4c46ccHn\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6q0sf1aiGu"
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
    print("🎉 HOÀN TẤT THIẾT LẬP LỊCH ĐĂNG TOÀN BỘ 4 NỀN TẢNG CHO 'REVIEW THẬT VIỆC THẬT'!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
