# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import uuid
import subprocess
import requests
from typing import Optional, Dict, Any, List, Callable

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

THREADS_MAX_CAPTION = 500
THREADS_CDN_MAX_MB  = 95

class ThreadsAPIUploader:
    def __init__(self, threads_user_id: str, access_token: str):
        self.threads_user_id = threads_user_id
        self.access_token    = access_token
        self.base_url        = "https://graph.threads.net/v1.0"
        self.last_error      = ""

    def _log(self, msg: str, log_cb: Optional[Callable[[str], None]] = None):
        print(msg, flush=True)
        if log_cb and callable(log_cb):
            try:
                log_cb(msg)
            except Exception:
                pass

    def _compress_for_cdn(self, video_path: str, log_cb: Optional[Callable[[str], None]] = None) -> tuple:
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb <= THREADS_CDN_MAX_MB:
            return video_path, False

        temp_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_ig")
        os.makedirs(temp_dir, exist_ok=True)
        name, ext = os.path.splitext(os.path.basename(video_path))
        uid       = uuid.uuid4().hex[:8]
        out_path  = os.path.join(temp_dir, f"{name}_{uid}_threads{ext}")

        self._log(f"🗜️ [Threads] File {file_size_mb:.1f}MB > {THREADS_CDN_MAX_MB}MB, đang compress cho CDN...", log_cb)
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-crf", "26", "-preset", "fast",
            "-b:v", "4000k", "-maxrate", "4500k", "-bufsize", "8000k",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            out_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=600)
            new_mb = os.path.getsize(out_path) / (1024 * 1024)
            self._log(f"  ✅ Compress xong: {new_mb:.1f}MB (gốc {file_size_mb:.1f}MB)", log_cb)
            return out_path, True
        except Exception as e:
            self._log(f"  ⚠️ Compress thất bại ({e}), dùng file gốc.", log_cb)
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception:
                    pass
            return video_path, False

    def _get_direct_video_url(self, video_path: str, log_cb: Optional[Callable[[str], None]] = None) -> Optional[str]:
        headers   = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0

        # 1. Uguu.se — chỉ file < 100MB
        if file_size < 100 * 1024 * 1024:
            for attempt in range(1, 3):
                try:
                    self._log(f"  🌐 Uguu.se CDN (lần {attempt}/2)...", log_cb)
                    with open(video_path, "rb") as f:
                        r = requests.post("https://uguu.se/upload.php", files={"files[]": f}, timeout=90)
                    d = r.json()
                    if d.get("success") and d.get("files"):
                        url = d["files"][0]["url"]
                        self._log(f"  ✅ Uguu.se: {url}", log_cb)
                        return url
                except Exception as e:
                    self._log(f"  ⚠️ Uguu.se lần {attempt}: {e}", log_cb)
                time.sleep(4 * attempt)

        # 2. Catbox.moe
        for attempt in range(1, 3):
            try:
                self._log(f"  🌐 Catbox.moe CDN (lần {attempt}/2)...", log_cb)
                with open(video_path, "rb") as f:
                    r = requests.post(
                        "https://catbox.moe/user/api.php",
                        headers=headers,
                        data={"reqtype": "fileupload"},
                        files={"fileToUpload": f},
                        timeout=120
                    )
                if r.status_code == 200 and r.text.startswith("http"):
                    url = r.text.strip()
                    self._log(f"  ✅ Catbox: {url}", log_cb)
                    return url
            except Exception as e:
                self._log(f"  ⚠️ Catbox lần {attempt}: {e}", log_cb)
            time.sleep(6 * attempt)

        # 3. Litterbox (24h link)
        for attempt in range(1, 3):
            try:
                self._log(f"  🌐 Litterbox CDN (lần {attempt}/2)...", log_cb)
                with open(video_path, "rb") as f:
                    r = requests.post(
                        "https://litterbox.catbox.moe/resources/internals/api.php",
                        headers=headers,
                        data={"reqtype": "fileupload", "time": "24h"},
                        files={"fileToUpload": f},
                        timeout=120
                    )
                if r.status_code == 200 and r.text.startswith("http"):
                    url = r.text.strip()
                    self._log(f"  ✅ Litterbox: {url}", log_cb)
                    return url
            except Exception as e:
                self._log(f"  ⚠️ Litterbox lần {attempt}: {e}", log_cb)
            time.sleep(6 * attempt)

        return None

    def upload_video_thread(
        self,
        video_path: str,
        caption: str,
        comment_link=None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        self.last_error = ""

        if not os.path.exists(video_path):
            self.last_error = f"Không tìm thấy video: {video_path}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        clean_caption = (caption or "").strip()
        if len(clean_caption) > THREADS_MAX_CAPTION:
            clean_caption = clean_caption[:THREADS_MAX_CAPTION - 3] + "..."

        self._log(f"[Threads API] 📁 {os.path.basename(video_path)}", log_cb)

        cdn_path, is_temp = self._compress_for_cdn(video_path, log_cb)

        self._log("⏳ [Threads 1/3] Đang tải video lên CDN...", log_cb)
        video_url = self._get_direct_video_url(cdn_path, log_cb)

        if is_temp and os.path.exists(cdn_path):
            try:
                os.remove(cdn_path)
            except Exception:
                pass

        if not video_url:
            self.last_error = "Tất cả CDN trung gian đều thất bại, không thể tải video lên Threads!"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        # Bước 1: Tạo container
        self._log("🚀 [Threads 2/3] Đang tạo Media Container...", log_cb)
        try:
            res = requests.post(
                f"{self.base_url}/{self.threads_user_id}/threads",
                data={
                    "media_type":  "VIDEO",
                    "video_url":   video_url,
                    "text":        clean_caption,
                    "access_token": self.access_token
                },
                timeout=30
            ).json()
        except Exception as ce:
            self.last_error = f"Ngoại lệ khi tạo container Threads: {ce}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        if "id" not in res:
            err_msg = res.get("error", {}).get("message") or str(res)
            self.last_error = f"Lỗi tạo Container Threads: {err_msg}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        container_id = res["id"]
        self._log(f"  Container ID: {container_id}. Chờ Threads xử lý video...", log_cb)

        # Bước 2: Poll status
        status = None
        for i in range(90):
            time.sleep(4)
            try:
                st_res = requests.get(
                    f"{self.base_url}/{container_id}",
                    params={"fields": "status,error_message", "access_token": self.access_token},
                    timeout=20
                ).json()
            except Exception as pe:
                self._log(f"  ⚠️ Mạng chập chờn ({i+1}/90): {pe}", log_cb)
                continue

            status  = st_res.get("status")
            err_msg = st_res.get("error_message", "")
            if (i + 1) % 5 == 0 or status in ["FINISHED", "ERROR"]:
                self._log(f"  ⏳ Trạng thái ({i+1}/90): {status}" + (f" — {err_msg}" if err_msg else ""), log_cb)

            if status == "FINISHED":
                self._log("✅ Threads xử lý video thành công!", log_cb)
                break
            if status == "ERROR":
                self.last_error = f"Threads báo lỗi xử lý: {err_msg or status}"
                self._log(f"❌ {self.last_error}", log_cb)
                return {"success": False, "error": self.last_error}

        if status != "FINISHED":
            self.last_error = f"Hết thời gian chờ Threads xử lý video (trạng thái cuối: {status})"
            self._log(f"⚠️ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        # Bước 3: Publish
        self._log("🎉 [Threads 3/3] Đang xuất bản bài viết...", log_cb)
        try:
            pub_res = requests.post(
                f"{self.base_url}/{self.threads_user_id}/threads_publish",
                data={"creation_id": container_id, "access_token": self.access_token},
                timeout=30
            ).json()
        except Exception as pe:
            self.last_error = f"Ngoại lệ khi xuất bản Threads: {pe}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        if "id" not in pub_res:
            err_msg = pub_res.get("error", {}).get("message") or str(pub_res)
            self.last_error = f"Lỗi xuất bản Threads: {err_msg}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        thread_id = pub_res["id"]
        permalink = f"https://www.threads.com/post/{thread_id}"
        try:
            p_info = requests.get(
                f"{self.base_url}/{thread_id}",
                params={"fields": "permalink", "access_token": self.access_token},
                timeout=15
            ).json()
            permalink = p_info.get("permalink", permalink)
        except Exception:
            pass

        self._log(f"✅ ĐÃ ĐĂNG THREADS THÀNH CÔNG! Link: {permalink}", log_cb)

        # Bước 4: Reply comment affiliate links
        if comment_link:
            self._log("💬 [Threads] Đang gửi bình luận reply affiliate...", log_cb)
            comments_to_post = self._parse_comments(comment_link)
            self._log("  ⏳ Chờ 15s để Threads server index bài viết trước khi reply...", log_cb)
            time.sleep(15)

            for idx, cmt in enumerate(comments_to_post, 1):
                if len(cmt) > THREADS_MAX_CAPTION - 10:
                    cmt = cmt[:THREADS_MAX_CAPTION - 13] + "..."

                reply_success = False
                for attempt in range(1, 4):
                    try:
                        time.sleep(5)
                        r_res = self.publish_reply(post_id=thread_id, text=cmt)
                        if r_res and "id" in r_res:
                            self._log(f"  ✅ Reply {idx} thành công (ID: {r_res['id']})", log_cb)
                            reply_success = True
                            break
                        else:
                            self._log(f"  ⚠️ Reply {idx} lần {attempt}: {r_res}", log_cb)
                    except Exception as e:
                        self._log(f"  ⚠️ Reply {idx} lần {attempt} exception: {e}", log_cb)
                    time.sleep(5 * attempt)

                if not reply_success:
                    self._log(f"  ❌ Reply {idx} thất bại sau 3 lần thử!", log_cb)

        return {"success": True, "id": thread_id, "permalink": permalink}

    def publish_reply(self, post_id: str, text: str) -> Optional[Dict[str, Any]]:
        res = requests.post(
            f"{self.base_url}/{self.threads_user_id}/threads",
            data={
                "media_type":   "TEXT",
                "text":         text,
                "reply_to_id":  post_id,
                "access_token": self.access_token
            },
            timeout=30
        ).json()

        if "id" not in res:
            return None

        time.sleep(2)
        pub_res = requests.post(
            f"{self.base_url}/{self.threads_user_id}/threads_publish",
            data={"creation_id": res["id"], "access_token": self.access_token},
            timeout=30
        ).json()
        return pub_res

    @staticmethod
    def _parse_comments(comment_text) -> list:
        if isinstance(comment_text, list):
            return [c.strip() for c in comment_text if c.strip()]
        if isinstance(comment_text, str):
            lines   = [l.strip() for l in comment_text.split("\n") if l.strip()]
            blocks, current = [], []
            for line in lines:
                current.append(line)
                if "http://" in line or "https://" in line:
                    blocks.append("\n".join(current))
                    current = []
            if current:
                blocks.append("\n".join(current))
            return blocks or [comment_text.strip()]
        return []
