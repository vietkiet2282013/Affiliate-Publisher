# -*- coding: utf-8 -*-
"""
Đăng Instagram Reels cho kênh Chăm Da Tiết Kiệm với video 1080p đã render chuẩn:
C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\4_1080p.mp4
Kèm tự động bình luận link Affiliate Shopee.
"""

import os
import sys
import json
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import InstagramReelsUploader

def main():
    print("=" * 70)
    print("🚀 ĐĂNG INSTAGRAM REELS - CHĂM DA TIẾT KIỆM (TẬP 4)")
    print("=" * 70)

    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brand = json.load(f)["cham_da_tiet_kiem"]

    ig_id = brand["instagram"]["ig_user_id"]
    token = brand["instagram"]["access_token"]

    video_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\4_1080p.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    ig_caption = (
        "Cứu cánh cho làn da khô ráp, lão hóa và thiếu sức sống! Dầu dưỡng tái tạo da La Mer The Renewal Oil cấp ẩm tầng sâu, khóa ẩm vượt trội cho lớp nền mướt mịn tự nhiên ✨ "
        "Đúng là đắt xắt ra miếng nhưng cực kỳ đáng đầu tư! Link sắm chính hãng mình ghim ngay bên dưới comment nha 👇\n\n"
        "#reels #viral #fyp #chamdatietkiem #lamervietnam #therenewaloil #facialoil #cangbongda #beautyhacks"
    )

    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20viz629n5"
    ]

    uploader = InstagramReelsUploader(ig_user_id=ig_id, access_token=token)
    res = uploader.upload_reel(
        video_path=video_path,
        caption=ig_caption,
        comment_text=ig_comments
    )

    print("\n" + "=" * 70)
    print(f"🎉 KẾT QUẢ ĐĂNG INSTAGRAM: {res}")
    print("=" * 70)

if __name__ == "__main__":
    main()
