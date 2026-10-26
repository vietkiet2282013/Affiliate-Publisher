import os
import sys
import time
import requests
from typing import Optional, Dict, Any

class PinterestUploader:
    """
    Pinterest REST API v5 Uploader
    Tải video nhị phân từ máy local và tạo Video Pin chuẩn quy trình 4 bước của Pinterest API v5.
    """
    def __init__(
        self,
        access_token: str,
        api_version: str = "v5",
        base_url: str = "https://api.pinterest.com/v5"
    ):
        self.access_token = str(access_token).strip()
        self.api_version = api_version
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def upload_video_pin(
        self,
        video_path: str,
        board_id: str,
        title: str,
        description: str,
        link: str,
        cover_image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Quy trình 4 bước tải video lên Pinterest:
        1. Register Media (POST /media)
        2. Binary Upload (POST lên upload_url với upload_parameters và file video)
        3. Polling Status (GET /media/{media_id} mỗi 3-5 giây cho đến khi succeeded)
        4. Create Pin (POST /pins với media_source dạng video_id)
        """
        if not os.path.exists(video_path):
            print(f"❌ Không tìm thấy file video: {video_path}")
            return None

        file_size = os.path.getsize(video_path)
        print(f"\n[Pinterest Video] 📁 Tệp: {os.path.basename(video_path)} | {file_size / (1024 * 1024):.2f} MB")

        # ==========================================
        # BƯỚC 1: REGISTER MEDIA
        # ==========================================
        print("⏳ [Pinterest 1/4] Đăng ký tải media (Register Media)...")
        register_url = f"{self.base_url}/media"
        register_payload = {"media_type": "video"}

        try:
            reg_res = requests.post(
                register_url,
                headers=self.headers,
                json=register_payload,
                timeout=30
            )
            reg_data = reg_res.json()
        except Exception as e:
            print(f"❌ Lỗi kết nối khi đăng ký media với Pinterest: {e}")
            return None

        if reg_res.status_code not in [200, 201]:
            print(f"❌ Lỗi đăng ký media (HTTP {reg_res.status_code}): {reg_data}")
            return None

        media_id = reg_data.get("media_id")
        upload_url = reg_data.get("upload_url")
        upload_parameters = reg_data.get("upload_parameters", {})

        if not media_id or not upload_url:
            print(f"❌ Phản hồi không hợp lệ từ Pinterest (thiếu media_id hoặc upload_url): {reg_data}")
            return None

        print(f"  Media ID: {media_id}")

        # ==========================================
        # BƯỚC 2: BINARY UPLOAD
        # ==========================================
        print("🚀 [Pinterest 2/4] Đang tải dữ liệu video nhị phân lên storage...")
        try:
            with open(video_path, "rb") as video_file:
                # Chuẩn bị multipart form-data: upload_parameters kèm theo file nhị phân
                files = {"file": (os.path.basename(video_path), video_file, "video/mp4")}
                upload_res = requests.post(
                    upload_url,
                    data=upload_parameters,
                    files=files,
                    timeout=600
                )

            if upload_res.status_code not in [200, 201, 204]:
                print(f"❌ Lỗi tải dữ liệu video lên storage (HTTP {upload_res.status_code}): {upload_res.text}")
                return None
            print("  Tải file nhị phân thành công.")
        except Exception as e:
            print(f"❌ Lỗi trong quá trình upload video nhị phân: {e}")
            return None

        # ==========================================
        # BƯỚC 3: POLLING STATUS
        # ==========================================
        print("⏳ [Pinterest 3/4] Đang thăm dò trạng thái xử lý video (Polling Status)...")
        status_url = f"{self.base_url}/media/{media_id}"
        max_attempts = 20
        status_success = False

        for attempt in range(1, max_attempts + 1):
            time.sleep(4)
            try:
                st_res = requests.get(
                    status_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=20
                )
                st_data = st_res.json()
            except Exception as e:
                print(f"  [Lần thử {attempt}/{max_attempts}] Lỗi khi kiểm tra trạng thái: {e}")
                continue

            current_status = st_data.get("status")
            print(f"  [Lần thử {attempt}/{max_attempts}] Trạng thái xử lý: {current_status}")

            if current_status == "succeeded":
                status_success = True
                print("✅ Video đã được Pinterest xử lý thành công!")
                break
            elif current_status == "failed":
                print(f"❌ Pinterest thông báo xử lý video thất bại: {st_data}")
                return None

        if not status_success:
            print(f"❌ Quá thời gian chờ Pinterest xử lý video ({max_attempts} lần thử).")
            return None

        # ==========================================
        # BƯỚC 4: CREATE PIN
        # ==========================================
        print("🎉 [Pinterest 4/4] Đang tạo Pin mới trên Pinterest...")
        pins_url = f"{self.base_url}/pins"
        
        media_source: Dict[str, Any] = {
            "source_type": "video_id",
            "media_id": media_id
        }
        if cover_image_url:
            media_source["cover_image_url"] = cover_image_url

        pin_payload = {
            "board_id": board_id,
            "title": title,
            "description": description,
            "link": link,
            "media_source": media_source
        }

        try:
            pin_res = requests.post(
                pins_url,
                headers=self.headers,
                json=pin_payload,
                timeout=30
            )
            pin_data = pin_res.json()
        except Exception as e:
            print(f"❌ Lỗi gửi yêu cầu tạo Pin: {e}")
            return None

        if pin_res.status_code not in [200, 201]:
            print(f"❌ Lỗi khi tạo Pin (HTTP {pin_res.status_code}): {pin_data}")
            return None

        pin_id = pin_data.get("id")
        if not pin_id:
            print(f"❌ Tạo Pin không trả về ID: {pin_data}")
            return None

        pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
        print(f"✅ ĐÃ ĐĂNG PINTEREST VIDEO PIN THÀNH CÔNG: {pin_url}")

        return {
            "success": True,
            "pin_id": pin_id,
            "url": pin_url
        }
