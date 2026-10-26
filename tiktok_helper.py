import os
import sys
import json
import argparse
import urllib.parse
import requests

CLIENT_KEY = "awdp8l94wzlttjmb"
CLIENT_SECRET = "sgt5dWTBOWhCQ5UbI0uvBHgdbV9xc4fu"
REDIRECT_URI = "https://localhost:8080/"
TOKEN_FILE = "tiktok_token.json"

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

def get_auth_url(client_key=CLIENT_KEY, redirect_uri=REDIRECT_URI):
    """Tạo URL xác thực cấp quyền TikTok"""
    params = {
        "client_key": client_key,
        "scope": "user.info.basic,video.upload,video.publish",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": "tiktok_auth"
    }
    return f"{TIKTOK_AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code, client_key=CLIENT_KEY, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI):
    """Đổi Code lấy Access Token từ TikTok API"""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    print("Đang gửi yêu cầu lấy Access Token từ TikTok...")
    res = requests.post(TIKTOK_TOKEN_URL, headers=headers, data=data)
    res_data = res.json()
    
    if "access_token" in res_data:
        token_info = res_data
    elif "data" in res_data and "access_token" in res_data["data"]:
        token_info = res_data["data"]
    else:
        raise Exception(f"Lỗi đổi token từ TikTok: {res_data}")

    with open(TOKEN_FILE, "w") as f:
        json.dump(token_info, f, indent=2)
    
    print(f"Đã lưu TikTok Access Token vào '{TOKEN_FILE}'!")
    return token_info["access_token"]

def get_valid_token():
    """Lấy token hợp lệ từ file tiktok_token.json"""
    if not os.path.exists(TOKEN_FILE):
        return None
    
    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)
    
    return token_data.get("access_token")

def upload_tiktok_video(video_path, title, access_token):
    """Đăng video lên TikTok bằng TikTok Content Posting API v2"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    file_size = os.path.getsize(video_path)

    # 1. Initiate Video Upload
    init_url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }

    body = {
        "post_info": {
            "title": title,
            "privacy_level": "PUBLIC_TO_EVERYONE",
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

    print("Đang khởi tạo phiên upload với TikTok API...")
    init_res = requests.post(init_url, headers=headers, json=body)
    init_data = init_res.json()

    if init_res.status_code != 200 or init_data.get("error", {}).get("code") != "ok":
        raise Exception(f"Lỗi khi khởi tạo TikTok upload: {init_data}")

    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    print(f"Khởi tạo thành công! Publish ID: {publish_id}")

    # 2. Upload Binary Data
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

    print("Upload file video lên TikTok thành công!")

    # 3. Check status
    status_url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
    status_body = {"publish_id": publish_id}
    status_res = requests.post(status_url, headers=headers, json=status_body)
    print("Trạng thái TikTok Publish:", status_res.json())
    return publish_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chương trình Python tải video lên TikTok")
    parser.add_argument("--video", default="Video 3 giây.mp4", help="Đường dẫn file video")
    parser.add_argument("--title", default="Video 3s Short #tiktok", help="Tiêu đề / Caption video")
    parser.add_argument("--code", help="Authorization Code từ TikTok Callback")

    args = parser.parse_args()

    if args.code:
        token = exchange_code_for_token(args.code)
        upload_tiktok_video(args.video, args.title, token)
    else:
        token = get_valid_token()
        if token:
            upload_tiktok_video(args.video, args.title, token)
        else:
            auth_url = get_auth_url()
            print("\nChưa có Access Token! Vui lòng truy cập đường dẫn sau để cấp quyền:")
            print(auth_url)
            print("\nSau khi cấp quyền, trình duyệt sẽ chuyển hướng tới URL chứa parameter '?code=XXX'")
            print("Hãy copy đoạn mã 'code' đó và chạy lệnh:")
            print(f"python3 tiktok_helper.py --code \"MÃ_CODE_CỦA_BẠN\" --video \"{args.video}\" --title \"{args.title}\"")
