# -*- coding: utf-8 -*-
"""
Sửa lại toàn bộ bình luận trên Facebook Reels cho video mới nhất của kênh Yêu Da Hơn Bồ (Reel ID: 2090937031521353)
theo đúng danh sách trong file 'Tập 2.xlsx' / 'Tập 2_copy_nhanh.txt'
"""

import os
import sys
import json
import time
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    print("🔧 SỬA BÌNH LUẬN FACEBOOK REELS - YÊU DA HƠN BỒ (TẬP 2)")
    print("=" * 70)

    brands_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    b = brands["yeu_da_hon_bo"]
    fb_token = b["facebook"]["access_token"]
    vid = "2090937031521353"
    print(f"Video Reel ID: {vid} (Bí kíp cho làn da căng mọng bóng mượt và gương mặt thon gọn...)")

    links_file = r"C:\Affiliate\Yêu Da Hơn Bồ\Link customed\Facebook\Tập 2_copy_nhanh.txt"
    links = parse_copy_nhanh(links_file)
    print(f"📊 Đã tải {len(links)} link chuẩn từ 'Tập 2_copy_nhanh.txt'")

    # 1. Lấy và xóa toàn bộ các bình luận cũ bị sai link
    print("\n⏳ [1/2] Đang xóa các bình luận cũ bị sai link trên Facebook Reels...")
    cm_res = requests.get(f"https://graph.facebook.com/v19.0/{vid}/comments?limit=100&access_token={fb_token}").json()
    old_comments = cm_res.get("data", [])
    print(f"  -> Tìm thấy {len(old_comments)} comment cũ.")
    for oc in old_comments:
        cid = oc.get("id")
        try:
            del_r = requests.delete(f"https://graph.facebook.com/v19.0/{cid}?access_token={fb_token}").json()
            print(f"     Đã xóa comment: {cid}")
            time.sleep(0.5)
        except Exception as e:
            pass

    # 2. Đăng lại từng comment riêng biệt với đúng link Tập 2
    print(f"\n🚀 [2/2] Đang đăng {len(links)} bình luận mới chuẩn theo 'Tập 2.xlsx'...")
    for idx, link_item in enumerate(links, 1):
        try:
            add_r = requests.post(
                f"https://graph.facebook.com/v19.0/{vid}/comments",
                data={"message": link_item, "access_token": fb_token}
            ).json()
            print(f"  ✅ [Bình luận {idx}/{len(links)}] Đã thêm: {add_r.get('id')}")
            time.sleep(1.5)
        except Exception as err:
            print(f"  ⚠️ Lỗi khi thêm bình luận {idx}: {err}")

    print("\n" + "=" * 70)
    print("🎉 HOÀN TẤT SỬA BÌNH LUẬN TRÊN FACEBOOK REELS YÊU DA HƠN BỒ!")
    print(f"🔗 Xem video tại: https://www.facebook.com/reel/{vid}")
    print("=" * 70)

if __name__ == "__main__":
    main()
