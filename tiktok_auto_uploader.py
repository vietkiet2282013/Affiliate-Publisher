import os
import sys
import time
import argparse
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiktok_browser_data")

def auto_upload_tiktok(video_path, caption, headless=False):
    """
    Tự động hóa đăng video lên TikTok bằng Playwright.
    Lưu và giữ nguyên trạng thái đăng nhập vào thư mục tiktok_browser_data.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    abs_video_path = os.path.abspath(video_path)
    print(f"\nKhởi động trình duyệt tự động đăng TikTok...")
    print(f"- File video: {abs_video_path}")
    print(f"- Caption/Tiêu đề: {caption}\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.new_page()
        print("Đang mở trang TikTok Studio Upload...")
        page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")

        time.sleep(3)
        # Kiểm tra xem có đang ở trang login không
        if "login" in page.url.lower() or page.query_selector("button:has-text('Log in')") or page.query_selector("iframe[src*='login']"):
            print("\n[CHÚ Ý] Bạn chưa đăng nhập TikTok trên trình duyệt!")
            print("Vui lòng đăng nhập trên cửa sổ trình duyệt...")
            while True:
                time.sleep(2)
                if "tiktokstudio/upload" in page.url.lower() and not page.query_selector("iframe[src*='login']"):
                    print("Đăng nhập thành công! Tiến hành tải video...")
                    break

        print("Đang chọn và tải file video lên...")
        time.sleep(3)

        # Chờ file input xuất hiện trên trang TikTok Studio mới
        try:
            file_input = page.wait_for_selector("input[type='file']", timeout=15000)
            if file_input:
                file_input.set_input_files(abs_video_path)
                print("Đã tải file video lên hệ thống TikTok!")
        except Exception:
            print("Không thấy tự chọn file, đang thử tải qua iframe/select file...")
            file_inputs = page.query_selector_all("input[type='file']")
            if file_inputs:
                file_inputs[0].set_input_files(abs_video_path)

        print("Đang chờ TikTok xử lý video (10s)...")
        time.sleep(10)

        # Điền Caption / Tiêu đề
        print(f"Đang điền Caption: {caption}")
        try:
            caption_box = page.query_selector("div[contenteditable='true']") or page.query_selector("textarea")
            if caption_box:
                caption_box.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(caption)
                time.sleep(2)
        except Exception as e:
            print(f"Lưu ý khi điền caption: {e}")

        # Bấm nút Post / Đăng
        print("Đang tìm nút Đăng (Post)...")
        time.sleep(3)
        post_btn = page.query_selector("button:has-text('Post')") or page.query_selector("button:has-text('Đăng')") or page.query_selector("div[role='button']:has-text('Post')")
        if post_btn:
            print("Đã tìm thấy nút Đăng! Tiến hành bấm Đăng...")
            post_btn.click()
            time.sleep(8)
            print("\nĐÃ ĐĂNG VIDEO LÊN TIKTOK THÀNH CÔNG!")
        else:
            print("\nVui lòng bấm nút 'Đăng' (Post) trên màn hình để hoàn tất!")

        time.sleep(5)
        context.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tự động đăng video TikTok qua Playwright")
    parser.add_argument("--video", default="Video 3 giây.mp4", help="Đường dẫn file video")
    parser.add_argument("--caption", default="Video 3s #TikTok #Shorts", help="Caption video")
    parser.add_argument("--headless", action="store_true", help="Chạy ẩn trình duyệt")

    args = parser.parse_args()

    try:
        auto_upload_tiktok(args.video, args.caption, headless=args.headless)
    except Exception as e:
        print(f"\nLỗi khi tự động đăng TikTok: {e}")
