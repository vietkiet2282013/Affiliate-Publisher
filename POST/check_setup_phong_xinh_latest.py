# -*- coding: utf-8 -*-
import sys
import json
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

brands_path = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_path, "r", encoding="utf-8") as f:
    brands = json.load(f)

b = brands["setup_phong_xinh"]
fb_token = b["facebook"]["access_token"]
fb_id = b["facebook"]["page_id"]
ig_token = b["instagram"]["access_token"]
ig_id = b["instagram"]["ig_user_id"]
th_token = b["threads"]["access_token"]
th_id = b["threads"]["user_id"]

print("=" * 70)
print("🔍 KIỂM TRA VIDEO MỚI NHẤT TRÊN KÊNH: SETUP PHÒNG XINH")
print("=" * 70)

# 1. FACEBOOK REELS
print("\n🔵 1. FACEBOOK REELS:")
try:
    r_fb = requests.get(f"https://graph.facebook.com/v19.0/{fb_id}/video_reels?fields=id,description,created_time,permalink_url&limit=3&access_token={fb_token}").json()
    data = r_fb.get("data", [])
    if data:
        for idx, item in enumerate(data, 1):
            vid = item.get('id')
            desc = item.get('description', '')[:60].replace('\n', ' ')
            ctime = item.get('created_time')
            print(f"  [{idx}] ID: {vid} | Ngày tạo: {ctime}")
            print(f"      Caption: {desc}...")
            print(f"      Link: https://www.facebook.com/reel/{vid}")
            # Check comment count
            cm_r = requests.get(f"https://graph.facebook.com/v19.0/{vid}/comments?access_token={fb_token}").json()
            cm_count = len(cm_r.get("data", []))
            print(f"      Số bình luận: {cm_count}")
    else:
        print("  Không tìm thấy Reels hoặc data rỗng:", r_fb)
except Exception as e:
    print("  Lỗi kiểm tra FB:", e)

# 2. INSTAGRAM REELS
print("\n🟣 2. INSTAGRAM REELS:")
try:
    r_ig = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}/media?fields=id,caption,media_type,permalink,timestamp,comments_count&limit=3&access_token={ig_token}").json()
    data = r_ig.get("data", [])
    if data:
        for idx, item in enumerate(data, 1):
            cap = str(item.get('caption', ''))[:60].replace('\n', ' ')
            print(f"  [{idx}] ID: {item.get('id')} | Loại: {item.get('media_type')} | Ngày tạo: {item.get('timestamp')}")
            print(f"      Caption: {cap}...")
            print(f"      Link: {item.get('permalink')}")
            print(f"      Số bình luận: {item.get('comments_count')}")
    else:
        print("  Không tìm thấy media IG:", r_ig)
except Exception as e:
    print("  Lỗi kiểm tra IG:", e)

# 3. THREADS
print("\n🧵 3. THREADS:")
try:
    r_th = requests.get(f"https://graph.threads.net/v1.0/{th_id}/threads?fields=id,text,media_type,permalink,timestamp&limit=3&access_token={th_token}").json()
    data = r_th.get("data", [])
    if data:
        for idx, item in enumerate(data, 1):
            txt = str(item.get('text', ''))[:60].replace('\n', ' ')
            print(f"  [{idx}] ID: {item.get('id')} | Loại: {item.get('media_type')} | Ngày tạo: {item.get('timestamp')}")
            print(f"      Nội dung: {txt}...")
            print(f"      Link: {item.get('permalink')}")
    else:
        print("  Không tìm thấy post Threads:", r_th)
except Exception as e:
    print("  Lỗi kiểm tra Threads:", e)

# 4. YOUTUBE SHORTS
print("\n🔴 4. YOUTUBE SHORTS:")
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    token_file = b["youtube"]["token_file"]
    creds = Credentials.from_authorized_user_file(token_file)
    youtube = build("youtube", "v3", credentials=creds)
    # Lấy video gần nhất
    pl_req = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_id = pl_req["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    v_req = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=3).execute()
    items = v_req.get("items", [])
    for idx, item in enumerate(items, 1):
        vid = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        pub_at = item["snippet"]["publishedAt"]
        print(f"  [{idx}] ID: {vid} | Ngày tạo: {pub_at}")
        print(f"      Tiêu đề: {title}")
        print(f"      Link: https://youtube.com/shorts/{vid}")
except Exception as e:
    print("  Lỗi kiểm tra YouTube:", e)

print("\n" + "=" * 70)
