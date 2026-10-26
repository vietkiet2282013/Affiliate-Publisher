# -*- coding: utf-8 -*-
"""
Schedule Runner - Tự động lập lịch và hẹn giờ đăng video cho thương hiệu "Dùng Rồi Mới Nói"
Đích danh duy nhất nền tảng: INSTAGRAM (Reels + Story)
Khung giờ hẹn: 12:00:00 (12h00 trưa ngày 2026-09-26)
Video: C:\\Affiliate\\Dùng Rồi Mới Nói\\Video_việt_hóa\\che mắt ngủ.mp4
Link Affiliate: C:\\Affiliate\\Dùng Rồi Mới Nói\\Link customed\\Instagram\\Che mắt ngủ.xlsx
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

from uploaders import InstagramReelsUploader

LOG_FILE = os.path.join(POST_DIR, "config", "scheduler_dung_roi_moi_noi.log")
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
    return brands.get("dung_roi_moi_noi", {})

def load_instagram_affiliate_links(excel_path: str):
    """Đọc danh sách link rút gọn Instagram từ file Excel"""
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
    """Format danh sách comment theo mẫu luân phiên kích thích click"""
    templates = [
        "Link sản phẩm ở đây: ",
        "Link xem và mua hàng ngay tại đây nè: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: ",
        "Link sản phẩm ở đây cho ai cần nha: ",
        "Link sản phẩm: "
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
        if not prefix.endswith(" "):
            prefix += " "
        comments.append(f"{prefix}{item['url']}")
    return comments

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

def update_queue(task: dict, remove_platforms: list = None):
    """Cập nhật hàng đợi schedule_queue.json"""
    queue = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []
    
    # Loại bỏ các task của Dùng Rồi Mới Nói thuộc các nền tảng bị hủy (threads, facebook, youtube)
    if remove_platforms:
        new_queue = []
        for t in queue:
            is_drmn = (t.get("brand_key") == "dung_roi_moi_noi")
            has_removed_plat = any(p in remove_platforms for p in t.get("platforms", []))
            if is_drmn and has_removed_plat:
                log(f"🗑️ Đã hủy task không sử dụng: {t.get('id')} ({t.get('platforms')})")
                continue
            new_queue.append(t)
        queue = new_queue

    # Cập nhật hoặc thêm task Instagram
    queue = [t for t in queue if t.get("id") != task.get("id")]
    queue.append(task)
    
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)
    log(f"📥 Đã đồng bộ task vào hàng đợi Scheduler: {task['id']} (Hẹn giờ: {task['scheduled_time_str']})")

def setup_and_run(wait_until_publish: bool = True):
    log("=" * 80)
    log("🚀 THIẾT LẬP HẸN GIỜ ĐĂNG VIDEO: DÙNG RỒI MỚI NÓI - DUY NHẤT INSTAGRAM")
    log("   Video: che mắt ngủ.mp4 | Khung giờ hẹn: 12:00:00 (12h00 trưa)")
    log("=" * 80)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Dùng Rồi Mới Nói\Video_việt_hóa\che mắt ngủ.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Nạp danh sách link Affiliate Instagram
    ig_excel = r"C:\Affiliate\Dùng Rồi Mới Nói\Link customed\Instagram\Che mắt ngủ.xlsx"
    ig_items = load_instagram_affiliate_links(ig_excel)
    log(f"📊 Đã nạp thành công {len(ig_items)} link Affiliate Instagram từ Excel.")

    ig_comments = format_comment_list(ig_items)

    # 2. Thiết lập thời gian xuất bản: 12:00:00 trưa nay (2026-09-26)
    now = datetime.datetime.now()
    base_date = now.date()
    target_dt = datetime.datetime.combine(base_date, datetime.time(12, 0, 0))
    if target_dt <= now:
        target_dt += datetime.timedelta(days=1)
    
    target_ts = int(target_dt.timestamp())
    log(f"📅 Thời điểm xuất bản mục tiêu: {target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Timestamp: {target_ts})")

    # 3. Caption chuẩn SEO Viral cho Instagram Reels
    ig_caption = (
        "Ngủ ngon sâu giấc bất chấp ánh sáng với chiếc bịt mắt ngủ 2 mặt ấm mát siêu êm ái ✨\n"
        "Thiết kế thông minh một mặt làm mát dịu mắt, một mặt giữ ấm thư giãn, quai co giãn tùy chỉnh không gây đau tai. "
        "Chân ái cho team văn phòng ngủ trưa hay đi du lịch tàu xe!\n"
        "Chi tiết các mẫu xịn nhất mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #dungroimoinoi #chematngu #bitmatngu #giadungthongminh #reviewgiadung #lifestyle #ngungon"
    )

    # 4. Đẩy task vào hàng đợi Scheduler Queue & Hủy các task threads, facebook, youtube của video này
    task_id = "task_ig_drmn_chematngu_12h"
    task = {
        "id": task_id,
        "brand_key": "dung_roi_moi_noi",
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": ig_caption,
        "comment": "\n".join(ig_comments),
        "platforms": ["instagram"],
        "scheduled_time_str": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": target_ts,
        "product_keyword": "Che mắt ngủ",
        "status": "PENDING"
    }

    update_queue(task, remove_platforms=["threads", "facebook", "youtube"])

    # 5. Khởi tạo sẵn Instagram Story Container nếu cần
    ig_cfg = brand_data.get("instagram", {})
    post_instagram_story_container(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)

    log("\n" + "=" * 80)
    log("⏰ BẮT ĐẦU TIẾN TRÌNH THEO DÕI VÀ ĐẾM NGƯỢC XUẤT BẢN INSTAGRAM VÀO 12:00:00...")
    log("=" * 80)

    if not wait_until_publish:
        log("ℹ️ Chế độ không chờ: Đã ghi nhận lịch hẹn vào queue thành công.")
        return

    # Vòng lặp đếm ngược chính xác đến 12:00:00
    while True:
        current_time = datetime.datetime.now()
        remaining_seconds = (target_dt - current_time).total_seconds()

        if remaining_seconds <= 0:
            log(f"\n🎉 [12:00:00] ĐÃ ĐẾN GIỜ HẸN XUẤT BẢN INSTAGRAM REELS!")
            try:
                ig_uploader = InstagramReelsUploader(
                    ig_user_id=ig_cfg["ig_user_id"],
                    access_token=ig_cfg["access_token"]
                )
                res_ig = ig_uploader.upload_reel(
                    video_path=video_path,
                    caption=ig_caption,
                    comment_text=ig_comments
                )
                log(f"✅ KẾT QUẢ ĐĂNG INSTAGRAM REEL: {res_ig}")
                
                # Cập nhật queue thành COMPLETED
                if os.path.exists(QUEUE_FILE):
                    try:
                        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                            q = json.load(f)
                        for t in q:
                            if t.get("id") == task_id:
                                t["status"] = "COMPLETED"
                                t["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                t["result"] = res_ig
                        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                            json.dump(q, f, indent=4, ensure_ascii=False)
                    except Exception as qe:
                        log(f"⚠️ Lỗi update queue: {qe}")
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reel: {e}\n{traceback.format_exc()}")
            break

        # Log tiến độ định kỳ
        if int(remaining_seconds) % 3600 == 0 or remaining_seconds < 120:
            log(f"⏳ Đang chạy nền... Còn {int(remaining_seconds // 3600)} giờ {int((remaining_seconds % 3600) // 60)} phút nữa tới 12:00:00 ({target_dt.strftime('%H:%M:%S')}).")
        
        time.sleep(15)

if __name__ == "__main__":
    wait_mode = True
    if len(sys.argv) > 1 and sys.argv[1] == "--nowait":
        wait_mode = False
    setup_and_run(wait_until_publish=wait_mode)
