# -*- coding: utf-8 -*-
"""
Script đăng hẹn giờ video Tập 4 cho thương hiệu "Yêu Da Hơn Bồ" lên 4 nền tảng:
- YouTube Shorts: 18h30 ngày 27/09/2026 (Server-side Google API v3)
- Facebook Reels (+ Story): 18h41 ngày 27/09/2026 (Server-side Meta Graph API)
- Instagram Reels (+ Story): 18h45 ngày 27/09/2026 (Chờ xuất bản đúng giờ)
- Threads: 18h50 ngày 27/09/2026 (Chờ xuất bản đúng giờ)
"""

import os
import sys
import time
import json
import requests
import datetime
import traceback

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

LOG_FILE = r"C:\Affiliate\post1\POST\config\scheduler_yeu_da_hon_bo_ep4.log"

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
    return brands.get("yeu_da_hon_bo", {})

def post_facebook_story(page_id: str, access_token: str, video_path: str):
    try:
        log("📘 Đang tạo Story cho Facebook Page Yêu Da Hơn Bồ...")
        file_size = os.path.getsize(video_path)
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/videos",
            data={
                "upload_phase": "start",
                "file_size": file_size,
                "access_token": access_token
            },
            timeout=30
        ).json()
        if "upload_session_id" in init_res:
            upload_session_id = init_res["upload_session_id"]
            headers = {
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size)
            }
            with open(video_path, "rb") as f:
                vbytes = f.read(1024 * 1024 * 10)
            r_up = requests.post(
                f"https://graph.facebook.com/v19.0/{upload_session_id}",
                headers=headers,
                data=vbytes,
                timeout=60
            ).json()
            log(f"  ✅ Trạng thái upload Story FB: {r_up}")
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng FB Story: {e}")

def post_instagram_story(ig_user_id: str, access_token: str, video_path: str):
    try:
        log("📸 Đang khởi tạo Story cho Instagram Business Yêu Da Hơn Bồ...")
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={
                "media_type": "STORIES",
                "upload_type": "resumable",
                "access_token": access_token
            },
            timeout=30
        ).json()
        if "id" in init_res:
            container_id = init_res["id"]
            log(f"  ✅ Đã tạo IG Story Container: {container_id}")
    except Exception as e:
        log(f"  ⚠️ Lưu ý đăng IG Story: {e}")

def reply_threads_comments(th_cfg: dict, thread_post_id: str, comments: list):
    log(f"💬 [Threads] Đang tự động gửi bình luận Affiliate vào Thread ID {thread_post_id}...")
    for idx, cmt in enumerate(comments, 1):
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
                log(f"  ✅ Đã gửi reply comment Threads {idx}: {cmt[:45]}...")
        except Exception as e:
            log(f"  ⚠️ Lỗi reply Threads {idx}: {e}")

def run_schedule():
    log("=" * 70)
    log("💖 BẮT ĐẦU QUY TRÌNH HẸN GIỜ ĐĂNG VIDEO (27/09/2026): YÊU DA HƠN BỒ (TẬP 4)")
    log("=" * 70)

    brand_data = load_config()
    
    # Tìm file video 4.mp4 trong thư mục video chưa đăng hoặc video đã đăng
    video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\video chưa đăng\4.mp4"
    if not os.path.exists(video_path):
        video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\video đã đăng\4.mp4"
    if not os.path.exists(video_path):
        video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\4.mp4"

    if not os.path.exists(video_path):
        log(f"❌ Không tìm thấy video Tập 4 tại bất kỳ đường dẫn nào!")
        return

    log(f"📁 Video sử dụng: {video_path}")

    # Metadata & SEO Chuẩn Viral cho 4 nền tảng
    # 1. YouTube Shorts (18:30:00 - 27/09/2026)
    yt_title = "Combo Kem Chống Nắng Phổ Rộng & Mặt Nạ V-Line Nâng Cơ Thon Gọn Mặt #Shorts"
    yt_desc = (
        "Bí quyết bảo vệ & định hình nhan sắc toàn diện: Chống nắng phổ rộng nâng tông bảo vệ da khỏi tia UV mẩn đỏ, kết hợp cùng mặt nạ định hình cằm V-line giúp cơ mặt thon gọn tự nhiên. "
        "Da vừa sáng mịn căng bóng vừa có cằm Vline thanh thoát!\n\n"
        "#Shorts #yeudahonbo #kemchongnang #matnanangco #matnavline #chamsocda #skincareroutine"
    )
    yt_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/50ZGAO79Dz",
        "Link sản phẩm: https://s.shopee.vn/1BMXbLLk0M",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/20veasIZJd",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8plyjQsYS4",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9fL5ixpNlL",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/5q8N9v3yXi",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6fhU9S0nqz",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/2gBLO6G1yK",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/3qNImFBabf",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/50ZGAO79F0",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/qjhCjN0hJ",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/20veasIZKe",
        "Link xem deal hot ở đây nhé mọi người: https://s.shopee.vn/8V98Kotp91",
        "Mọi người săn voucher giảm giá tại đây nha: https://s.shopee.vn/6VO3x91iEA"
    ]

    # 2. Facebook Reels & Story (18:41:00 - 27/09/2026)
    fb_title = "Bí quyết chống nắng nâng tông và đai định hình cằm V-Line thon gọn"
    fb_caption = (
        "Nắng gắt dễ sạm da mà nọng cằm lại làm gương mặt bớt thon gọn? "
        "Bỏ túi ngay bộ đôi cứu tinh: Kem chống nắng phổ rộng bảo vệ da tối đa kết hợp đai mặt nạ định hình cằm V-line thon gọn nhẹ nhàng ✨\n\n"
        "👉 Sắm ngay Kem chống nắng La Prairie & Clinicos chính hãng tại: https://s.shopee.vn/W6qo7OGsA\n\n"
        "#reels #viral #fyp #yeudahonbo #kemchongnang #nangcovline #skincaretips #lamdep"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6qo7OGsA",
        "Link sản phẩm: https://s.shopee.vn/1LfxneL6bL",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/1BMXbLLjyN",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2VrvBnGfIk",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8fSYX7tBn3",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/AAHMJsnTkS",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5fowxc4bsh",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/7AdkkMytq6",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/2qUlaPFOdN",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/40giyYAxGi",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/5AsgMh6Vu3",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/1137P2MNMM",
        "Link xem deal hot ở đây nhé mọi người: https://s.shopee.vn/2BF4nBHvzh",
        "Mọi người săn voucher giảm giá tại đây nha: https://s.shopee.vn/8fSYX7tBo4"
    ]

    # 3. Instagram Reels & Story (18:45:00 - 27/09/2026)
    ig_caption = (
        "Bí quyết dưỡng da căng bóng chống sạm nắng và định hình góc mặt V-line thanh thoát! "
        "Kem chống nắng phổ rộng kết hợp đai nạ định hình cằm giúp cơ mặt săn chắc không lo chảy xệ ✨ "
        "Link trọn bộ skincare chính hãng mình để dưới cmt nha 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #sunscreen #vlinemask #skincareroutine #beautytips"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/4VczZT93Eo",
        "Link sản phẩm: https://s.shopee.vn/1AaDCQBN3",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/1VzNzxKTKS",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/2LYUzUHIdj",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9AOp82rHmA",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/9zxw7Zo75R",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6AlDYX2hro",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/70KKY3zXB5",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/30oBmiElIQ",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/4B09ArAJvl",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/1AaDCQBO4",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/1BMXbLLk1P",
        "Link xem deal hot ở đây nhé mọi người: https://s.shopee.vn/2LYUzUHIek",
        "Mọi người săn voucher giảm giá tại đây nha: https://s.shopee.vn/8plyjQsYT7"
    ]

    # 4. Threads (18:50:00 - 27/09/2026)
    th_caption = (
        "Mùa này vừa lo da sạm đen vừa lo nọng cằm chảy xệ thì lưu ngay combo này! KCN phổ rộng nâng tông bảo vệ da siêu đỉnh, kết hợp đai đeo cằm V-line định hình thon gọn ✨\n\n"
        "🛒 Link sắm đồ dưỡng da chính hãng nè cả nhà:\n"
        "1. KCN Clinicos / AHC căng mướt da: https://s.shopee.vn/W6qo7OHMA\n"
        "2. Mặt nạ V-Line định hình cằm: https://s.shopee.vn/60RnME3LCn\n\n"
        "#yeudahonbo #skincare #sunscreen #vlinemask"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/4LJZNA9gZn",
        "Link sản phẩm: https://s.shopee.vn/W6qo7OHMA",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/1LfxneL6fR",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/8AWHwCv5ns",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/905Ovjrv79",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/AUuCiUmD4Y",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/60RnME3LCn",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/7VGb8yxdAC",
        "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/3B7bz1E7xT",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/4LJZNA9gao",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/BU0PVPY37",
        "Nhấp vào link này để xem thông tin và mua hàng nha mọi người: https://s.shopee.vn/1LfxneL6gS",
        "Link xem deal hot ở đây nhé mọi người: https://s.shopee.vn/2VrvBnGfJn",
        "Mọi người săn voucher giảm giá tại đây nha: https://s.shopee.vn/905Ovjrv8A"
    ]

    # Thiết lập mốc thời gian xuất bản mục tiêu: 27/09/2026
    target_date = datetime.date(2026, 9, 27)
    yt_dt = datetime.datetime.combine(target_date, datetime.time(18, 30, 0))
    fb_dt = datetime.datetime.combine(target_date, datetime.time(18, 41, 0))
    ig_dt = datetime.datetime.combine(target_date, datetime.time(18, 45, 0))
    th_dt = datetime.datetime.combine(target_date, datetime.time(18, 50, 0))

    log(f"📅 YouTube Shorts xuất bản lúc: {yt_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 Facebook Reels (+Story) xuất bản lúc: {fb_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 Instagram Reels (+Story) xuất bản lúc: {ig_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 Threads xuất bản lúc: {th_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. YOUTUBE SHORTS (Hẹn giờ qua Native Google API v3)
    log("\n🔴 [1/4] Khởi tạo & Lập lịch YouTube Shorts (Google API v3)...")
    try:
        yt_cfg = brand_data.get("youtube", {})
        token_path = os.path.join(POST_DIR, yt_cfg.get("token_file", "credentials/youtube_tokens/yeu_da_hon_bo.json"))
        yt_uploader = YouTubeShortsUploader(token_file=token_path)
        
        utc_target = yt_dt - datetime.timedelta(hours=7)
        publish_at_rfc3339 = utc_target.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=yt_title,
            description=yt_desc,
            tags=["Shorts", "yeudahonbo", "kemchongnang", "matnanangco", "matnavline"],
            comment_text=yt_comments,
            privacy_status="private",
            publish_at=publish_at_rfc3339
        )
        log(f"✅ Kết quả YouTube Shorts: {res_yt}")
    except Exception as e:
        log(f"❌ Lỗi lên lịch YouTube Shorts: {e}\n{traceback.format_exc()}")

    # 2. FACEBOOK REELS & STORY (Hẹn giờ qua Native Meta Graph API)
    log("\n🔷 [2/4] Khởi tạo & Lập lịch Facebook Reels (Meta API Scheduled)...")
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
            scheduled_time=int(fb_dt.timestamp())
        )
        log(f"✅ Kết quả Facebook Reels: {res_fb}")
        post_facebook_story(fb_cfg["page_id"], fb_cfg["access_token"], video_path)
    except Exception as e:
        log(f"❌ Lỗi lên lịch Facebook Reels: {e}\n{traceback.format_exc()}")

    # 3 & 4. INSTAGRAM REELS (+ STORY) & THREADS (Chạy đếm ngược xuất bản tự động trên máy)
    log("\n📸 [3/4] & 🧵 [4/4] Đang đưa Instagram & Threads vào trình theo dõi đếm ngược xuất bản máy tính...")
    
    ig_done = False
    th_done = False

    while True:
        current_time = datetime.datetime.now()

        # Xuất bản Instagram Reels + Story
        if not ig_done and current_time >= ig_dt:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ VÀNG INSTAGRAM ({ig_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN INSTAGRAM REELS & STORY...")
            try:
                ig_cfg = brand_data.get("instagram", {})
                
                # Tải video lên Catbox CDN trước để lấy URL direct cho Instagram container
                file_size = os.path.getsize(video_path)
                headers = {"User-Agent": "Mozilla/5.0"}
                video_url = None
                try:
                    with open(video_path, "rb") as f:
                        r = requests.post("https://catbox.moe/user/api.php", headers=headers, data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=300)
                    if r.status_code == 200 and r.text.startswith("http"):
                        video_url = r.text.strip()
                except Exception as ex_cb:
                    log(f"  ⚠️ Lỗi upload Catbox IG: {ex_cb}")

                if video_url:
                    # Đăng qua video_url
                    ig_url = f"https://graph.facebook.com/v19.0/{ig_cfg['ig_user_id']}/media"
                    r_ct = requests.post(ig_url, data={"media_type": "REELS", "video_url": video_url, "caption": ig_caption, "access_token": ig_cfg["access_token"]}).json()
                    if "id" in r_ct:
                        container_id = r_ct["id"]
                        log(f"  ✅ Đã tạo IG Reel container từ URL: {container_id}")
                        for _ in range(30):
                            time.sleep(3)
                            st = requests.get(f"https://graph.facebook.com/v19.0/{container_id}", params={"fields": "status_code,status", "access_token": ig_cfg["access_token"]}).json()
                            if st.get("status_code") == "FINISHED":
                                break
                        pub = requests.post(f"https://graph.facebook.com/v19.0/{ig_cfg['ig_user_id']}/media_publish", data={"creation_id": container_id, "access_token": ig_cfg["access_token"]}).json()
                        log(f"  ✅ Kết quả publish IG Reels: {pub}")
                        if "id" in pub:
                            media_id = pub["id"]
                            for idx, c in enumerate(ig_comments, 1):
                                time.sleep(2)
                                requests.post(f"https://graph.facebook.com/v19.0/{media_id}/comments", data={"message": c, "access_token": ig_cfg["access_token"]})
                else:
                    # Fallback binary upload
                    ig_uploader = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
                    res_ig = ig_uploader.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
                    log(f"✅ Kết quả Instagram Reels Fallback: {res_ig}")

                post_instagram_story(ig_cfg["ig_user_id"], ig_cfg["access_token"], video_path)
            except Exception as e:
                log(f"❌ Lỗi xuất bản Instagram Reels: {e}\n{traceback.format_exc()}")
            ig_done = True

        # Xuất bản Threads
        if not th_done and current_time >= th_dt:
            log(f"\n⏰ ĐÃ ĐẾN GIỜ VÀNG THREADS ({th_dt.strftime('%H:%M:%S')})! BẮT ĐẦU XUẤT BẢN THREADS...")
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
                log(f"✅ Kết quả Threads: {res_th}")
                if res_th and "id" in res_th:
                    reply_threads_comments(th_cfg, res_th["id"], th_comments)
            except Exception as e:
                log(f"❌ Lỗi xuất bản Threads: {e}\n{traceback.format_exc()}")
            th_done = True

        if ig_done and th_done:
            log("\n🎉 HOÀN THÀNH TẤT CẢ TIẾN TRÌNH HẸN GIỜ CHO YÊU DA HƠN BỒ TẬP 4 (YOUTUBE, FACEBOOK, INSTAGRAM, THREADS)!")
            break

        time.sleep(10)

if __name__ == "__main__":
    run_schedule()
