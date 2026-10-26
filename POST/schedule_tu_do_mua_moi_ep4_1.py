# -*- coding: utf-8 -*-
"""
Schedule & Auto-Publisher Runner cho thương hiệu "Tủ Đồ Mùa Mới"
Video: C:\Affiliate\Tủ Đồ Mùa Mới\video_việt_hóa\4-1.mp4
4 Nền tảng:
- YouTube Shorts: Native Google API v3 Scheduled (status.publishAt chuẩn RFC 3339 UTC, status.privacyStatus: "private")
- Facebook (Reels + Story):
    + Reels: Meta Graph API scheduled_publish_time (Unix timestamp) & video_state: "SCHEDULED"
    + Story: Gọi endpoint POST /{page_id}/video_stories
- Instagram (Reels + Story):
    + Reels: Đẩy task vào hàng đợi POST/config/schedule_queue.json
    + Story: Tạo media container dạng Story (media_type: "STORIES")
- Threads: Đẩy task vào hàng đợi POST/config/schedule_queue.json

Thời gian hẹn giờ tối nay (2026-09-25) từ khoảng 19:00:
- YouTube Shorts:        19:05:00
- Facebook Reels & Story: 19:14:00 (lệch 9 phút)
- Instagram Reels & Story: 19:23:00 (lệch 9 phút)
- Threads:                19:32:00 (lệch 9 phút)
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
    YouTubeShortsUploader,
    ThreadsAPIUploader
)

LOG_FILE = os.path.join(POST_DIR, "config", "scheduler_tu_do_mua_moi_ep4_1.log")
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
    return brands.get("tu_do_mua_moi", {})

def load_affiliate_links(excel_path: str):
    if not os.path.exists(excel_path):
        log(f"❌ Không tìm thấy file Excel: {excel_path}")
        return []
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    items = []
    for r in rows[1:]:
        if r and len(r) > 2 and r[2]:
            stt = r[0]
            name = str(r[1]).strip() if r[1] else ""
            url = str(r[2]).strip()
            if url.startswith("http"):
                items.append({"stt": stt, "name": name, "url": url})
    return items

def format_comments(items, template_file=r"C:\Affiliate\post1\comment.txt"):
    templates = [
        "Link sản phẩm ở đây: ",
        "Link sản phẩm: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
        "Link xem và mua hàng ngay tại đây nè: ",
        "Link sản phẩm ở đây cho ai cần nha: ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: ",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: ",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: "
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
    for idx, it in enumerate(items):
        prefix = templates[idx % len(templates)]
        comments.append(f"{prefix}{it['url']} ({it['name']})")
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
    except Exception as e:
        log(f"  ⚠️ Lưu ý tạo IG Story container: {e}")
        return {"success": False, "error": str(e)}

def push_to_schedule_queue(task: dict):
    queue = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []
    queue = [t for t in queue if t.get("id") != task.get("id")]
    queue.append(task)
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)
    log(f"📥 Đã đưa task vào hàng đợi Scheduler: {task['id']} ({task['scheduled_time_str']})")

def main():
    log("=" * 80)
    log("👗 KHỞI ĐỘNG HỆ THỐNG HẸN GIỜ ĐĂNG VIDEO: TỦ ĐỒ MÙA MỚI (TẬP 4-1)")
    log("   Video: C:\\Affiliate\\Tủ Đồ Mùa Mới\\video_việt_hóa\\4-1.mp4")
    log("   4 Nền tảng: YouTube Shorts, Facebook Reels + Story, Instagram Reels + Story, Threads")
    log("=" * 80)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Tủ Đồ Mùa Mới\video_việt_hóa\4-1.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Đọc danh sách link Affiliate từ 4 file Excel
    fb_excel = r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\Facebook\Tập 4.xlsx"
    ig_excel = r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\Instagram\Tập 4.xlsx"
    th_excel = r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\Threads\Tập 4.xlsx"
    yt_excel = r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\YouTube\Tập 4.xlsx"

    fb_items = load_affiliate_links(fb_excel)
    ig_items = load_affiliate_links(ig_excel)
    th_items = load_affiliate_links(th_excel)
    yt_items = load_affiliate_links(yt_excel)

    log(f"📊 Đã nạp thành công link Affiliate Tập 4:")
    log(f"   - Facebook:  {len(fb_items)} links")
    log(f"   - Instagram: {len(ig_items)} links")
    log(f"   - Threads:   {len(th_items)} links")
    log(f"   - YouTube:   {len(yt_items)} links")

    fb_comments = format_comments(fb_items)
    ig_comments = format_comments(ig_items)
    th_comments = format_comments(th_items)
    yt_comments = format_comments(yt_items)

    # 2. Tính toán lịch hẹn giờ giãn cách tự nhiên (Bắt đầu từ ~19:05 tối nay 2026-09-25)
    now = datetime.datetime.now()
    base_date = now.date()

    yt_target = datetime.datetime.combine(base_date, datetime.time(19, 5, 0))
    if yt_target <= now:
        yt_target += datetime.timedelta(days=1)
        base_date = yt_target.date()

    fb_target = datetime.datetime.combine(base_date, datetime.time(19, 14, 0))
    fb_story_target = datetime.datetime.combine(base_date, datetime.time(19, 15, 0))

    ig_target = datetime.datetime.combine(base_date, datetime.time(19, 23, 0))
    ig_story_target = datetime.datetime.combine(base_date, datetime.time(19, 24, 0))

    th_target = datetime.datetime.combine(base_date, datetime.time(19, 32, 0))

    fb_target_ts = int(fb_target.timestamp())
    ig_target_ts = int(ig_target.timestamp())
    th_target_ts = int(th_target.timestamp())

    log("\n⏰ PHÂN BỔ THỜI GIAN HẸN GIỜ XUẤT BẢN:")
    log(f"   1. YouTube Shorts:        {yt_target.strftime('%Y-%m-%d %H:%M:%S')} (RFC 3339 UTC)")
    log(f"   2. Facebook Reels:        {fb_target.strftime('%Y-%m-%d %H:%M:%S')} (Unix TS: {fb_target_ts}) + Story: {fb_story_target.strftime('%H:%M:%S')}")
    log(f"   3. Instagram Reels:       {ig_target.strftime('%Y-%m-%d %H:%M:%S')} + Story: {ig_story_target.strftime('%H:%M:%S')}")
    log(f"   4. Threads:               {th_target.strftime('%Y-%m-%d %H:%M:%S')}")

    # 3. Tiêu đề, Mô tả và Hashtags chuẩn SEO Viral
    # A. YouTube Shorts
    yt_title = "Tips Chọn Chân Váy Xếp Ly & Đuôi Cá Tôn Dáng Cực Đỉnh Cho Nàng Nấm Lùn #Shorts"
    yt_desc = (
        "Gợi ý cách chọn và phối chân váy xếp ly tennis, chân váy đuôi cá lụa tôn dáng hack chân dài miên man. "
        "Đi làm, đi học hay đi chơi diện lên đều chuẩn tiểu thư Hàn Quốc xinh xắn!\n\n"
        "👉 Toàn bộ link sản phẩm chính hãng mình ghim ở BÌNH LUẬN ĐẦU TIÊN nhé 👇\n\n"
        "#Shorts #tudomuamoi #chanvayxeply #chanvayduoica #phoidoxinh #thoitrangnu #ootd #koreanstyle"
    )
    yt_tags = [
        "Shorts", "tudomuamoi", "chanvayxeply", "chanvayduoica", "phoidoxinh",
        "thoitrangnu", "vaytennis", "aokieu", "ootdvietnam", "koreanstyle"
    ]

    # B. Facebook Reels
    fb_title = "Bí kíp phối chân váy xếp ly và đuôi cá hack dáng chuẩn phong cách Hàn Quốc"
    fb_first_link = fb_items[0]['url'] if fb_items else "https://shopee.vn"
    fb_caption = (
        "Chân váy xếp ly và chân váy đuôi cá mặc sao cho vừa hack dáng vừa thanh lịch? "
        "Xem ngay gợi ý phối đồ cực xinh này của Tủ Đồ Mùa Mới nhé các nàng ơi! "
        "Tôn vòng 2, che khuyết điểm đùi to và kéo dài chân cực kỳ đỉnh chóp ✨\n\n"
        f"👉 Sắm ngay chân váy xếp ly tuyết mưa siêu hot tại: {fb_first_link}\n"
        "👉 Toàn bộ link chi tiết từng món đồ mình ghim dưới phần BÌNH LUẬN nha!\n\n"
        "#reels #viral #fyp #tudomuamoi #chanvayxeply #chanvayduoica #thoitrangnu #phoidodep"
    )

    # C. Instagram Reels
    ig_caption = (
        "Gợi ý phối chân váy xếp ly & chân váy đuôi cá hack chân dài miên man cho các nàng ✨ "
        "Dù là đi học, đi làm công sở hay hẹn hò cuối tuần diện lên đều chuẩn visual tiểu thư ngọt ngào! "
        "Link trọn bộ chân váy và áo kiểu xinh xỉu mình để sẵn dưới COMMENT nha 👇\n\n"
        "#reels #viral #fyp #tudomuamoi #outfitinspiration #chanvayxeply #chanvayduoica #koreanfashion #ootdvietnam #dailylook"
    )

    # D. Threads (< 500 ký tự)
    th_link1 = th_items[0]['url'] if len(th_items) > 0 else ""
    th_link2 = th_items[1]['url'] if len(th_items) > 1 else ""
    th_link3 = th_items[8]['url'] if len(th_items) > 8 else ""
    th_caption = (
        "Chân váy xếp ly hay chân váy đuôi cá là chân ái của mấy bà? Phối cùng sơ mi hay áo kiểu là tôn dáng dã man luôn ✨\n\n"
        "🛒 Link sắm chân váy chuẩn đẹp:\n"
        f"1. Chân váy xếp ly Hàn Quốc: {th_link1}\n"
        f"2. Chân váy tennis tuyết mưa: {th_link2}\n"
        f"3. Chân váy đuôi cá lụa sang chảnh: {th_link3}\n\n"
        "#tudomuamoi #thoitrangnu #chanvay #ootd"
    )

    results = {}

    # =========================================================================
    # BƯỚC 1: YOUTUBE SHORTS (Native API Scheduled Publish)
    # =========================================================================
    log("\n🔴 [1/4] THỰC THI HẸN GIỜ YOUTUBE SHORTS (Google API v3)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/tu_do_mua_moi.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)

        utc_target = yt_target - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        log(f"   📅 Thời điểm phát hành (UTC RFC 3339): {publish_at_rfc3339}")

        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=yt_tags,
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        results["youtube"] = res_yt
        log(f"   ✅ Phản hồi API YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"   ❌ Lỗi YouTube Shorts: {e}\n{traceback.format_exc()}")
        results["youtube"] = {"success": False, "error": str(e)}

    # =========================================================================
    # BƯỚC 2: FACEBOOK REELS & STORY (Native Meta Graph API Scheduled)
    # =========================================================================
    log("\n🔷 [2/4] THỰC THI HẸN GIỜ FACEBOOK REELS & STORY (Meta Graph API)...")
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
        log(f"   ❌ Lỗi Facebook Reels/Story: {e}\n{traceback.format_exc()}")
        results["facebook_reels"] = {"success": False, "error": str(e)}

    # =========================================================================
    # BƯỚC 3: INSTAGRAM REELS & STORY (Scheduler Queue & Stories container)
    # =========================================================================
    log("\n📸 [3/4] ĐẨY TASK INSTAGRAM REELS & STORY VÀO SCHEDULER QUEUE...")
    try:
        ig_cfg = brand_data.get("instagram", {})
        ig_task_id = f"task_ig_tdmm_ep4_{int(time.time())}"
        ig_task = {
            "id": ig_task_id,
            "brand_key": "tu_do_mua_moi",
            "video_path": os.path.abspath(video_path),
            "title": "",
            "caption": ig_caption,
            "comment": "\n".join(ig_comments),
            "platforms": ["instagram"],
            "scheduled_time_str": ig_target.strftime("%Y-%m-%d %H:%M:%S"),
            "scheduled_timestamp": ig_target_ts,
            "product_keyword": "Chân váy xếp ly & Chân váy đuôi cá",
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

    # =========================================================================
    # BƯỚC 4: THREADS (Scheduler Queue)
    # =========================================================================
    log("\n🧵 [4/4] ĐẨY TASK THREADS VÀO SCHEDULER QUEUE...")
    try:
        th_task_id = f"task_th_tdmm_ep4_{int(time.time())}"
        th_task = {
            "id": th_task_id,
            "brand_key": "tu_do_mua_moi",
            "video_path": os.path.abspath(video_path),
            "title": "",
            "caption": th_caption,
            "comment": "\n".join(th_comments),
            "platforms": ["threads"],
            "scheduled_time_str": th_target.strftime("%Y-%m-%d %H:%M:%S"),
            "scheduled_timestamp": th_target_ts,
            "product_keyword": "Chân váy xếp ly & Chân váy đuôi cá",
            "status": "PENDING"
        }
        push_to_schedule_queue(th_task)
        results["threads"] = {"success": True, "task_id": th_task_id, "status": "PENDING", "queue": QUEUE_FILE}
    except Exception as e:
        log(f"   ❌ Lỗi đưa Threads vào Scheduler: {e}\n{traceback.format_exc()}")
        results["threads"] = {"success": False, "error": str(e)}

    log("\n" + "=" * 80)
    log("🏁 ĐÃ HOÀN TẤT THIẾT LẬP LỊCH HẸN GIỜ TRÊN CẢ 4 NỀN TẢNG CHO TỦ ĐỒ MÙA MỚI (TẬP 4-1)!")
    log("=" * 80)

    # In kết quả tổng hợp ra file
    summary_path = os.path.join(POST_DIR, "config", "schedule_tu_do_mua_moi_ep4_1_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "brand": "Tủ Đồ Mùa Mới",
            "video": video_path,
            "timestamps": {
                "youtube": yt_target.strftime("%Y-%m-%d %H:%M:%S"),
                "facebook_reels": fb_target.strftime("%Y-%m-%d %H:%M:%S"),
                "facebook_story": fb_story_target.strftime("%Y-%m-%d %H:%M:%S"),
                "instagram_reels": ig_target.strftime("%Y-%m-%d %H:%M:%S"),
                "instagram_story": ig_story_target.strftime("%Y-%m-%d %H:%M:%S"),
                "threads": th_target.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "titles": {
                "youtube": yt_title,
                "facebook": fb_title,
                "instagram_caption": ig_caption,
                "threads_caption": th_caption
            },
            "results": results
        }, f, indent=4, ensure_ascii=False)
    log(f"📄 Tóm tắt đã lưu tại: {summary_path}")

if __name__ == "__main__":
    main()
