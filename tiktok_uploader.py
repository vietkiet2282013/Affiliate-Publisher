import os
import sys
import json
import argparse
import requests

# TikTok Content Posting API v2
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

def upload_tiktok_video(video_path, title, access_token):
    """
    Đăng video lên TikTok bằng TikTok Content Posting API v2
    
    Yêu cầu:
    - access_token với scope: video.upload (hoặc video.publish)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    file_size = os.path.getsize(video_path)

    # 1. Khởi tạo phiên Upload (Initiate Video Upload)
    init_url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }

    body = {
        "post_info": {
            "title": title,
            "privacy_level": "PUBLIC_TO_EVERYONE",  # PUBLIC_TO_EVERYONE, SELF_ONLY, MUTUAL_FOLLOW_FRIENDS
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1
        }
    }

    print("Đang gửi yêu cầu khởi tạo upload tới TikTok API...")
    init_res = requests.post(init_url, headers=headers, json=body)
    init_data = init_res.json()

    if init_res.status_code != 200 or init_data.get("error", {}).get("code") != "ok":
        raise Exception(f"Lỗi khi khởi tạo TikTok upload: {init_data}")

    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    print(f"Khởi tạo thành công! Publish ID: {publish_id}")

    # 2. Upload dữ liệu file video (Binary Upload)
    print("Đang tải dữ liệu video lên TikTok server...")
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Length": str(file_size),
        "Content-Range": f"bytes 0-{file_size-1}/{file_size}"
    }

    upload_res = requests.put(upload_url, headers=upload_headers, data=video_bytes)
    if upload_res.status_code not in (200, 201):
        raise Exception(f"Lỗi khi tải video data lên TikTok: Status {upload_res.status_code}, {upload_res.text}")

    print("Tải video lên TikTok thành công!")

    # 3. Kiểm tra trạng thái xử lý
    status_url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
    status_body = {"publish_id": publish_id}
    status_res = requests.post(status_url, headers=headers, json=status_body)
    print("Trạng thái TikTok Publish:", status_res.json())
    return publish_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chương trình Python tải video lên TikTok")
    parser.add_argument("--video", required=True, help="Đường dẫn file video")
    parser.add_argument("--title", required=True, help="Tiêu đề / Caption video")
    parser.add_argument("--token", required=True, help="TikTok User Access Token")

    args = parser.parse_args()

    try:
        upload_tiktok_video(args.video, args.title, args.token)
    except Exception as e:
        print(f"\nLỗi khi đăng video lên TikTok: {e}")
