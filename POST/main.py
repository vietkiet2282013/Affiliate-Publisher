import os
import sys
import json
import argparse
from typing import Dict, Any, List

from uploaders import (
    FacebookReelsUploader,
    InstagramReelsUploader,
    YouTubeShortsUploader,
    TikTokPlaywrightUploader,
    TikTokAPIUploader,
    ThreadsAPIUploader,
    PinterestUploader
)
from scheduler import add_schedule_task

def load_brands_config(config_path: str = "config/brands.json") -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    if not os.path.exists(full_path):
        print(f"❌ Không tìm thấy file cấu hình: {full_path}")
        sys.exit(1)
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_videos_in_folder(folder_name: str) -> List[str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_folder = os.path.join(base_dir, folder_name)
    if not os.path.exists(target_folder):
        return []
    valid_extensions = (".mp4", ".mov", ".MP4", ".MOV")
    return [
        os.path.join(target_folder, f)
        for f in os.listdir(target_folder)
        if f.endswith(valid_extensions) and not f.startswith(".")
    ]

def interactive_mode():
    brands = load_brands_config()
    brand_keys = list(brands.keys())

    print("\n" + "="*65)
    print("🎬 CHƯƠNG TRÌNH ĐĂNG VIDEO ĐA NỀN TẢNG (6 TRONG 1)")
    print("   [YouTube Shorts + Facebook Reels + Instagram + TikTok + Threads + Pinterest]")
    print("="*65)

    print("\n👉 CHỌN THƯƠNG HIỆU / KÊNH MUỐN ĐĂNG:")
    for idx, key in enumerate(brand_keys, 1):
        print(f"  [{idx}] {brands[key]['name']} ({key})")

    choice = input("\n👉 Nhập lựa chọn (1-3) [mặc định 1]: ").strip() or "1"
    try:
        selected_key = brand_keys[int(choice) - 1]
    except Exception:
        print("❌ Lựa chọn không hợp lệ!")
        sys.exit(1)

    brand_data = brands[selected_key]
    print(f"\n✅ Đã chọn thương hiệu: {brand_data['name']}")

    # Hiển thị danh sách video trong folder của thương hiệu
    video_files = list_videos_in_folder(brand_data["folder"])
    print(f"\n📂 Danh sách video trong thư mục '{brand_data['folder']}':")
    if video_files:
        for idx, v in enumerate(video_files, 1):
            print(f"  [{idx}] {os.path.basename(v)}")
        print(f"  [0] Nhập đường dẫn video khác...")
        
        v_choice = input(f"\n👉 Chọn video (0-{len(video_files)}): ").strip()
        if v_choice == "0":
            video_path = input("👉 Nhập đường dẫn file video (.mp4/.mov): ").strip().strip("'").strip('"')
        else:
            try:
                video_path = video_files[int(v_choice) - 1]
            except Exception:
                print("❌ Lựa chọn không hợp lệ!")
                sys.exit(1)
    else:
        print("  (Chưa có video trong thư mục)")
        video_path = input("👉 Nhập đường dẫn file video (.mp4/.mov): ").strip().strip("'").strip('"')

    if not os.path.exists(video_path):
        print(f"❌ File video không tồn tại: {video_path}")
        sys.exit(1)

    # Tiêu đề & Caption
    default_title = f"{brand_data['name']} - Review Thật Trải Nghiệm Thật"
    title = input(f"\n👉 Nhập Tiêu đề [{default_title}]: ").strip() or default_title

    default_caption = f"{brand_data['name']}! Trải nghiệm thực tế, đánh giá chi tiết 🔥 #reels #shorts #tiktok #threads #pinterest #review #viral #fyp"
    caption = input(f"👉 Nhập Caption & Hashtags [{default_caption}]: ").strip() or default_caption

    default_comment = f"🔥 Mọi người quan tâm sản phẩm chính hãng giá ưu đãi có thể xem tại: https://s.shopee.vn/lotboncautron ❤️"
    comment = input(f"👉 Nhập Link Shopee Affiliate / Bình luận [{default_comment}]: ").strip() or default_comment

    # Nhập từ khóa sản phẩm TikTok Shop
    default_prod = "Kéo cắt gà"
    product_keyword = input(f"👉 Nhập từ khóa sản phẩm TikTok Shop muốn gắn [{default_prod}]: ").strip() or default_prod

    # Chọn nền tảng đăng
    print(f"\n👉 CHỌN NỀN TẢNG MUỐN ĐĂNG:")
    print("  [1] Tất cả các nền tảng (YouTube + Facebook + Instagram + TikTok + Threads + Pinterest)")
    print("  [2] Chỉ đăng YouTube Shorts")
    print("  [3] Chỉ đăng Facebook Reels")
    print("  [4] Chỉ đăng Instagram Reels")
    print("  [5] Chỉ đăng TikTok (Gắn giỏ hàng TikTok Shop)")
    print("  [6] Chỉ đăng Threads (Threads REST API)")
    print("  [7] Chỉ đăng Pinterest (Pinterest v5 REST API)")
    p_choice = input("👉 Nhập lựa chọn (1-7) [mặc định 1]: ").strip() or "1"

    # Chọn chế độ: Đăng ngay hoặc Hẹn giờ
    print(f"\n👉 CHỌN CHẾ ĐỘ ĐĂNG BÀI:")
    print("  [1] Đăng ngay lập tức (Publish Now)")
    print("  [2] Hẹn giờ đăng tự động (Schedule Post)")
    mode_choice = input("👉 Nhập lựa chọn (1-2) [mặc định 1]: ").strip() or "1"

    if mode_choice == "2":
        sched_time = input("⏰ Nhập thời gian muốn đăng (ví dụ '19:30' hoặc '2026-08-23 20:00'): ").strip()
        platform_mapping = {
            "1": ["youtube", "facebook", "instagram", "threads", "tiktok", "pinterest"],
            "2": ["youtube"],
            "3": ["facebook"],
            "4": ["instagram"],
            "5": ["tiktok"],
            "6": ["threads"],
            "7": ["pinterest"]
        }
        target_platforms = platform_mapping.get(p_choice, ["youtube", "facebook", "instagram", "threads", "tiktok", "pinterest"])
        add_schedule_task(
            brand_key=selected_key,
            video_path=video_path,
            title=title,
            caption=caption,
            comment=comment,
            platforms=target_platforms,
            scheduled_datetime=sched_time,
            product_keyword=product_keyword
        )
    else:
        execute_upload(brand_data, video_path, title, caption, comment, product_keyword, p_choice)

def execute_upload(brand_data, video_path, title, caption, comment, product_keyword, platform_choice):
    print("\n" + "="*65)
    print(f"🚀 BẮT ĐẦU ĐĂNG TẢI CHO THƯƠNG HIỆU: {brand_data['name'].upper()}")
    print("="*65)

    # 1. YouTube Shorts
    if platform_choice in ["1", "2"]:
        print("\n🔴 [1/6] ĐĂNG LÊN YOUTUBE SHORTS...")
        yt_cfg = brand_data.get("youtube", {})
        yt_uploader = YouTubeShortsUploader(
            token_file=yt_cfg.get("token_file", "credentials/youtube_tokens/default.json")
        )
        yt_uploader.upload_short(video_path=video_path, title=title, description=caption, comment_text=comment, privacy_status="public")

    # 2. Facebook Reels
    if platform_choice in ["1", "3"]:
        print("\n🔷 [2/6] ĐĂNG LÊN FACEBOOK REELS...")
        fb_cfg = brand_data.get("facebook", {})
        if fb_cfg.get("page_id") and fb_cfg.get("access_token"):
            fb_uploader = FacebookReelsUploader(
                page_id=fb_cfg["page_id"],
                access_token=fb_cfg["access_token"]
            )
            fb_uploader.upload_reel(video_path=video_path, title=title, caption=caption, comment_text=comment)

    # 3. Instagram Reels
    if platform_choice in ["1", "4"]:
        print("\n📸 [3/6] ĐĂNG LÊN INSTAGRAM REELS...")
        ig_cfg = brand_data.get("instagram", {})
        if ig_cfg.get("ig_user_id") and ig_cfg.get("access_token"):
            ig_uploader = InstagramReelsUploader(
                ig_user_id=ig_cfg["ig_user_id"],
                access_token=ig_cfg["access_token"]
            )
            ig_uploader.upload_reel(video_path=video_path, caption=caption, comment_text=comment)

    # 4. TikTok (Playwright Automation & Gắn giỏ hàng TikTok Shop)
    if platform_choice in ["1", "5"]:
        print("\n🎵 [4/6] ĐĂNG LÊN TIKTOK (GẮN SẢN PHẨM TIKTOK SHOP)...")
        tiktok_uploader = TikTokPlaywrightUploader()
        tiktok_uploader.upload_video_with_product(
            video_path=video_path,
            caption=caption,
            product_keyword=product_keyword,
            headless=False
        )

    # 5. Threads (Meta Threads REST API)
    if platform_choice in ["1", "6"]:
        print("\n🧵 [5/6] ĐĂNG LÊN THREADS (THREADS REST API)...")
        th_cfg = brand_data.get("threads", {})
        if th_cfg.get("user_id") and th_cfg.get("access_token"):
            th_uploader = ThreadsAPIUploader(
                threads_user_id=th_cfg["user_id"],
                access_token=th_cfg["access_token"]
            )
            th_uploader.upload_video_thread(
                video_path=video_path,
                caption=caption,
                comment_link=comment
            )
        else:
            print("⚠️ Chưa cấu hình user_id hoặc access_token cho Threads!")

    # 6. Pinterest (Pinterest v5 REST API)
    if platform_choice in ["1", "7"]:
        print("\n📌 [6/6] ĐĂNG LÊN PINTEREST (PINTEREST v5 REST API)...")
        pin_cfg = brand_data.get("pinterest", {})
        access_token = pin_cfg.get("access_token") or os.getenv("PINTEREST_ACCESS_TOKEN")
        board_id = pin_cfg.get("board_id") or os.getenv("PINTEREST_BOARD_ID")
        destination_link = pin_cfg.get("link") or comment

        if access_token and board_id:
            pin_uploader = PinterestUploader(access_token=access_token)
            pin_uploader.upload_video_pin(
                video_path=video_path,
                board_id=board_id,
                title=title,
                description=caption,
                link=destination_link
            )
        else:
            print("⚠️ Chưa cấu hình access_token hoặc board_id cho Pinterest trong brands.json hoặc .env!")


    print("\n" + "="*65)
    print(f"✨ HOÀN TẤT TẤT CẢ TIẾN TRÌNH CHO: {brand_data['name']}")
    print("="*65)

if __name__ == "__main__":
    interactive_mode()
