import os
import sys
import time
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright

class TikTokPlaywrightUploader:
    """
    Tự động hóa đăng video lên TikTok Studio & Gắn Giỏ hàng / Sản phẩm TikTok Shop qua Playwright
    """
    def __init__(self, browser_data_dir: str = "credentials/tiktok_browser_data"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.browser_data_dir = os.path.join(base_dir, browser_data_dir) if not os.path.isabs(browser_data_dir) else browser_data_dir
        os.makedirs(self.browser_data_dir, exist_ok=True)

    def upload_video_with_product(
        self,
        video_path: str,
        caption: str,
        product_keyword: Optional[str] = None,
        headless: bool = False,
        wait_seconds_for_product: int = 15
    ) -> Optional[Dict[str, Any]]:
        """
        Upload video và gắn sản phẩm TikTok Shop:
        :param video_path: Đường dẫn file video
        :param caption: Nội dung caption và hashtags
        :param product_keyword: Tên sản phẩm muốn tìm và gắn từ giỏ hàng TikTok Shop
        :param headless: False để hiện trình duyệt (khuyên dùng khi cần đăng nhập hoặc chọn sản phẩm)
        :param wait_seconds_for_product: Thời gian chờ bạn xem và xác nhận sản phẩm
        """
        if not os.path.exists(video_path):
            print(f"❌ Không tìm thấy file video: {video_path}")
            return None

        abs_video_path = os.path.abspath(video_path)
        print("\n" + "="*60)
        print("🚀 [TikTok Studio] BẮT ĐẦU QUY TRÌNH TẢI VIDEO & GẮN SẢN PHẨM")
        print("="*60)
        print(f"📁 Video: {os.path.basename(video_path)}")
        print(f"🛍️ Sản phẩm TikTok Shop: {product_keyword or '(Chưa chỉ định keyword)'}")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.browser_data_dir,
                headless=headless,
                viewport={"width": 1366, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )

            page = context.new_page()
            print("\n🌐 Đang mở trang tải lên TikTok Studio (tiktok.com/tiktokstudio/upload)...")
            page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
            time.sleep(4)

            # 1. Kiểm tra trạng thái đăng nhập
            if "login" in page.url.lower() or page.query_selector("button:has-text('Log in')") or page.query_selector("iframe[src*='login']"):
                print("\n⚠️ [CHÚ Ý] Bạn chưa đăng nhập TikTok trên trình duyệt!")
                print("👉 Vui lòng đăng nhập tài khoản TikTok của bạn trên cửa sổ trình duyệt vừa mở...")
                while True:
                    time.sleep(3)
                    if "tiktokstudio/upload" in page.url.lower() and not page.query_selector("iframe[src*='login']"):
                        print("✅ Đăng nhập TikTok thành công!")
                        break

            # 2. Tải file video lên
            print("⏳ Đang tải file video vào hệ thống TikTok...")
            time.sleep(2)
            try:
                file_input = page.wait_for_selector("input[type='file']", timeout=15000)
                if file_input:
                    file_input.set_input_files(abs_video_path)
                    print("✅ Đã đưa file video vào khung tải lên!")
            except Exception:
                file_inputs = page.query_selector_all("input[type='file']")
                if file_inputs:
                    file_inputs[0].set_input_files(abs_video_path)
                    print("✅ Đã đưa file video vào khung tải lên!")

            print("⏳ Đang chờ TikTok xử lý video sơ bộ (8s)...")
            time.sleep(8)

            # 3. Điền Caption & Hashtags
            print(f"✍️ Đang điền Caption: '{caption[:50]}...'")
            try:
                caption_elem = page.query_selector("div[contenteditable='true']") or page.query_selector("div.notranslate[contenteditable='true']")
                if caption_elem:
                    caption_elem.click()
                    page.keyboard.press("Meta+A")
                    page.keyboard.press("Backspace")
                    page.keyboard.type(caption, delay=20)
                    print("✅ Đã điền Caption và Hashtags!")
            except Exception as e:
                print(f"⚠️ Lỗi điền caption: {e}")

            # 4. Gắn sản phẩm TikTok Shop (Giỏ hàng vàng)
            print("\n🛍️ [TikTok Shop] Tiến hành gắn sản phẩm vào video...")
            try:
                # Tìm nút "Thêm liên kết" hoặc "Sản phẩm" / "Product"
                product_btn = page.query_selector("button:has-text('Sản phẩm')") or \
                              page.query_selector("div:has-text('Thêm liên kết')") or \
                              page.query_selector("button:has-text('Product')") or \
                              page.query_selector("div:has-text('Product link')") or \
                              page.query_selector("[data-e2e='add-product-btn']")

                if product_btn:
                    print("👉 Đã tìm thấy nút Thêm sản phẩm, đang click...")
                    product_btn.click()
                    time.sleep(3)

                    # Nếu có keyword tìm kiếm sản phẩm
                    if product_keyword:
                        search_input = page.query_selector("input[placeholder*='Tìm kiếm']") or page.query_selector("input[placeholder*='Search']")
                        if search_input:
                            search_input.fill(product_keyword)
                            page.keyboard.press("Enter")
                            time.sleep(3)

                    print(f"⏳ Dành {wait_seconds_for_product}s để bạn kiểm tra / chọn sản phẩm mong muốn trên màn hình...")
                    time.sleep(wait_seconds_for_product)
                else:
                    print("ℹ️ Bạn có thể trực tiếp click chọn Sản phẩm / Giỏ hàng trên giao diện trình duyệt.")
                    time.sleep(5)
            except Exception as e:
                print(f"⚠️ Thao tác sản phẩm: {e}")

            # 5. Xuất bản / Đăng
            print("\n🚀 Đang chuẩn bị xuất bản video...")
            try:
                post_btn = page.query_selector("button:has-text('Đăng')") or \
                           page.query_selector("button:has-text('Post')") or \
                           page.query_selector("[data-e2e='post_video_button']")

                if post_btn and not post_btn.is_disabled():
                    print("🎉 Đang click nút ĐĂNG...")
                    post_btn.click()
                    time.sleep(5)
                    print("✅ ĐÃ GỬI YÊU CẦU ĐĂNG VIDEO LÊN TIKTOK THÀNH CÔNG!")
                else:
                    print("ℹ️ Nút Đăng đang chờ bạn kiểm tra lần cuối trên màn hình.")
                    time.sleep(10)
            except Exception as e:
                print(f"⚠️ Lỗi click nút đăng: {e}")

            print("\n" + "="*60)
            print("✨ HOÀN TẤT TIẾN TRÌNH ĐĂNG TIKTOK!")
            print("="*60)
            context.close()
            return {"success": True}
