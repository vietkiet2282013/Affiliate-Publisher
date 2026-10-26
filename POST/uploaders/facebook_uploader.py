import os
import sys
import time
import json
import re
import datetime
import requests
from typing import Optional, Dict, Any, List, Callable

class FacebookReelsUploader:
    def __init__(self, page_id: str, access_token: str, api_version: str = "v19.0"):
        self.page_id = str(page_id).strip()
        self.access_token = str(access_token).strip()
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.last_error = ""

    def _log(self, msg: str, log_cb: Optional[Callable[[str], None]] = None):
        print(msg, flush=True)
        if log_cb and callable(log_cb):
            try:
                log_cb(msg)
            except Exception:
                pass

    def check_permissions(self):
        if not self.page_id or not self.access_token:
            return False, "Thiếu PAGE_ID hoặc ACCESS_TOKEN"
        url = f"{self.base_url}/{self.page_id}"
        params = {"fields": "id,name", "access_token": self.access_token}
        try:
            res = requests.get(url, params=params, timeout=15)
            data = res.json()
            if "error" in data:
                return False, data["error"]
            return True, data
        except Exception as e:
            return False, str(e)

    def upload_reel(
        self,
        video_path: str,
        caption: str = "",
        title: str = "",
        comment_text: Optional[str] = None,
        scheduled_time: Optional[int] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        self.last_error = ""

        if not os.path.exists(video_path):
            self.last_error = f"Không tìm thấy file video: {video_path}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        file_size = os.path.getsize(video_path)
        self._log(f"[Facebook Reels] 📁 Tệp: {os.path.basename(video_path)} | {file_size / (1024*1024):.2f} MB", log_cb)

        # Bước 1: Start session
        self._log("⏳ [Facebook 1/3] Khởi tạo phiên upload...", log_cb)
        init_url = f"{self.base_url}/{self.page_id}/video_reels"
        try:
            init_res = requests.post(init_url, data={"upload_phase": "start", "access_token": self.access_token}, timeout=20).json()
        except Exception as ie:
            self.last_error = f"Không thể kết nối API Facebook khởi tạo: {ie}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        if "error" in init_res:
            err_msg = init_res['error'].get('message') or str(init_res['error'])
            self.last_error = f"Lỗi khởi tạo Facebook: {err_msg}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        video_id = init_res.get("video_id")
        upload_url = init_res.get("upload_url")
        if not video_id or not upload_url:
            self.last_error = f"Facebook không trả về video_id hoặc upload_url: {init_res}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        # Bước 2: Binary transfer
        self._log("🚀 [Facebook 2/3] Đang tải dữ liệu video lên Meta...", log_cb)
        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "offset": "0",
            "file_size": str(file_size),
            "Content-Type": "application/octet-stream"
        }
        try:
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            upload_res = requests.post(upload_url, headers=headers, data=video_bytes, timeout=600)
            if upload_res.status_code not in [200, 201]:
                self.last_error = f"Lỗi khi tải dữ liệu video lên Facebook (HTTP {upload_res.status_code}): {upload_res.text[:150]}"
                self._log(f"❌ {self.last_error}", log_cb)
                return {"success": False, "error": self.last_error}
        except Exception as ue:
            self.last_error = f"Ngoại lệ khi upload video lên Facebook: {ue}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        # Bước 3: Finish & Publish
        self._log("🎉 [Facebook 3/3] Hoàn tất và xuất bản Reel...", log_cb)
        clean_caption = caption or ""
        if clean_caption:
            clean_caption = re.sub(
                r'(?:https?://)?(?:s\.shopee\.vn|shope\.ee|shopee\.vn|shorten\.asia|affiliate\.shopee\.vn)[^\s\'"<>]+',
                '',
                clean_caption,
                flags=re.IGNORECASE
            )
            clean_caption = re.sub(r'(?:mua ngay tại|mua chính hãng giá tốt tại|mua tại|link mua|link sp|link sản phẩm|tham khảo tại|xem tại)\s*', '', clean_caption, flags=re.IGNORECASE)
            clean_caption = re.sub(r'\s{2,}', ' ', clean_caption).strip()
            clean_caption = re.sub(r'\n{3,}', '\n\n', clean_caption).strip()

        finish_payload = {
            "upload_phase": "finish",
            "access_token": self.access_token,
            "video_id": video_id,
            "description": clean_caption,
            "title": title
        }
        if scheduled_time:
            finish_payload["video_state"] = "SCHEDULED"
            finish_payload["scheduled_publish_time"] = scheduled_time
        else:
            finish_payload["video_state"] = "PUBLISHED"

        try:
            finish_res = requests.post(f"{self.base_url}/{self.page_id}/video_reels", data=finish_payload, timeout=20).json()
        except Exception as fe:
            self.last_error = f"Ngoại lệ khi xuất bản Facebook Reel: {fe}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        if "error" in finish_res or not finish_res.get("success", False):
            err_msg = finish_res.get("error", {}).get("message") if isinstance(finish_res.get("error"), dict) else str(finish_res)
            self.last_error = f"Lỗi xuất bản Facebook Reel: {err_msg}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        post_id = finish_res.get("post_id")
        reel_url = f"https://www.facebook.com/reel/{video_id}"
        self._log(f"✅ ĐÃ ĐĂNG FACEBOOK REEL THÀNH CÔNG: {reel_url}", log_cb)

        # Bước 4: Bình luận tự động
        comments_to_post = []
        if comment_text:
            if isinstance(comment_text, list):
                comments_to_post = [c.strip() for c in comment_text if c.strip()]
            elif isinstance(comment_text, str):
                lines = [line.strip() for line in comment_text.split("\n") if line.strip()]
                current_block = []
                for line in lines:
                    current_block.append(line)
                    if "http://" in line or "https://" in line:
                        comments_to_post.append("\n".join(current_block))
                        current_block = []
                if current_block:
                    comments_to_post.append("\n".join(current_block))
            if not comments_to_post and isinstance(comment_text, str) and comment_text.strip():
                comments_to_post = [comment_text.strip()]

        if scheduled_time:
            self._log("⏰ [Facebook] Video ở trạng thái HẸN GIỜ (chưa công khai). Meta API không hỗ trợ bình luận trực tiếp trước khi xuất bản.", log_cb)
            if comments_to_post:
                try:
                    queue_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "schedule_queue.json")
                    q_data = []
                    if os.path.exists(queue_file):
                        with open(queue_file, "r", encoding="utf-8") as _qf:
                            q_data = json.load(_qf)
                    q_data.append({
                        "id": f"fb_comment_{video_id}",
                        "type": "fb_scheduled_comment",
                        "video_id": video_id,
                        "page_id": self.page_id,
                        "access_token": self.access_token,
                        "comments": comments_to_post,
                        "scheduled_timestamp": scheduled_time + 45,
                        "scheduled_time_str": datetime.datetime.fromtimestamp(scheduled_time + 45).strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "PENDING"
                    })
                    os.makedirs(os.path.dirname(queue_file), exist_ok=True)
                    with open(queue_file, "w", encoding="utf-8") as _qf:
                        json.dump(q_data, _qf, indent=4, ensure_ascii=False)
                    self._log(f"  📌 Đã lưu {len(comments_to_post)} bình luận affiliate vào hàng đợi hẹn giờ!", log_cb)
                except Exception as _e_q:
                    self._log(f"  ⚠️ Không thể lưu queue bình luận Facebook hẹn giờ: {_e_q}", log_cb)
        elif comments_to_post:
            target_comment_id = video_id
            self._log(f"💬 [Facebook] Đang đăng {len(comments_to_post)} bình luận tự động chứa link Shopee...", log_cb)
            time.sleep(3)
            for idx, c in enumerate(comments_to_post, 1):
                comment_posted = False
                for attempt in range(1, 4):
                    try:
                        time.sleep(2)
                        c_res = requests.post(
                            f"{self.base_url}/{target_comment_id}/comments",
                            data={"message": c, "access_token": self.access_token},
                            timeout=25
                        ).json()
                        if "id" in c_res:
                            self._log(f"  ✅ Đã thêm bình luận Facebook {idx}: '{c[:45]}...' (ID: {c_res['id']})", log_cb)
                            comment_posted = True
                            break
                        else:
                            self._log(f"  ⚠️ Lỗi thêm bình luận {idx} lần {attempt}: {c_res}", log_cb)
                    except Exception as e:
                        self._log(f"  ⚠️ Thử lại bình luận Facebook {idx} lần {attempt} thất bại: {e}", log_cb)
                    time.sleep(3)
                if not comment_posted:
                    self._log(f"  ❌ Thất bại gửi bình luận Facebook {idx} sau 3 lần thử!", log_cb)

        return {"success": True, "video_id": video_id, "post_id": post_id, "reel_url": reel_url}

    def share_to_story(self, video_id: str) -> Optional[Dict[str, Any]]:
        try:
            print(f"📖 [Facebook Story] Đang share Reel lên Story (video_id: {video_id})...", flush=True)
            res = requests.post(
                f"{self.base_url}/{self.page_id}/video_stories",
                data={
                    "upload_phase": "finish",
                    "video_id": video_id,
                    "access_token": self.access_token
                },
                timeout=20
            ).json()
            if res.get("success"):
                print("✅ [Facebook Story] Đã share lên Story thành công!", flush=True)
                return {"success": True, "story_id": res.get("post_id", "")}
            else:
                print(f"⚠️ [Facebook Story] Không share được lên Story: {res}", flush=True)
                return None
        except Exception as e:
            print(f"⚠️ [Facebook Story] Lỗi: {e}", flush=True)
            return None
