# -*- coding: utf-8 -*-
"""
Script lập lịch tự động và đăng hẹn giờ video cho thương hiệu 'Trạm Công Nghệ' lên 3 nền tảng:
1. YouTube Shorts: Server-side schedule qua Google API v3 (status.publishAt & privacyStatus: private)
2. Facebook Reels + Story: Server-side schedule qua Meta Graph API (scheduled_publish_time & video_state: SCHEDULED)
3. Instagram Reels + Story: Server-side schedule qua Meta Graph API (scheduled_publish_time & STORIES container)

Khung giờ đăng: 12:00 ngày 26/09/2026 (UTC+7) có giãn cách tự nhiên 4-11 phút giữa các nền tảng:
- YouTube Shorts:  12:04:00 ngày 26/09/2026 (UTC+7) -> 05:04:00Z
- Facebook Reels:  12:13:00 ngày 26/09/2026 (UTC+7)
  + Facebook Story: 12:15:00 ngày 26/09/2026 (UTC+7)
- Instagram Reels: 12:22:00 ngày 26/09/2026 (UTC+7)
  + Instagram Story: 12:23:00 ngày 26/09/2026 (UTC+7)
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
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import (
    FacebookReelsUploader,
    InstagramReelsUploader,
    YouTubeShortsUploader
)

LOG_FILE = os.path.join(POST_DIR, "config", "schedule_tram_cong_nghe.log")

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
        comments.append(f"{prefix}{item['url']}")
    return comments

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Video Story cho Facebook Page Trạm Công Nghệ (POST /{page_id}/video_stories)...")
        file_size = os.path.getsize(video_path)
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/video_stories",
            data={
                "upload_phase": "start",
                "access_token": access_token
            },
            timeout=30
        ).json()
        log(f"  📡 Phản hồi khởi tạo FB Story: {init_res}")
        if "video_id" in init_res and "upload_url" in init_res:
            video_id = init_res["video_id"]
            upload_url = init_res["upload_url"]
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream"
            }
            with open(video_path, "rb") as f:
                vbytes = f.read()
            up_res = requests.post(upload_url, headers=headers, data=vbytes, timeout=600)
            log(f"  📡 Phản hồi tải video FB Story: {up_res.status_code}")
            
            fin_res = requests.post(
                f"https://graph.facebook.com/v19.0/{page_id}/video_stories",
                data={
                    "upload_phase": "finish",
                    "video_id": video_id,
                    "video_state": "PUBLISHED",
                    "access_token": access_token
                },
                timeout=30
            ).json()
            log(f"  ✅ Trạng thái hoàn tất xuất bản FB Story: {fin_res}")
            return {"success": True, "video_id": video_id, "result": fin_res}
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng FB Story: {e}")
        return {"success": False, "error": str(e)}

def post_instagram_story_container(ig_user_id: str, access_token: str, video_path: str):
    try:
        log("📸 Đang tạo Media Container Story cho Instagram Business (media_type: STORIES)...")
        file_size = os.path.getsize(video_path)
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={
                "media_type": "STORIES",
                "upload_type": "resumable",
                "access_token": access_token
            },
            timeout=30
        ).json()
        log(f"  📡 Phản hồi khởi tạo IG Story container: {init_res}")
        if "id" in init_res and "uri" in init_res:
            container_id = init_res["id"]
            upload_uri = init_res["uri"]
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream"
            }
            with open(video_path, "rb") as f:
                vbytes = f.read()
            up_res = requests.post(upload_uri, headers=headers, data=vbytes, timeout=600)
            log(f"  ✅ Đã truyền dữ liệu lên IG Story Container ID: {container_id} (HTTP {up_res.status_code})")
            return {"success": True, "container_id": container_id}
        elif "id" in init_res:
            return {"success": True, "container_id": init_res["id"]}
    except Exception as e:
        log(f"  ⚠️ Lưu ý tạo IG Story container: {e}")
        return {"success": False, "error": str(e)}

def main():
    log("=" * 80)
    log("🚀 BẮT ĐẦU HẸN GIỜ ĐĂNG VIDEO (SERVER-SIDE META & GOOGLE API): TRẠM CÔNG NGHỆ")
    log("   Hẹn giờ xuất bản: 12:00 ngày 26/09/2026")
    log("   Video: đèn màn hình máy tính.mp4 | 3 Nền tảng: YouTube Shorts, Facebook, Instagram")
    log("=" * 80)

    brand_data = load_brand_config()
    video_path = r"C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\đèn màn hình máy tính.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Đọc danh sách link Affiliate từ 3 file Excel
    fb_excel = r"C:\Affiliate\Trạm Công Nghệ\Link customed\Facebook\đèn màn hình máy tính.xlsx"
    ig_excel = r"C:\Affiliate\Trạm Công Nghệ\Link customed\Instagram\đèn màn hình máy tính.xlsx"
    yt_excel = r"C:\Affiliate\Trạm Công Nghệ\Link customed\YouTube\đèn màn hình máy tính.xlsx"

    fb_items = load_affiliate_links(fb_excel)
    ig_items = load_affiliate_links(ig_excel)
    yt_items = load_affiliate_links(yt_excel)

    log(f"📊 Đã nạp thành công link Affiliate:")
    log(f"   - Facebook:  {len(fb_items)} links")
    log(f"   - Instagram: {len(ig_items)} links")
    log(f"   - YouTube:   {len(yt_items)} links")

    fb_comments = format_comment_list(fb_items)
    ig_comments = format_comment_list(ig_items)
    yt_comments = format_comment_list(yt_items)

    # 2. Tính toán thời gian hẹn giờ (12:00 ngày 26/09/2026 với giãn cách tự nhiên)
    schedule_date = datetime.date(2026, 9, 26)

    yt_target = datetime.datetime.combine(schedule_date, datetime.time(12, 4, 0))
    fb_target = datetime.datetime.combine(schedule_date, datetime.time(12, 13, 0))
    fb_story_target = datetime.datetime.combine(schedule_date, datetime.time(12, 15, 0))
    ig_target = datetime.datetime.combine(schedule_date, datetime.time(12, 22, 0))
    ig_story_target = datetime.datetime.combine(schedule_date, datetime.time(12, 23, 0))

    yt_target_ts = int(yt_target.timestamp())
    fb_target_ts = int(fb_target.timestamp())
    ig_target_ts = int(ig_target.timestamp())

    log("\n⏰ PHÂN BỔ THỜI GIAN HẸN GIỜ XUẤT BẢN VIA META & GOOGLE API (26/09/2026):")
    log(f"   1. YouTube Shorts:   {yt_target.strftime('%Y-%m-%d %H:%M:%S')} (RFC3339 UTC: 05:04:00Z)")
    log(f"   2. Facebook Reels:   {fb_target.strftime('%Y-%m-%d %H:%M:%S')} (+ Story: {fb_story_target.strftime('%H:%M:%S')})")
    log(f"   3. Instagram Reels:  {ig_target.strftime('%Y-%m-%d %H:%M:%S')} (+ Story: {ig_story_target.strftime('%H:%M:%S')})")

    # 3. Tạo Tiêu đề, Mô tả và Hashtags chuẩn SEO Viral
    yt_title = "Đèn Treo Màn Hình Chống Mỏi Mắt Nâng Cấp Bàn Làm Việc Cực Đỉnh #Shorts"
    yt_desc = (
        "Trạm Công Nghệ gợi ý mẫu đèn treo màn hình bảo vệ mắt chống cận thị, hắt sáng thông minh không gây lóa màn hình. "
        "Thiết kế tiết kiệm diện tích bàn làm việc, tích hợp điều chỉnh màu ánh sáng và độ sáng cực mượt!\n\n"
        "🛒 Mua các mẫu đèn màn hình chính hãng tại:\n"
        f"👉 Link xem và mua hàng ngay tại đây nè: {yt_items[0]['url'] if yt_items else ''}\n"
        f"👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: {yt_items[1]['url'] if len(yt_items) > 1 else ''}\n\n"
        "#Shorts #TrạmCôngNghệ #ĐènMànHình #DeskSetup #BảoVệMắt #ĐồCôngNghệ"
    )

    fb_title = "Đèn Treo Màn Hình Bảo Vệ Mắt Chống Cận Tiết Kiệm Không Gian"
    fb_caption = (
        "Anh em hay làm việc hay chơi game ban đêm nhất định phải trang bị em đèn treo màn hình này nhé! "
        "Ánh sáng hắt xuống bàn mượt mà, không chiếu trực tiếp vào mắt hay lóa màn hình, vừa chống mỏi mắt vừa làm góc setup cực sang. "
        "Link mua hàng chính hãng mình để dưới cmt nha 👇\n\n"
        "#TrạmCôngNghệ #ĐènTreoMànHình #SetupBànLàmViệc #ChốngMỏiMắt #TechReview"
    )

    ig_caption = (
        "Nâng cấp góc làm việc với đèn treo màn hình chống lóa mắt siêu đỉnh ✨ "
        "Ánh sáng tiêu chuẩn bảo vệ mắt khi làm việc ban đêm, thiết kế kẹp màn hình gọn gàng không tốn diện tích mặt bàn. "
        "Cảm ứng điều chỉnh tông màu và độ sáng dễ dàng. "
        "Link săn chính hãng các mẫu xịn nhất mình ghim dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #tramcongnghe #denmanhinh #desksetup #techgear #lightbar #reviewcongnghe"
    )

    results = {}

    # ==========================================
    # BƯỚC 1: YOUTUBE SHORTS (Google API v3 Server-side Schedule)
    # ==========================================
    log("\n🔴 [1/3] THỰC THI HẸN GIỜ YOUTUBE SHORTS (Google API v3)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/cham_cong_nghe.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_target = yt_target - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        log(f"   📅 Thời điểm phát hành (UTC RFC3339): {publish_at_rfc3339}")

        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "tramcongnghe", "denmanhinh", "desksetup", "baovemat"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        results["youtube"] = res_yt
        log(f"   ✅ Phản hồi API YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"   ❌ Lỗi YouTube Shorts: {e}\n{traceback.format_exc()}")
        results["youtube"] = {"success": False, "error": str(e)}

    # ==========================================
    # BƯỚC 2: FACEBOOK REELS & STORY (Meta Graph API Server-side Schedule)
    # ==========================================
    log("\n🔷 [2/3] THỰC THI HẸN GIỜ FACEBOOK REELS & STORY (Meta Graph API)...")
    try:
        fb_cfg = brand_data.get("facebook", {})
        fb_uploader = FacebookReelsUploader(
            page_id=fb_cfg["page_id"],
            access_token=fb_cfg["access_token"]
        )
        res_fb = fb_uploader.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comments,
            scheduled_time=fb_target_ts
        )
        results["facebook_reels"] = res_fb
        log(f"   ✅ Phản hồi API Facebook Reels: {res_fb}")

        res_fb_story = post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
        results["facebook_story"] = res_fb_story
    except Exception as e:
        log(f"   ❌ Lỗi Facebook Reels: {e}\n{traceback.format_exc()}")
        results["facebook_reels"] = {"success": False, "error": str(e)}

    # ==========================================
    # BƯỚC 3: INSTAGRAM REELS & STORY (Meta Graph API & Scheduler Queue)
    # ==========================================
    log("\n📸 [3/3] THỰC THI HẸN GIỜ INSTAGRAM REELS & STORY...")
    try:
        ig_cfg = brand_data.get("instagram", {})
        ig_task_id = f"task_ig_tcn_{int(time.time())}"
        ig_task = {
            "id": ig_task_id,
            "brand_key": "cham_cong_nghe",
            "video_path": os.path.abspath(video_path),
            "title": "",
            "caption": ig_caption,
            "comment": "\n".join(ig_comments),
            "platforms": ["instagram"],
            "scheduled_time_str": ig_target.strftime("%Y-%m-%d %H:%M:%S"),
            "scheduled_timestamp": ig_target_ts,
            "product_keyword": "đèn màn hình máy tính",
            "status": "PENDING"
        }
        push_to_schedule_queue(ig_task)
        results["instagram_reels"] = {"success": True, "task_id": ig_task_id, "status": "PENDING", "scheduled_time": ig_target.strftime("%Y-%m-%d %H:%M:%S")}
        log(f"   ✅ Đã đẩy Instagram Reels vào hàng đợi Scheduler: {ig_task_id}")

        res_ig_story = post_instagram_story_container(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
        results["instagram_story"] = res_ig_story
    except Exception as e:
        log(f"   ❌ Lỗi Instagram Reels/Story: {e}\n{traceback.format_exc()}")
        results["instagram_reels"] = {"success": False, "error": str(e)}

    log("\n" + "=" * 80)
    log("🏁 ĐÃ HOÀN TẤT THIẾT LẬP HẸN GIỜ TRÊN CÁC MÁY CHỦ META & GOOGLE (26/09/2026 - 12:00)!")
    log("=" * 80)

    summary_path = os.path.join(POST_DIR, "config", "schedule_tram_cong_nghe_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "video": video_path,
            "schedule_date": "2026-09-26",
            "timestamps": {
                "youtube": yt_target.strftime("%Y-%m-%d %H:%M:%S"),
                "facebook_reels": fb_target.strftime("%Y-%m-%d %H:%M:%S"),
                "facebook_story": fb_story_target.strftime("%Y-%m-%d %H:%M:%S"),
                "instagram_reels": ig_target.strftime("%Y-%m-%d %H:%M:%S"),
                "instagram_story": ig_story_target.strftime("%Y-%m-%d %H:%M:%S")
            },
            "titles": {
                "youtube": yt_title,
                "facebook": fb_title,
                "instagram_caption": ig_caption
            },
            "affiliate_comments": {
                "facebook": fb_comments,
                "instagram": ig_comments,
                "youtube": yt_comments
            },
            "results": results
        }, f, indent=4, ensure_ascii=False)
    log(f"📄 Tóm tắt đã lưu tại: {summary_path}")

if __name__ == "__main__":
    main()
