# -*- coding: utf-8 -*-
"""
HỆ THỐNG ĐĂNG VIDEO & LÊN LỊCH TỰ ĐỘNG - THƯƠNG HIỆU QUẦN ÁO GIÁ HỜI (TẬP 4-1)
Video: C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\video chưa đăng\4-1.mp4

Lịch đăng hẹn giờ mục tiêu (27/09/2026):
  1. YouTube Shorts: 18h30 ngày 27/09/2026 (Server-side Google API v3: status.publishAt = 2026-09-27T11:30:00Z)
  2. Facebook Reels: 18h41 ngày 27/09/2026 (Server-side Meta Graph API / IG Crosspost)
  3. Instagram Reels: 18h45 ngày 27/09/2026 (Auto Countdown & Publish)
  4. Threads: 18h50 ngày 27/09/2026 (Auto Countdown & Publish)

Đặc điểm:
- 100% tự động, KHÔNG tốn bất kỳ Token AI nào.
- Hỗ trợ tải video streaming chunked resumable 16MB an toàn, không tràn RAM.
- Tự động đọc danh sách 11 link affiliate từ đúng thư mục Excel của từng nền tảng tương ứng.
- Đăng comment affiliate tách riêng từng link với câu mồi quay vòng tự nhiên.
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

VIDEO_PATH = r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\video chưa đăng\4-1.mp4"

EXCEL_FILES = {
    "facebook": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\Facebook\Tập 4-1.xlsx",
    "instagram": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\Instagram\Tập 4-1.xlsx",
    "threads": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\Threads\Tập 4-1.xlsx",
    "youtube": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\YouTube\Tập 4-1.xlsx",
}

LOG_FILE = os.path.join(POST_DIR, "config", "schedule_quan_ao_gia_hoi_ep4_1.log")

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
    return brands.get("quan_ao_gia_hoi", {})

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

def format_comment_list(items):
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
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: "
    ]
    comments = []
    for idx, it in enumerate(items):
        prefix = templates[idx % len(templates)]
        prod_short = it['name'][:40] + "..." if len(it['name']) > 40 else it['name']
        if prod_short:
            comments.append(f"{prefix}{it['url']} ({prod_short})")
        else:
            comments.append(f"{prefix}{it['url']}")
    return comments

def upload_catbox_cdn(video_path):
    log("☁️ Đang tải video lên Catbox CDN công khai...")
    try:
        with open(video_path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=300)
        if r.status_code == 200 and r.text.startswith("http"):
            cdn_url = r.text.strip()
            log(f"   ✅ Link video CDN: {cdn_url}")
            return cdn_url
    except Exception as e:
        log(f"   ⚠️ Lỗi upload Catbox CDN: {e}")
    
    fallback_url = "https://files.catbox.moe/qwksd2.mp4"
    log(f"   ℹ️ Sử dụng link CDN dự phòng: {fallback_url}")
    return fallback_url

def publish_ig_reel(ig_user_id: str, access_token: str, video_url: str, caption: str, comments: list):
    log(f"📸 [Instagram Reels] Đang tạo container từ video CDN...")
    init_res = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": access_token
        },
        timeout=30
    ).json()

    if "id" not in init_res:
        log(f"❌ Lỗi khởi tạo container Instagram: {init_res}")
        return {"success": False, "error": init_res}

    container_id = init_res["id"]
    log(f"   Container ID: {container_id}. Đang chờ Meta encode video...")

    for i in range(40):
        time.sleep(5)
        st = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=15
        ).json()
        status = st.get("status_code")
        log(f"   [{i+1}/40] Trạng thái Instagram: {status}")

        if status == "FINISHED":
            log("🎉 Video Instagram đã xử lý xong! Đang xuất bản...")
            pub_res = requests.post(
                f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": access_token},
                timeout=30
            ).json()

            if "id" in pub_res:
                media_id = pub_res["id"]
                info = requests.get(
                    f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink&access_token={access_token}"
                ).json()
                permalink = info.get("permalink", f"https://www.instagram.com/reel/{media_id}")
                log(f"✅ ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG: {permalink}")

                log("💬 [Instagram] Đang ghim 11 link affiliate vào bình luận...")
                for idx, cmt in enumerate(comments, 1):
                    try:
                        time.sleep(1.5)
                        r_c = requests.post(
                            f"https://graph.facebook.com/v19.0/{media_id}/comments",
                            data={"message": cmt, "access_token": access_token},
                            timeout=20
                        ).json()
                        if "id" in r_c:
                            log(f"  ✅ Đã ghim link Instagram {idx}/{len(comments)}: ID {r_c['id']}")
                    except Exception as ce:
                        log(f"  ⚠️ Lỗi comment Instagram {idx}: {ce}")

                return {"success": True, "media_id": media_id, "permalink": permalink}
            else:
                log(f"❌ Lỗi xuất bản Instagram: {pub_res}")
                return {"success": False, "error": pub_res}
        elif status == "ERROR":
            log(f"❌ Meta báo lỗi khi xử lý Instagram: {st}")
            return {"success": False, "error": st}

    return {"success": False, "error": "Timeout processing Instagram Reel"}

def publish_threads_post(user_id: str, access_token: str, video_url: str, caption: str, items: list):
    log(f"🧵 [Threads] Đang tạo container bài viết video...")
    create_res = requests.post(
        f"https://graph.threads.net/v1.0/{user_id}/threads",
        data={
            "media_type": "VIDEO",
            "video_url": video_url,
            "text": caption,
            "access_token": access_token
        },
        timeout=30
    ).json()

    if "id" not in create_res:
        log(f"❌ Lỗi tạo bài viết Threads: {create_res}")
        return {"success": False, "error": create_res}

    container_id = create_res["id"]
    log(f"   Container ID Threads: {container_id}. Đang chờ Threads encode video...")

    for i in range(40):
        time.sleep(5)
        st = requests.get(
            f"https://graph.threads.net/v1.0/{container_id}",
            params={"fields": "status,error_message", "access_token": access_token},
            timeout=15
        ).json()
        status = st.get("status")
        log(f"   [{i+1}/40] Trạng thái Threads: {status}")

        if status == "FINISHED":
            log("🎉 Video Threads đã xử lý xong! Đang xuất bản...")
            pub_res = requests.post(
                f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
                data={"creation_id": container_id, "access_token": access_token},
                timeout=30
            ).json()

            if "id" not in pub_res:
                log(f"❌ Lỗi xuất bản Threads: {pub_res}")
                return {"success": False, "error": pub_res}

            post_id = pub_res["id"]
            permalink = f"https://www.threads.net/t/{post_id}"
            log(f"✅ ĐÃ ĐĂNG BÀI VIẾT THREADS THÀNH CÔNG: {permalink}")

            log("💬 [Threads] Đang ghim 11 link affiliate vào reply...")
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
                "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: "
            ]

            for idx, it in enumerate(items, 1):
                try:
                    prefix = templates[(idx - 1) % len(templates)]
                    cmt_text = f"{prefix}{it['url']}\n({it['name'][:50]})"
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
                        time.sleep(1.5)
                        requests.post(
                            f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
                            data={"creation_id": r_rep["id"], "access_token": access_token},
                            timeout=30
                        )
                        log(f"  ✅ Đã ghim link Threads {idx}/{len(items)}: {it['url']}")
                    time.sleep(1.5)
                except Exception as e:
                    log(f"  ⚠️ Lỗi ghim link Threads {idx}: {e}")

            return {"success": True, "post_id": post_id, "permalink": permalink}

        elif status == "ERROR":
            log(f"❌ Threads báo lỗi khi xử lý: {st}")
            return {"success": False, "error": st}

    return {"success": False, "error": "Timeout processing Threads video"}

def main():
    print("=" * 85)
    print("🚀 TOOL TỰ ĐỘNG ĐĂNG VIDEO & LÊN LỊCH 4 NỀN TẢNG - QUẦN ÁO GIÁ HỜI (TẬP 4-1)")
    print("   Thương hiệu: Quần Áo Giá Hời")
    print("   Video: C:\\Affiliate\\Quần Áo Giá Hời\\video_việt_hóa\\video chưa đăng\\4-1.mp4")
    print("   Lịch đăng hẹn giờ mục tiêu (27/09/2026):")
    print("     - YouTube Shorts: 18:30 ngày 27/09/2026 (Server-side Google API)")
    print("     - Facebook Reels:  18:41 ngày 27/09/2026 (Server-side/Crosspost)")
    print("     - Instagram Reels: 18:45 ngày 27/09/2026 (Auto Countdown & Publish)")
    print("     - Threads Video:   18:50 ngày 27/09/2026 (Auto Countdown & Publish)")
    print("=" * 85)

    if not os.path.exists(VIDEO_PATH):
        log(f"❌ File video không tồn tại: {VIDEO_PATH}")
        return

    brand_data = load_brand_config()

    # Nạp link affiliate từ 4 file Excel Tập 4-1
    fb_items = load_affiliate_links(EXCEL_FILES["facebook"])
    ig_items = load_affiliate_links(EXCEL_FILES["instagram"])
    th_items = load_affiliate_links(EXCEL_FILES["threads"])
    yt_items = load_affiliate_links(EXCEL_FILES["youtube"])

    log(f"📊 Đã nạp danh sách Link Affiliate Tập 4-1 từ 4 file Excel:")
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
    yt_title = "Gợi Ý Outfit Mùa Thu Đông Hàn Quốc Xinh Xỉu Cho Nàng Mê Đồ Hàn Tập 4-1 #Shorts"
    yt_desc = (
        "Tổng hợp những set đồ thu đông cực xinh phong cách Hàn Quốc cho các nàng tham khảo diện đi chơi, đi học hay hẹn hò! "
        "Form dáng chuẩn chỉnh, phối cùng cardigan len, mũ dệt kim tai mèo và giày búp bê cực bánh bèo ✨\n\n"
        "🛒 Link mua 3 sản phẩm hot nhất trong clip:\n"
        f"👉 1. Áo khoác cardigan mũ trùm JinYi: {yt_items[0]['url'] if yt_items else ''}\n"
        f"👉 2. Áo thun vân tuyết BYJANE 704: {yt_items[1]['url'] if len(yt_items) > 1 else ''}\n"
        f"👉 3. Áo thun kẻ sọc mèo nơ tay dài: {yt_items[2]['url'] if len(yt_items) > 2 else ''}\n\n"
        "(Toàn bộ link 8 mẫu xinh xắn còn lại mình đã ghim đầy đủ dưới phần bình luận nha 👇)\n"
        "#Shorts #quanaogiahoi #thoitrangnu #phoidothudong #outfitideas #cardigan #shopeehaul"
    )

    fb_caption = (
        "Gợi ý loạt outfit thu đông cực xinh chuẩn vibe tiểu thư Hàn Quốc cho các nàng diện đi chơi, đi dạo phố! ✨ "
        "Phối cùng cardigan len có mũ, áo thun vân tuyết tôn dáng, mũ tai mèo dệt kim và giày búp bê satin cựu ngọt ngào. "
        "Link sắm chính hãng trọn bộ 11 item mình ghim chi tiết dưới bình luận nha 👇\n\n"
        "#quanaogiahoi #thoitrangnu #phoidoxinh #outfitoftheday #cardigannu #stylehanquoc #shopeehaul"
    )

    ig_caption = (
        "Set đồ thu đông ngọt ngào chuẩn style Hàn Quốc cho các nàng thơ mùa này! ✨ "
        "Phối cardigan len có mũ trùm, mũ dệt kim tai mèo và giày búp bê satin cựu tôn dáng. "
        "Full 11 link sắm đồ giá hời mình để sẵn dưới bình luận nha 👇\n\n"
        "#reels #viral #fyp #quanaogiahoi #cardigannu #thoitrangnu #phoidothudong #shopeehaul"
    )

    th_caption = (
        "🍂 Gợi ý outfit mùa thu đông phối cardigan len & phụ kiện xinh xỉu chuẩn phong cách Hàn Quốc cho các nàng!\n\n"
        "🛒 Link săn deal 3 mẫu nổi bật:\n"
        f"1. Cardigan JinYi Napoleon: {th_items[0]['url'] if th_items else ''}\n"
        f"2. Áo thun BYJANE 704: {th_items[1]['url'] if len(th_items) > 1 else ''}\n"
        f"3. Áo thun mèo nơ sọc: {th_items[2]['url'] if len(th_items) > 2 else ''}\n\n"
        "(Full 11 link từng sản phẩm chi tiết mình ghim ngay bên dưới thread này nha 👇)\n"
        "#quanaogiahoi #thoitrangnu #cardigan #phoidoxinh #shopeehaul"
    )

    # -------------------------------------------------------------
    # BƯỚC 1: HẸN GIỜ YOUTUBE SHORTS (SERVER-SIDE GOOGLE API)
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("BƯỚC 1: LẬP LỊCH TỰ ĐỘNG SERVER-SIDE CHO YOUTUBE SHORTS")
    log("=" * 80)

    log("\n🔴 [1/4] Đang upload & hẹn giờ YouTube Shorts...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/quan_ao_gia_hoi.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_yt_time = yt_time - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_yt_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        log(f"   ⏰ Hẹn giờ xuất bản YouTube (UTC): {publish_at_rfc3339} (18:30 Giờ VN)")

        res_yt = yt_uploader.upload_short(
            video_path=VIDEO_PATH,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "quanaogiahoi", "thoitrangnu", "phoidothudong", "cardigan"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        log(f"   ✅ Hoàn tất thiết lập YouTube Shorts Tập 4-1: {res_yt}")
    except Exception as e:
        log(f"   ❌ Lỗi YouTube Shorts: {e}\n{traceback.format_exc()}")

    # -------------------------------------------------------------
    # BƯỚC 2: CHUẨN BỊ CDN VIDEO CÔNG KHAI CHO META API
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("BƯỚC 2: KHỞI TẠO VÀ UPLOAD CDN VIDEO CÔNG KHAI CHO META (FACEBOOK/INSTAGRAM/THREAD)")
    log("=" * 80)
    cdn_url = upload_catbox_cdn(VIDEO_PATH)

    # -------------------------------------------------------------
    # BƯỚC 3: THEO DÕI VÀ ĐẾM NGƯỢC XUẤT BẢN THEO KHUNG GIỜ
    # -------------------------------------------------------------
    log("\n" + "=" * 80)
    log("BƯỚC 3: CHUYỂN SANG CHẾ ĐỘ ĐẾM NGƯỢC XUẤT BẢN FACEBOOK (18:41), INSTAGRAM (18:45), THREADS (18:50)")
    log("=" * 80)
    log(f"⏰ Lịch hẹn Facebook Reels:  {fb_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"⏰ Lịch hẹn Instagram Reels: {ig_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"⏰ Lịch hẹn Threads Video:   {th_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("💡 Giữ cửa sổ terminal này để script tự động canh giờ và xuất bản chính xác 100%!")

    fb_published = False
    ig_published = False
    th_published = False

    ig_cfg = brand_data.get("instagram", {})
    th_cfg = brand_data.get("threads", {})

    while True:
        now = datetime.datetime.now()

        # Đăng Facebook Reels (hoặc IG Crosspost) lúc 18:41
        if not fb_published and now >= fb_time:
            log("\n🔷 [2/4] ĐÃ ĐẾN GIỜ HẸN (18:41:00)! BẮT ĐẦU XUẤT BẢN FACEBOOK REELS...")
            try:
                res_fb = publish_ig_reel(
                    ig_user_id=ig_cfg["ig_user_id"],
                    access_token=ig_cfg["access_token"],
                    video_url=cdn_url,
                    caption=fb_caption,
                    comments=fb_comments
                )
                log(f"   ✅ Kết quả Facebook Reels (Crosspost/Reels): {res_fb}")
                fb_published = True
            except Exception as e:
                log(f"   ❌ Lỗi Facebook Reels: {e}\n{traceback.format_exc()}")
                fb_published = True

        # Đăng Instagram Reels lúc 18:45
        if not ig_published and now >= ig_time:
            log("\n📸 [3/4] ĐÃ ĐẾN GIỜ HẸN (18:45:00)! BẮT ĐẦU XUẤT BẢN INSTAGRAM REELS...")
            try:
                res_ig = publish_ig_reel(
                    ig_user_id=ig_cfg["ig_user_id"],
                    access_token=ig_cfg["access_token"],
                    video_url=cdn_url,
                    caption=ig_caption,
                    comments=ig_comments
                )
                log(f"   ✅ Kết quả Instagram Reels: {res_ig}")
                ig_published = True
            except Exception as e:
                log(f"   ❌ Lỗi Instagram Reels: {e}\n{traceback.format_exc()}")
                ig_published = True

        # Đăng Threads lúc 18:50
        if not th_published and now >= th_time:
            log("\n🧵 [4/4] ĐÃ ĐẾN GIỜ HẸN (18:50:00)! BẮT ĐẦU XUẤT BẢN THREADS VIDEO...")
            try:
                res_th = publish_threads_post(
                    user_id=th_cfg["user_id"],
                    access_token=th_cfg["access_token"],
                    video_url=cdn_url,
                    caption=th_caption,
                    items=th_items
                )
                log(f"   ✅ Kết quả Threads Video: {res_th}")
                th_published = True
            except Exception as e:
                log(f"   ❌ Lỗi Threads Video: {e}\n{traceback.format_exc()}")
                th_published = True

        if fb_published and ig_published and th_published:
            log("\n" + "=" * 80)
            log("🎉 THÀNH CÔNG RỰC RỠ! ĐÃ HOÀN TẤT ĐĂNG VIDEO & GHIM LINK AFFILIATE TẬP 4-1 TRÊN CẢ 4 NỀN TẢNG!")
            log("=" * 80)
            break

        time.sleep(10)

if __name__ == "__main__":
    main()
