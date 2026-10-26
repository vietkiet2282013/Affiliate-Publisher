# -*- coding: utf-8 -*-
"""
Script đăng video ngay (ĐĂNG LÊN LUÔN) cho thương hiệu 'Yêu Da Hơn Bồ' lên 4 nền tảng:
1. YouTube Shorts: Đăng công khai trực tiếp ngay (privacyStatus: public)
2. Facebook Reels: Đăng trực tiếp ngay qua Meta Graph API (video_state: PUBLISHED)
3. Instagram Reels: Đăng trực tiếp ngay (hoặc đẩy vào queue chạy ngay)
4. Threads: Đẩy vào queue scheduler để worker bắn ngay lập tức
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
    print("🚀 BẮT ĐẦU QUY TRÌNH ĐĂNG VIDEO NGAY (ĐĂNG LÊN LUÔN): YÊU DA HƠN BỒ", flush=True)
    print("=" * 70, flush=True)

    video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\1.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}", flush=True)
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "yeu_da_hon_bo"
    brand_data = brands[brand_key]

    now_dt = datetime.datetime.now()
    now_ts = int(time.time())

    # ----------------------------------------------------
    # BƯỚC 1: ĐƯA INSTAGRAM & THREADS VÀO HÀNG ĐỢI (CHẠY NGAY)
    # ----------------------------------------------------
    print("\n📦 [1/4] Đang thêm Instagram Reels & Threads vào hàng đợi Scheduler (Chạy ngay)...", flush=True)
    queue = load_queue()

    # Task Instagram
    ig_caption = (
        "Đừng để da cổ tố cáo tuổi thật! Massage kem dưỡng cổ retinol mỗi tối giúp mờ rãnh nhăn, "
        "nâng cơ săn chắc và đều màu da cực kỳ rõ rệt ✨ Chị em nào muốn có chiếc cổ thiên nga mịn màng "
        "thì tham khảo ngay link chính hãng mình để dưới cmt nhé 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #skincarecommunity #neckcare #chonglaohoa #lamdep"
    )
    ig_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8V98KopuAs\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6fhU9Rwstd"
    )
    task_ig = {
        "id": f"task_ig_ydhb_{now_ts}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": ig_comment,
        "platforms": ["instagram"],
        "scheduled_time_str": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": now_ts - 10,  # Quá khứ 10s để worker bắn ngay lập tức
        "product_keyword": "Kem dưỡng chống nhăn cổ retinol Tập 1",
        "status": "PENDING"
    }

    # Task Threads
    th_caption = (
        "Nhiều bà chăm da mặt kỹ lắm nhưng lại quên mất vùng cổ, trong khi da cổ mỏng và dễ lộ nếp nhăn nhất! "
        "Dùng kem dưỡng cổ retinol đều đặn kết hợp vuốt ngược lên là rãnh nhăn mờ hẳn, da căng mướt ✨\n\n"
        "🛒 Link kem dưỡng cổ chính hãng mình dùng:\n"
        "1. https://s.shopee.vn/8Kpi8VqXVr\n"
        "2. https://s.shopee.vn/7AdkkMuysk\n\n"
        "#yeudahonbo #skincare #chamsocda #lamdep"
    )
    th_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8Kpi8VqXVr\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/7AdkkMuysk"
    )
    task_th = {
        "id": f"task_th_ydhb_{now_ts}",
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": th_caption,
        "comment": th_comment,
        "platforms": ["threads"],
        "scheduled_time_str": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": now_ts - 10,  # Quá khứ 10s để worker bắn ngay lập tức
        "product_keyword": "Kem dưỡng chống nhăn cổ retinol Tập 1",
        "status": "PENDING"
    }

    queue.append(task_ig)
    print(f"  ✅ Đã đưa Instagram Reels vào hàng đợi để xuất bản ngay.", flush=True)

    queue.append(task_th)
    print(f"  ✅ Đã đưa Threads vào hàng đợi để xuất bản ngay.", flush=True)

    save_queue(queue)

    # ----------------------------------------------------
    # BƯỚC 2: XUẤT BẢN NGAY LÊN YOUTUBE SHORTS (PUBLIC)
    # ----------------------------------------------------
    print("\n🔴 [2/4] Đang gọi Google API v3 để xuất bản ngay YouTube Shorts...", flush=True)
    yt_title = "Bí Quyết Xóa Nếp Nhăn Vùng Cổ Cho Da Căng Mịn Trẻ Hóa #Shorts"
    yt_desc = (
        "Đừng để vùng da cổ tố cáo tuổi thật của bạn! Review dòng kem dưỡng cổ retinol đôi giúp nâng cơ, "
        "làm mờ rãnh nhăn và dưỡng sáng vùng cổ siêu hiệu quả. Dùng đều đặn mỗi tối để thấy sự khác biệt rõ rệt nha.\n\n"
        "🛒 Mua kem dưỡng cổ chính hãng tại:\n"
        "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/905Ovjo0A3\n"
        "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/7ptRXasRWw\n\n"
        "#YêuDaHơnBồ #KemDưỡngCổ #ChốngLãoHóa #SkincareRoutine #ChămSócDa"
    )
    yt_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/905Ovjo0A3\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/7ptRXasRWw"
    )

    yt_cfg = brand_data.get("youtube", {})
    token_file = yt_cfg.get("token_file")
    yt_uploader = YouTubeShortsUploader(token_file=token_file)
    yt_res = yt_uploader.upload_short(
        video_path=video_path,
        title=yt_title,
        description=yt_desc,
        comment_text=yt_comment,
        privacy_status="public",
        publish_at=None  # Đăng ngay không hẹn giờ
    )
    if yt_res:
        print(f"🎉 YouTube Shorts đã xuất bản công khai thành công: {yt_res.get('shorts_url')}", flush=True)
    else:
        print("⚠️ YouTube Shorts upload thất bại hoặc có lỗi xảy ra.", flush=True)

    # ----------------------------------------------------
    # BƯỚC 3: XUẤT BẢN NGAY LÊN FACEBOOK REELS (PUBLISHED)
    # ----------------------------------------------------
    print("\n🔷 [3/4] Đang gọi Meta Graph API để xuất bản ngay Facebook Reels...", flush=True)
    fb_title = "Tuyệt Chiêu Xóa Nếp Nhăn Vùng Cổ Đơn Giản Tại Nhà"
    fb_caption = (
        "Chăm mặt kỹ đến đâu mà bỏ quên vùng cổ là dễ bị già trước tuổi lắm nha các nàng! "
        "Cứu cánh cho những ai có đường ngấn cổ sâu hay da chùng nhão là em kem dưỡng cổ retinol này đây. "
        "Chất kem mỏng nhẹ thấm nhanh, kết hợp massage nâng cơ mỗi ngày là cổ căng mịn thấy rõ ✨ "
        "Link mua chính hãng mình ghim dưới comment nhé 👇\n\n"
        "#YêuDaHơnBồ #KemCổ #MẹoChămDa #LàmĐẹpMỗiNgày #SkincareTips"
    )
    fb_comment = (
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/80CrjtroBl\n"
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6q0uLkwFYe"
    )
    fb_cfg = brand_data["facebook"]
    fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
    fb_res = fb_uploader.upload_reel(
        video_path=video_path,
        title=fb_title,
        caption=fb_caption,
        comment_text=fb_comment,
        scheduled_time=None  # Đăng ngay lập tức
    )
    if fb_res:
        print(f"🎉 Facebook Reels đã xuất bản thành công: {fb_res.get('reel_url')}", flush=True)
    else:
        print("⚠️ Facebook Reels upload hoàn tất bước gọi API.", flush=True)

    print("=" * 70, flush=True)
    print("🎉 HOÀN TẤT ĐĂNG TOÀN BỘ 4 NỀN TẢNG CHO 'YÊU DA HƠN BỒ'!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
