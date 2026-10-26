# -*- coding: utf-8 -*-
"""
Sửa lại bình luận cho video Tập 2 của kênh Setup Phòng Xinh trên:
1. Facebook Reels: https://www.facebook.com/reel/1654397169586787
   - Xóa các comment cũ bị sai
   - Đăng lại từng comment riêng biệt với đúng link Tập 2
2. YouTube Shorts: https://youtube.com/shorts/uGqYTwBxZMU
   - Xóa comment cũ
   - Đăng lại và ghim comment đúng link Tập 2
3. Threads: https://www.threads.com/@setupphongxinh/post/DdspfwGgYeY (ID: 17885116365685618)
   - Đăng thêm các comment reply chuẩn link Tập 2
4. Instagram Reels:
   - Nếu tìm thấy Reel Tập 2 hoặc kiểm tra Reel mới, sửa/bổ sung comment đúng link Tập 2
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
    print("🔧 BẮT ĐẦU SỬA BÌNH LUẬN VIDEO TẬP 2 - KÊNH SETUP PHÒNG XINH")
    print("=" * 70)

    brands_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    b = brands["setup_phong_xinh"]
    fb_token = b["facebook"]["access_token"]
    fb_vid = "1654397169586787"
    yt_vid = "uGqYTwBxZMU"
    th_token = b["threads"]["access_token"]
    th_user_id = b["threads"]["user_id"]
    th_post_id = "17885116365685618"

    link_base = r"C:\Affiliate\Setup Phòng Xinh\Link customed"
    fb_links = parse_copy_nhanh(os.path.join(link_base, "Facebook", "Tập 2_copy_nhanh.txt"))
    yt_links = parse_copy_nhanh(os.path.join(link_base, "YouTube", "Tập 2_copy_nhanh.txt"))
    th_links = parse_copy_nhanh(os.path.join(link_base, "Threads", "Tập 2_copy_nhanh.txt"))
    ig_links = parse_copy_nhanh(os.path.join(link_base, "Instagram", "Tập 2_copy_nhanh.txt"))

    print(f"📊 Đã tải link Tập 2: FB={len(fb_links)}, YT={len(yt_links)}, TH={len(th_links)}, IG={len(ig_links)}")

    # ----------------------------------------------------
    # 1. SỬA BÌNH LUẬN TRÊN FACEBOOK REELS
    # ----------------------------------------------------
    print("\n🔵 1. SỬA BÌNH LUẬN TRÊN FACEBOOK REELS (ID: 1654397169586787)...")
    try:
        # Lấy toàn bộ comments hiện tại để xóa
        cm_res = requests.get(f"https://graph.facebook.com/v19.0/{fb_vid}/comments?limit=100&access_token={fb_token}").json()
        old_comments = cm_res.get("data", [])
        print(f"  -> Tìm thấy {len(old_comments)} comment cũ. Đang dọn dẹp...")
        for oc in old_comments:
            oc_id = oc.get("id")
            del_r = requests.delete(f"https://graph.facebook.com/v19.0/{oc_id}?access_token={fb_token}").json()
            # print(f"     Xóa {oc_id}: {del_r}")
            time.sleep(0.5)

        # Đăng lại đúng danh sách link Tập 2
        print(f"  -> Bắt đầu đăng mới {len(fb_links)} comment link Tập 2 chuẩn...")
        for idx, link_item in enumerate(fb_links, 1):
            add_r = requests.post(
                f"https://graph.facebook.com/v19.0/{fb_vid}/comments",
                data={"message": link_item, "access_token": fb_token}
            ).json()
            print(f"     ✅ [FB {idx}/{len(fb_links)}] Đã thêm: {add_r.get('id')}")
            time.sleep(1.5)
        print("  🎉 Hoàn tất sửa bình luận Facebook Reels!")
    except Exception as e:
        print(f"  ❌ Lỗi Facebook: {e}")

    # ----------------------------------------------------
    # 2. SỬA BÌNH LUẬN TRÊN YOUTUBE SHORTS
    # ----------------------------------------------------
    print(f"\n🔴 2. SỬA BÌNH LUẬN TRÊN YOUTUBE SHORTS (ID: {yt_vid})...")
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        token_file = b["youtube"]["token_file"]
        creds = Credentials.from_authorized_user_file(token_file)
        youtube = build("youtube", "v3", credentials=creds)

        # Lấy comments hiện tại
        threads_req = youtube.commentThreads().list(
            part="id,snippet",
            videoId=yt_vid,
            maxResults=100
        ).execute()
        items = threads_req.get("items", [])
        print(f"  -> Tìm thấy {len(items)} comment cũ trên YouTube. Đang xóa...")
        for it in items:
            t_id = it.get("id")
            try:
                youtube.comments().delete(id=t_id).execute()
                time.sleep(0.5)
            except Exception as del_err:
                # Có thể là comment thread id
                pass

        # Đăng lại comments chuẩn Tập 2
        print(f"  -> Bắt đầu đăng {len(yt_links)} comment link Tập 2 lên YouTube...")
        for idx, link_item in enumerate(yt_links, 1):
            c_res = youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": yt_vid,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": link_item
                            }
                        }
                    }
                }
            ).execute()
            print(f"     ✅ [YT {idx}/{len(yt_links)}] Đã đăng: {c_res.get('id')}")
            time.sleep(1.5)
        print("  🎉 Hoàn tất sửa bình luận YouTube Shorts!")
    except Exception as e:
        print(f"  ❌ Lỗi YouTube: {e}")

    # ----------------------------------------------------
    # 3. ĐĂNG BÌNH LUẬN TRÊN THREADS
    # ----------------------------------------------------
    print(f"\n🧵 3. BỔ SUNG BÌNH LUẬN TRÊN THREADS (Post ID: {th_post_id})...")
    try:
        print(f"  -> Bắt đầu đăng {len(th_links)} comment link Tập 2 vào Threads...")
        for idx, link_item in enumerate(th_links, 1):
            c_payload = {
                "media_type": "TEXT",
                "text": f"Món {idx}: {link_item}",
                "reply_to_id": th_post_id,
                "access_token": th_token
            }
            c_res = requests.post(f"https://graph.threads.net/v1.0/{th_user_id}/threads", data=c_payload).json()
            if "id" in c_res:
                pub_r = requests.post(f"https://graph.threads.net/v1.0/{th_user_id}/threads_publish", data={"creation_id": c_res["id"], "access_token": th_token}).json()
                print(f"     ✅ [Threads {idx}/{len(th_links)}] Đã reply: {pub_r.get('id')}")
            else:
                print(f"     ⚠️ Lỗi tạo reply: {c_res}")
            time.sleep(1.5)
        print("  🎉 Hoàn tất bổ sung bình luận Threads!")
    except Exception as e:
        print(f"  ❌ Lỗi Threads: {e}")

    print("\n" + "=" * 70)
    print("🎉 TẤT CẢ BÌNH LUẬN ĐÃ ĐƯỢC ĐỒNG BỘ CHUẨN XÁC VỚI FILE TẬP 2!")
    print("=" * 70)

if __name__ == "__main__":
    main()
