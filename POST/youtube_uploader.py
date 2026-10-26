"""
===================================================================
YOUTUBE SHORTS UPLOADER (Google YouTube Data API v3)
Tác giả: Antigravity AI
Chức năng: Upload video lên YouTube Shorts tự động với OAuth 2.0
===================================================================
"""

import os
import sys
import time
import pickle
from typing import Optional, Dict, Any, List
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeShortsUploader:
    """
    Class xử lý upload video lên YouTube Shorts
    """
    def __init__(
        self,
        client_secret_file: str = "client_secret.json",
        token_pickle_file: str = "youtube_token.pickle"
    ):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(client_secret_file):
            self.client_secret_file = os.path.join(base_dir, client_secret_file)
        else:
            self.client_secret_file = client_secret_file

        if not os.path.isabs(token_pickle_file):
            self.token_pickle_file = os.path.join(base_dir, token_pickle_file)
        else:
            self.token_pickle_file = token_pickle_file

        self.youtube = None

    def authenticate(self):
        """Xác thực OAuth 2.0 với Google và lưu Token tự động"""
        credentials = None

        if os.path.exists(self.token_pickle_file):
            try:
                with open(self.token_pickle_file, "rb") as token:
                    credentials = pickle.load(token)
            except Exception as e:
                print(f"⚠️ Không đọc được token cũ: {e}")

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    print("🔄 Đang tự động làm mới (refresh) YouTube Token...")
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"⚠️ Lỗi làm mới token: {e}, yêu cầu đăng nhập lại...")
                    credentials = None

            if not credentials or not credentials.valid:
                if not os.path.exists(self.client_secret_file):
                    print(f"\n❌ [THIẾU FILE CẤU HÌNH GOOGLE]")
                    print(f"Không tìm thấy file: {self.client_secret_file}")
                    print("👉 Vui lòng tải file 'client_secret.json' từ Google Cloud Console và bỏ vào thư mục này!")
                    return False

                print("\n🌐 Đang mở trình duyệt để xác thực tài khoản Google kênh YouTube của bạn...")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)
                credentials = flow.run_local_server(port=0)

            with open(self.token_pickle_file, "wb") as token:
                pickle.dump(credentials, token)
                print("💾 Đã lưu phiên đăng nhập vào 'youtube_token.pickle' (lần sau sẽ không cần đăng nhập lại).")

        self.youtube = build("youtube", "v3", credentials=credentials)
        print("✅ Kết nối thành công với YouTube Data API!")
        return True

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",
        category_id: str = "22"
    ) -> Optional[Dict[str, Any]]:
        """
        Upload video lên YouTube Shorts
        :param video_path: Đường dẫn file video (.mp4, .mov)
        :param title: Tiêu đề video (sẽ tự động gắn #Shorts nếu chưa có)
        :param description: Mô tả video
        :param tags: Danh sách thẻ tags
        :param privacy_status: 'public', 'private', hoặc 'unlisted'
        :param category_id: ID danh mục (mặc định '22': People & Blogs)
        """
        if not os.path.exists(video_path):
            print(f"❌ Không tìm thấy file video: {video_path}")
            return None

        if not self.youtube:
            if not self.authenticate():
                return None

        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        tags = tags or ["Shorts", "Viral", "Review"]

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        file_size = os.path.getsize(video_path)
        print(f"\n==================================================")
        print(f"📁 Tệp tin Shorts: {os.path.basename(video_path)}")
        print(f"📦 Dung lượng: {file_size / (1024*1024):.2f} MB")
        print(f"🎯 Quyền riêng tư: {privacy_status}")
        print(f"==================================================")

        try:
            media = MediaFileUpload(video_path, chunksize=1024*1024*2, resumable=True)
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            print("\n🚀 Đang truyền tải video lên máy chủ YouTube...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    print(f"  ⏳ Tiến trình tải lên: {percent}%")

            video_id = response.get("id")
            shorts_url = f"https://youtube.com/shorts/{video_id}"

            print(f"\n==================================================")
            print(f"🎊 CHÚC MỪNG! BẠN ĐÃ ĐĂNG YOUTUBE SHORTS THÀNH CÔNG!")
            print(f"🆔 Video ID: {video_id}")
            print(f"🔗 Link xem Shorts: {shorts_url}")
            print(f"==================================================")

            return {
                "success": True,
                "video_id": video_id,
                "shorts_url": shorts_url
            }

        except Exception as e:
            print(f"❌ Lỗi khi upload video lên YouTube: {e}")
            return None
