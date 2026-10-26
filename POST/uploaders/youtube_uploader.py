import os
import sys
import time
import json
import socket

# Force IPv4 to prevent IPv6 routing timeout on Google APIs
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

import re
import datetime
from typing import Optional, Dict, Any, List, Callable
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

class YouTubeShortsUploader:
    def __init__(
        self,
        client_secret_file: str = "client_secret.json",
        token_file: str = "token.json"
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.client_secret_file = os.path.join(base_dir, client_secret_file) if not os.path.isabs(client_secret_file) else client_secret_file
        self.token_file = os.path.join(base_dir, token_file) if not os.path.isabs(token_file) else token_file
        self.youtube = None
        self.last_error = ""

    def _log(self, msg: str, log_cb: Optional[Callable[[str], None]] = None):
        print(msg, flush=True)
        if log_cb and callable(log_cb):
            try:
                log_cb(msg)
            except Exception:
                pass

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                self.last_error = f"Lỗi đọc token: {e}"
                print(f"⚠️ {self.last_error}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.last_error = f"Lỗi refresh token: {e}"
                    print(f"⚠️ {self.last_error}")
                    creds = None

            if not creds or not creds.valid:
                if not os.path.exists(self.client_secret_file):
                    self.last_error = f"Không tìm thấy client_secret tại: {self.client_secret_file}"
                    print(f"❌ {self.last_error}")
                    return False

                print("\n🌐 Đang mở trình duyệt để xác thực kênh YouTube...")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)
                creds = flow.run_local_server(port=0, prompt="consent")

            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        self.youtube = build("youtube", "v3", credentials=creds)
        return True

    @staticmethod
    def clean_and_space_description(desc: str, comments_to_post: Optional[List[str]] = None) -> str:
        full_desc = (desc or "").strip()

        if comments_to_post and "shopee.vn" not in full_desc.lower() and "s.shopee.vn" not in full_desc.lower():
            formatted_blocks = []
            seen_urls = set()
            for c in comments_to_post:
                c_clean = c.strip()
                if not c_clean:
                    continue
                urls = re.findall(r'https?://[^\s<>"\']+', c_clean)
                if not urls:
                    continue
                u = urls[0]
                u_key = u.rstrip("/?#&").lower()
                if u_key in seen_urls:
                    continue
                seen_urls.add(u_key)
                prefix = c_clean.replace(u, "").strip()
                if prefix:
                    formatted_blocks.append(f"{prefix}\n{u}")
                else:
                    formatted_blocks.append(u)
            if formatted_blocks:
                links_block = "\n\n".join(formatted_blocks)
                full_desc = f"{full_desc}\n\n🛒 MUA SẢN PHẨM TẠI ĐÂY:\n\n{links_block}".strip()
                return full_desc

        header_patterns = [
            r"🛒\s*(?:LINK\s*)?MUA SẢN PHẨM CHÍNH HÃNG TẠI ĐÂY:?",
            r"🛒\s*(?:LINK\s*)?MUA SẢN PHẨM TẠI ĐÂY:?",
            r"🛒\s*MUA SẢN PHẨM TẠI ĐÂY:?",
            r"🛒\s*Mua sản phẩm chính hãng.*?:?"
        ]

        for pat in header_patterns:
            match = re.search(pat, full_desc, flags=re.IGNORECASE)
            if match:
                start_pos = match.start()
                header_str = match.group(0).strip()
                if not header_str.endswith(":"):
                    header_str += ":"
                main_part = full_desc[:start_pos].strip()
                tail_part = full_desc[match.end():].strip()

                hashtag_match = re.search(r'(\n\s*#[^\n]+)+\s*$', tail_part)
                hashtags = ""
                if hashtag_match:
                    hashtags = hashtag_match.group(0).strip()
                    tail_part = tail_part[:hashtag_match.start()].strip()

                raw_lines = [l.strip() for l in tail_part.split("\n") if l.strip()]
                items = []
                seen_urls = set()
                curr_prefix = []
                for line in raw_lines:
                    line_urls = re.findall(r'https?://[^\s<>"\']+', line)
                    if line_urls:
                        u = line_urls[0]
                        u_key = u.rstrip("/?#&").lower()
                        if u_key not in seen_urls:
                            seen_urls.add(u_key)
                            p_line = line.replace(u, "").strip()
                            if p_line:
                                curr_prefix.append(p_line)
                            p_text = " ".join(curr_prefix).strip()
                            if p_text:
                                items.append(f"{p_text}\n{u}")
                            else:
                                items.append(u)
                        curr_prefix = []
                    else:
                        curr_prefix.append(line)
                if curr_prefix:
                    items.append(" ".join(curr_prefix).strip())

                if items:
                    formatted_tail = "\n\n".join(items)
                    res = f"{main_part}\n\n{header_str}\n\n{formatted_tail}"
                    if hashtags:
                        res += f"\n\n{hashtags}"
                    return res.strip()

        return full_desc

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        comment_text: Optional[str] = None,
        privacy_status: str = "public",
        publish_at: Optional[str] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        self.last_error = ""

        if not os.path.exists(video_path):
            self.last_error = f"Không tìm thấy file video: {video_path}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        if not self.youtube:
            if not self.authenticate():
                if not self.last_error:
                    self.last_error = "Không thể xác thực YouTube OAuth2 token"
                self._log(f"❌ {self.last_error}", log_cb)
                return {"success": False, "error": self.last_error}

        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        tags = tags or ["Shorts", "Review", "Viral", "Trending"]

        full_desc = self.clean_and_space_description(description, None)

        status_dict = {
            "selfDeclaredMadeForKids": False
        }

        if publish_at:
            status_dict["privacyStatus"] = "private"
            status_dict["publishAt"] = publish_at
            self._log(f"⏰ Chế độ: HẸN GIỜ XUẤT BẢN YOUTUBE VÀO LÚC: {publish_at}", log_cb)
        else:
            status_dict["privacyStatus"] = privacy_status

        body = {
            "snippet": {
                "title": title,
                "description": full_desc,
                "tags": tags,
                "categoryId": "22"
            },
            "status": status_dict
        }

        file_size = os.path.getsize(video_path)
        self._log(f"[YouTube Shorts] 📁 Tệp: {os.path.basename(video_path)} | {file_size / (1024*1024):.2f} MB", log_cb)

        try:
            media = MediaFileUpload(video_path, chunksize=1024*1024*16, resumable=True)
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            self._log("🚀 [YouTube] Đang truyền tải video lên máy chủ YouTube...", log_cb)
            response = None
            retries = 0
            while response is None:
                try:
                    status, response = request.next_chunk(num_retries=10)
                    if status:
                        pct = int(status.progress() * 100)
                        self._log(f"  ⏳ Tiến trình tải lên YouTube: {pct}%", log_cb)
                    retries = 0
                except Exception as e:
                    retries += 1
                    err_str = str(e).lower()
                    if "quotaexceeded" in err_str or "quota" in err_str or "403" in err_str:
                        self.last_error = "Tài khoản YouTube đã hết hạn ngạch (quota) upload trong ngày!"
                        self._log(f"❌ {self.last_error}", log_cb)
                        return {"success": False, "error": self.last_error}
                    if retries > 10:
                        raise e
                    self._log(f"  ⚠️ Mạng gián đoạn ({e}), tự động kết nối lại lần {retries}/10 sau 3s...", log_cb)
                    time.sleep(3)

            video_id = response.get("id")
            shorts_url = f"https://youtube.com/shorts/{video_id}"
            
            if publish_at:
                self._log(f"✅ ĐÃ TẢI LÊN & LÊN LỊCH YOUTUBE THÀNH CÔNG: {shorts_url}", log_cb)
            else:
                self._log(f"✅ ĐÃ ĐĂNG YOUTUBE SHORTS THÀNH CÔNG: {shorts_url}", log_cb)

            return {"success": True, "video_id": video_id, "shorts_url": shorts_url, "publish_at": publish_at}

        except Exception as e:
            err_str = str(e).lower()
            if "quotaexceeded" in err_str or "quota" in err_str or "403" in err_str:
                self.last_error = "Tài khoản YouTube đã hết hạn ngạch (quota) upload trong ngày!"
            else:
                self.last_error = f"Lỗi đăng video lên YouTube: {e}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}
