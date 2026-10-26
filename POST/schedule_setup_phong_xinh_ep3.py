# -*- coding: utf-8 -*-
"""
Schedule Runner - Tự động lập lịch và đăng hẹn giờ cho thương hiệu "Setup Phòng Xinh" (Tập 3)
Video: C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\3.mp4
3 Nền tảng:
- YouTube Shorts: Server-side schedule Google API v3 (12:04:00 ngày 26/09/2026)
- Facebook Reels + Story: Server-side schedule Meta Graph API (12:13:00 & 12:14:00 ngày 26/09/2026)
- Instagram Reels + Story: Scheduler Queue + Media Container Story (12:21:00 & 12:22:00 ngày 26/09/2026)
(Đã loại trừ Threads theo yêu cầu của người dùng)
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

LOG_FILE = os.path.join(POST_DIR, "config", "scheduler_setup_phong_xinh.log")
QUEUE_FILE = os.path.join(POST_DIR, "config", "schedule_queue.json")

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_config():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    return brands.get("setup_phong_xinh", {})

def load_affiliate_links(excel_path: str):
    """Đọc danh sách link rút gọn từ file Excel đã custom"""
    if not os.path.exists(excel_path):
        log(f"❌ Không tìm thấy file Excel: {excel_path}")
        return []
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = rows[0]
    link_idx = 2  # default column 'Link Affiliate (Rút gọn)'
    name_idx = 1  # default column 'Tên sản phẩm'
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
    """Format danh sách comment theo mẫu luân phiên kích thích click"""
    templates = [
        "Link sản phẩm ở đây: ",
        "Link xem và mua hàng ngay tại đây nè: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: ",
        "Link sản phẩm ở đây cho ai cần nha: ",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: "
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
        comments.append(f"{prefix}{item['name']}: {item['url']}" if item.get('name') else f"{prefix}{item['url']}")
    return comments

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    """Đăng bổ sung Video Story cho Facebook Page"""
    try:
        log("📘 Đang tạo Story cho Facebook Page (endpoint: POST /{page_id}/video_stories)...")
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
            # Upload video binary stream
            with open(video_path, "rb") as f:
                vbytes = f.read()
            up_res = requests.post(upload_url, headers=headers, data=vbytes, timeout=600)
            log(f"  📡 Phản hồi tải video FB Story: {up_res.status_code}")
            
            # Finish Story
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
        else:
            return {"success": False, "error": init_res}
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng FB Story: {e}")
        return {"success": False, "error": str(e)}

def post_instagram_story_container(ig_user_id: str, access_token: str, video_path: str):
    """Khởi tạo media container dạng Story cho Instagram Business"""
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
        else:
            return {"success": False, "error": init_res}
    except Exception as e:
        log(f"  ⚠️ Lưu ý tạo IG Story container: {e}")
        return {"success": False, "error": str(e)}

def push_to_schedule_queue(task: dict):
    """Đẩy task vào file schedule_queue.json"""
    queue = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []
    
    # Kiểm tra xem task đã tồn tại chưa (tránh trùng)
    queue = [t for t in queue if t.get("id") != task.get("id")]
    queue.append(task)
    
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)
    log(f"📥 Đã thêm task vào hàng đợi Scheduler: {task['id']} ({task['scheduled_time_str']})")

def main():
    log("=" * 80)
    log("🚀 KHỞI ĐỘNG HỆ THỐNG LẬP LỊCH HẸN GIỜ ĐĂNG VIDEO: SETUP PHÒNG XINH (TẬP 3)")
    log("   Thời gian mục tiêu: 12:00 ngày 26/09/2026")
    log("   3 Nền tảng: YouTube Shorts, Facebook (Reels + Story), Instagram (Reels + Story)")
    log("   (Bỏ qua Threads theo yêu cầu)")
    log("=" * 80)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\3.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Đọc danh sách link Affiliate từ các file Excel Tập 3
    fb_excel = r"C:\Affiliate\Setup Phòng Xinh\Link customed\Facebook\Tập 3.xlsx"
    ig_excel = r"C:\Affiliate\Setup Phòng Xinh\Link customed\Instagram\Tập 3.xlsx"
    yt_excel = r"C:\Affiliate\Setup Phòng Xinh\Link customed\YouTube\Tập 3.xlsx"

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

    # 2. Tính toán lịch hẹn giờ giãn cách tự nhiên quanh mốc 12:00 ngày 26/09/2026
    target_date = datetime.date(2026, 9, 26)
    
    yt_target = datetime.datetime.combine(target_date, datetime.time(12, 4, 0))
    fb_target = datetime.datetime.combine(target_date, datetime.time(12, 13, 0))
    fb_story_target = datetime.datetime.combine(target_date, datetime.time(12, 14, 0))
    
    ig_story_target = datetime.datetime.combine(target_date, datetime.time(12, 21, 0))
    ig_target = datetime.datetime.combine(target_date, datetime.time(12, 22, 0))

    yt_target_ts = int(yt_target.timestamp())
    fb_target_ts = int(fb_target.timestamp())
    ig_target_ts = int(ig_target.timestamp())

    log("\n⏰ PHÂN BỔ THỜI GIAN HẸN GIỜ XUẤT BẢN (NGÀY 26/09/2026):")
    log(f"   1. YouTube Shorts:   {yt_target.strftime('%Y-%m-%d %H:%M:%S')} (Giãn cách tự nhiên 12:04)")
    log(f"   2. Facebook Reels:   {fb_target.strftime('%Y-%m-%d %H:%M:%S')} (+ Story: {fb_story_target.strftime('%H:%M:%S')})")
    log(f"   3. Instagram Reels:  {ig_target.strftime('%Y-%m-%d %H:%M:%S')} (+ Story: {ig_story_target.strftime('%H:%M:%S')})")

    # 3. Tạo Tiêu đề, Mô tả và Hashtags chuẩn SEO Viral
    # A. YouTube Shorts
    yt_title = "Top 3 món đồ decor phòng ngủ & nhà tắm cực tiện lợi ai cũng nên có #Shorts"
    yt_desc = (
        "Gợi ý những món đồ setup phòng ngủ, góc nhà tắm & phòng bếp siêu gọn gàng, tiện ích mà giá cực hạt dẻ cho mọi không gian sống!\n"
        "1. Kệ gắn tường chịu lực không cần khoan đục\n"
        "2. Tủ sấy quần áo gấp gọn khử khuẩn\n"
        "3. Đèn LED cảm biến chuyển động xoay 360 độ hút nam châm\n\n"
        "👇 Link sắm các sản phẩm chính hãng trong video:\n"
    )
    for idx, item in enumerate(yt_items[:5], 1):
        yt_desc += f"{idx}. {item['name'][:40]}: {item['url']}\n"
    yt_desc += "\n(Xem thêm đầy đủ link sản phẩm tại phần bình luận bên dưới nhé!)\n\n"
    yt_desc += "#Shorts #setupphongxinh #decorphong #kedantuong #tusayquanao #dencambien #lifestyle #tienich"

    # B. Facebook Reels
    fb_title = "Gợi ý combo decor & tiện ích phòng tắm, phòng ngủ siêu tiện lợi"
    fb_link1 = fb_items[0]['url'] if len(fb_items) > 0 else "https://shopee.vn"
    fb_link2 = fb_items[6]['url'] if len(fb_items) > 6 else (fb_items[1]['url'] if len(fb_items) > 1 else "")
    fb_link3 = fb_items[8]['url'] if len(fb_items) > 8 else (fb_items[2]['url'] if len(fb_items) > 2 else "")
    fb_caption = (
        "Phòng nhỏ hay nhà thuê mà ngại khoan tường thì lưu ngay combo tiện ích này nha mọi người! ✨\n"
        "Kệ dán tường chịu lực 10kg để đồ siêu gọn gàng, tủ sấy quần áo khô ráo thơm tho mùa ẩm, kèm chiếc đèn cảm biến chuyển động tự sáng thông minh cực chill.\n\n"
        "👉 Link sắm ngay sản phẩm chính hãng giá ưu đãi:\n"
        f"1. Kệ dán tường đa năng chịu lực: {fb_link1}\n"
        f"2. Tủ sấy quần áo khử khuẩn: {fb_link2}\n"
        f"3. Đèn led cảm biến xoay 360: {fb_link3}\n\n"
        "(Toàn bộ 13 link sản phẩm chi tiết mình để sẵn ở bình luận bên dưới nhé!)\n\n"
        "#reels #viral #fyp #setupphongxinh #decorphong #kedantuong #giadungtienich"
    )

    # C. Instagram Reels
    ig_caption = (
        "Góc phòng ngủ và nhà tắm gọn gàng, tiện nghi hơn bao giờ hết với combo decor thông minh này ✨\n"
        "Không cần khoan tường, lắp đặt 1 nốt nhạc: Kệ gắn tường chịu tải siêu khủng, tủ sấy quần áo đa năng khử khuẩn, và đèn led cảm biến từ tính xoay 360 tự bật sáng khi có người.\n\n"
        "👇 Chi tiết link mua sắm từng món chính hãng mình ghim ở phần comment bên dưới nha cả nhà!\n\n"
        "#reels #viral #setupphongxinh #decorroom #homedecor #setupdecor #phongdep #tienichgiadinh"
    )

    results = {}

    # ==========================================
    # BƯỚC 1: YOUTUBE SHORTS (Native API Scheduled)
    # ==========================================
    log("\n🔴 [1/3] THỰC THI HẸN GIỜ YOUTUBE SHORTS (Google API v3)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/setup_phong_xinh.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        # Local time UTC+7 -> convert to UTC
        utc_target = yt_target - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        log(f"   📅 Thời điểm phát hành (UTC RFC3339): {publish_at_rfc3339}")

        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "setupphongxinh", "decorphong", "kedantuong", "tusayquanao", "dencambien", "tienich"],
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
    # BƯỚC 2: FACEBOOK REELS & STORY (Meta Graph API)
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

        # Facebook Story
        res_fb_story = post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
        results["facebook_story"] = res_fb_story
    except Exception as e:
        log(f"   ❌ Lỗi Facebook Reels: {e}\n{traceback.format_exc()}")
        results["facebook_reels"] = {"success": False, "error": str(e)}

    # ==========================================
    # BƯỚC 3: INSTAGRAM REELS & STORY (Scheduler Queue & Stories container)
    # ==========================================
    log("\n📸 [3/3] ĐẨY TASK INSTAGRAM REELS & STORY VÀO SCHEDULER QUEUE...")
    try:
        ig_cfg = brand_data.get("instagram", {})
        ig_task_id = f"task_ig_spx_{int(time.time())}"
        ig_task = {
            "id": ig_task_id,
            "brand_key": "setup_phong_xinh",
            "video_path": os.path.abspath(video_path),
            "title": "",
            "caption": ig_caption,
            "comment": "\n".join(ig_comments),
            "platforms": ["instagram"],
            "scheduled_time_str": ig_target.strftime("%Y-%m-%d %H:%M:%S"),
            "scheduled_timestamp": ig_target_ts,
            "product_keyword": "Kệ dán tường, Tủ sấy quần áo & Đèn cảm biến (Tập 3)",
            "status": "PENDING"
        }
        push_to_schedule_queue(ig_task)
        results["instagram_reels"] = {"success": True, "task_id": ig_task_id, "status": "PENDING", "queue": QUEUE_FILE}

        # Tạo container Story
        res_ig_story = post_instagram_story_container(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
        results["instagram_story"] = res_ig_story
    except Exception as e:
        log(f"   ❌ Lỗi đưa Instagram vào Scheduler: {e}\n{traceback.format_exc()}")
        results["instagram_reels"] = {"success": False, "error": str(e)}

    log("\n" + "=" * 80)
    log("🏁 ĐÃ HOÀN TẤT THIẾT LẬP LỊCH HẸN GIỜ TRÊN 3 NỀN TẢNG (YOUTUBE, FACEBOOK, INSTAGRAM)!")
    log("=" * 80)

    # In kết quả tổng hợp
    summary_path = os.path.join(POST_DIR, "config", "schedule_setup_phong_xinh_ep3_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "brand": "Setup Phòng Xinh",
            "episode": "Tập 3",
            "video": video_path,
            "timestamps": {
                "youtube": yt_target.strftime("%Y-%m-%d %H:%M:%S"),
                "facebook_reels": fb_target.strftime("%Y-%m-%d %H:%M:%S"),
                "facebook_story": fb_story_target.strftime("%Y-%m-%d %H:%M:%S"),
                "instagram_story": ig_story_target.strftime("%Y-%m-%d %H:%M:%S"),
                "instagram_reels": ig_target.strftime("%Y-%m-%d %H:%M:%S")
            },
            "titles": {
                "youtube": yt_title,
                "facebook": fb_title,
                "instagram_caption": ig_caption
            },
            "results": results
        }, f, indent=4, ensure_ascii=False)
    log(f"📄 Tóm tắt đã lưu tại: {summary_path}")

if __name__ == "__main__":
    main()
