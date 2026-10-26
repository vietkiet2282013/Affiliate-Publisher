# -*- coding: utf-8 -*-
"""
Chạy đăng lại Meta (Facebook Reels, IG, Threads) cho 3 thương hiệu:
1. Chăm Da Tiết Kiệm
2. Quần Áo Giá Hời
3. Yêu Da Hơn Bồ
(Không đăng lại YouTube Shorts vì YouTube đã lên thành công 100%)
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
    ThreadsAPIUploader
)

LOG_FILE = r"C:\Affiliate\post1\POST\config\instant_retry_3_brands.log"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_brands():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def reply_threads_comments(th_cfg: dict, thread_post_id: str, comments: list):
    log(f"  💬 [Threads] Đang tự động gửi bình luận Affiliate vào Thread {thread_post_id}...")
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
                requests.post(
                    f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                    data={"creation_id": r_c["id"], "access_token": th_cfg["access_token"]},
                    timeout=20
                )
                log(f"    ✅ Đã gửi comment Threads {idx}: {cmt[:40]}...")
        except Exception as e:
            log(f"    ⚠️ Lỗi reply Threads {idx}: {e}")

# ==============================================================================
# 1. CHĂM DA TIẾT KIỆM
# ==============================================================================
def publish_cham_da_tiet_kiem(brands):
    log("\n" + "="*70)
    log("🚀 [1/3] ĐĂNG LẠI META CHO: CHĂM DA TIẾT KIỆM")
    log("="*70)
    brand_data = brands.get("cham_da_tiet_kiem", {})
    video_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\4.mp4"

    fb_title = "Dầu dưỡng tái tạo La Mer The Renewal Oil"
    fb_caption = (
        "Dầu dưỡng tái tạo đỉnh chóp La Mer The Renewal Oil phục hồi cấp ẩm chuyên sâu ✨ "
        "Da căng bóng ngậm nước ngay sau vài giọt! Cùng Chăm Da Tiết Kiệm review chân thực nhé. "
        "Link sản phẩm chính hãng mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #chamdatietkiem #lamer #therenewaloil #dauduongda #skincareroutine"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6vCL7rpo"
    ]

    ig_caption = (
        "Cứu tinh cho làn da khô ráp, thiếu sức sống hay treatment! Dầu dưỡng tái tạo da La Mer The Renewal Oil đa năng "
        "thẩm thấu nhanh, nuôi dưỡng da căng mọng, mịn màng và phục hồi hàng rào bảo vệ da đỉnh cao ✨ "
        "Đầu tư một lần dùng mê li! Link sắm hàng chuẩn Auth bên dưới comment nha 👇\n\n"
        "#reels #viral #fyp #chamdatietkiem #lamer #skincareroutine #dauduong #beautytips"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6vCL7rpo"
    ]

    th_caption = (
        "Mùa hanh khô hay da đang treatment thì dầu dưỡng tái tạo La Mer The Renewal Oil đúng là chân ái! Nhỏ 2-3 giọt xoa đều là da căng bóng, ngậm nước và phục hồi hàng rào ẩm siêu nhanh ✨\n\n"
        "🛒 Link sắm dầu dưỡng La Mer chính hãng:\n"
        "👉 https://s.shopee.vn/W6vCL7rpo\n\n"
        "#chamdatietkiem #lamer #skincare #dauduongda"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/W6vCL7rpo"
    ]

    # Facebook Reels
    try:
        log("🔷 [Facebook] Đang đăng Reel Chăm Da Tiết Kiệm...")
        fb_cfg = brand_data.get("facebook", {})
        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        res_fb = fb.upload_reel(video_path=video_path, title=fb_title, caption=fb_caption, comment_text=fb_comments, scheduled_time=None)
        log(f"✅ Kết quả Facebook Reels [Chăm Da Tiết Kiệm]: {res_fb}")
    except Exception as e:
        log(f"❌ Lỗi Facebook Reels [Chăm Da Tiết Kiệm]: {e}\n{traceback.format_exc()}")

    # Instagram Reels
    try:
        log("📸 [Instagram] Đang đăng Reel Chăm Da Tiết Kiệm...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels [Chăm Da Tiết Kiệm]: {res_ig}")
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels [Chăm Da Tiết Kiệm]: {e}\n{traceback.format_exc()}")

    # Threads
    try:
        log("🧵 [Threads] Đang đăng Threads Chăm Da Tiết Kiệm...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads [Chăm Da Tiết Kiệm]: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads [Chăm Da Tiết Kiệm]: {e}\n{traceback.format_exc()}")

# ==============================================================================
# 2. QUẦN ÁO GIÁ HỜI
# ==============================================================================
def publish_quan_ao_gia_hoi(brands):
    log("\n" + "="*70)
    log("👗 [2/3] ĐĂNG LẠI META CHO: QUẦN ÁO GIÁ HỜI")
    log("="*70)
    brand_data = brands.get("quan_ao_gia_hoi", {})
    video_path = r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\2.mp4"

    fb_title = "Tổng hợp áo khoác mùa đông giá rẻ xu hướng"
    fb_caption = (
        "Tổng hợp những mẫu áo khoác mùa đông siêu xinh, hack dáng tôn da mà giá hạt dẻ không tưởng ✨ "
        "Từ măng tô dáng dài, cardigan len đến nỉ croptop năng động, sắm ngay kẻo lỡ nha! "
        "Toàn bộ link shop uy tín mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #quanaogiahoi #aokhoacnu #cardigan #mangto #thoitrangnu #ootd"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/50JslL5sWn",
        "Link sản phẩm: https://s.shopee.vn/5pq4Yh6x5r",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/2VrvjX87wA",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/gArZ2iI3D",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2ft6sBqC1C",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/9Ul90mR3tC",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/3LBgN7e01I"
    ]

    ig_caption = (
        "Gợi ý loạt áo khoác mùa đông cực đỉnh vừa ấm vừa sang chảnh cho các nàng đây! "
        "Form dáng chuẩn chỉnh, phối đồ đi học, đi chơi hay đi làm đều siêu nổi bật ✨ "
        "Giá đang sale cực hời! Chi tiết từng mẫu mình để sẵn link mua dưới comment nha 👇\n\n"
        "#reels #viral #fyp #quanaogiahoi #fashionstyle #aokhoac #winteroutfit #thoitranggenz"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/3Apn5V5s1l",
        "Link sản phẩm: https://s.shopee.vn/20veq01kS1",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/1qMKi8k41r",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AAHLbM3o4y",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/50JslW9Z21"
    ]

    th_caption = (
        "Tổng hợp outfit áo khoác đông siêu xinh, ấm áp và cực kỳ tôn dáng cho hội chị em ✨ Săn ngay deal áo đẹp giá siêu hời nha!\n\n"
        "🛒 Link sắm từng mẫu áo khoác xinh nè:\n"
        "1. Áo khoác Cardigan len dày dặn: https://s.shopee.vn/8fD7h5W201\n"
        "2. Áo Măng tô dạ suông Hàn Quốc: https://s.shopee.vn/4VNRf7a505\n"
        "3. Áo nỉ Croptop năng động cá tính: https://s.shopee.vn/60CQ9h3k8s\n\n"
        "#quanaogiahoi #thoitrangnu #aokhoacmuadong #ootd"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/8fD7h5W201",
        "Link sản phẩm: https://s.shopee.vn/4VNRf7a505",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/60CQ9h3k8s",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AUeqx8W7rA"
    ]

    # Facebook Reels
    try:
        log("🔷 [Facebook] Đang đăng Reel Quần Áo Giá Hời...")
        fb_cfg = brand_data.get("facebook", {})
        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        res_fb = fb.upload_reel(video_path=video_path, title=fb_title, caption=fb_caption, comment_text=fb_comments, scheduled_time=None)
        log(f"✅ Kết quả Facebook Reels [Quần Áo Giá Hời]: {res_fb}")
    except Exception as e:
        log(f"❌ Lỗi Facebook Reels [Quần Áo Giá Hời]: {e}\n{traceback.format_exc()}")

    # Instagram Reels
    try:
        log("📸 [Instagram] Đang đăng Reel Quần Áo Giá Hời...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels [Quần Áo Giá Hời]: {res_ig}")
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels [Quần Áo Giá Hời]: {e}\n{traceback.format_exc()}")

    # Threads
    try:
        log("🧵 [Threads] Đang đăng Threads Quần Áo Giá Hời...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads [Quần Áo Giá Hời]: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads [Quần Áo Giá Hời]: {e}\n{traceback.format_exc()}")

# ==============================================================================
# 3. YÊU DA HƠN BỒ
# ==============================================================================
def publish_yeu_da_hon_bo(brands):
    log("\n" + "="*70)
    log("💖 [3/3] ĐĂNG LẠI META CHO: YÊU DA HƠN BỒ")
    log("="*70)
    brand_data = brands.get("yeu_da_hon_bo", {})
    video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\2.mp4"

    fb_title = "Top toner pad và mặt nạ định hình cằm V-line"
    fb_caption = (
        "Bí kíp cho làn da căng mọng bóng mượt và gương mặt thon gọn sắc nét ✨ "
        "Top toner pad cấp ẩm dịu da đỉnh nhất cùng mặt nạ định hình V-line giúp gương mặt thanh thoát rõ rệt! "
        "Chi tiết link mua chính hãng mình để dưới phần bình luận nha 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #tonerpad #matnavline #skincareroutine #chamsocda"
    )
    fb_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/5pq4YnF7qM",
        "Link sản phẩm: https://s.shopee.vn/2VrvjXb7nB",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/6Kpf5c48k1",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/9A9X9h21lO",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2ft6sBvD4F",
        "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/3Apn5V9B8P",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/9Ul90mUk8M",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/70FshV81oK",
        "Mình để sẵn link mua hàng ở đây cho mọi người tham khảo: https://s.shopee.vn/20veq04nF5",
        "Bạn nào quan tâm thì bấm trực tiếp vào link này nhé: https://s.shopee.vn/1qMKi8nW2r",
        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/8fD7h5Z33R",
        "Link ở đây nha: https://s.shopee.vn/4VNRf7de2M"
    ]

    ig_caption = (
        "Gợi ý routine chăm da chuẩn Hàn cho nàng da mụn, nhạy cảm thiếu ẩm! "
        "Bộ đôi toner pad làm dịu tức thì kết hợp mặt nạ nâng cơ thon gọn hàm V-line siêu hiệu quả ✨ "
        "Chăm chỉ mỗi ngày để có làn da phát sáng nha! Link sản phẩm chính hãng ở comment 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #beautyreview #skincaretips #tonerpadkorea #vline"
    )
    ig_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/50JslL8nB1",
        "Link sản phẩm: https://s.shopee.vn/AAHLbM5l8k",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/60CQ9h6X3l",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AUeqx8ZZ5m",
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3LBgN7h34F"
    ]

    th_caption = (
        "Muốn da căng bóng mịn màng không tì vết lại có góc nghiêng thần thánh? Tậu ngay combo Toner Pad cấp ẩm sâu + Mặt nạ thon gọn cằm V-line này nha ✨\n\n"
        "🛒 Link sắm đồ dưỡng da chính hãng:\n"
        "1. Toner Pad Torriden cấp nước đa tầng: https://s.shopee.vn/20w1w8a74H\n"
        "2. Toner Pad Balanceful Cica làm dịu da mụn: https://s.shopee.vn/8zqWw2f35A\n"
        "3. Mặt nạ định hình cằm V-Line nâng cơ: https://s.shopee.vn/1g4Kk6q81m\n\n"
        "#yeudahonbo #skincare #tonerpad #matnavline"
    )
    th_comments = [
        "Link sản phẩm ở đây: https://s.shopee.vn/20w1w8a74H",
        "Link sản phẩm: https://s.shopee.vn/8zqWw2f35A",
        "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/1g4Kk6q81m",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/AUesr4Y12k"
    ]

    # Facebook Reels
    try:
        log("🔷 [Facebook] Đang đăng Reel Yêu Da Hơn Bồ...")
        fb_cfg = brand_data.get("facebook", {})
        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        res_fb = fb.upload_reel(video_path=video_path, title=fb_title, caption=fb_caption, comment_text=fb_comments, scheduled_time=None)
        log(f"✅ Kết quả Facebook Reels [Yêu Da Hơn Bồ]: {res_fb}")
    except Exception as e:
        log(f"❌ Lỗi Facebook Reels [Yêu Da Hơn Bồ]: {e}\n{traceback.format_exc()}")

    # Instagram Reels
    try:
        log("📸 [Instagram] Đang đăng Reel Yêu Da Hơn Bồ...")
        ig_cfg = brand_data.get("instagram", {})
        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        res_ig = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=ig_comments)
        log(f"✅ Kết quả Instagram Reels [Yêu Da Hơn Bồ]: {res_ig}")
    except Exception as e:
        log(f"❌ Lỗi Instagram Reels [Yêu Da Hơn Bồ]: {e}\n{traceback.format_exc()}")

    # Threads
    try:
        log("🧵 [Threads] Đang đăng Threads Yêu Da Hơn Bồ...")
        th_cfg = brand_data.get("threads", {})
        th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
        log(f"✅ Kết quả Threads [Yêu Da Hơn Bồ]: {res_th}")
        if res_th and "id" in res_th:
            reply_threads_comments(th_cfg, res_th["id"], th_comments)
    except Exception as e:
        log(f"❌ Lỗi Threads [Yêu Da Hơn Bồ]: {e}\n{traceback.format_exc()}")

def main():
    brands = load_brands()
    log("🚀 BẮT ĐẦU ĐĂNG LẠI META (FB, IG, THREADS) CHO 3 THƯƠNG HIỆU VỚI TOKEN MỚI...")
    publish_cham_da_tiet_kiem(brands)
    publish_quan_ao_gia_hoi(brands)
    publish_yeu_da_hon_bo(brands)
    log("\n🎉 HOÀN TẤT TIẾN TRÌNH ĐĂNG LẠI CHO 3 THƯƠNG HIỆU!")

if __name__ == "__main__":
    main()
