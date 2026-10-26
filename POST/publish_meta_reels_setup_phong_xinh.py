# -*- coding: utf-8 -*-
"""
Đăng bổ sung Facebook Reels và Instagram Reels cho Tập 1 - Setup Phòng Xinh
- Facebook caption kèm 1 link chính hãng: https://s.shopee.vn/50ZJQNuvif
- Bình luận tách riêng biệt từng link cho cả Facebook và Instagram
"""

import os
import sys
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import FacebookReelsUploader, InstagramReelsUploader

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
    print("🚀 ĐĂNG BỔ SUNG FACEBOOK REELS & INSTAGRAM REELS - SETUP PHÒNG XINH")
    print("=" * 70)

    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\1.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "setup_phong_xinh"
    brand_data = brands[brand_key]

    links_base = r"C:\Affiliate\Setup Phòng Xinh\Link customed"
    fb_links = parse_copy_nhanh(os.path.join(links_base, "Facebook", "Tập 1_copy_nhanh.txt"))
    ig_links = parse_copy_nhanh(os.path.join(links_base, "Instagram", "Tập 1_copy_nhanh.txt"))

    print(f"📊 Đã tải links: FB={len(fb_links)}, IG={len(ig_links)}")

    results = {}

    # 1. FACEBOOK REELS
    print("\n🔵 [1/2] ĐĂNG LÊN FACEBOOK REELS...")
    main_fb_link = "https://s.shopee.vn/50ZJQNuvif"
    fb_title = "Dây Chốt Khóa Đa Năng Cực Tiện Cho Phòng Xinh"
    fb_caption = (
        f"Góc phòng xinh gọn gàng, an toàn tuyệt đối với chốt khóa tủ lạnh & ngăn kéo đa năng! "
        f"Ai cần mua chốt khóa chính hãng bấm ngay link này nhé 👉 {main_fb_link}\n\n"
        f"Trọn bộ phụ kiện và đồ chơi cho mèo cưng mình ghim từng link bên dưới bình luận nha 👇\n\n"
        f"#SetupPhongXinh #DecorPhong #GiaDungThongMinh #ThuCung #MeoYeu"
    )
    fb_comment_payload = "\n".join(fb_links) if fb_links else ""

    try:
        fb_cfg = brand_data["facebook"]
        fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        fb_res = fb_uploader.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comment_payload
        )
        if fb_res:
            results["facebook"] = fb_res.get("reel_url")
            print(f"✅ Facebook Reels thành công: {results['facebook']}")
        else:
            results["facebook"] = "Thất bại khi upload Facebook"
    except Exception as e:
        results["facebook"] = f"Lỗi: {e}"
        print(f"❌ Facebook error: {e}")

    # 2. INSTAGRAM REELS
    print("\n🟣 [2/2] ĐĂNG LÊN INSTAGRAM REELS...")
    ig_caption = (
        "Góc setup phòng xinh và giải pháp an toàn tuyệt đối cho bé yêu và thú cưng! "
        "Chi tiết các món phụ kiện xinh xắn mình ghim dưới comment nhé 👇✨\n\n"
        "#setupphongxinh #decor #roomdecor #homedecor #cats #thucung #viral"
    )
    ig_comment_payload = "\n".join(ig_links) if ig_links else ""

    try:
        ig_cfg = brand_data["instagram"]
        ig_uploader = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        ig_res = ig_uploader.upload_reel(
            video_path=video_path,
            caption=ig_caption,
            comment_text=ig_comment_payload
        )
        if ig_res:
            results["instagram"] = ig_res.get("reel_url")
            print(f"✅ Instagram Reels thành công: {results['instagram']}")
        else:
            results["instagram"] = "Thất bại khi upload Instagram"
    except Exception as e:
        results["instagram"] = f"Lỗi: {e}"
        print(f"❌ Instagram error: {e}")

    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ:")
    for k, v in results.items():
        print(f"- {k.upper()}: {v}")
    print("=" * 70)

if __name__ == "__main__":
    main()
