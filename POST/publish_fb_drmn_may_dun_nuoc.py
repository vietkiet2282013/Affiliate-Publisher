# -*- coding: utf-8 -*-
"""
Đăng video 'máy đun nước tức thời 3 giây' lên Facebook Reels cho kênh Dùng Rồi Mới Nói
- Kèm 1 link ở caption
- Bình luận lần lượt từng link affiliate riêng biệt theo đúng file 'máy đun nước tức thời 3 giây.xlsx'
"""

import os
import sys
import json
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import FacebookReelsUploader

def parse_copy_nhanh(file_path):
    items = []
    if not os.path.exists(file_path):
        return items
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]
    for line in lines:
        if line.startswith("http://") or line.startswith("https://"):
            items.append(line)
    return items

def main():
    print("=" * 70)
    print("🚀 ĐĂNG FACEBOOK REELS & BÌNH LUẬN - DÙNG RỒI MỚI NÓI (MÁY ĐUN NƯỚC 3S)")
    print("=" * 70)

    video_path = r"C:\Affiliate\Dùng Rồi Mới Nói\Video_việt_hóa\bình đun nước mang đi du lịch.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    brands_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_data = brands["dung_roi_moi_noi"]
    fb_token = brand_data["facebook"]["access_token"]
    fb_id = brand_data["facebook"]["page_id"]

    links_file = r"C:\Affiliate\Dùng Rồi Mới Nói\Link customed\Facebook\máy đun nước tức thời 3 giây_copy_nhanh.txt"
    links = parse_copy_nhanh(links_file)
    print(f"📊 Đã tải {len(links)} link từ Facebook copy nhanh")

    main_link = "https://s.shopee.vn/3LR26tEnAP"
    fb_title = "Máy Đun Nước Nóng Tức Thời 3 Giây Cực Tiện Mang Đi Du Lịch"
    fb_caption = (
        f"Đi du lịch, công tác hay để bàn làm việc mà có em máy đun nước tức thì 3 giây này thì chuẩn bài luôn cả nhà ơi! "
        f"Bấm nút 3 giây là có nước sôi pha sữa, trà, cà phê chuẩn nhiệt độ 🔥\n\n"
        f"👉 Sắm ngay máy đun nước mini chính hãng tại: {main_link}\n\n"
        f"Chi tiết từng mẫu máy đun nước mình ghim link bên dưới bình luận nhé 👇\n\n"
        f"#DungRoiMoiNoi #MayDunNuoc3s #BinhDunNuocDuLich #GiaDungThongMinh #ReviewThat #TienIchGiaDinh"
    )

    fb_uploader = FacebookReelsUploader(page_id=fb_id, access_token=fb_token)
    res = fb_uploader.upload_reel(
        video_path=video_path,
        title=fb_title,
        caption=fb_caption,
        comment_text="\n".join(links)
    )

    if res:
        print("\n" + "=" * 70)
        print(f"🎉 ĐÃ ĐĂNG FACEBOOK REELS THÀNH CÔNG: {res.get('reel_url')}")
        print("=" * 70)
    else:
        print("❌ Lỗi đăng Facebook Reels")

if __name__ == "__main__":
    main()
