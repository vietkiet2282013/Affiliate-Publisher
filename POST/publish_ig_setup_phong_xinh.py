# -*- coding: utf-8 -*-
import os
import sys
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import InstagramReelsUploader

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
    print("🚀 ĐĂNG INSTAGRAM REELS - SETUP PHÒNG XINH (1_threads.mp4)")
    print("=" * 70)

    # Sử dụng bản video 153MB chuẩn
    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\1_threads.mp4"
    if not os.path.exists(video_path):
        video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\1.mp4"

    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "setup_phong_xinh"
    brand_data = brands[brand_key]

    links_base = r"C:\Affiliate\Setup Phòng Xinh\Link customed"
    ig_links = parse_copy_nhanh(os.path.join(links_base, "Instagram", "Tập 1_copy_nhanh.txt"))

    ig_caption = (
        "Góc setup phòng xinh và giải pháp an toàn tuyệt đối cho bé yêu và thú cưng! "
        "Chi tiết các món phụ kiện xinh xắn mình ghim dưới comment nhé 👇✨\n\n"
        "#setupphongxinh #decor #roomdecor #homedecor #cats #thucung #viral"
    )
    ig_comment_payload = "\n".join(ig_links) if ig_links else ""

    ig_cfg = brand_data["instagram"]
    ig_uploader = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
    ig_res = ig_uploader.upload_reel(
        video_path=video_path,
        caption=ig_caption,
        comment_text=ig_comment_payload
    )
    print("Kết quả:", ig_res)

if __name__ == "__main__":
    main()
