# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import uuid
import shutil
import subprocess
import requests
from typing import Optional, Dict, Any, Callable

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

class InstagramReelsUploader:
    """
    Class xử lý upload video lên Instagram Reels qua Resumable Binary Upload (curl subprocess)
    và Auto-Comment affiliate links.
    """
    def __init__(self, ig_user_id: str, access_token: str, api_version: str = "v19.0"):
        self.ig_user_id = str(ig_user_id).strip()
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

    def _get_video_duration(self, video_path: str) -> float:
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video_path]
            out = subprocess.check_output(cmd, timeout=30).decode()
            return float(json.loads(out)["format"]["duration"])
        except Exception:
            return 0.0

    def _trim_video_to_89s(self, video_path: str, log_cb: Optional[Callable[[str], None]] = None) -> str:
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_ig")
        os.makedirs(temp_dir, exist_ok=True)
        base_name = os.path.basename(video_path)
        name, ext = os.path.splitext(base_name)
        unique_id = uuid.uuid4().hex[:8]
        out_path = os.path.join(temp_dir, f"{name}_{unique_id}_89s{ext}")
        self._log("✂️ Video dài hơn 90s, đang cắt nhanh 89s (giữ nguyên chất lượng 4K)...", log_cb)
        cmd = ["ffmpeg", "-y", "-i", video_path, "-t", "89", "-c", "copy",
               "-movflags", "+faststart", "-map_metadata", "-1", out_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return out_path

    def _compress_for_cdn(self, video_path: str, log_cb: Optional[Callable[[str], None]] = None) -> tuple:
        """Nếu video > 90MB, nén nhanh xuống 1080x1920 bitrate 4Mbps để CDN nhận ngay 100%."""
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb <= 90:
            return video_path, False

        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_ig")
        os.makedirs(temp_dir, exist_ok=True)
        name, ext = os.path.splitext(os.path.basename(video_path))
        uid = uuid.uuid4().hex[:8]
        out_path = os.path.join(temp_dir, f"{name}_{uid}_cdn{ext}")

        self._log(f"🗜️ [Instagram CDN] File {file_size_mb:.1f}MB > 90MB, đang nén nhanh cho CDN...", log_cb)
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
            self._log(f"  ✅ Nén CDN xong: {new_mb:.1f}MB (gốc {file_size_mb:.1f}MB)", log_cb)
            return out_path, True
        except Exception as e:
            self._log(f"  ⚠️ Nén CDN thất bại ({e}), dùng file hiện tại.", log_cb)
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception:
                    pass
            return video_path, False

    def _fix_moov_atom(self, video_path: str, log_cb: Optional[Callable[[str], None]] = None) -> tuple:
        """
        Đảm bảo moov atom ở đầu file (faststart) và xóa edit list (edts).
        Meta rupload từ chối file có moov atom ở cuối hoặc có edit list.
        Trả về (fixed_path, is_temp).
        """
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_ig")
        os.makedirs(temp_dir, exist_ok=True)
        name, ext = os.path.splitext(os.path.basename(video_path))
        uid = uuid.uuid4().hex[:6]
        out_path = os.path.join(temp_dir, f"{name}_{uid}_fixed{ext}")
        try:
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-c", "copy",
                "-movflags", "+faststart",
                "-map_metadata", "-1",   # Xóa edit list và metadata thừa
                out_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            if result.returncode == 0 and os.path.exists(out_path):
                self._log("  ✅ Đã chuẩn hóa moov atom (faststart) cho Meta.", log_cb)
                return out_path, True
        except Exception as e:
            self._log(f"  ⚠️ Không thể fix moov atom: {e}. Dùng file gốc.", log_cb)
        return video_path, False

    def _upload_via_curl(self, upload_uri: str, video_path: str, file_size: int, log_cb: Optional[Callable[[str], None]] = None) -> bool:
        """
        Dùng curl subprocess để upload file lên rupload.facebook.com.
        """
        self._log(f"🚀 [Instagram] Đang truyền tải trực tiếp bằng curl (file: {file_size/(1024*1024):.1f} MB)...", log_cb)
        cmd = [
            "curl",
            "-4",                          # Force IPv4 — tránh IPv6 routing issue
            "-s",                          # Silent output
            "--retry", "3",                # Tự retry 3 lần nếu mạng lỗi
            "--retry-delay", "5",
            "--retry-connrefused",
            "-X", "POST",
            "-H", f"Authorization: OAuth {self.access_token}",
            "-H", "offset: 0",
            "-H", f"file_size: {file_size}",
            "-H", "Content-Type: application/octet-stream",
            "-T", video_path,              # --upload-file: đọc trực tiếp từ disk
            upload_uri
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                self._log("  ✅ curl upload hoàn tất (return code 0)", log_cb)
                return True
            else:
                err_detail = result.stderr[:200] if result.stderr else f"Exit code {result.returncode}"
                self._log(f"  ❌ curl exit {result.returncode}: {err_detail}", log_cb)
                self.last_error = f"Lỗi curl upload lên Meta: {err_detail}"
                return False
        except subprocess.TimeoutExpired:
            self.last_error = "curl upload timeout (>600s)"
            self._log(f"  ❌ {self.last_error}", log_cb)
            return False
        except Exception as e:
            self.last_error = f"curl exception: {e}"
            self._log(f"  ❌ {self.last_error}", log_cb)
            return False

    def upload_reel(
        self,
        video_path: str,
        caption: str = "",
        comment_text: Optional[str] = None,
        scheduled_publish_time: Optional[int] = None,
        log_cb: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        self.last_error = ""

        if not self.ig_user_id or not self.access_token:
            self.last_error = "Thiếu IG_USER_ID hoặc ACCESS_TOKEN cấu hình Instagram!"
            self._log(f"⚠️ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        if not os.path.exists(video_path):
            self.last_error = f"Không tìm thấy file video: {video_path}"
            self._log(f"❌ {self.last_error}", log_cb)
            return {"success": False, "error": self.last_error}

        # Kiểm tra thời lượng: Instagram Reels tối đa 90 giây
        actual_video_path = video_path
        is_temp_file = False
        duration = self._get_video_duration(video_path)
        if duration > 90.0:
            try:
                actual_video_path = self._trim_video_to_89s(video_path, log_cb)
                is_temp_file = True
            except Exception as te:
                self._log(f"⚠️ Không thể cắt video: {te}. Thử tải file gốc.", log_cb)

        file_size = os.path.getsize(actual_video_path)
        self._log(f"[Instagram Reels] 📁 {os.path.basename(actual_video_path)} | {file_size/(1024*1024):.2f} MB", log_cb)

        # Chuẩn hóa moov atom trước khi upload để tránh ProcessingFailedError
        self._log("⚙️ Chuẩn hóa container video (faststart)...", log_cb)
        fixed_path, is_fixed_temp = self._fix_moov_atom(actual_video_path, log_cb)
        if is_fixed_temp:
            if is_temp_file:
                self._cleanup_temp(actual_video_path, True)  # Xóa file 89s cũ
            actual_video_path = fixed_path
            is_temp_file = True
            file_size = os.path.getsize(actual_video_path)
            self._log(f"  ✅ File đã chuẩn hóa: {file_size/(1024*1024):.2f} MB", log_cb)

        container_id = None
        used_strategy = None

        # ── Chiến lược 1: Resumable Direct Upload (rupload.facebook.com) ───────────
        max_rupload_attempts = 2
        for attempt in range(1, max_rupload_attempts + 1):
            try:
                self._log(f"⏳ [Instagram 1/4] Khởi tạo resumable container (lần {attempt}/{max_rupload_attempts})...", log_cb)
                init_res = requests.post(
                    f"{self.base_url}/{self.ig_user_id}/media",
                    data={
                        "media_type": "REELS",
                        "upload_type": "resumable",
                        "caption": caption,
                        "access_token": self.access_token
                    },
                    timeout=30
                ).json()

                if "id" not in init_res or "uri" not in init_res:
                    err_msg = init_res.get("error", {}).get("message") or str(init_res)
                    self.last_error = f"Meta API từ chối khởi tạo resumable container: {err_msg}"
                    self._log(f"  ⚠️ Khởi tạo resumable thất bại: {err_msg}", log_cb)
                    break  # Lỗi init → chuyển sang CDN fallback

                cid = init_res["id"]
                upload_uri = init_res["uri"]
                self._log(f"  ✅ Container ID: {cid}", log_cb)

                # Thử truyền tải bằng curl
                success = self._upload_via_curl(upload_uri, actual_video_path, file_size, log_cb)
                
                # Nếu curl không thành công, thử requests streaming dự phòng
                if not success:
                    self._log("  ⚠️ Thử truyền tải bằng requests stream dự phòng...", log_cb)
                    try:
                        headers = {
                            "Authorization": f"OAuth {self.access_token}",
                            "offset": "0",
                            "file_size": str(file_size),
                            "Content-Type": "application/octet-stream"
                        }
                        with open(actual_video_path, "rb") as vf:
                            req_up = requests.post(upload_uri, headers=headers, data=vf, timeout=300)
                        if req_up.status_code in [200, 201]:
                            success = True
                            self._log("  ✅ Requests stream hoàn tất thành công!", log_cb)
                    except Exception as _e_req:
                        self._log(f"  ⚠️ Requests stream thất bại: {_e_req}", log_cb)

                if success:
                    container_id = cid
                    used_strategy = "resumable"
                    break
                else:
                    self._log(f"  ⚠️ Upload resumable lần {attempt} thất bại.", log_cb)
                    time.sleep(4)

            except Exception as e:
                self.last_error = f"Ngoại lệ khi upload resumable: {e}"
                self._log(f"  ⚠️ Ngoại lệ resumable lần {attempt}: {e}", log_cb)
                time.sleep(4)

        # ── Hàm nội bộ kiểm tra trạng thái xử lý container ─────────────────────────
        def _wait_for_container(cid: str) -> bool:
            self._log(f"⏳ [Instagram 3/4] Đang đợi Meta xử lý và mã hóa video (Container: {cid})...", log_cb)
            st_code = ""
            for poll_idx in range(30):  # Tối đa 30 lần x 4s = 2 phút (chống treo nghẽn hàng đợi)
                time.sleep(4)
                try:
                    status_res = requests.get(
                        f"{self.base_url}/{cid}",
                        params={"fields": "status_code,status", "access_token": self.access_token},
                        timeout=20
                    ).json()
                except Exception as pe:
                    self._log(f"  ⚠️ Mạng chập chờn ({poll_idx+1}/30): {pe}", log_cb)
                    continue

                st_code = status_res.get("status_code", "")
                if (poll_idx + 1) % 5 == 0 or st_code in ["FINISHED", "ERROR"]:
                    self._log(f"  ⏳ Trạng thái ({poll_idx+1}/30): {st_code}", log_cb)

                if st_code == "FINISHED":
                    self._log("✅ Video đã được Instagram xử lý hoàn tất 100%!", log_cb)
                    return True
                if st_code == "ERROR":
                    err_msg = status_res.get("status") or status_res.get("error_message") or str(status_res)
                    self.last_error = f"Meta báo lỗi xử lý container {cid}: {err_msg}"
                    self._log(f"❌ {self.last_error}", log_cb)
                    return False
            self.last_error = f"Quá thời gian chờ Meta xử lý video (>2 phút, trạng thái: {st_code})"
            self._log(f"⚠️ {self.last_error}", log_cb)
            return False

        ready = False
        if container_id:
            ready = _wait_for_container(container_id)
            if not ready:
                self._log("⚠️ Container resumable không hoàn thành (lỗi xử lý hoặc timeout). Tự động kích hoạt Fallback CDN...", log_cb)
                container_id = None

        # ── Chiến lược 2: Fallback qua CDN đa nguồn nếu resumable thất bại ─────────────
        if not container_id:
            self._log("⏳ [Instagram Fallback] Đang chuẩn bị tải video lên CDN trung gian chất lượng cao...", log_cb)
            cdn_src_path, cdn_is_temp = self._compress_for_cdn(actual_video_path, log_cb)
            video_url = self._get_direct_video_url(cdn_src_path, log_cb)
            if cdn_is_temp and os.path.exists(cdn_src_path):
                self._cleanup_temp(cdn_src_path, True)

            if video_url:
                self._log(f"🚀 [Instagram Fallback] Khởi tạo container qua CDN URL: {video_url[:60]}...", log_cb)
                init_res = requests.post(
                    f"{self.base_url}/{self.ig_user_id}/media",
                    data={
                        "media_type": "REELS",
                        "video_url": video_url,
                        "caption": caption,
                        "access_token": self.access_token
                    },
                    timeout=45
                ).json()
                if "id" in init_res:
                    container_id = init_res["id"]
                    used_strategy = "cdn"
                    self._log(f"  ✅ Container ID qua CDN: {container_id}", log_cb)
                    ready = _wait_for_container(container_id)
                else:
                    err_msg = init_res.get("error", {}).get("message") or str(init_res)
                    self.last_error = f"Meta API từ chối tạo container qua CDN: {err_msg}"
                    self._log(f"  ❌ CDN container init thất bại: {err_msg}", log_cb)
            else:
                if not self.last_error:
                    self.last_error = "Tất cả các dịch vụ CDN trung gian đều không nhận video hoặc timeout"

        if not container_id or not ready:
            if not self.last_error:
                self.last_error = "Tất cả các phương thức upload Instagram (Resumable và CDN fallback) đều thất bại!"
            self._log(f"❌ {self.last_error}", log_cb)
            self._cleanup_temp(actual_video_path, is_temp_file)
            return {"success": False, "error": self.last_error}

        # ── Bước 4: Publish Reel (có retry 3 lần) ──────────────────────────────────
        self._log("🎉 [Instagram 4/4] Đang xuất bản Instagram Reel...", log_cb)
        media_id = None
        for p_attempt in range(1, 4):
            try:
                time.sleep(2)
                pub_res = requests.post(
                    f"{self.base_url}/{self.ig_user_id}/media_publish",
                    data={"creation_id": container_id, "access_token": self.access_token},
                    timeout=35
                ).json()

                if "id" in pub_res:
                    media_id = pub_res["id"]
                    break
                elif "error" in pub_res:
                    err_msg = pub_res["error"].get("message", "")
                    self.last_error = f"Meta từ chối xuất bản lần {p_attempt}: {err_msg}"
                    self._log(f"  ⚠️ {self.last_error}", log_cb)
                    time.sleep(5)
            except Exception as _e_pub:
                self.last_error = f"Ngoại lệ xuất bản lần {p_attempt}: {_e_pub}"
                self._log(f"  ⚠️ {self.last_error}", log_cb)
                time.sleep(5)

        if not media_id:
            if not self.last_error:
                self.last_error = "Lỗi xuất bản Instagram Reel sau 3 lần thử!"
            self._log(f"❌ {self.last_error}", log_cb)
            self._cleanup_temp(actual_video_path, is_temp_file)
            return {"success": False, "error": self.last_error}

        permalink = f"https://www.instagram.com/reel/{media_id}"
        try:
            info = requests.get(
                f"{self.base_url}/{media_id}",
                params={"fields": "permalink", "access_token": self.access_token},
                timeout=15
            ).json()
            permalink = info.get("permalink", permalink)
        except Exception:
            pass

        self._log(f"✅ ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG! URL: {permalink}", log_cb)

        # ── Bước 5: Auto-comment affiliate links ─────────────────────────────────
        if comment_text and media_id:
            self._log("💬 [Instagram] Đang đăng bình luận affiliate...", log_cb)
            comments_to_post = self._parse_comments(comment_text)

            self._log("  ⏳ Chờ 10s cho Reel kích hoạt hoàn toàn trên Meta server...", log_cb)
            time.sleep(10)

            for idx, c in enumerate(comments_to_post, 1):
                comment_posted = False
                for attempt in range(1, 4):
                    try:
                        time.sleep(3)
                        c_res = requests.post(
                            f"{self.base_url}/{media_id}/comments",
                            data={"message": c, "access_token": self.access_token},
                            timeout=25
                        ).json()
                        if "id" in c_res:
                            self._log(f"  ✅ Bình luận {idx} thành công (ID: {c_res['id']})", log_cb)
                            comment_posted = True
                            break
                        else:
                            self._log(f"  ⚠️ Bình luận {idx} lần {attempt}: {c_res}", log_cb)
                    except Exception as e:
                        self._log(f"  ⚠️ Retry bình luận {idx} lần {attempt}: {e}", log_cb)
                    time.sleep(5)
                if not comment_posted:
                    self._log(f"  ❌ Bình luận {idx} thất bại sau 3 lần thử!", log_cb)

        self._cleanup_temp(actual_video_path, is_temp_file)
        return {"success": True, "media_id": media_id, "permalink": permalink}

    def share_to_story(self, media_id: str, video_path: str = "") -> Optional[Dict[str, Any]]:
        """Tạo Instagram Story từ Reel đã đăng."""
        print(f"\n📖 [Instagram Story] Đang tạo Story từ Reel (media_id: {media_id})...", flush=True)
        video_url = ""
        try:
            info = requests.get(
                f"{self.base_url}/{media_id}",
                params={"fields": "media_url,permalink", "access_token": self.access_token},
                timeout=15
            ).json()
            video_url = info.get("media_url", "")
            if video_url:
                print(f"  ✅ Lấy được media_url từ Reel: {video_url[:60]}...", flush=True)
        except Exception as e:
            print(f"  ⚠️ Không lấy được media_url: {e}", flush=True)

        if not video_url and video_path and os.path.exists(video_path):
            print("  🌐 Fallback: upload file gốc lên CDN để tạo Story...", flush=True)
            video_url = self._get_direct_video_url(video_path) or ""

        if not video_url:
            print("  ❌ [Instagram Story] Không có video URL để tạo Story.", flush=True)
            return None

        try:
            init_res = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                data={
                    "media_type": "STORIES",
                    "video_url": video_url,
                    "access_token": self.access_token
                },
                timeout=30
            ).json()

            if "id" not in init_res:
                print(f"  ❌ [Instagram Story] Tạo container thất bại: {init_res}", flush=True)
                return None

            container_id = init_res["id"]
            print(f"  ⏳ Container Story ID: {container_id}. Đợi xử lý...", flush=True)

            for i in range(30):
                time.sleep(4)
                try:
                    st = requests.get(
                        f"{self.base_url}/{container_id}",
                        params={"fields": "status_code", "access_token": self.access_token},
                        timeout=15
                    ).json()
                    code = st.get("status_code")
                    if code == "FINISHED":
                        break
                    if code == "ERROR":
                        print(f"  ❌ [Instagram Story] Lỗi xử lý container: {st}", flush=True)
                        return None
                except Exception:
                    continue

            pub_res = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": self.access_token},
                timeout=25
            ).json()

            if "id" in pub_res:
                story_id = pub_res["id"]
                print(f"✅ [Instagram Story] Đã đăng Story thành công! (ID: {story_id})", flush=True)
                return {"success": True, "story_id": story_id}
            else:
                print(f"  ❌ [Instagram Story] Publish thất bại: {pub_res}", flush=True)
                return None
        except Exception as e:
            print(f"  ❌ [Instagram Story] Lỗi: {e}", flush=True)
            return None

    def _get_direct_video_url(self, video_path: str, log_cb: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """Fallback CDN chain với retry và backoff."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0

        # 1. Uguu.se — chỉ file < 100MB, rất ổn định
        if file_size < 100 * 1024 * 1024:
            for attempt in range(1, 3):
                try:
                    self._log(f"  🌐 Uguu.se CDN (lần {attempt})...", log_cb)
                    with open(video_path, "rb") as f:
                        r = requests.post("https://uguu.se/upload.php", files={"files[]": f}, timeout=60)
                    d = r.json()
                    if d.get("success") and d.get("files"):
                        url = d["files"][0]["url"]
                        self._log(f"  ✅ Uguu.se: {url}", log_cb)
                        return url
                except Exception as e:
                    self._log(f"  ⚠️ Uguu.se lần {attempt}: {e}", log_cb)
                    time.sleep(3)

        # 2. Catbox.moe — hỗ trợ file lớn hơn
        for attempt in range(1, 3):
            try:
                self._log(f"  🌐 Catbox.moe CDN (lần {attempt})...", log_cb)
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
                time.sleep(5)

        # 3. Litterbox (24h link)
        try:
            self._log("  🌐 Litterbox CDN...", log_cb)
            with open(video_path, "rb") as f:
                r = requests.post(
                    "https://litterbox.catbox.moe/resources/internals/api.php",
                    headers=headers,
                    data={"reqtype": "fileupload", "time": "24h"},
                    files={"fileToUpload": f},
                    timeout=90
                )
            if r.status_code == 200 and r.text.startswith("http"):
                url = r.text.strip()
                self._log(f"  ✅ Litterbox: {url}", log_cb)
                return url
        except Exception as e:
            self._log(f"  ⚠️ Litterbox: {e}", log_cb)

        # 4. Tmpfiles CDN
        try:
            self._log("  🌐 Tmpfiles CDN...", log_cb)
            with open(video_path, "rb") as f:
                r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=60).json()
            if r.get("status") == "success":
                url = r["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
                self._log(f"  ✅ Tmpfiles: {url}", log_cb)
                return url
        except Exception as e:
            self._log(f"  ⚠️ Tmpfiles: {e}", log_cb)

        return None

    @staticmethod
    def _parse_comments(comment_text) -> list:
        if isinstance(comment_text, list):
            return [c.strip() for c in comment_text if c.strip()]
        if isinstance(comment_text, str):
            lines = [l.strip() for l in comment_text.split("\n") if l.strip()]
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

    @staticmethod
    def _cleanup_temp(path: str, is_temp: bool):
        if is_temp and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
