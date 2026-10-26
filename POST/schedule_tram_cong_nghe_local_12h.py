# -*- coding: utf-8 -*-
"""
Schedule Runner - Tự động lập lịch và hẹn giờ đăng video cho thương hiệu "Trạm Công Nghệ"
2 Nền tảng: INSTAGRAM (Reels + Story) & THREADS
Khung giờ hẹn: Đúng 12:00:00 ngày 26/09/2026 (12h00 trưa)
Video: C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\đèn màn hình máy tính.mp4
Link Affiliate: 
- Instagram: C:\Affiliate\Trạm Công Nghệ\Link customed\Instagram\đèn màn hình máy tính.xlsx
- Threads:   C:\Affiliate\Trạm Công Nghệ\Link customed\Threads\đèn màn hình máy tính.xlsx
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

from uploaders import InstagramReelsUploader, ThreadsAPIUploader

LOG_FILE = os.path.join(POST_DIR, "config", "scheduler_tram_cong_nghe_local_12h.log")
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
    return brands.get("cham_cong_nghe", {})

def load_affiliate_links_from_excel(excel_path: str):
    if not os.path.exists(excel_path):
        log(f"❌ Không tìm thấy file Excel: {excel_path}")
        return []
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = rows[0]
    link_idx, name_idx = 2, 1
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
    for idx, item in enumerate(items):
        prefix = templates[idx % len(templates)]
        if not prefix.endswith(" "):
            prefix += " "
        short_name = item['name'][:55] + "..." if len(item['name']) > 55 else item['name']
        comments.append(f"{prefix}{item['url']} ({short_name})")
    return comments

def post_instagram_story_container(ig_user_id: str, access_token: str, video_path: str):
    """Khởi tạo media container dạng Story cho Instagram Business"""
    try:
        log("📸 Đang tạo Media Container Story cho Instagram Business (media_type: STORIES)...")
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={
                "media_type": "STORIES",
                "upload_type": "resumable",
                "access_token": access_token
            },
            timeout=30
        ).json()
        log(f"  📡 Phản hồi tạo Story container: {init_res}")
        return init_res
    except Exception as e:
        log(f"  ⚠️ Lưu ý tạo IG Story container: {e}")
        return None

def update_queue(tasks: list):
    queue = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception:
            queue = []
    
    task_ids = {t["id"] for t in tasks}
    queue = [t for t in queue if t.get("id") not in task_ids]
    for t in tasks:
        queue.append(t)
        log(f"📥 Đã đồng bộ task vào hàng đợi Scheduler: {t['id']} ({t['scheduled_time_str']})")
    
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)

def setup_and_run(wait_until_publish: bool = True):
    log("=" * 80)
    log("🚀 THIẾT LẬP HẸN GIỜ ĐĂNG VIDEO: TRẠM CÔNG NGHỆ - INSTAGRAM & THREADS")
    log("   Thời gian xuất bản: Đúng 12:00:00 ngày 26/09/2026")
    log("   Video: đèn màn hình máy tính.mp4")
    log("=" * 80)

    brand_data = load_config()
    video_path = r"C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\đèn màn hình máy tính.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Nạp danh sách Affiliate links
    ig_excel = r"C:\Affiliate\Trạm Công Nghệ\Link customed\Instagram\đèn màn hình máy tính.xlsx"
    th_excel = r"C:\Affiliate\Trạm Công Nghệ\Link customed\Threads\đèn màn hình máy tính.xlsx"

    ig_items = load_affiliate_links_from_excel(ig_excel)
    th_items = load_affiliate_links_from_excel(th_excel)

    log(f"📊 Đã nạp {len(ig_items)} link Instagram & {len(th_items)} link Threads.")

    ig_comments = format_comment_list(ig_items)
    th_comments = format_comment_list(th_items)

    # 2. Thiết lập mục tiêu: Đúng 12:00:00 ngày 26/09/2026
    target_dt = datetime.datetime(2026, 9, 26, 12, 0, 0)
    now = datetime.datetime.now()
    if target_dt <= now:
        target_dt += datetime.timedelta(days=1)
    
    target_ts = int(target_dt.timestamp())
    log(f"📅 Thời điểm xuất bản mục tiêu: {target_dt.strftime('%Y-%m-%d %H:%M:%S')} (Unix Timestamp: {target_ts})")

    # 3. Caption chuẩn SEO Viral
    ig_caption = (
        "Nâng cấp góc làm việc với đèn treo màn hình chống lóa mắt siêu đỉnh ✨\n"
        "Ánh sáng tiêu chuẩn bảo vệ mắt khi làm việc ban đêm, thiết kế kẹp màn hình gọn gàng không tốn diện tích mặt bàn. "
        "Cảm ứng điều chỉnh tông màu và độ sáng dễ dàng. "
        "Link săn chính hãng các mẫu xịn nhất mình ghim dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #tramcongnghe #denmanhinh #desksetup #techgear #lightbar #reviewcongnghe"
    )

    th_caption = (
        "Góc làm việc ban đêm nhất định phải trang bị em đèn treo màn hình bảo vệ mắt này nha anh em! ✨\n"
        "Ánh sáng hắt xuống bàn mượt mà, không chiếu trực tiếp vào mắt hay lóa màn hình, vừa chống mỏi mắt vừa làm góc setup cực sang.\n\n"
        "🛒 Link sắm trọn bộ các mẫu đèn màn hình chính hãng trong video:\n"
        f"1. Đèn bàn học LED 3 màu: {th_items[0]['url'] if th_items else ''}\n"
        f"2. Đèn Sidohome SF301 LED RGB: {th_items[1]['url'] if len(th_items) > 1 else ''}\n"
        f"3. Đèn Lymax L1 Plus đa chế độ: {th_items[2]['url'] if len(th_items) > 2 else ''}\n\n"
        "(Toàn bộ link các dòng còn lại mình đã ghim ở bình luận bên dưới nhé 👇)\n"
        "#tramcongnghe #denmanhinh #desksetup #congnghe #lightbar"
    )

    # 4. Đẩy task vào hàng đợi Scheduler Queue
    task_ig_id = "task_ig_tcn_12h_20260926"
    task_th_id = "task_th_tcn_12h_20260926"

    task_ig = {
        "id": task_ig_id,
        "brand_key": "cham_cong_nghe",
        "video_path": os.path.abspath(video_path),
        "title": "Đèn Treo Màn Hình Máy Tính Bảo Vệ Mắt Chống Cận",
        "caption": ig_caption,
        "comment": "\n".join(ig_comments),
        "platforms": ["instagram"],
        "scheduled_time_str": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": target_ts,
        "product_keyword": "Đèn treo màn hình máy tính",
        "status": "PENDING_WINDOWS_SCHEDULER"
    }

    task_th = {
        "id": task_th_id,
        "brand_key": "cham_cong_nghe",
        "video_path": os.path.abspath(video_path),
        "title": "",
        "caption": th_caption,
        "comment": "\n".join(th_comments),
        "platforms": ["threads"],
        "scheduled_time_str": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": target_ts,
        "product_keyword": "Đèn treo màn hình máy tính",
        "status": "PENDING_WINDOWS_SCHEDULER"
    }

    update_queue([task_ig, task_th])

    # 5. Khởi tạo Story container
    ig_cfg = brand_data.get("instagram", {})
    post_instagram_story_container(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)

    log("\n" + "=" * 80)
    log("⏰ BẮT ĐẦU TIẾN TRÌNH THEO DÕI VÀ ĐẾM NGƯỢC XUẤT BẢN ĐÚNG 12:00:00 (26/09/2026)...")
    log("=" * 80)

    if not wait_until_publish:
        log("ℹ️ Chế độ không chờ: Đã ghi nhận lịch hẹn vào queue thành công.")
        return

    # Vòng lặp đếm ngược chính xác đến 12:00:00
    while True:
        current_time = datetime.datetime.now()
        remaining_seconds = (target_dt - current_time).total_seconds()

        if remaining_seconds <= 0:
            log(f"\n🎉 [12:00:00] ĐÃ ĐẾN GIỜ HẸN! TIẾN HÀNH XUẤT BẢN INSTAGRAM & THREADS...")
            
            # --- 1. INSTAGRAM REELS ---
            try:
                log("📸 Đang xuất bản Instagram Reels...")
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
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reel: {e}\n{traceback.format_exc()}")

            # --- 2. THREADS ---
            try:
                log("🧵 Đang xuất bản Threads...")
                th_cfg = brand_data.get("threads", {})
                th_uploader = ThreadsAPIUploader(
                    threads_user_id=th_cfg["user_id"],
                    access_token=th_cfg["access_token"]
                )
                res_th = th_uploader.upload_video_thread(
                    video_path=video_path,
                    caption=th_caption,
                    comment_link=None
                )
                log(f"✅ KẾT QUẢ ĐĂNG THREADS: {res_th}")

                # Reply bình luận Shopee vào bài viết Threads
                if res_th and "id" in res_th:
                    post_id = res_th["id"]
                    log(f"💬 Đang gửi các bình luận Affiliate vào Thread ID {post_id}...")
                    for idx, cmt in enumerate(th_comments, 1):
                        try:
                            time.sleep(2)
                            th_uploader.publish_reply(post_id=post_id, text=cmt)
                            log(f"  ✅ Đã reply comment Threads {idx}: {cmt[:45]}...")
                        except Exception as ce:
                            log(f"  ⚠️ Lỗi reply comment {idx}: {ce}")
            except Exception as e:
                log(f"❌ Lỗi xuất bản Threads: {e}\n{traceback.format_exc()}")

            # Cập nhật queue thành COMPLETED
            try:
                if os.path.exists(QUEUE_FILE):
                    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                        q = json.load(f)
                    for t in q:
                        if t.get("id") in [task_ig_id, task_th_id]:
                            t["status"] = "COMPLETED"
                            t["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                        json.dump(q, f, indent=4, ensure_ascii=False)
            except Exception as qe:
                log(f"⚠️ Lỗi update queue: {qe}")

            log("\n🏁 HOÀN TẤT QUY TRÌNH HẸN GIỜ XUẤT BẢN CHO TRẠM CÔNG NGHỆ (INSTAGRAM & THREADS)!")
            break

        # Log định kỳ mỗi 30 phút hoặc khi còn dưới 120s
        if int(remaining_seconds) % 1800 == 0 or remaining_seconds < 120:
            hours = int(remaining_seconds // 3600)
            mins = int((remaining_seconds % 3600) // 60)
            secs = int(remaining_seconds % 60)
            log(f"⏳ Đang chạy nền máy tính: Còn {hours} giờ {mins} phút {secs} giây nữa tới 12:00:00 ({target_dt.strftime('%H:%M:%S')}).")

        time.sleep(15)

if __name__ == "__main__":
    wait_mode = True
    if len(sys.argv) > 1 and sys.argv[1] == "--nowait":
        wait_mode = False
    setup_and_run(wait_until_publish=wait_mode)
