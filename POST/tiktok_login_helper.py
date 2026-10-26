import os
import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials", "tiktok_browser_data")
os.makedirs(USER_DATA_DIR, exist_ok=True)

def open_login_window():
    print("="*60)
    print("🌐 ĐANG MỞ CỬA SỔ ĐĂNG NHẬP TIKTOK...")
    print("="*60)
    print("👉 Trên cửa sổ trình duyệt vừa mở, bạn có thể:")
    print("   1. Bấm 'Tiếp tục với Facebook' (Continue with Facebook)")
    print("   2. Hoặc Mở App TikTok trên điện thoại quét mã QR (Nhanh nhất)")
    print("="*60)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.new_page()
        page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")

        print("\n⏳ Đang đợi bạn đăng nhập trên trình duyệt...")
        while True:
            time.sleep(3)
            # Kiểm tra nếu đã vào trang chủ hoặc TikTok Studio
            if "tiktokstudio" in page.url.lower() or (page.url.startswith("https://www.tiktok.com/") and "login" not in page.url.lower()):
                # Thử chuyển đến tiktokstudio/upload để lưu session hoàn tất
                print("🎉 ĐÃ NHẬN DIỆN ĐĂNG NHẬP THÀNH CÔNG!")
                page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
                time.sleep(4)
                print("💾 ĐÃ LƯU PHIÊN ĐĂNG NHẬP VÀO: credentials/tiktok_browser_data")
                break

        context.close()
        print("\n✨ ĐÃ HOÀN TẤT ĐĂNG NHẬP TIKTOK!")

if __name__ == "__main__":
    open_login_window()
