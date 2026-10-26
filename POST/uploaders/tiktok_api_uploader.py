import os
import sys
import time
import json
import urllib.parse
import requests
from typing import Optional, Dict, Any, List

TIKTOK_AUTH_BASE = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

class TikTokAPIUploader:
    """
    TikTok Content Posting API v2 Uploader (REST API thuần)
    """
    def __init__(
        self,
        client_key: str = "sbaw7p91stzjqly9kg",
        client_secret: str = "XMahHsnaxXe0Q8571FX091T4eCdeVOxq",
        redirect_uri: str = "https://httpbin.org/get",
        token_file: str = "credentials/tiktok_tokens/default.json"
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.client_key = client_key
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = os.path.join(base_dir, token_file) if not os.path.isabs(token_file) else token_file
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        self.access_token = None
        self.refresh_token = None
        self._load_token()

    def _load_token(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
            except Exception as e:
                print(f"⚠️ Lỗi đọc file token TikTok: {e}")

    def _save_token(self, token_data: dict):
        with open(self.token_file, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=4, ensure_ascii=False)
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        print(f"💾 Đã lưu Access Token TikTok vào: {self.token_file}")

    def upload_to_inbox(
        self,
        video_path: str,
        caption: str = "",
        location: str = "Hà Nội",
        hashtags: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Đẩy video sang ứng dụng TikTok (Send to TikTok App / Drafts) kèm Caption, Hashtags & Vị trí
        """
        if not os.path.exists(video_path):
            print(f"❌ Không tìm thấy file video: {video_path}")
            return None

        if not self.access_token:
            print("❌ Chưa có Access Token TikTok!")
            return None

        file_size = os.path.getsize(video_path)

        # Xây dựng nội dung caption hoàn chỉnh
        tags = hashtags or ["HaNoi", "Hanoi", "review", "shorts", "reels", "viral", "fyp"]
        tag_str = " ".join([f"#{t.strip('#')}" for t in tags if t])
        
        full_title = caption.strip()
        if location and location not in full_title:
            full_title = f"{full_title} - Tại {location}" if full_title else f"Tại {location}"
        if tag_str:
            full_title = f"{full_title} {tag_str}"

        print(f"\n[TikTok API] 📁 Tệp: {os.path.basename(video_path)} | {file_size / (1024*1024):.2f} MB")
        print(f"✍️ Caption & Hashtags & Vị trí: {full_title}")
        print("⏳ [TikTok API 1/3] Đang gửi video sang ứng dụng TikTok...")

        url = f"{TIKTOK_API_BASE}/post/publish/inbox/video/init/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        body = {
            "post_info": {
                "title": full_title
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }

        res = requests.post(url, headers=headers, json=body, timeout=30).json()
        if res.get("error", {}).get("code") != "ok":
            print(f"❌ Lỗi khởi tạo upload TikTok: {res}")
            return None

        publish_id = res["data"]["publish_id"]
        upload_url = res["data"]["upload_url"]

        # Upload binary
        print("🚀 [TikTok API 2/3] Đang truyền tải dữ liệu video...")
        with open(video_path, "rb") as f:
            vbytes = f.read()

        up_headers = {
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            "Content-Type": "video/mp4"
        }
        up_res = requests.put(upload_url, headers=up_headers, data=vbytes, timeout=600)
        if up_res.status_code not in [200, 201]:
            print(f"❌ Lỗi tải binary TikTok: {up_res.status_code}")
            return None

        # Check status
        print("🎉 [TikTok API 3/3] Đang hoàn tất...")
        status_url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
        for _ in range(10):
            time.sleep(2)
            st_res = requests.post(status_url, headers=headers, json={"publish_id": publish_id}, timeout=20).json()
            status = st_res.get("data", {}).get("status")
            if status == "SEND_TO_USER_INBOX":
                print(f"\n✅ ĐÃ ĐẨY VIDEO THÀNH CÔNG VỀ HỘP THƯ ỨNG DỤNG TIKTOK TRÊN ĐIỆN THOẠI CỦA BẠN!")
                print(f"📱 Video đã có sẵn Tiêu đề, Hashtags và Vị trí Hà Nội.")
                return {"success": True, "publish_id": publish_id, "status": status}
            if status == "FAILED":
                print(f"❌ Lỗi: {st_res.get('data', {}).get('fail_reason')}")
                return None

        return {"success": True, "publish_id": publish_id}
