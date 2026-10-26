# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def log(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def upload_fb_reel_resumable(page_id: str, access_token: str, video_path: str, title: str, description: str, scheduled_time: int, video_id: str = None):
    file_size = os.path.getsize(video_path)
    log(f"Starting FB Reel upload: {os.path.basename(video_path)} ({file_size / (1024*1024):.2f} MB)")

    # If video_id not provided, start session
    if not video_id:
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/video_reels",
            data={"upload_phase": "start", "access_token": access_token},
            timeout=30
        ).json()
        log(f"Init response: {init_res}")
        if "video_id" not in init_res:
            log(f"❌ Failed to init session: {init_res}")
            return None
        video_id = init_res["video_id"]

    upload_url = f"https://rupload.facebook.com/video-upload/v26.0/{video_id}"

    # Check current offset
    check_headers = {
        "Authorization": f"OAuth {access_token}",
        "file_size": str(file_size)
    }
    check_res = requests.get(upload_url, headers=check_headers, timeout=30).json()
    start_offset = int(check_res.get("offset", 0))
    log(f"Current server offset: {start_offset} bytes ({start_offset / (1024*1024):.2f} MB)")

    chunk_size = 16 * 1024 * 1024  # 16 MB chunks
    with open(video_path, "rb") as f:
        f.seek(start_offset)
        current_offset = start_offset
        
        while current_offset < file_size:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": str(current_offset),
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream"
            }
            
            # Retry loop for chunk upload
            success = False
            for attempt in range(5):
                try:
                    res = requests.post(upload_url, headers=headers, data=chunk, timeout=90)
                    if res.status_code in [200, 201, 206]:
                        current_offset += len(chunk)
                        log(f"  Uploaded: {current_offset / (1024*1024):.1f} / {file_size / (1024*1024):.1f} MB ({(current_offset/file_size)*100:.1f}%)")
                        success = True
                        break
                    else:
                        log(f"  ⚠️ Chunk error (HTTP {res.status_code}): {res.text[:150]}, retrying {attempt+1}/5...")
                        time.sleep(3)
                except Exception as e:
                    log(f"  ⚠️ Exception uploading chunk: {e}, retrying {attempt+1}/5...")
                    time.sleep(3)
            
            if not success:
                log(f"❌ Failed to upload chunk after 5 attempts at offset {current_offset}")
                return None

    log("🎉 Video bytes upload completed! Proceeding to finish phase...")

    # Finish phase
    finish_payload = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "description": description,
        "title": title,
        "video_state": "SCHEDULED",
        "scheduled_publish_time": scheduled_time
    }
    finish_res = requests.post(
        f"https://graph.facebook.com/v19.0/{page_id}/video_reels",
        data=finish_payload,
        timeout=30
    ).json()
    log(f"Finish response: {finish_res}")
    return finish_res

if __name__ == "__main__":
    with open(r"C:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)["cham_cong_nghe"]["facebook"]
    
    page_id = cfg["page_id"]
    token = cfg["access_token"]
    video_path = r"C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\đèn màn hình máy tính.mp4"
    scheduled_time = 1790399580  # 2026-09-26 12:13:00 UTC+7
    
    title = "Đèn Treo Màn Hình Bảo Vệ Mắt Chống Cận Tiết Kiệm Không Gian"
    caption = (
        "Anh em hay làm việc hay chơi game ban đêm nhất định phải trang bị em đèn treo màn hình này nhé! "
        "Ánh sáng hắt xuống bàn mượt mà, không chiếu trực tiếp vào mắt hay lóa màn hình, vừa chống mỏi mắt vừa làm góc setup cực sang. "
        "Link mua hàng chính hãng mình để dưới cmt nha 👇\n\n"
        "#TrạmCôngNghệ #ĐènTreoMànHình #SetupBànLàmViệc #ChốngMỏiMắt #TechReview"
    )
    
    # We can resume on the existing video_id 1879463273465659
    upload_fb_reel_resumable(
        page_id=page_id,
        access_token=token,
        video_path=video_path,
        title=title,
        description=caption,
        scheduled_time=scheduled_time,
        video_id="1879463273465659"
    )
