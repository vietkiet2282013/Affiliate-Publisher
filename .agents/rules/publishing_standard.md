# QUY TRÌNH CHUẨN XUẤT BẢN VIDEO MULTI-PLATFORM & AFFILIATE

Áp dụng cho toàn bộ 7 thương hiệu/kênh trong hệ thống (cấu hình tại `POST/config/brands.json`):
1. **Nói Thật Dùng Thật** (`noi_that_dung_that`)
2. **Dùng Rồi Mới Nói** (`dung_roi_moi_noi`)
3. **Review Thật Việc Thật** (`review_that_viec_that`)
4. **Setup Phòng Xinh** (`setup_phong_xinh`)
5. **Tủ Đồ Mùa Mới** (`tu_do_mua_moi`)
6. **Trạm Công Nghệ** / YT: Chạm Công Nghệ (`cham_cong_nghe`)
7. **Góc Tập Luyện** (`goc_tap_luyen`)

---

## 1. TIÊU CHUẨN CHẤT LƯỢNG VIDEO (QUY TẮC BẮT BUỘC)
- 🔴 **YouTube Shorts & 🔷 Facebook Reels / Facebook Story:**
  - **ĐĂNG THẲNG FILE GỐC 4K NGUYÊN BẢN (2160x3840)** từ máy tính.
  - Tuyệt đối KHÔNG render lại, KHÔNG nén, giữ trọn 100% độ sắc nét gốc.
- 📸 **Instagram Reels & 🧵 Threads:**
  - Chuyển đổi sang chuẩn Full HD **1080x1920 (High Bitrate)** để đáp ứng đúng quy định kỹ thuật tối đa của Meta Graph API (tránh lỗi `Invalid resolution: width > 1080px`).
  - Upload file 1080p qua curl lên CDN (uguu.se) để lấy public URL cho Meta API.
- 📖 **Instagram Story:**
  - Cắt đúng 59 giây đầu tiên (quy định cứng của Instagram Story là tối đa 60 giây).

---

## 2. QUY TRÌNH GẮN LINK AFFILIATE CHUẨN SEO
Đọc danh sách link rút gọn từ file CSV (`Sub_id1`, `Liên kết chuyển đổi`).
Tự động đăng bình luận theo thứ tự luân phiên mẫu:
1. `Link sản phẩm ở đây: <URL 1>`
2. `Link xem và mua hàng ngay tại đây nè: <URL 2>`
3. `Link sản phẩm ở đây nha mọi người: <URL 3>`
4. `Link sản phẩm ở đây, mọi người ủng hộ nhé: <URL 4>`
5. `Link sản phẩm: <URL 5...>`

Gắn đầy đủ bình luận vào: YouTube, Facebook Reels, Instagram Reels, Threads.

---

## 3. NỀN TẢNG XUẤT BẢN ĐỒNG THỜI MỖI KHI ĐĂNG
Mỗi lần đăng video phải xuất bản trọn gói lên:
1. 🔴 **YouTube Shorts / Video**
2. 🔷 **Facebook Reels**
3. 📖 **Facebook Page Story**
4. 📸 **Instagram Reels**
5. 📖 **Instagram Story** (bản 59s)
6. 🧵 **Threads** (@username)
