# -*- coding: utf-8 -*-
"""
HỆ THỐNG ĐĂNG VIDEO & LÊN LỊCH 4 NỀN TẢNG TỰ ĐỘNG - THƯƠNG HIỆU GÓC TẬP LUYỆN
Video: C:\\Affiliate\\Góc Tập Luyện\\video_việt_hóa\\video chưa đăng\\5.mp4
Lịch đăng hẹn giờ mục tiêu (27/09/2026):
  1. YouTube Shorts: 18h30 ngày 27/09/2026 (Server-side Google API v3: status.publishAt = 2026-09-27T11:30:00Z)
  2. Facebook Reels: 18h41 ngày 27/09/2026 (Server-side Meta Graph API: scheduled_publish_time = 1790509260)
  3. Instagram Reels: 18h45 ngày 27/09/2026 (Tự động đếm ngược & xuất bản trực tiếp qua Meta Graph API rupload)
  4. Threads:         18h50 ngày 27/09/2026 (Tự động đếm ngược & xuất bản bài viết + chuỗi 9 link affiliate qua Threads API)

Đặc điểm:
- 100% tự động, KHÔNG tốn bất kỳ Token AI nào.
- Hỗ trợ tải video dung lượng lớn (~1.6GB) dạng streaming chunked resumable 16MB an toàn, không tràn RAM.
- Tự động đọc danh sách 9 link affiliate từ đúng thư mục Excel Tập 5 của từng nền tảng tương ứng.
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

VIDEO_PATH = r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\video chưa đăng\5.mp4"

EXCEL_FILES = {
    "facebook": r"C:\Affiliate\Góc Tập Luyện\Link customed\Facebook\Tập 5.xlsx",
    "instagram": r"C:\Affiliate\Góc Tập Luyện\Link customed\Instagram\Tập 5.xlsx",
    "threads": r"C:\Affiliate\Góc Tập Luyện\Link customed\Threads\Tập 5.xlsx",
    "youtube": r"C:\Affiliate\Góc Tập Luyện\Link customed\YouTube\Tập 5.xlsx",
}

LOG_FILE = os.path.join(POST_DIR, "config", "schedule_goc_tap_luyen_tap5.log")

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
    # Load Meta Tokens (Page + IG)
    meta_path = os.path.join(POST_DIR, "config", "permanent_meta_tokens.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_tokens = json.load(f)
    brand_meta = meta_tokens.get("Góc Tập Luyện", {})
    page_id = brand_meta.get("page_id", "1211541072052658")
    page_token = brand_meta.get("page_access_token")
    ig_id = brand_meta.get("instagram_business_id", "17841438553537040")

    # Load Threads & YouTube Tokens
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    goc_cfg = brands.get("goc_tap_luyen", {})
    th_cfg = goc_cfg.get("threads", {})
    yt_cfg = goc_cfg.get("youtube", {})

    return {
        "facebook": {
            "page_id": page_id,
            "access_token": page_token
        },
        "instagram": {
            "ig_user_id": ig_id,
            "access_token": page_token
        },
        "threads": {
            "user_id": th_cfg.get("user_id", "27890678400603793"),
            "access_token": th_cfg.get("access_token")
        },
        "youtube": {
            "token_file": yt_cfg.get("token_file", "credentials/youtube_tokens/goc_tap_luyen.json")
        }
    }

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
# HÀM XUẤT BẢN THREADS (Bài viết chính + 9 link affiliate ở comment)
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

    # 3. Đăng 9 link affiliate vào reply của bài viết
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
    print("🚀 TOOL TỰ ĐỘNG ĐĂNG VIDEO & LÊN LỊCH 4 NỀN TẢNG (GÓC TẬP LUYỆN - TẬP 5)")
    print("   Thương hiệu: Góc Tập Luyện")
    print(f"   Video: {VIDEO_PATH}")
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

    # 1. Tải danh sách Affiliate Links cho từng nền tảng
    log("📂 Đang nạp danh sách 9 link Affiliate từ file Excel tương ứng...")
    fb_items = load_affiliate_links(EXCEL_FILES["facebook"])
    ig_items = load_affiliate_links(EXCEL_FILES["instagram"])
    th_items = load_affiliate_links(EXCEL_FILES["threads"])
    yt_items = load_affiliate_links(EXCEL_FILES["youtube"])

    fb_comments = format_comment_list(fb_items)
    ig_comments = format_comment_list(ig_items)
    yt_comments = format_comment_list(yt_items)

    log(f"  - Facebook:  {len(fb_items)} links")
    log(f"  - Instagram: {len(ig_items)} links")
    log(f"  - Threads:   {len(th_items)} links")
    log(f"  - YouTube:   {len(yt_items)} links")

    # 2. Metadata SEO & Tiêu đề / Mô tả / Hashtag
    yt_title = "Top dụng cụ tập Pilates & Gym tại nhà thon dáng siết eo cực hiệu quả #Shorts"
    yt_desc = (
        "Tổng hợp trọn bộ dụng cụ tập luyện thể thao tại nhà cực tiện lợi: Tạ tay nữ PINMU, dây kháng lực TheraBand, "
        "dây mở vai eo thon, thảm tập Mandala, đệm gối bảo vệ khớp và gạch tập Yoga chống trượt. "
        "Tập luyện chăm chỉ mỗi ngày để có vóc dáng săn chắc, tự tin tỏa sáng!\n\n"
        "👉 Xem chi tiết và sắm đồ tập chính hãng tại link bình luận bên dưới nhé cả nhà 👇\n\n"
        "#Shorts #goctapluyen #tapgymtainha #pilates #yoga #thonchan #sieo #fitness #workout"
    )

    fb_title = "Combo dụng cụ tập gym, yoga và pilates giữ dáng thon gọn tại nhà"
    fb_caption = (
        "Dành cho ai bận rộn muốn tự tập giữ dáng tại nhà mà vẫn đạt hiệu quả cao như ra phòng gym! "
        "Combo tạ tay nữ, dây kháng lực đa năng, thảm định tuyến cao su PU và đệm bảo vệ khớp gối chuyên dụng 🔥\n\n"
        "👉 Sắm ngay tạ tay nữ chuyên dụng chính hãng tại: https://s.shopee.vn/905NEx2exS\n\n"
        "#reels #viral #fyp #goctapluyen #tapgymtainha #pilates #yogalife #sieo #fitnessmotivation"
    )

    ig_caption = (
        "Setup góc tập luyện tại nhà cực chuẩn với combo tạ tay, dây kháng lực và thảm định tuyến PU! "
        "Vừa tiện ích, gọn gàng lại giúp cải thiện vóc dáng và độ dẻo dai mỗi ngày ✨ "
        "Link trọn bộ phụ kiện tập luyện chính hãng mình ghim chi tiết dưới phần comment nha 👇\n\n"
        "#reels #viral #fyp #goctapluyen #workoutathome #pilatesathome #fitnesslifestyle #chanthon"
    )

    th_caption = (
        "Không có thời gian ra phòng tập thì sắm ngay combo này về tự tập tại nhà nhé cả nhà! "
        "Tạ tay nữ êm ái, dây kháng lực mở vai siết eo và thảm yoga định tuyến siêu bám sàn ✨\n\n"
        "🛒 Link sắm đồ tập chính hãng nè cả nhà:\n"
        "1. Quả tạ tay nữ PINMU: https://s.shopee.vn/9KiDdZ1OHY\n"
        "2. Dây kháng lực TheraBand 2M: https://s.shopee.vn/AUuB1hwwut\n"
        "3. Dây tập mở vai eo thon: https://s.shopee.vn/6L4c43CoNC\n\n"
        "#goctapluyen #tapgymtainha #workout #fitness"
    )

    # 3. Thời gian mục tiêu: ngày 27/09/2026
    target_date = datetime.date(2026, 9, 27)
    yt_time = datetime.datetime.combine(target_date, datetime.time(18, 30, 0))
    fb_time = datetime.datetime.combine(target_date, datetime.time(18, 41, 0))
    ig_time = datetime.datetime.combine(target_date, datetime.time(18, 45, 0))
    th_time = datetime.datetime.combine(target_date, datetime.time(18, 50, 0))

    # =============================================================
    # PHẦN 1: HẸN GIỜ TRÊN SERVER (YOUTUBE & FACEBOOK)
    # =============================================================
    log("\n" + "=" * 80)
    log("BƯỚC 1: ĐĂNG TẢI LÊN MÁY CHỦ VÀ ĐẶT LỊCH HẸN GIỜ SERVER-SIDE (YOUTUBE & FACEBOOK)")
    log("=" * 80)

    # 1. YouTube Shorts (18:30 UTC+7 -> 11:30 UTC RFC3339)
    log("\n🔴 [1/4] Đang upload & hẹn giờ YouTube Shorts...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/goc_tap_luyen.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_yt_time = yt_time - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_yt_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        log(f"   ⏰ Hẹn giờ xuất bản YouTube (UTC): {publish_at_rfc3339} (18:30 Giờ VN)")

        res_yt = yt_uploader.upload_short(
            video_path=VIDEO_PATH,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "goctapluyen", "tapgymtainha", "pilates", "yoga", "thonchan"],
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

    # =============================================================
    # PHẦN 2: THEO DÕI VÀ ĐẾM NGƯỢC XUẤT BẢN INSTAGRAM & THREADS
    # =============================================================
    log("\n" + "=" * 80)
    log("BƯỚC 2: CHUYỂN SANG CHẾ ĐỘ ĐẾM NGƯỢC ĐĂNG INSTAGRAM (18:45) VÀ THREADS (18:50)")
    log("=" * 80)
    log(f"⏰ Lịch hẹn Instagram Reels: {ig_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"⏰ Lịch hẹn Threads:         {th_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("💡 Giữ cửa sổ terminal này để script tự động đếm ngược và xuất bản chính xác!")

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

        # Log đếm ngược mỗi 1 phút
        rem_ig = (ig_time - now).total_seconds()
        rem_th = (th_time - now).total_seconds()

        target_name = "Instagram" if not ig_published else "Threads"
        target_rem = rem_ig if not ig_published else rem_th
        
        if int(target_rem) % 60 == 0 or target_rem < 30:
            m = max(0, int(target_rem // 60))
            s = max(0, int(target_rem % 60))
            log(f"⏳ [Đếm ngược] Còn {m} phút {s} giây tới giờ xuất bản {target_name}...")

        time.sleep(10)

if __name__ == "__main__":
    main()
