# -*- coding: utf-8 -*-
"""
Sửa lại toàn bộ bình luận cho video mới nhất trên YouTube kênh Trạm Công Nghệ (rD6qjh7JMSk)
theo đúng danh sách trong file 'cam máy tính tracking.xlsx'
"""

import os
import sys
import json
import time

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
    print("🔧 SỬA BÌNH LUẬN YOUTUBE SHORTS - TRẠM CÔNG NGHỆ (CAM MÁY TÍNH TRACKING)")
    print("=" * 70)

    brands_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    b = brands["cham_cong_nghe"]
    token_file = os.path.join(BASE_DIR, b["youtube"]["token_file"])

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(token_file)
    youtube = build("youtube", "v3", credentials=creds)

    vid = "rD6qjh7JMSk"
    print(f"Video ID: {vid} (Webcam AI tự động xoay tracking...)")

    links_file = r"C:\Affiliate\Trạm Công Nghệ\Link customed\YouTube\cam máy tính tracking_copy_nhanh.txt"
    links = parse_copy_nhanh(links_file)
    print(f"📊 Đã tải {len(links)} link chuẩn từ 'cam máy tính tracking_copy_nhanh.txt'")

    # 1. Xóa các bình luận cũ bị sai link
    print("\n⏳ [1/2] Đang xóa các bình luận cũ bị sai...")
    threads_req = youtube.commentThreads().list(
        part="id,snippet",
        videoId=vid,
        maxResults=100
    ).execute()
    old_items = threads_req.get("items", [])
    print(f"  -> Tìm thấy {len(old_items)} comment cũ trên YouTube.")
    for it in old_items:
        cid = it["id"]
        try:
            youtube.comments().delete(id=cid).execute()
            print(f"     Đã xóa comment {cid}")
            time.sleep(0.5)
        except Exception as e:
            pass

    # 2. Đăng lại từng bình luận riêng biệt chuẩn xác
    print(f"\n🚀 [2/2] Đang đăng {len(links)} bình luận mới chuẩn theo 'cam máy tính tracking.xlsx'...")
    for idx, link_item in enumerate(links, 1):
        try:
            c_res = youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": vid,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": link_item
                            }
                        }
                    }
                }
            ).execute()
            print(f"  ✅ [Bình luận {idx}/{len(links)}] Đã đăng: {c_res.get('id')}")
            time.sleep(1.5)
        except Exception as err:
            print(f"  ⚠️ Lỗi khi đăng bình luận {idx}: {err}")

    print("\n" + "=" * 70)
    print("🎉 HOÀN TẤT SỬA BÌNH LUẬN TRÊN YOUTUBE TRẠM CÔNG NGHỆ!")
    print(f"🔗 Xem video tại: https://youtube.com/shorts/{vid}")
    print("=" * 70)

if __name__ == "__main__":
    main()
