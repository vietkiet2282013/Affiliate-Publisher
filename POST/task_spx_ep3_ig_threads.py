# -*- coding: utf-8 -*-
"""
Task Runner - Đăng Video Tập 3 cho thương hiệu Setup Phòng Xinh
Lên 2 nền tảng:
- Instagram: Reels + Story (kèm 13 bình luận affiliate tương ứng)
- Threads: Video + Auto-reply 13 comment affiliate tương ứng
Được kích hoạt bởi Windows Task Scheduler hoặc chạy thủ công/hàng đợi vào lúc 12:00 ngày 26/09/2026.
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
    InstagramReelsUploader,
    ThreadsAPIUploader
)
from token_refresher import refresh_meta_tokens_if_needed

LOG_FILE = r"C:\Affiliate\post1\POST\config\task_spx_ep3_ig_threads.log"
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
        if item.get("name"):
            comments.append(f"{prefix}{item['name']}: {item['url']}")
        else:
            comments.append(f"{prefix}{item['url']}")
    return comments

def post_instagram_story(ig_user_id: str, access_token: str, video_path: str):
    """Đăng bổ sung lên Instagram Story"""
    try:
        log("📸 Đang khởi tạo Story cho Instagram Business (media_type: STORIES)...")
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
            log(f"  ✅ Đã tải dữ liệu lên IG Story Container ID: {container_id} (HTTP {up_res.status_code})")
            return container_id
        elif "id" in init_res:
            return init_res["id"]
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng IG Story: {e}")
    return None

def update_queue_status(task_ids: list, status: str = "COMPLETED"):
    """Cập nhật trạng thái trong schedule_queue.json"""
    if not os.path.exists(QUEUE_FILE):
        return
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            queue = json.load(f)
        updated = False
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for t in queue:
            if t.get("id") in task_ids:
                t["status"] = status
                t["completed_at"] = now_str
                updated = True
        if updated:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=4, ensure_ascii=False)
            log(f"📝 Đã cập nhật trạng thái các task {task_ids} thành {status}")
    except Exception as e:
        log(f"⚠️ Lỗi cập nhật queue: {e}")

def run_post():
    log("=" * 80)
    log("🚀 BẮT ĐẦU TIẾN TRÌNH XUẤT BẢN: SETUP PHÒNG XINH (TẬP 3)")
    log("   Thời gian thực thi: 12:00 ngày 26/09/2026")
    log("   Nền tảng: Instagram (Reels + Story) và Threads (Video + 13 Replies)")
    log("=" * 80)

    brand_data = load_config()

    # ── Tự động kiểm tra & gia hạn token trước khi upload ──
    log("🔐 Kiểm tra token Meta trước khi đăng...")
    refresh_meta_tokens_if_needed("setup_phong_xinh", ["instagram", "threads"])
    brand_data = load_config()   # Reload sau refresh

    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\3.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video: {video_path}")
        return

    # 1. Đọc dữ liệu link Affiliate từ file Excel Tập 3
    ig_excel = r"C:\Affiliate\Setup Phòng Xinh\Link customed\Instagram\Tập 3.xlsx"
    th_excel = r"C:\Affiliate\Setup Phòng Xinh\Link customed\Threads\Tập 3.xlsx"

    ig_items = load_affiliate_links(ig_excel)
    th_items = load_affiliate_links(th_excel)

    log(f"📊 Đã nạp danh sách link Affiliate:")
    log(f"   - Instagram: {len(ig_items)} links")
    log(f"   - Threads:   {len(th_items)} links")

    ig_comments = format_comment_list(ig_items)
    th_comments = format_comment_list(th_items)

    # 2. Chuẩn bị nội dung Caption chuẩn SEO
    # Instagram Caption
    ig_caption = (
        "Góc phòng ngủ và nhà tắm gọn gàng, tiện nghi hơn bao giờ hết với combo decor thông minh này ✨\n"
        "Không cần khoan tường, lắp đặt 1 nốt nhạc: Kệ gắn tường chịu tải siêu khủng, tủ sấy quần áo đa năng khử khuẩn, và đèn led cảm biến từ tính xoay 360 tự bật sáng khi có người.\n\n"
        "👇 Chi tiết link mua sắm từng món chính hãng mình ghim ở phần comment bên dưới nha cả nhà!\n\n"
        "#reels #viral #setupphongxinh #decorroom #homedecor #setupdecor #phongdep #tienichgiadinh"
    )

    # Threads Caption (< 500 ký tự)
    th_link1 = th_items[0]['url'] if len(th_items) > 0 else ""
    th_link2 = th_items[6]['url'] if len(th_items) > 6 else (th_items[1]['url'] if len(th_items) > 1 else "")
    th_link3 = th_items[8]['url'] if len(th_items) > 8 else (th_items[2]['url'] if len(th_items) > 2 else "")
    th_caption = (
        "Phòng nhỏ hay nhà thuê ngại khoan tường thì lưu ngay combo này nha! ✨ Kệ dán tường chịu lực 10kg để đồ siêu gọn, tủ sấy quần áo khử khuẩn thơm tho và đèn led cảm biến từ tính xoay 360 cực chill.\n\n"
        "🛒 Link sắm đồ decor chính hãng:\n"
        f"1. Kệ dán tường đa năng: {th_link1}\n"
        f"2. Tủ sấy quần áo SUNHOUSE: {th_link2}\n"
        f"3. Đèn led cảm biến xoay 360: {th_link3}\n\n"
        "#setupphongxinh #decorphong #kedantuong #tienich"
    )

    results = {}

    # ==========================================
    # PHẦN 1: XUẤT BẢN INSTAGRAM (REELS & STORY)
    # ==========================================
    log("\n📸 [1/2] Đang xuất bản Instagram Reels & Story...")
    try:
        ig_cfg = brand_data.get("instagram", {})
        ig_uploader = InstagramReelsUploader(
            ig_user_id=ig_cfg["ig_user_id"],
            access_token=ig_cfg["access_token"]
        )
        res_ig = ig_uploader.upload_reel(
            video_path=video_path,
            caption=ig_caption,
            comment_text=ig_comments
        )
        results["instagram_reels"] = res_ig
        log(f"✅ Kết quả Instagram Reels: {res_ig}")

        story_cid = post_instagram_story(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
        results["instagram_story"] = {"success": bool(story_cid), "container_id": story_cid}
    except Exception as e:
        log(f"❌ Lỗi đăng Instagram Reels: {e}\n{traceback.format_exc()}")
        results["instagram_reels"] = {"success": False, "error": str(e)}

    # Giãn cách 3-5 phút giữa các nền tảng (giảm tải mạng và tránh spam)
    log("\n⏳ Nghỉ giãn cách 3 phút trước khi đăng Threads...")
    time.sleep(180)

    # ==========================================
    # PHẦN 2: XUẤT BẢN THREADS (VIDEO & 13 REPLIES)
    # ==========================================
    log("\n🧵 [2/2] Đang xuất bản Threads Video & 13 Comment Affiliate...")
    try:
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
        results["threads"] = res_th
        log(f"✅ Kết quả Threads Video: {res_th}")

        if res_th and "id" in res_th:
            thread_post_id = res_th["id"]
            log(f"💬 Đang gửi 13 bình luận Affiliate nối tiếp vào Thread ID: {thread_post_id}...")
            replies_ok = 0
            for idx, cmt in enumerate(th_comments, 1):
                try:
                    time.sleep(2)
                    r_c = requests.post(
                        f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads",
                        data={
                            "media_type": "TEXT_POST",
                            "text": cmt,
                            "reply_to_id": thread_post_id,
                            "access_token": th_cfg["access_token"]
                        },
                        timeout=20
                    ).json()
                    if "id" in r_c:
                        pub_c = requests.post(
                            f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                            data={"creation_id": r_c["id"], "access_token": th_cfg["access_token"]},
                            timeout=20
                        ).json()
                        if "id" in pub_c:
                            replies_ok += 1
                            log(f"  ✅ Đã reply comment Threads {idx}: {cmt[:45]}...")
                        else:
                            log(f"  ⚠️ Lỗi xuất bản comment {idx}: {pub_c}")
                    else:
                        log(f"  ⚠️ Lỗi tạo comment container {idx}: {r_c}")
                except Exception as ce:
                    log(f"  ⚠️ Lỗi gửi comment Threads {idx}: {ce}")
            log(f"🎉 Đã hoàn tất gửi {replies_ok}/{len(th_comments)} comment affiliate lên Threads!")
    except Exception as e:
        log(f"❌ Lỗi đăng Threads: {e}\n{traceback.format_exc()}")
        results["threads"] = {"success": False, "error": str(e)}

    # 3. Cập nhật Queue & Ghi tóm tắt
    update_queue_status(["task_ig_spx_ep3_12h", "task_th_spx_ep3_12h", "task_ig_spx_1790360766"])

    summary_file = r"C:\Affiliate\post1\POST\config\task_spx_ep3_ig_threads_summary.json"
    try:
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "brand": "Setup Phòng Xinh",
                "episode": "Tập 3",
                "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "results": results
            }, f, indent=4, ensure_ascii=False)
        log(f"📄 Tóm tắt đã lưu tại: {summary_file}")
    except Exception:
        pass

    log("\n" + "=" * 80)
    log("🏁 HOÀN TẤT ĐĂNG VIDEO SETUP PHÒNG XINH TẬP 3 LÊN INSTAGRAM & THREADS!")
    log("=" * 80)

if __name__ == "__main__":
    run_post()
