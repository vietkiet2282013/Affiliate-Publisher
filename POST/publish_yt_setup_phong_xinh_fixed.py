# -*- coding: utf-8 -*-
"""
Đăng video 1-sửa lại.mp4 lên kênh YouTube Setup Phòng Xinh
- Tiêu đề & mô tả chuẩn SEO Shorts
- Tự động đăng và ghim 12 comment riêng biệt tương ứng từng sản phẩm trong Tập 1
"""

import os
import sys
import json
import csv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import YouTubeShortsUploader

def parse_youtube_links(csv_path):
    links = []
    if not os.path.exists(csv_path):
        return links
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 3 and row[2].startswith("http"):
                name = row[1].strip()
                url = row[2].strip()
                links.append(f"{url} ({name})")
    return links

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU ĐĂNG YOUTUBE SHORTS (1-sửa lại.mp4) - SETUP PHÒNG XINH")
    print("=" * 70)

    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\1-sửa lại.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    csv_path = r"C:\Affiliate\Setup Phòng Xinh\Link customed\YouTube\Tập 1.csv"
    yt_links = parse_youtube_links(csv_path)
    print(f"📊 Đã tải {len(yt_links)} link sản phẩm từ Tập 1.csv")

    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_data = brands["setup_phong_xinh"]
    token_file = brand_data["youtube"]["token_file"]

    yt_title = "Dây chốt khóa an toàn & góc setup siêu cưng cho boss 😻 #Shorts"
    yt_desc = (
        "Bảo vệ bé yêu và các boss với dây chốt khóa an toàn tủ lạnh, ngăn kéo thông minh! "
        "Chi tiết link các món đồ decor và phụ kiện phòng ngủ/thú cưng mình ghim ngay dưới phần bình luận nhé 👇\n\n"
        "#setupphongxinh #decorphong #thucung #meocon #dogiadung #shorts"
    )
    yt_comment_payload = "\n".join(yt_links) if yt_links else ""

    uploader = YouTubeShortsUploader(token_file=token_file)
    res = uploader.upload_short(
        video_path=video_path,
        title=yt_title,
        description=yt_desc,
        comment_text=yt_comment_payload,
        privacy_status="public"
    )

    if res:
        url = res.get("shorts_url")
        print("\n" + "=" * 70)
        print(f"🎉 ĐÃ ĐĂNG YOUTUBE SHORTS THÀNH CÔNG: {url}")
        print("=" * 70)
    else:
        print("❌ Lỗi khi upload video lên YouTube")

if __name__ == "__main__":
    main()
