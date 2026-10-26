import os
import sys
import argparse
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Scope để upload video và bình luận
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

def get_authenticated_service(client_secrets_file=CLIENT_SECRETS_FILE, token_file=TOKEN_FILE):
    """
    Xác thực tài khoản YouTube qua OAuth 2.0.
    Tự động lưu và làm mới token trong token_file.
    """
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"Refreshing access token for {token_file}...")
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                raise FileNotFoundError(
                    f"Không tìm thấy file '{client_secrets_file}'.\n"
                    "Bạn cần tải file OAuth 2.0 Client Credentials (dạng JSON) từ Google Cloud Console "
                    f"và đặt vào thư mục này với tên '{client_secrets_file}'."
                )
            print("Đang mở trình duyệt để ủy quyền tài khoản YouTube...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Lưu token cho các lần sử dụng sau
        with open(token_file, "w") as token:
            token.write(creds.to_json())
            print(f"Đã lưu token vào '{token_file}'")

    return build("youtube", "v3", credentials=creds)

def add_comment_to_video(youtube, video_id, comment_text):
    """Đăng bình luận vào video YouTube vừa upload"""
    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
        youtube.commentThreads().insert(part="snippet", body=body).execute()
        print(f"Đã thêm bình luận tự động thành công!")
    except Exception as e:
        print(f"Lưu ý về bình luận API: {e}")

def upload_short(
    video_path,
    title,
    description="",
    tags=None,
    category_id="22",  # 22 là "People & Blogs"
    privacy_status="public",  # public, private, hoặc unlisted
    comment="",
    client_secrets_file=CLIENT_SECRETS_FILE,
    token_file=TOKEN_FILE
):
    """
    Tải video ngắn (Shorts) lên YouTube kèm Bình luận.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    # Đảm bảo hashtag #Shorts có trong title hoặc description
    if "#shorts" not in title.lower() and "#shorts" not in description.lower():
        title = f"{title} #Shorts"

    youtube = get_authenticated_service(client_secrets_file, token_file)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or ["Shorts", "YouTubeShorts", "Viral", "Xuhuong"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024 * 5,
        resumable=True,
        mimetype="video/*"
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print(f"\nBắt đầu tải video lên YouTube...")
    print(f"- File: {video_path}")
    print(f"- Tiêu đề: {title}")
    print(f"- Quyền riêng tư: {privacy_status}\n")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"Tiến độ upload: {progress}%", end="\r", flush=True)

    print(f"\nUpload thành công!")
    video_id = response.get("id")
    video_url = f"https://www.youtube.com/shorts/{video_id}"
    print(f"ID Video: {video_id}")
    print(f"Link YouTube Short: {video_url}")

    if comment:
        print(f"\nĐang tự động đăng bình luận: '{comment}'")
        add_comment_to_video(youtube, video_id, comment)

    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chương trình Python tải video lên YouTube Shorts")
    parser.add_argument("--video", required=True, help="Đường dẫn đến file video (.mp4, .mov, ...)")
    parser.add_argument("--title", required=True, help="Tiêu đề video")
    parser.add_argument("--description", default="", help="Mô tả video")
    parser.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"], help="Quyền riêng tư (public/private/unlisted)")
    parser.add_argument("--category", default="22", help="ID danh mục (22: People & Blogs, 24: Entertainment, v.v.)")
    parser.add_argument("--token", default=TOKEN_FILE, help="File token lưu xác thực kênh (mặc định: token.json)")
    parser.add_argument("--comment", default="", help="Nội dung bình luận tự động vào video")

    args = parser.parse_args()

    try:
        upload_short(
            video_path=args.video,
            title=args.title,
            description=args.description,
            privacy_status=args.privacy,
            category_id=args.category,
            token_file=args.token,
            comment=args.comment
        )
    except Exception as e:
        print(f"\nLỗi khi tải video lên: {e}")
