# -*- coding: utf-8 -*-
"""
Task Runner - Đăng Video "Cây Lăn Massage Mắt & Dưỡng Mắt Marubi" (Video 5)
Cho thương hiệu: Chăm Da Tiết Kiệm (cham_da_tiet_kiem)
Lên 2 nền tảng:
1. Instagram Reels (+ Story + 9 bình luận affiliate link)
2. Threads (+ 9 replies affiliate link)
Được kích hoạt bởi Windows Task Scheduler vào đúng 12:00:00 ngày 26/09/2026.
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
from token_refresher import refresh_meta_tokens_if_needed

LOG_FILE = r"C:\Affiliate\post1\POST\config\task_cdtk_ig_threads_12h.log"
QUEUE_FILE = r"C:\Affiliate\post1\POST\config\schedule_queue.json"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_brand_config():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    return brands.get("cham_da_tiet_kiem", {})

def load_excel_links(excel_path: str):
    """Đọc danh sách link rút gọn từ file Excel"""
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
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
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
        if not prefix.endswith(" "):
            prefix += " "
        comments.append(f"{prefix}{item['url']}")
    return comments

def post_instagram_story(ig_user_id: str, access_token: str, video_path: str):
    """Tải và khởi tạo Story cho Instagram Business"""
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
            log(f"  ✅ Đã tải Story lên Instagram Container ID: {container_id} (HTTP {up_res.status_code})")
            time.sleep(10)
            pub_res = requests.post(
                f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": access_token},
                timeout=30
            ).json()
            log(f"  🎉 Kết quả phát hành Story: {pub_res}")
            return pub_res
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng IG Story: {e}")

def update_queue_status(task_id: str, status: str, result_dict: dict):
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
            for t in queue:
                if t.get("id") == task_id:
                    t["status"] = status
                    t["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    t["result"] = result_dict
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log(f"⚠️ Lỗi update queue: {e}")

def run_task():
    log("=" * 80)
    log("🚀 [12:00:00] BẮT ĐẦU XUẤT BẢN VIDEO CHĂM DA TIẾT KIỆM (INSTAGRAM & THREADS)")
    log("=" * 80)

    brand_data = load_brand_config()

    # ── Tự động kiểm tra & gia hạn token trước khi upload ──
    log("🔐 Kiểm tra token Meta trước khi đăng...")
    refresh_meta_tokens_if_needed("cham_da_tiet_kiem", ["instagram", "threads"])
    brand_data = load_brand_config()   # Reload sau refresh    video_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\5.mp4"
    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Đọc danh sách Affiliate Link từ Excel
    ig_excel = r"C:\Affiliate\Chăm Da Tiết Kiệm\Link customed\Instagram\cây lăn massage mắt.xlsx"
    th_excel = r"C:\Affiliate\Chăm Da Tiết Kiệm\Link customed\Threads\cây lăn massage mắt.xlsx"

    ig_items = load_excel_links(ig_excel)
    th_items = load_excel_links(th_excel)

    log(f"📊 Link nạp được: Instagram ({len(ig_items)} links), Threads ({len(th_items)} links)")

    ig_comments = format_comment_list(ig_items)
    th_comments = format_comment_list(th_items)

    # 2. Nội dung Caption
    ig_caption = (
        "Bí quyết xóa tan quầng thâm & vết chân chim với liệu pháp 'dĩ du dưỡng nhãn' massage mắt tại nhà cực đơn giản ✨\n"
        "Kết hợp tinh dầu dưỡng mắt Marubi cùng cây lăn massage kim loại ấn huyệt giúp thư giãn mắt mỏi, kích thích lưu thông máu và nâng cơ mắt hiệu quả.\n"
        "Chi tiết link cây lăn massage & tinh dầu chính hãng mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #chamdatietkiem #massagemat #marubi #duongmat #giamquangtham #skincarehacks #chonglaohoa"
    )

    top_3_threads = "\n".join([f"👉 {it['name'][:35]}...: {it['url']}" for it in th_items[:3]])
    th_caption = (
        "Bí quyết xóa tan bọng mắt & quầng thâm với liệu pháp massage mắt 'dĩ du dưỡng nhãn' tại nhà cực đỉnh ✨\n"
        "Dùng tinh dầu kết hợp thanh lăn massage ấn huyệt giảm mỏi mắt tức thì, mờ nếp nhăn đuôi mắt rõ rệt.\n\n"
        f"🛒 Link tham khảo sản phẩm chính hãng:\n{top_3_threads}\n\n"
        "#chamdatietkiem #massagemat #marubi #duongmat #skincaretips"
    )

    results = {}

    # ----------------------------------------------------
    # A. XUẤT BẢN THREADS (VIDEO + REPLIES)
    # ----------------------------------------------------
    log("\n" + "=" * 60)
    log("🧵 1. TIẾN HÀNH ĐĂNG LÊN THREADS (VIDEO + REPLIES)")
    log("=" * 60)
    try:
        th_cfg = brand_data.get("threads", {})
        th_uploader = ThreadsAPIUploader(
            threads_user_id=th_cfg["user_id"],
            access_token=th_cfg["access_token"]
        )
        first_link = th_items[0]["url"] if th_items else None
        res_th = th_uploader.upload_video_thread(
            video_path=video_path,
            caption=th_caption,
            comment_link=first_link
        )
        log(f"✅ Kết quả đăng Threads Video: {res_th}")
        results["threads"] = res_th

        if res_th and res_th.get("id"):
            thread_id = res_th["id"]
            log(f"💬 Bắt đầu comment {len(th_comments)} link Affiliate vào bài viết Threads...")
            for idx, c_txt in enumerate(th_comments, 1):
                try:
                    time.sleep(2)
                    c_res = th_uploader.publish_reply(post_id=thread_id, text=c_txt)
                    if c_res and "id" in c_res:
                        log(f"  ✅ Đã reply comment Threads {idx}/{len(th_comments)}: (ID: {c_res['id']})")
                    else:
                        log(f"  ⚠️ Lỗi reply Threads {idx}: {c_res}")
                except Exception as ce:
                    log(f"  ⚠️ Ngoại lệ comment Threads {idx}: {ce}")
    except Exception as e:
        log(f"❌ Lỗi đăng Threads: {e}\n{traceback.format_exc()}")
        results["threads"] = {"success": False, "error": str(e)}

    # ----------------------------------------------------
    # B. XUẤT BẢN INSTAGRAM REELS + STORY
    # ----------------------------------------------------
    log("\n" + "=" * 60)
    log("📸 2. TIẾN HÀNH ĐĂNG LÊN INSTAGRAM (REELS + COMMENTS + STORY)")
    log("=" * 60)
    try:
        # Tải lại config để đón token mới nếu người dùng cập nhật
        refreshed_data = load_brand_config()
        ig_cfg = refreshed_data.get("instagram", {})
        ig_uploader = InstagramReelsUploader(
            ig_user_id=ig_cfg["ig_user_id"],
            access_token=ig_cfg["access_token"]
        )
        res_ig = ig_uploader.upload_reel(
            video_path=video_path,
            caption=ig_caption,
            comment_text=ig_comments
        )
        log(f"✅ Kết quả đăng Instagram Reel: {res_ig}")
        results["instagram_reels"] = res_ig

        # Đăng thêm Story
        post_instagram_story(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi đăng Instagram: {e}\n{traceback.format_exc()}")
        results["instagram_reels"] = {"success": False, "error": str(e)}

    # Cập nhật hàng đợi schedule
    update_queue_status("task_cdtk_ig_threads_12h", "COMPLETED", results)
    log("\n🎉 HOÀN TẤT QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO CHĂM DA TIẾT KIỆM!")

if __name__ == "__main__":
    run_task()
