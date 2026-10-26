# -*- coding: utf-8 -*-
"""
Sửa lại bình luận trên YouTube Shorts cho video mới nhất của Review Thật Việc Thật (eVHooLOdsts)
theo đúng danh sách trong file 'đệm lưng.xlsx' / 'đệm lưng_copy_nhanh.txt'
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
    print("🔧 SỬA BÌNH LUẬN YOUTUBE SHORTS - REVIEW THẬT VIỆC THẬT (ĐỆM LƯNG)")
    print("=" * 70)

    brands_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    b = brands["review_that_viec_that"]
    token_file = os.path.join(BASE_DIR, b["youtube"]["token_file"])

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(token_file)
    youtube = build("youtube", "v3", credentials=creds)

    vid = "eVHooLOdsts"
    print(f"Video ID: {vid} (Cứu tinh cho người đau lưng thoái hóa: Đệm kê thắt lưng...)")

    links_file = r"C:\Affiliate\Review Thật Việc Thật\Link customed\YouTube\đệm lưng_copy_nhanh.txt"
    links = parse_copy_nhanh(links_file)
    print(f"📊 Đã tải {len(links)} link chuẩn từ đệm lưng_copy_nhanh.txt")

    # 1. Lấy và xóa các bình luận cũ bị sai
    print("\n⏳ [1/2] Đang xóa bình luận cũ bị sai...")
    threads_req = youtube.commentThreads().list(
        part="id,snippet",
        videoId=vid,
        maxResults=100
    ).execute()
    old_items = threads_req.get("items", [])
    print(f"  -> Tìm thấy {len(old_items)} comment cũ.")
    for it in old_items:
        cid = it["id"]
        try:
            youtube.comments().delete(id=cid).execute()
            print(f"     Đã xóa comment {cid}")
            time.sleep(0.5)
        except Exception as e:
            # Nếu delete bằng comment id không được thì bỏ qua
            pass

    # 2. Đăng lại từng comment riêng biệt với đúng link đệm lưng
    print(f"\n🚀 [2/2] Đang đăng {len(links)} bình luận mới chuẩn theo 'đệm lưng.xlsx'...")
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
    print("🎉 HOÀN TẤT SỬA BÌNH LUẬN TRÊN YOUTUBE REVIEW THẬT VIỆC THẬT!")
    print(f"🔗 Xem video tại: https://youtube.com/shorts/{vid}")
    print("=" * 70)

if __name__ == "__main__":
    main()
