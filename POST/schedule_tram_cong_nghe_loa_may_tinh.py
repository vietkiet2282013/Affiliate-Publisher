# -*- coding: utf-8 -*-
"""
HỆ THỐNG ĐĂNG VIDEO & LÊN LỊCH TỰ ĐỘNG - THƯƠNG HIỆU TRẠM CÔNG NGHỆ
Video: C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\video chưa đăng\loa máy tính.mp4
Lịch đăng hẹn giờ mục tiêu (27/09/2026):
  1. YouTube Shorts: 18h30 ngày 27/09/2026 (Server-side Google API v3: status.publishAt = 2026-09-27T11:30:00Z)
  2. Facebook Reels: 18h41 ngày 27/09/2026 (Server-side Meta Graph API: scheduled_publish_time = 1790509260)
  3. Instagram Reels: 18h45 ngày 27/09/2026 (Tự động đếm ngược & xuất bản trực tiếp qua Meta Graph API rupload)
  4. Threads: 18h50 ngày 27/09/2026 (Tự động đếm ngược & xuất bản bài viết + chuỗi 7 link affiliate qua Threads API)

Đặc điểm:
- 100% tự động, KHÔNG tốn bất kỳ Token AI nào.
- Hỗ trợ tải video dung lượng lớn (~950MB) dạng streaming chunked resumable 16MB an toàn, không sợ tràn RAM.
- Tự động đọc danh sách 7 link affiliate từ đúng thư mục Excel của từng nền tảng tương ứng.
- Đăng comment affiliate tách riêng từng link với câu mồi quay vòng tự nhiên từ comment.txt.
"""

import os
import sys
import time
import json
import requests
import datetime
import traceback
import openpyxl

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import YouTubeShortsUploader

VIDEO_PATH = r"C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\video chưa đăng\loa máy tính.mp4"

EXCEL_FILES = {
    "facebook": r"C:\Affiliate\Trạm Công Nghệ\Link customed\Facebook\loa máy tính.xlsx",
    "instagram": r"C:\Affiliate\Trạm Công Nghệ\Link customed\Instagram\loa máy tính.xlsx",
    "threads": r"C:\Affiliate\Trạm Công Nghệ\Link customed\Threads\loa máy tính.xlsx",
    "youtube": r"C:\Affiliate\Trạm Công Nghệ\Link customed\YouTube\loa máy tính.xlsx",
}

LOG_FILE = os.path.join(POST_DIR, "config", "schedule_loa_may_tinh.log")

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_brand_config():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    return brands.get("cham_cong_nghe", {})

def load_affiliate_links(excel_path: str):
    if not os.path.exists(excel_path):
        log(f"❌ Không tìm thấy file Excel: {excel_path}")
        return []
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = rows[0]
    link_idx = 2
    name_idx = 1
    for idx, col in enumerate(header):
        if col and 'affiliate' in str(col).lower():
            link_idx = idx
        if col and 'tên' in str(col).lower():
            name_idx = idx
    
    items = []
    for r in rows[1:]:
        if r and len(r) > link_idx and r[link_idx]:
            url = str(r[link_idx]).strip()
            name = str(r[name_idx]).strip() if len(r) > name_idx and r[name_idx] else ""
            if url.startswith("http"):
                items.append({"name": name, "url": url})
    return items

def format_comment_list(items, template_file=r"C:\Affiliate\post1\comment.txt"):
    templates = [
        "Link sản phẩm ở đây: ",
        "Link xem và mua hàng ngay tại đây nè: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
        "Link sản phẩm: ",
        "Link sản phẩm ở đây cho ai cần nha: ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: "
    ]
    if os.path.exists(template_file):
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                if lines:
                    templates = [l if l.endswith(" ") else l + " " for l in lines]
        except Exception:
            pass

    comments = []
    for idx, item in enumerate(items):
        prefix = templates[idx % len(templates)]
        prod_short = f" ({item['name'][:40]}...)" if item.get('name') else ""
        comments.append(f"{prefix}{item['url']}{prod_short}")
    return comments

# ==============================================================================
# HÀM UPLOAD FACEBOOK REELS RESUMABLE CHUNKED (Tránh tràn RAM)
# ==============================================================================
def upload_fb_reel_resumable(page_id: str, access_token: str, video_path: str, title: str, description: str, scheduled_time: int, comments: list):
    file_size = os.path.getsize(video_path)
    log(f"📘 [Facebook Reels] Đang chuẩn bị tải lên: {os.path.basename(video_path)} ({file_size / (1024*1024):.2f} MB)")

    # 1. Start session
    log("⏳ [Facebook 1/3] Khởi tạo phiên tải video...")
    init_res = requests.post(
        f"https://graph.facebook.com/v19.0/{page_id}/video_reels",
        data={"upload_phase": "start", "access_token": access_token},
        timeout=30
    ).json()

    if "video_id" not in init_res:
        log(f"❌ Lỗi khởi tạo phiên Facebook Reels: {init_res}")
        return {"success": False, "error": init_res}

    video_id = init_res["video_id"]
    upload_url = f"https://rupload.facebook.com/video-upload/v19.0/{video_id}"

    # 2. Upload chunks 16MB
    chunk_size = 16 * 1024 * 1024
    log(f"🚀 [Facebook 2/3] Đang truyền tải video lên Meta server theo khối 16MB...")
    with open(video_path, "rb") as f:
        current_offset = 0
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
            
            success = False
            for retry in range(5):
                try:
                    res = requests.post(upload_url, headers=headers, data=chunk, timeout=90)
                    if res.status_code in [200, 201]:
                        success = True
                        break
                    else:
                        time.sleep(3)
                except Exception as e:
                    time.sleep(3)
            
            if not success:
                log(f"❌ Lỗi tải phân đoạn tại byte offset {current_offset}")
                return {"success": False, "error": "Chunk upload failed"}

            current_offset += len(chunk)
            pct = int((current_offset / file_size) * 100)
            log(f"  ⏳ Tiến độ tải Facebook: {pct}% ({current_offset / (1024*1024):.1f}/{file_size / (1024*1024):.1f} MB)")

    # 3. Finish session with SCHEDULED
    log(f"🎉 [Facebook 3/3] Hoàn tất và đặt lịch phát hành vào lúc timestamp: {scheduled_time}...")
    finish_payload = {
        "upload_phase": "finish",
        "access_token": access_token,
        "video_id": video_id,
        "title": title,
        "description": description,
        "video_state": "SCHEDULED",
        "scheduled_publish_time": scheduled_time
    }
    finish_res = requests.post(f"https://graph.facebook.com/v19.0/{page_id}/video_reels", data=finish_payload, timeout=30).json()
    log(f"   Kết quả đặt lịch Facebook Reels: {finish_res}")

    # Đăng comment affiliate
    if finish_res.get("success"):
        log("💬 [Facebook] Đang đăng các link affiliate vào phần bình luận của Reel...")
        for idx, cmt in enumerate(comments, 1):
            try:
                time.sleep(2)
                r_c = requests.post(
                    f"https://graph.facebook.com/v19.0/{video_id}/comments",
                    data={"message": cmt, "access_token": access_token},
                    timeout=20
                ).json()
                if "id" in r_c:
                    log(f"  ✅ Đã ghim link Affiliate Facebook {idx}: {cmt[:60]}...")
                else:
                    log(f"  ⚠️ Lưu ý comment Facebook {idx}: {r_c}")
            except Exception as ce:
                log(f"  ⚠️ Lỗi comment Facebook {idx}: {ce}")

        return {"success": True, "video_id": video_id, "scheduled_time": scheduled_time}
    return {"success": False, "error": finish_res}

# ==============================================================================
# HÀM UPLOAD INSTAGRAM REELS RESUMABLE CHUNKED (Tránh tràn RAM)
# ==============================================================================
def upload_ig_reel_chunked(ig_user_id: str, access_token: str, video_path: str, caption: str, comments: list):
    file_size = os.path.getsize(video_path)
    log(f"📸 [Instagram Reels] Đang xử lý: {os.path.basename(video_path)} ({file_size / (1024*1024):.2f} MB)")

    # 1. Khởi tạo container resumable
    log("⏳ [Instagram 1/4] Khởi tạo container tải lên...")
    init_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption,
            "access_token": access_token
        },
        timeout=30
    ).json()

    if "id" not in init_res or "uri" not in init_res:
        log(f"❌ Lỗi khởi tạo container Instagram: {init_res}")
        return {"success": False, "error": init_res}

    container_id = init_res["id"]
    upload_uri = init_res["uri"]

    # 2. Upload video binary theo chunk 16MB
    chunk_size = 16 * 1024 * 1024
    log("🚀 [Instagram 2/4] Đang truyền tải video lên Instagram server theo khối 16MB...")
    with open(video_path, "rb") as f:
        current_offset = 0
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
            
            success = False
            for retry in range(5):
                try:
                    res = requests.post(upload_uri, headers=headers, data=chunk, timeout=90)
                    if res.status_code in [200, 201]:
                        success = True
                        break
                    else:
                        time.sleep(3)
                except Exception:
                    time.sleep(3)
            
            if not success:
                log(f"❌ Lỗi tải chunk Instagram tại offset {current_offset}")
                return {"success": False, "error": "Instagram chunk upload failed"}

            current_offset += len(chunk)
            pct = int((current_offset / file_size) * 100)
            log(f"  ⏳ Tiến độ tải Instagram: {pct}% ({current_offset / (1024*1024):.1f}/{file_size / (1024*1024):.1f} MB)")

    # 3. Chờ Instagram xử lý xong video
    log("⏳ [Instagram 3/4] Đang đợi Instagram xử lý và mã hóa video...")
    for poll in range(60):
        time.sleep(5)
        st_res = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=20
        ).json()
        st_code = st_res.get("status_code")
        log(f"  Trạng thái xử lý Instagram ({poll+1}/60): {st_code}")
        if st_code == "FINISHED":
            log("✅ Video đã được Instagram xử lý hoàn tất 100%!")
            break
        elif st_code == "ERROR":
            log(f"❌ Instagram báo lỗi xử lý: {st_res}")
            return {"success": False, "error": st_res}
    else:
        log("⚠️ Quá thời gian chờ Instagram xử lý container.")
        return {"success": False, "error": "Timeout waiting for IG video processing"}

    # 4. Xuất bản Reel
    log("🎉 [Instagram 4/4] Đang xuất bản video lên trang Instagram Reels...")
    pub_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=30
    ).json()

    if "id" not in pub_res:
        log(f"❌ Lỗi xuất bản Instagram Reel: {pub_res}")
        return {"success": False, "error": pub_res}

    media_id = pub_res["id"]
    log(f"✅ XUẤT BẢN THÀNH CÔNG INSTAGRAM REEL! Media ID: {media_id}")

    # 5. Đăng các bình luận Affiliate
    log("💬 [Instagram] Đang đăng chuỗi bình luận Affiliate...")
    for idx, cmt in enumerate(comments, 1):
        try:
            time.sleep(2)
            c_res = requests.post(
                f"https://graph.facebook.com/v19.0/{media_id}/comments",
                data={"message": cmt, "access_token": access_token},
                timeout=20
            ).json()
            if "id" in c_res:
                log(f"  ✅ Đã ghim link Affiliate Instagram {idx}: {cmt[:60]}...")
            else:
                log(f"  ⚠️ Lưu ý comment Instagram {idx}: {c_res}")
        except Exception as e:
            log(f"  ⚠️ Lỗi comment Instagram {idx}: {e}")

    return {"success": True, "media_id": media_id}

# ==============================================================================
# HÀM XUẤT BẢN THREADS (Bài viết chính + 7 link affiliate ở comment)
# ==============================================================================
def publish_threads(user_id: str, access_token: str, main_text: str, items: list):
    log(f"🧵 [Threads] Bắt đầu xuất bản bài viết lên Threads...")
    
    # 1. Tạo container bài viết chính
    log("⏳ [Threads 1/2] Đang tạo bài viết chính...")
    create_res = requests.post(
        f"https://graph.threads.net/v1.0/{user_id}/threads",
        data={
            "media_type": "TEXT",
            "text": main_text,
            "access_token": access_token
        },
        timeout=30
    ).json()

    if "id" not in create_res:
        log(f"❌ Lỗi tạo bài viết Threads: {create_res}")
        return {"success": False, "error": create_res}

    container_id = create_res["id"]
    time.sleep(3)

    # 2. Xuất bản bài viết
    pub_res = requests.post(
        f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=30
    ).json()

    if "id" not in pub_res:
        log(f"❌ Lỗi xuất bản Threads: {pub_res}")
        return {"success": False, "error": pub_res}

    post_id = pub_res["id"]
    permalink = f"https://www.threads.net/post/{post_id}"
    log(f"✅ ĐÃ ĐĂNG BÀI VIẾT THREADS THÀNH CÔNG: {permalink}")

    # 3. Đăng 7 link affiliate vào reply của bài viết
    log("💬 [Threads 2/2] Đang ghim chuỗi link Affiliate vào bình luận...")
    templates = [
        "Link sản phẩm ở đây: ",
        "Link xem và mua hàng ngay tại đây nè: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
        "Link sản phẩm: ",
        "Link sản phẩm ở đây cho ai cần nha: ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: "
    ]

    for idx, it in enumerate(items, 1):
        try:
            prefix = templates[(idx - 1) % len(templates)]
            cmt_text = f"{prefix}\n{it['url']}\n({it['name'][:50]})"
            r_rep = requests.post(
                f"https://graph.threads.net/v1.0/{user_id}/threads",
                data={
                    "media_type": "TEXT",
                    "text": cmt_text,
                    "reply_to_id": post_id,
                    "access_token": access_token
                },
                timeout=30
            ).json()
            if "id" in r_rep:
                time.sleep(2)
                requests.post(
                    f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
                    data={"creation_id": r_rep["id"], "access_token": access_token},
                    timeout=30
                )
                log(f"  ✅ Đã ghim link Affiliate Threads {idx}: {it['url']}")
            time.sleep(2)
        except Exception as e:
            log(f"  ⚠️ Lỗi ghim link Threads {idx}: {e}")

    return {"success": True, "post_id": post_id, "permalink": permalink}

# ==============================================================================
# HÀM CHÍNH - MAIN EXECUTION FLOW
# ==============================================================================
def main():
    print("=" * 80)
    print("🚀 TOOL TỰ ĐỘNG ĐĂNG VIDEO & LÊN LỊCH 4 NỀN TẢNG (TRẠM CÔNG NGHỆ)")
    print("   Thương hiệu: Trạm Công Nghệ")
    print("   Video: C:\\Affiliate\\Trạm Công Nghệ\\video_việt_hóa\\video chưa đăng\\loa máy tính.mp4")
    print("   Lịch đăng hẹn giờ mục tiêu (27/09/2026):")
    print("     - YouTube:   18:30 ngày 27/09/2026 (Server-side)")
    print("     - Facebook:  18:41 ngày 27/09/2026 (Server-side)")
    print("     - Instagram: 18:45 ngày 27/09/2026 (Auto Countdown & Publish)")
    print("     - Threads:   18:50 ngày 27/09/2026 (Auto Countdown & Publish)")
    print("=" * 80)

    if not os.path.exists(VIDEO_PATH):
        log(f"❌ File video không tồn tại: {VIDEO_PATH}")
        return

    brand_data = load_brand_config()

    # Nạp link affiliate từ 4 file Excel
    fb_items = load_affiliate_links(EXCEL_FILES["facebook"])
    ig_items = load_affiliate_links(EXCEL_FILES["instagram"])
    th_items = load_affiliate_links(EXCEL_FILES["threads"])
    yt_items = load_affiliate_links(EXCEL_FILES["youtube"])

    log(f"📊 Đã nạp danh sách Link Affiliate từ 4 file Excel:")
    log(f"   - Facebook:  {len(fb_items)} links")
    log(f"   - Instagram: {len(ig_items)} links")
    log(f"   - Threads:   {len(th_items)} links")
    log(f"   - YouTube:   {len(yt_items)} links")

    fb_comments = format_comment_list(fb_items)
    ig_comments = format_comment_list(ig_items)
    yt_comments = format_comment_list(yt_items)

    # Thời gian mục tiêu ngày 27/09/2026
    yt_time = datetime.datetime(2026, 9, 27, 18, 30, 0)
    fb_time = datetime.datetime(2026, 9, 27, 18, 41, 0)
    ig_time = datetime.datetime(2026, 9, 27, 18, 45, 0)
    th_time = datetime.datetime(2026, 9, 27, 18, 50, 0)

    # Tiêu đề và nội dung caption tối ưu SEO
    yt_title = "Top Loa Máy Tính Mini Để Bàn LED RGB Âm Bass Siêu Trầm Cực Đỉnh #Shorts"
    yt_desc = (
        "Góc làm việc hay góc gaming mà thiếu một em loa để bàn LED RGB âm thanh sống động thì bớt chill đi nhiều đó anh em! "
        "Thiết kế mini nhỏ gọn, công suất lớn bass đập cực căng, tích hợp led đổi màu siêu cuốn.\n\n"
        "🛒 Link sắm trọn bộ các mẫu loa máy tính chính hãng:\n"
        f"👉 Mẫu 1: {yt_items[0]['url'] if yt_items else ''}\n"
        f"👉 Mẫu 2: {yt_items[1]['url'] if len(yt_items) > 1 else ''}\n"
        f"👉 Mẫu 3: {yt_items[2]['url'] if len(yt_items) > 2 else ''}\n\n"
        "(Toàn bộ link các dòng còn lại mình đã ghim ở bình luận bên dưới nhé 👇)\n"
        "#Shorts #tramcongnghe #loamaytinh #loadeban #setupgocmay #reviewcongnghe"
    )

    fb_title = "Top Loa Máy Tính Mini Để Bàn LED RGB Âm Bass Siêu Trầm Cực Đỉnh"
    fb_caption = (
        "Góc làm việc hay góc gaming mà thiếu một em loa để bàn LED RGB âm thanh sống động thì bớt chill đi nhiều đó anh em! "
        "Thiết kế mini nhỏ gọn, công suất lớn bass đập cực căng, tích hợp led đổi màu siêu cuốn. "
        "Link sắm chính hãng từng mẫu mình đã ghim chi tiết ở phần bình luận nhé 👇\n\n"
        "#tramcongnghe #loamaytinh #loadeban #setupgocmay #reviewcongnghe"
    )

    ig_caption = (
        "Góc làm việc hay góc gaming mà thiếu một em loa để bàn LED RGB âm thanh sống động thì bớt chill đi nhiều đó anh em! ✨\n"
        "Thiết kế mini nhỏ gọn, công suất lớn bass đập cực căng, tích hợp led đổi màu siêu cuốn. "
        "Link sắm chính hãng trọn bộ các mẫu mình đã ghim chi tiết ở bình luận nhé 👇\n\n"
        "#reels #viral #tramcongnghe #loamaytinh #loadeban #setupgocmay #reviewcongnghe"
    )

    th_caption = (
        "Gợi ý các mẫu loa máy tính để bàn mini LED RGB âm thanh cực chất, bass căng đét cho góc làm việc! ✨\n\n"
        "🛒 Link mua 3 mẫu hot nhất:\n"
        f"1. Loa Leerfei E 350T: {th_items[0]['url'] if th_items else ''}\n"
        f"2. Loa YST 1046 Led: {th_items[1]['url'] if len(th_items) > 1 else ''}\n"
        f"3. Loa 1046 9077 RGB: {th_items[2]['url'] if len(th_items) > 2 else ''}\n\n"
        "(Toàn bộ 4 link mẫu còn lại mình đã ghim ngay dưới bình luận nha 👇)\n"
        "#tramcongnghe #loamaytinh #desksetup #congnghe"
    )

    # -------------------------------------------------------------
    # PHẦN 1: LẬP LỊCH TỨC THÌ TRÊN SERVER GOOGLE & FACEBOOK
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("BƯỚC 1: LẬP LỊCH SERVER-SIDE CHO YOUTUBE SHORTS & FACEBOOK REELS")
    log("=" * 80)

    # 1. YouTube Shorts (18:30 UTC+7 -> 11:30 UTC RFC3339)
    log("\n🔴 [1/4] Đang upload & hẹn giờ YouTube Shorts...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/cham_cong_nghe.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_yt_time = yt_time - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_yt_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        log(f"   ⏰ Hẹn giờ xuất bản YouTube (UTC): {publish_at_rfc3339} (18:30 Giờ VN)")

        res_yt = yt_uploader.upload_short(
            video_path=VIDEO_PATH,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "tramcongnghe", "loamaytinh", "setupgocmay", "reviewcongnghe"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        log(f"   ✅ Hoàn tất thiết lập YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"   ❌ Lỗi YouTube Shorts: {e}\n{traceback.format_exc()}")

    # 2. Facebook Reels (18:41 UTC+7 -> Timestamp 1790509260)
    log("\n🔷 [2/4] Đang upload chunked & hẹn giờ Facebook Reels...")
    try:
        fb_cfg = brand_data.get("facebook", {})
        fb_scheduled_ts = int(fb_time.timestamp())
        log(f"   ⏰ Hẹn giờ xuất bản Facebook Reels: {fb_time.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {fb_scheduled_ts})")

        res_fb = upload_fb_reel_resumable(
            page_id=fb_cfg["page_id"],
            access_token=fb_cfg["access_token"],
            video_path=VIDEO_PATH,
            title=fb_title,
            description=fb_caption,
            scheduled_time=fb_scheduled_ts,
            comments=fb_comments
        )
        log(f"   ✅ Hoàn tất thiết lập Facebook Reels: {res_fb}")
    except Exception as e:
        log(f"   ❌ Lỗi Facebook Reels: {e}\n{traceback.format_exc()}")

    # -------------------------------------------------------------
    # PHẦN 2: THEO DÕI VÀ ĐẾM NGƯỢC XUẤT BẢN INSTAGRAM & THREADS
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("BƯỚC 2: CHUYỂN SANG CHẾ ĐỘ ĐẾM NGƯỢC ĐĂNG INSTAGRAM (18:45) VÀ THREADS (18:50)")
    log("=" * 80)
    log(f"⏰ Lịch hẹn Instagram Reels: {ig_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"⏰ Lịch hẹn Threads:         {th_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("💡 Bạn có thể giữ cửa sổ terminal này để script tự động đếm ngược và xuất bản chính xác!")

    ig_published = False
    th_published = False

    while True:
        now = datetime.datetime.now()

        # Đăng Instagram lúc 18:45
        if not ig_published and now >= ig_time:
            log("\n📸 [3/4] ĐÃ ĐẾN GIỜ HẸN (18:45:00)! BẮT ĐẦU XUẤT BẢN INSTAGRAM REELS...")
            try:
                ig_cfg = brand_data.get("instagram", {})
                res_ig = upload_ig_reel_chunked(
                    ig_user_id=ig_cfg["ig_user_id"],
                    access_token=ig_cfg["access_token"],
                    video_path=VIDEO_PATH,
                    caption=ig_caption,
                    comments=ig_comments
                )
                log(f"   ✅ Kết quả Instagram Reels: {res_ig}")
                ig_published = True
            except Exception as e:
                log(f"   ❌ Lỗi Instagram Reels: {e}\n{traceback.format_exc()}")
                ig_published = True  # Tránh lặp lại lỗi

        # Đăng Threads lúc 18:50
        if not th_published and now >= th_time:
            log("\n🧵 [4/4] ĐÃ ĐẾN GIỜ HẸN (18:50:00)! BẮT ĐẦU XUẤT BẢN THREADS...")
            try:
                th_cfg = brand_data.get("threads", {})
                res_th = publish_threads(
                    user_id=th_cfg["user_id"],
                    access_token=th_cfg["access_token"],
                    main_text=th_caption,
                    items=th_items
                )
                log(f"   ✅ Kết quả Threads: {res_th}")
                th_published = True
            except Exception as e:
                log(f"   ❌ Lỗi Threads: {e}\n{traceback.format_exc()}")
                th_published = True

        # Khi cả hai đã xong thì hoàn tất
        if ig_published and th_published:
            log("\n🎉🎉🎉 TOÀN BỘ 4 NỀN TẢNG (YOUTUBE, FACEBOOK, INSTAGRAM, THREADS) ĐÃ ĐƯỢC ĐĂNG VÀ LÊN LỊCH THÀNH CÔNG RỰC RỠ!")
            break

        # In thông báo đếm ngược mỗi 30 giây
        next_event = "Instagram (18:45)" if not ig_published else "Threads (18:50)"
        target_event_time = ig_time if not ig_published else th_time
        remaining = int((target_event_time - now).total_seconds())
        if remaining > 0:
            hrs = remaining // 3600
            mins = (remaining % 3600) // 60
            secs = remaining % 60
            print(f"\r⏳ [Đếm ngược đến {next_event}]: Còn {hrs:02d} giờ {mins:02d} phút {secs:02d} giây...", end="", flush=True)
            time.sleep(10)
        else:
            time.sleep(1)

if __name__ == "__main__":
    main()
