import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_data = os.path.join(base_dir, "credentials/threads_browser_data")
    os.makedirs(user_data, exist_ok=True)
    
    print("==================================================")
    print("🚀 MỞ TRÌNH DUYỆT ĐĂNG NHẬP THREADS BẰNG INSTAGRAM")
    print("==================================================")
    print("👉 Hãy bấm 'Đăng nhập bằng Instagram' trên cửa sổ trình duyệt...")
    print("👉 Sau khi đăng nhập thành công, phiên đăng nhập sẽ được lưu vĩnh viễn!")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data,
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.new_page()
        page.goto("https://www.threads.net/login")
        
        while True:
            time.sleep(3)
            # Nếu đã vào feed chính
            if page.url == "https://www.threads.net/" or "login" not in page.url:
                print("\n🎉 ĐÃ ĐĂNG NHẬP THREADS THÀNH CÔNG!")
                time.sleep(3)
                break

        context.close()
        print("💾 Đã lưu phiên đăng nhập Threads vào credentials/threads_browser_data!")

if __name__ == "__main__":
    main()
