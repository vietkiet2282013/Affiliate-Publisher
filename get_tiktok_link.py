import os
import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiktok_browser_data")

def get_tiktok_links():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        print("Đang truy cập trang Quản lý nội dung TikTok Studio...")
        page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="networkidle")
        time.sleep(5)

        found_links = set()
        links = page.query_selector_all("a[href*='/video/']")
        for l in links:
            href = l.get_attribute("href")
            if href:
                found_links.add(href)

        if not found_links:
            # Kiểm tra trang profile
            print("Đang kiểm tra trang cá nhân TikTok...")
            page.goto("https://www.tiktok.com/", wait_until="domcontentloaded")
            time.sleep(4)
            links = page.query_selector_all("a[href*='/video/']")
            for l in links:
                href = l.get_attribute("href")
                if href:
                    found_links.add(href)

        print("\n--- KẾT QUẢ LINK TIKTOK ---")
        for link in found_links:
            print("Link:", link)

        context.close()

if __name__ == "__main__":
    get_tiktok_links()
