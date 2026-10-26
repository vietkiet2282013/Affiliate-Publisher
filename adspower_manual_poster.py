# -*- coding: utf-8 -*-
"""
Module tự động hóa chuẩn bị và đăng video lên cả 4 nền tảng (Facebook, Instagram, Threads, YouTube)
thông qua trình duyệt AdsPower và Playwright CDP.
Hỗ trợ đăng ở chế độ riêng tư (Private/Unlisted) và tự động comment link affiliate ngay sau khi đăng.
"""

import os
import sys
import time
import requests
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, BrowserContext, Page

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class AdsPowerManualPoster:
    def __init__(self, api_host: str = "127.0.0.1", api_port: int = 50325):
        self.base_url = f"http://{api_host}:{api_port}"

    def ensure_valid_proxy(self, profile_id: str):
        """Nếu proxy của profile bị lỗi, chuyển sang no_proxy để không bị tắc nghẽn mạng."""
        try:
            requests.post(
                f"{self.base_url}/api/v1/user/update",
                json={"user_id": profile_id, "user_proxy_config": {"proxy_soft": "no_proxy"}},
                timeout=5
            )
        except Exception:
            pass

    def get_connection_info(self, profile_id: Optional[str] = None) -> Dict[str, Any]:
        """Lấy thông tin debug_port và WebSocket để kết nối Playwright CDP."""
        try:
            r = requests.get(f"{self.base_url}/status", timeout=2)
            if r.status_code != 200 or r.json().get("code") != 0:
                raise ConnectionError("AdsPower API chưa sẵn sàng. Hãy mở app AdsPower!")
        except Exception:
            raise ConnectionError(f"❌ Không kết nối được AdsPower tại {self.base_url}. Vui lòng bật AdsPower!")

        # 1. Nếu không có profile_id, tự động lấy profile đang mở
        if not profile_id:
            r = requests.get(f"{self.base_url}/api/v1/browser/local-active", timeout=3)
            data = r.json()
            active_list = data.get("data", {}).get("list", [])
            if active_list:
                info = active_list[0]
                return {
                    "profile_id": info.get("user_id"),
                    "debug_port": info.get("debug_port"),
                    "cdp_url": f"http://127.0.0.1:{info.get('debug_port')}"
                }
            raise RuntimeError("❌ Không tìm thấy profile nào đang mở trong AdsPower! Vui lòng chỉ định hoặc mở profile.")

        # Đảm bảo profile không bị treo bởi proxy chết
        self.ensure_valid_proxy(profile_id)

        # 2. Nếu có profile_id, kiểm tra xem nó có đang active không
        r = requests.get(f"{self.base_url}/api/v1/browser/active", params={"user_id": profile_id}, timeout=3)
        data = r.json()
        if data.get("code") == 0 and data.get("data", {}).get("status") == "Active":
            debug_port = data.get("data", {}).get("debug_port")
            return {
                "profile_id": profile_id,
                "debug_port": debug_port,
                "cdp_url": f"http://127.0.0.1:{debug_port}"
            }

        # 3. Khởi chạy profile nếu chưa mở
        print(f"⚡ [AdsPower] Đang khởi chạy profile {profile_id}...")
        r = requests.get(f"{self.base_url}/api/v1/browser/start", params={"user_id": profile_id, "open_tabs": 1}, timeout=30)
        start_data = r.json()
        if start_data.get("code") == 0:
            debug_port = start_data.get("data", {}).get("debug_port")
            return {
                "profile_id": profile_id,
                "debug_port": debug_port,
                "cdp_url": f"http://127.0.0.1:{debug_port}"
            }
        else:
            raise RuntimeError(f"❌ Lỗi khởi động profile {profile_id}: {start_data.get('msg')}")

    def _upload_file_cdp(self, page: Page, selector: str, file_path: str):
        """Upload file trực tiếp qua CDP DOM.setFileInputFiles (không giới hạn 50MB)."""
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Không tìm thấy file video: {abs_path}")

        cdp = page.context.new_cdp_session(page)
        doc = cdp.send("DOM.getDocument")
        root_id = doc["root"]["nodeId"]
        res = cdp.send("DOM.querySelector", {"nodeId": root_id, "selector": selector})
        node_id = res.get("nodeId")
        if not node_id:
            raise RuntimeError(f"Không tìm thấy phần tử {selector} để upload file!")

        cdp.send("DOM.setFileInputFiles", {"files": [abs_path], "nodeId": node_id})

    # =========================================================================
    # 1. YOUTUBE SHORTS (UNLISTED / KHÔNG CÔNG KHAI)
    # =========================================================================
    def process_youtube(
        self,
        context: BrowserContext,
        video_path: str,
        title: str,
        description: str,
        comments: List[str] = None,
        privacy: str = "private",
        progress_cb=None
    ):
        """Mở tab YouTube Studio, tải video lên, cấu hình Không công khai (Unlisted), xuất bản và comment."""
        if progress_cb: progress_cb(10, "🔴 [YouTube] Đang mở tab YouTube Studio...")
        page = None
        for p in context.pages:
            if "studio.youtube.com" in p.url:
                page = p
                break
        if not page:
            page = context.new_page()
            page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)
        page.bring_to_front()

        # Kiểm tra xem dialog upload đã mở sẵn chưa
        has_dialog = page.locator('ytcp-uploads-dialog').count() > 0
        if not has_dialog:
            upload_btn = page.locator('#upload-icon, #upload-button, [aria-label="Tải video lên"]').first
            if upload_btn.is_visible():
                upload_btn.click(force=True, timeout=5000)
                time.sleep(2)
            else:
                create_btn = page.locator('#create-icon, ytcp-button#create-icon, #create-button').first
                if create_btn.is_visible():
                    create_btn.click(force=True, timeout=5000)
                    time.sleep(1)
                    page.locator('text="Tải video lên", text="Upload videos"').first.click(force=True, timeout=5000)
                    time.sleep(2)

        # Upload video qua CDP
        if page.locator('input[type="file"]').count() > 0:
            if progress_cb: progress_cb(15, "🔴 [YouTube] Đang tải file video lên YouTube Shorts...")
            try:
                self._upload_file_cdp(page, 'input[type="file"]', video_path)
                time.sleep(5)
            except Exception as e:
                if progress_cb: progress_cb(15, f"ℹ️ [YouTube] File input: {e}")

        # Điền tiêu đề & mô tả (kèm link affiliate trong mô tả để chắc chắn)
        if progress_cb: progress_cb(20, "🔴 [YouTube] Đang điền tiêu đề & mô tả chuẩn SEO...")
        try:
            yt_title = title if "#shorts" in title.lower() else f"{title} #shorts"
            title_boxes = page.locator('#textbox[contenteditable="true"]').all()
            if title_boxes:
                title_boxes[0].click(force=True)
                title_boxes[0].fill(yt_title)
            if len(title_boxes) > 1:
                title_boxes[1].click(force=True)
                full_desc = (description or "").strip()
                if comments and "shopee.vn" not in full_desc.lower() and "s.shopee.vn" not in full_desc.lower():
                    full_desc += "\n\n🛒 MUA SẢN PHẨM CHÍNH HÃNG TẠI ĐÂY:\n\n" + "\n\n".join(comments)
                if "#shorts" not in full_desc.lower():
                    full_desc += "\n\n#Shorts"
                title_boxes[1].fill(full_desc)
        except Exception as e:
            if progress_cb: progress_cb(20, f"ℹ️ [YouTube] Tiêu đề: {e}")

        # Chọn "Không dành cho trẻ em"
        try:
            r = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first
            r.evaluate('el => el.click()')
            time.sleep(1)
        except Exception:
            pass

        # Bấm Next 3 lần đến bước Chế độ hiển thị
        for _ in range(3):
            next_btn = page.locator('#next-button').first
            if next_btn.is_visible() and next_btn.get_attribute("aria-disabled") != "true":
                next_btn.click(force=True)
                time.sleep(2)

        # Cấu hình Không công khai (Unlisted)
        video_url = None
        try:
            unlisted = page.locator('tp-yt-paper-radio-button[name="UNLISTED"]').first
            if unlisted.is_visible():
                if progress_cb: progress_cb(24, "🔒 [YouTube] Đang cấu hình chế độ 'Không công khai' (Unlisted)...")
                unlisted.evaluate('el => el.click()')
                time.sleep(1)

            # Lấy URL video
            links = page.locator('ytcp-uploads-dialog a[href*="youtu.be"], ytcp-uploads-dialog a[href*="youtube.com/shorts"]').all()
            for l in links:
                href = l.get_attribute("href")
                if href and ("youtu.be" in href or "shorts" in href):
                    video_url = href
                    break
        except Exception as e:
            if progress_cb: progress_cb(24, f"ℹ️ [YouTube] Visibility: {e}")

        # Bấm Lưu (Xuất bản)
        done_btn = page.locator('#done-button').first
        if done_btn.is_visible() and done_btn.get_attribute("aria-disabled") != "true":
            if progress_cb: progress_cb(26, "🚀 [YouTube] Đang lưu video Shorts ở chế độ Không công khai...")
            done_btn.click(force=True)
            time.sleep(5)

        # Đóng popup nếu có
        close_btn = page.locator('#close-button').first
        if close_btn.is_visible():
            close_btn.click(force=True)
            time.sleep(2)

        # Comment link affiliate vào video Shorts
        if comments and video_url:
            cmt_text = comments[0] if isinstance(comments, list) else str(comments)
            if progress_cb: progress_cb(28, f"💬 [YouTube] Đang mở video {video_url} để ghim bình luận affiliate...")
            try:
                watch_page = context.new_page()
                watch_page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)
                cmt_placeholder = watch_page.locator('#simplebox-placeholder, #placeholder-area').first
                if cmt_placeholder.is_visible():
                    cmt_placeholder.click(force=True)
                    time.sleep(1)
                    input_box = watch_page.locator('#contenteditable-root[contenteditable="true"]').first
                    if input_box.is_visible():
                        input_box.fill(cmt_text)
                        time.sleep(1)
                        submit_btn = watch_page.locator('#submit-button').first
                        if submit_btn.is_visible():
                            submit_btn.click(force=True)
                            time.sleep(2)
                            if progress_cb: progress_cb(29, "💬 [YouTube] Đã gửi bình luận affiliate thành công!")
                watch_page.close()
            except Exception as e:
                if progress_cb: progress_cb(28, f"ℹ️ [YouTube] Bình luận: {e}")

        if progress_cb: progress_cb(30, f"✅ [YouTube] Đã hoàn tất Shorts (Không công khai)! Link: {video_url or 'YouTube Studio'}")

    # =========================================================================
    # 2. FACEBOOK REELS
    # =========================================================================
    def process_facebook(
        self,
        context: BrowserContext,
        video_path: str,
        caption: str,
        comments: List[str] = None,
        privacy: str = "private",
        progress_cb=None
    ):
        """Mở tab Facebook Reels, tải video lên, điền caption, đăng và comment link affiliate."""
        if progress_cb: progress_cb(35, "🟢 [Facebook] Đang mở giao diện Facebook Reels...")
        page = None
        for p in context.pages:
            if "facebook.com/reels/create" in p.url:
                page = p
                break
        if not page:
            page = context.new_page()
            page.goto("https://www.facebook.com/reels/create/?surface=ADDL_PROFILE_PLUS", wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)
        page.bring_to_front()
        page.on("dialog", lambda d: d.accept())

        # Nếu chưa ở trang create
        if "facebook.com/reels/create" not in page.url:
            page.goto("https://www.facebook.com/reels/create/?surface=ADDL_PROFILE_PLUS", wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)

        # 1. Upload video
        if page.locator('input[type="file"]').count() > 0:
            if progress_cb: progress_cb(42, "🟢 [Facebook] Đang tải file video lên Reels...")
            try:
                self._upload_file_cdp(page, 'input[type="file"]', video_path)
            except Exception as e:
                if progress_cb: progress_cb(42, f"ℹ️ [Facebook] Input video: {e}")

        # Chờ nút Tiếp bật
        start_t = time.time()
        while time.time() - start_t < 40:
            next_btns = page.locator('[role="button"]:has-text("Tiếp"), div[aria-label="Tiếp"]').all()
            if next_btns and next_btns[-1].get_attribute("aria-disabled") != "true":
                break
            time.sleep(1.5)

        # 2. Điền Caption
        if progress_cb: progress_cb(48, "🟢 [Facebook] Đang điền mô tả & hashtag...")
        time.sleep(1)
        for sel in [
            'div[aria-label="Mô tả thước phim của bạn..."][contenteditable="true"]',
            'div[aria-label*="bạn đang nghĩ gì"][contenteditable="true"]',
            'div[role="textbox"][contenteditable="true"]'
        ]:
            box = page.locator(sel).first
            if box.is_visible():
                box.click(force=True)
                try:
                    box.fill(caption)
                except Exception:
                    page.keyboard.insert_text(caption)
                break

        # 3. Nhấn Tiếp để đến bước Đăng cuối cùng
        for _ in range(4):
            time.sleep(1.5)
            # Kiểm tra xem đã thấy nút Đăng chính xác chưa
            has_dang = False
            for b in page.locator('[role="button"]').all():
                if b.is_visible():
                    txt = b.inner_text().strip()
                    aria = b.get_attribute("aria-label") or ""
                    if (txt == "Đăng" or aria == "Đăng") and "Quảng bá" not in txt:
                        has_dang = True
                        break
            if has_dang:
                break
            next_btn = page.locator('[role="button"]:has-text("Tiếp"), div[aria-label="Tiếp"]').last
            if next_btn.is_visible() and next_btn.get_attribute("aria-disabled") != "true":
                next_btn.click(force=True)
                time.sleep(2)

        # 4. Bấm nút ĐĂNG CHÍNH XÁC (Tránh bấm nhầm "Quảng bá bài viết...")
        publish_btn = None
        for b in page.locator('[role="button"]').all():
            if b.is_visible():
                txt = b.inner_text().strip()
                aria = b.get_attribute("aria-label") or ""
                if (txt == "Đăng" or aria == "Đăng") and "Quảng bá" not in txt:
                    publish_btn = b
                    break

        if publish_btn and publish_btn.get_attribute("aria-disabled") != "true":
            if progress_cb: progress_cb(52, "🚀 [Facebook] Đang bấm nút 'Đăng' Thước phim...")
            publish_btn.click(force=True)
            time.sleep(10)

        # 5. Comment link affiliate nếu có
        if comments:
            cmt_text = comments[0] if isinstance(comments, list) else str(comments)
            if progress_cb: progress_cb(55, "💬 [Facebook] Đang chuẩn bị bình luận link affiliate...")
            try:
                time.sleep(4)
                cmt_box = page.locator('div[aria-label*="Viết bình luận"][contenteditable="true"], div[aria-label*="Bình luận"]').first
                if cmt_box.is_visible():
                    cmt_box.click(force=True)
                    cmt_box.fill(cmt_text)
                    page.keyboard.press("Enter")
                    time.sleep(2)
                    if progress_cb: progress_cb(56, "💬 [Facebook] Đã bình luận link affiliate thành công!")
            except Exception as e:
                if progress_cb: progress_cb(55, f"ℹ️ [Facebook] Comment: {e}")

        if progress_cb: progress_cb(58, "✅ [Facebook] Đã hoàn tất đăng Facebook Reels!")

    # =========================================================================
    # 3. INSTAGRAM REELS
    # =========================================================================
    def process_instagram(
        self,
        context: BrowserContext,
        video_path: str,
        caption: str,
        comments: List[str] = None,
        privacy: str = "private",
        progress_cb=None
    ):
        """Mở tab Instagram, tải video lên, điền caption, chia sẻ và comment link affiliate."""
        if progress_cb: progress_cb(62, "🟣 [Instagram] Đang mở giao diện Instagram...")
        page = None
        for p in context.pages:
            if "instagram.com" in p.url:
                page = p
                break
        if not page:
            page = context.new_page()
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)
        page.bring_to_front()

        # Đóng dialog bất thường nếu có
        close_btns = page.locator('svg[aria-label="Đóng"], [aria-label="Đóng"]').all()
        for c in close_btns:
            if c.is_visible():
                c.click(force=True)
                time.sleep(1)

        # 1. Bấm nút [+] Tạo trong thanh bên trái nếu chưa có input file
        if page.locator('input[type="file"]').count() == 0:
            if progress_cb: progress_cb(65, "🟣 [Instagram] Đang bấm nút 'Tạo'...")
            tao_el = page.locator('div:has(> span:text-is("Tạo")), a:has(span:text-is("Tạo")), svg[aria-label="Bài viết mới"]').first
            if tao_el.is_visible():
                tao_el.click(force=True)
                time.sleep(1.5)
                # Bấm menu "Bài viết"
                bv = page.get_by_text("Bài viết", exact=True).first
                if bv.is_visible():
                    bv.click(force=True)
                    time.sleep(2)

        # 2. Upload video qua CDP
        if progress_cb: progress_cb(70, "🟣 [Instagram] Đang tải file video vào khung tạo Reels...")
        try:
            page.wait_for_selector('input[type="file"]', state="attached", timeout=15000)
            self._upload_file_cdp(page, 'input[type="file"]', video_path)
            time.sleep(5)
        except Exception as e:
            if progress_cb: progress_cb(70, f"ℹ️ [Instagram] Upload video: {e}")

        # Bấm nút xác nhận nếu có popup "Thước phim được chia sẻ..."
        ok_btn = page.locator('[role="button"]:has-text("OK"), button:has-text("OK")').first
        if ok_btn.is_visible():
            ok_btn.click(force=True)
            time.sleep(1)

        # 3. Bấm Tiếp qua các bước Cắt & Chỉnh sửa
        if progress_cb: progress_cb(74, "🟣 [Instagram] Đang xử lý các bước định dạng video...")
        for _ in range(4):
            time.sleep(2)
            dialog = page.locator('div[role="dialog"]').first
            # Nếu đã tới ô chú thích thì dừng
            if dialog.locator('div[aria-label*="chú thích"][contenteditable="true"]').count() > 0:
                break
            next_btn = dialog.locator('div[role="button"]:has-text("Tiếp"), button:has-text("Tiếp"), span:has-text("Tiếp")').first
            if next_btn.is_visible():
                next_btn.click(force=True)

        # 4. Điền Chú thích
        if progress_cb: progress_cb(76, "🟣 [Instagram] Đang điền chú thích & hashtag...")
        try:
            caption_box = page.locator('div[aria-label*="chú thích"][contenteditable="true"], div[role="textbox"][contenteditable="true"]').first
            if caption_box.is_visible():
                caption_box.click(force=True)
                caption_box.fill(caption)
                time.sleep(1.5)
        except Exception as e:
            if progress_cb: progress_cb(76, f"ℹ️ [Instagram] Caption: {e}")

        # 5. Bấm Chia sẻ
        if progress_cb: progress_cb(80, "🚀 [Instagram] Đang bấm nút 'Chia sẻ' Reel...")
        dialog = page.locator('div[role="dialog"]').first
        share_btn = dialog.locator('div[role="button"]:has-text("Chia sẻ"), button:has-text("Chia sẻ"), span:has-text("Chia sẻ")').first
        if share_btn.is_visible():
            share_btn.click(force=True)
            time.sleep(8)

        # 6. Comment link affiliate nếu có
        if comments:
            cmt_text = comments[0] if isinstance(comments, list) else str(comments)
            try:
                time.sleep(4)
                cmt_box = page.locator('textarea[aria-label*="Thêm bình luận"], [aria-label*="bình luận"]').first
                if cmt_box.is_visible():
                    if progress_cb: progress_cb(83, "💬 [Instagram] Đang bình luận link affiliate...")
                    cmt_box.click(force=True)
                    cmt_box.fill(cmt_text)
                    page.locator('button:has-text("Đăng")').first.click(force=True)
                    time.sleep(2)
                    if progress_cb: progress_cb(84, "💬 [Instagram] Đã bình luận thành công!")
            except Exception as e:
                if progress_cb: progress_cb(83, f"ℹ️ [Instagram] Comment: {e}")

        if progress_cb: progress_cb(85, "✅ [Instagram] Đã hoàn tất đăng Instagram Reels!")

    # =========================================================================
    # 4. THREADS
    # =========================================================================
    def process_threads(
        self,
        context: BrowserContext,
        video_path: str,
        caption: str,
        comments: List[str] = None,
        privacy: str = "private",
        progress_cb=None
    ):
        """Mở tab Threads, tải video lên, điền text, đăng bài và comment."""
        if progress_cb: progress_cb(88, "🔵 [Threads] Đang mở giao diện Threads...")
        page = None
        for p in context.pages:
            if "threads.com" in p.url or "threads.net" in p.url:
                page = p
                break
        if not page:
            page = context.new_page()
            page.goto("https://www.threads.com/", wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)
        page.bring_to_front()

        # 1. Bấm nút Tạo bài viết mới (+)
        editables = page.locator('[contenteditable="true"]').all()
        if not editables:
            try:
                target = page.locator('svg[aria-label="Tạo"]').last
                if not target.is_visible():
                    target = page.locator('[aria-label*="soạn bài viết mới"], div[role="button"]:has-text("Có gì mới?")').first
                if target.is_visible():
                    target.click(force=True)
                    time.sleep(2)
            except Exception as e:
                if progress_cb: progress_cb(88, f"ℹ️ [Threads] Bấm Tạo mới: {e}")

        # 2. Điền text nội dung
        if progress_cb: progress_cb(91, "🔵 [Threads] Đang điền nội dung bài viết...")
        try:
            editables = page.locator('[contenteditable="true"]').all()
            if editables:
                editables[0].click(force=True)
                editables[0].fill(caption)
                time.sleep(1)
        except Exception:
            pass

        # 3. Upload video qua CDP
        try:
            page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
            if progress_cb: progress_cb(93, "🔵 [Threads] Đang đính kèm file video vào bài Thread...")
            self._upload_file_cdp(page, 'input[type="file"]', video_path)
            time.sleep(5)
        except Exception as e:
            if progress_cb: progress_cb(93, f"ℹ️ [Threads] Đính kèm video: {e}")

        # 4. Bấm Đăng
        if progress_cb: progress_cb(96, "🚀 [Threads] Đang bấm nút 'Đăng' bài Thread...")
        post_btn = page.locator('[role="button"]:has-text("Đăng"), button:has-text("Đăng")').last
        if post_btn.is_visible() and post_btn.get_attribute("aria-disabled") != "true":
            post_btn.click(force=True)
            time.sleep(6)

        # 5. Comment link affiliate nếu có
        if comments:
            cmt_text = comments[0] if isinstance(comments, list) else str(comments)
            try:
                time.sleep(3)
                reply_btn = page.locator('svg[aria-label="Trả lời"], [aria-label="Reply"]').first
                if reply_btn.is_visible():
                    if progress_cb: progress_cb(98, "💬 [Threads] Đang gửi bình luận link affiliate...")
                    reply_btn.click(force=True)
                    time.sleep(1)
                    r_box = page.locator('[contenteditable="true"]').last
                    r_box.fill(cmt_text)
                    page.locator('[role="button"]:has-text("Đăng"), button:has-text("Đăng")').last.click(force=True)
                    time.sleep(2)
                    if progress_cb: progress_cb(99, "💬 [Threads] Đã trả lời link affiliate thành công!")
            except Exception as e:
                if progress_cb: progress_cb(98, f"ℹ️ [Threads] Comment: {e}")

        if progress_cb: progress_cb(100, "✅ [Threads] Đã hoàn tất đăng bài Threads!")

    # =========================================================================
    # POST ALL ORCHESTRATOR
    # =========================================================================
    def post_all(
        self,
        profile_id: Optional[str],
        video_path: str,
        title: str,
        caption: str,
        platforms: List[str] = None,
        comments_map: Dict[str, List[str]] = None,
        privacy: str = "private",
        progress_cb=None
    ) -> Dict[str, Any]:
        """
        Thực hiện mở tab, xuất bản ở chế độ riêng tư và bình luận link affiliate trên cả 4 nền tảng.
        """
        if not platforms:
            platforms = ["youtube", "facebook", "instagram", "threads"]

        if not comments_map:
            comments_map = {}

        if progress_cb: progress_cb(5, "🔗 Đang kết nối AdsPower profile và kiểm tra mạng...")
        conn_info = self.get_connection_info(profile_id=profile_id)
        cdp_url = conn_info["cdp_url"]
        actual_pid = conn_info["profile_id"]

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]

            # 1. YouTube
            if "youtube" in platforms:
                try:
                    yt_cmts = ["📌 Link sản phẩm mình để ở dưới phần mô tả của video nhé"]
                    self.process_youtube(context, video_path, title, caption, comments=yt_cmts, privacy=privacy, progress_cb=progress_cb)
                except Exception as e:
                    if progress_cb: progress_cb(30, f"⚠️ Lỗi YouTube: {e}")

            # 2. Facebook
            if "facebook" in platforms:
                try:
                    fb_cmts = comments_map.get("facebook", [])
                    self.process_facebook(context, video_path, caption, comments=fb_cmts, privacy=privacy, progress_cb=progress_cb)
                except Exception as e:
                    if progress_cb: progress_cb(58, f"⚠️ Lỗi Facebook: {e}")

            # 3. Instagram
            if "instagram" in platforms:
                try:
                    ig_cmts = comments_map.get("instagram", [])
                    self.process_instagram(context, video_path, caption, comments=ig_cmts, privacy=privacy, progress_cb=progress_cb)
                except Exception as e:
                    if progress_cb: progress_cb(85, f"⚠️ Lỗi Instagram: {e}")

            # 4. Threads
            if "threads" in platforms:
                try:
                    th_cmts = comments_map.get("threads", [])
                    self.process_threads(context, video_path, caption, comments=th_cmts, privacy=privacy, progress_cb=progress_cb)
                except Exception as e:
                    if progress_cb: progress_cb(100, f"⚠️ Lỗi Threads: {e}")

            if progress_cb:
                progress_cb(100, "🎉 Đã đăng hoàn tất 4 nền tảng và ghim link affiliate vào bình luận!")

            return {
                "success": True,
                "profile_id": actual_pid,
                "platforms": platforms,
                "message": "Đã đăng hoàn tất 4 nền tảng và bình luận link affiliate!"
            }
