# -*- coding: utf-8 -*-
"""
Kịch bản tự động thực thi lập lịch và xuất bản video Tập 3 cho thương hiệu 'Quần Áo Giá Hời'
Theo Phương án 1:
1. YouTube Shorts: Hẹn giờ trực tiếp qua Google YouTube API v3 (status.publishAt = 2026-09-26T05:00:00Z - 12:00:00 UTC+7)
2. Instagram Reels & Story: Khởi tạo và lập lịch xuất bản lúc 12:00:00 trưa 26/09/2026
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

BASE_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, BASE_DIR)

from uploaders import YouTubeShortsUploader, InstagramReelsUploader

QUEUE_FILE = os.path.join(BASE_DIR, "config", "schedule_queue.json")
LOG_FILE = os.path.join(BASE_DIR, "config", "scheduler_quan_ao_gia_hoi_ep3.log")

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def main():
    log("=" * 80)
    log("👗 BẮT ĐẦU THIẾT LẬP HẸN GIỜ ĐĂNG VIDEO: QUẦN ÁO GIÁ HỜI (TẬP 3)")
    log("=" * 80)

    video_path = r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\3.mp4"
    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "quan_ao_gia_hoi"
    brand_data = brands[brand_key]

    # Target: 12:00:00 ngày 26/09/2026
    target_dt = datetime.datetime(2026, 9, 26, 12, 0, 0)
    target_ts = int(target_dt.timestamp())
    log(f"📅 Mốc thời gian mục tiêu: {target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Epoch: {target_ts})")

    # ----------------------------------------------------
    # BỘ LINK SẢN PHẨM & BÌNH LUẬN THEO QUY CHUẨN
    # ----------------------------------------------------
    # 1. YouTube Comments (10 sản phẩm)
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/7VGeNvTjyg (Áo thun dài tay trơn xẻ tà)",
        "Link sản phẩm: https://s.shopee.vn/905SAgO1w5 (Áo khoác cardigan Peonyb mùa thu đông)",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/AUuFxRIJtU (Set 3 món cardigan + ba lỗ + chân váy ngắn)",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/BU3eRverb (Áo thun hai mảnh giả thời trang)",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1Lg12arDUw (Áo thun dài tay kẻ sọc vằn form rộng)",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/3B7fDxkEmP (Áo khoác cardigan basic dáng ngắn ôm body AK64)",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/4LJcc6fnPk (Áo thun cổ tim tay dài bozip PQ13)",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/4qFtD1dtOx (Áo thun tay dài khuy hoa nhí MaoMao)",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/6AlGnTXANb (Áo thun tăm thỏ tay dài phối cúc tôn dáng)",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/7KxEBcSj0w (Áo khoác cardigan dáng dài BYJANE 945)"
    ]

    # 2. Instagram Comments (10 sản phẩm)
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/70KNn0VdzV (Áo thun dài tay trơn xẻ tà)",
        "Link sản phẩm: https://s.shopee.vn/8V9BZlPvwu (Áo khoác cardigan Peonyb mùa thu đông)",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/8fSbm4PIc3 (Set 3 món cardigan + ba lỗ + chân váy ngắn)",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AAHPYpJaZS (Áo thun hai mảnh giả thời trang)",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1BMaqHrqpp (Áo thun dài tay kẻ sọc vằn form rộng)",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/2LYYEQnPTA (Áo khoác cardigan basic dáng ngắn ôm body AK64)",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2qUopLlVSN (Áo thun cổ tim tay dài bozip PQ13)",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/40gmDUh45i (Áo thun tay dài khuy hoa nhí MaoMao)",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/5q8QOra5NB (Áo thun tăm thỏ tay dài phối cúc tôn dáng)",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/7AdnzJTMLp (Áo khoác cardigan dáng dài BYJANE 945)"
    ]

    # ----------------------------------------------------
    # PHẦN 1: HẸN GIỜ TRỰC TIẾP LÊN YOUTUBE SHORTS (SERVER-SIDE API)
    # ----------------------------------------------------
    log("\n🔴 [1/2] Đang tải lên và thiết lập lịch công khai trên YouTube Shorts (Server-Side)...")
    yt_title = "Gợi Ý Phối Đồ Thu Đông Với Áo Khoác Cardigan & Áo Thun Cực Xinh #Shorts"
    yt_desc = (
        "Tổng hợp những set đồ thu đông tôn dáng cực đỉnh: Áo thun dài tay xẻ tà, set 3 món cardigan chân váy, áo giả 2 mảnh và cardigan len tăm thanh lịch chuẩn Hàn Quốc! "
        "Form rộng che khuyết điểm, chất vải mềm mịn mặc đi học đi làm đều cực xinh ✨\n\n"
        "🛒 Danh sách sản phẩm trong clip:\n"
        "👉 Áo thun dài tay trơn xẻ tà: https://s.shopee.vn/7VGeNvTjyg\n"
        "👉 Áo khoác cardigan Peonyb: https://s.shopee.vn/905SAgO1w5\n"
        "👉 Set 3 món cardigan + chân váy: https://s.shopee.vn/AUuFxRIJtU\n\n"
        "#QuầnÁoGiáHời #Cardigan #ÁoThunDàiTay #PhốiĐồĐẹp #OOTD #ThờiTrangNữ"
    )

    # 12:00 UTC+7 tương đương 05:00 UTC (Z)
    publish_at_rfc3339 = "2026-09-26T05:00:00Z"

    yt_cfg = brand_data.get("youtube", {})
    token_file = yt_cfg.get("token_file")
    token_full_path = os.path.join(BASE_DIR, token_file) if not os.path.isabs(token_file) else token_file

    yt_uploader = YouTubeShortsUploader(token_file=token_full_path)
    yt_res = yt_uploader.upload_short(
        video_path=video_path,
        title=yt_title,
        description=yt_desc,
        tags=["Shorts", "QuầnÁoGiáHời", "Cardigan", "ÁoThun", "OOTD", "ThoiTrangNu"],
        comment_text=yt_comments,
        privacy_status="private",
        publish_at=publish_at_rfc3339
    )

    if yt_res and yt_res.get("success"):
        log(f"🎉 YOUTUBE SHORTS ĐÃ ĐƯỢC HẸN GIỜ TRÊN MÁY CHỦ GOOGLE THÀNH CÔNG!")
        log(f"   🔗 Link Shorts: {yt_res.get('shorts_url')}")
        log(f"   ⏰ Thời gian công khai tự động: 12:00:00 ngày 26/09/2026 (Giờ Việt Nam)")
    else:
        log("⚠️ Lỗi upload YouTube Shorts hoặc chưa hoàn tất.")

    # ----------------------------------------------------
    # PHẦN 2: LẬP LỊCH INSTAGRAM REELS & STORY CHO MỐC 12:00:00
    # ----------------------------------------------------
    log("\n📸 [2/2] Đang thiết lập lịch xuất bản cho Instagram Reels & Story...")
    ig_caption = (
        "Thời tiết se lạnh diện những mẫu áo thun dài tay và cardigan len này là chuẩn bài luôn các nàng ơi! ✨ "
        "Form dáng rộng rãi giấu eo đỉnh chóp, chất liệu mềm mại thoáng khí, phối cùng chân váy hay jean suông đều ra vibe nàng thơ Hàn Quốc. "
        "Toàn bộ mẫu đẹp giá hời mình ghim chi tiết dưới bình luận nha 👇\n\n"
        "#reels #viral #fyp #quanaogiahoi #cardigan #outfitoftheday #thoitrangnu #phoidoxinh #shopeehaul"
    )

    # Đưa vào file schedule_queue.json
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
        else:
            queue = []
    except Exception:
        queue = []

    task_id = f"task_ig_qagh_ep3_12h_{int(time.time())}"
    task = {
        "id": task_id,
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": "Set Đồ Thu Đông & Cardigan Len Tôn Dáng Chuẩn Hàn Quốc",
        "caption": ig_caption,
        "comment": "\n".join(ig_comments),
        "platforms": ["instagram", "instagram_story"],
        "scheduled_time_str": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": target_ts,
        "product_keyword": "Thời trang thu đông, áo thun & cardigan Tập 3",
        "status": "PENDING"
    }

    # Tránh trùng lặp task
    queue = [t for t in queue if not (t.get("brand_key") == brand_key and t.get("product_keyword") == task["product_keyword"] and t.get("status") == "PENDING")]
    queue.append(task)

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)

    log(f"✅ Đã ghi nhận lịch hẹn Instagram Reels & Story vào hệ thống Queue: {target_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # Đăng ký chạy background runner theo dõi chính xác đến 12:00:00 ngày 26/09/2026
    log("=" * 80)
    log("🎉 ĐÃ HOÀN TẤT THIẾT LẬP LỊCH ĐĂNG GIAI ĐOẠN 1 CHO 'QUẦN ÁO GIÁ HỜI'!")
    log("=" * 80)

if __name__ == "__main__":
    main()
