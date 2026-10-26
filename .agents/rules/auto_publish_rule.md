# 🎯 QUY TẮC TỰ ĐỘNG XUẤT BẢN VIDEO MULTI-PLATFORM & GẮN LINK AFFILIATE

## ⚡ 1. ĐIỀU KIỆN KÍCH HOẠT (TRIGGER)
Bất cứ khi nào người dùng gửi tin nhắn có chứa file video và file CSV kèm yêu cầu đăng lên kênh, ví dụ:
`@[video.mp4] @[link.csv] đăng lên kênh [Tên Kênh]` (hoặc các câu tương tự như "đăng lên kênh X ở 4 nền tảng", "đăng video này đi",...)

👉 **HỆ THỐNG PHẢI TỰ ĐỘNG THỰC HIỆN TRỌN GÓI TOÀN BỘ CÁC BƯỚC DƯỚI ĐÂY MÀ KHÔNG CẦN HỎI LẠI!**

---

## 🏷️ 2. BẢNG MÃ KÊNH & CẤU HÌNH HỆ THỐNG (`POST/config/brands.json`)
Tự động đối chiếu tên kênh tiếng Việt người dùng yêu cầu với mã thương hiệu trong `brands.json`:
1. **Nói Thật Dùng Thật** -> `noi_that_dung_that`
2. **Dùng Rồi Mới Nói** -> `dung_roi_moi_noi`
3. **Review Thật Việc Thật** -> `review_that_viec_that`
4. **Setup Phòng Xinh** -> `setup_phong_xinh`
5. **Tủ Đồ Mùa Mới** -> `tu_do_mua_moi`
6. **Trạm Công Nghệ** / YT: Chạm Công Nghệ -> `cham_cong_nghe`
7. **Góc Tập Luyện** -> `goc_tap_luyen`

---

## 🎬 3. QUY TRÌNH KỸ THUẬT XỬ LÝ VIDEO & BẢO ĐẢM CHẤT LƯỢNG CAO NHẤT

### A. 🔴 YouTube Shorts & 🔷 Facebook Reels (100% GỐC 4K NGUYÊN BẢN):
- **ĐĂNG THẲNG FILE GỐC 4K (2160x3840)** từ máy tính của người dùng!
- Tuyệt đối KHÔNG render lại, KHÔNG giảm dung lượng, giữ nguyên 100% độ sắc nét Ultra HD.
- **YouTube:** Dùng `YouTubeShortsUploader` với `chunksize=2MB` và vòng lặp `next_chunk(num_retries=10)` tự động kết nối lại khi mạng chập chờn.
- **Facebook Reels:** Sử dụng lệnh `curl -s -X POST -H "Authorization: OAuth <token>" -H "offset: 0" -H "file_size: <size>" -H "Content-Type: application/octet-stream" -T "<file_4k>" "<upload_url>"` để truyền tải dữ liệu trực tiếp từ ổ cứng (tránh lỗi out of memory).

### B. 📸 Instagram Reels (100% GỐC 4K NGUYÊN BẢN - RESUMABLE DIRECT UPLOAD):
- **GIỮ NGUYÊN ĐỘ PHÂN GIẢI GỐC (4K 2160x3840 hoặc 1080p gốc)**, tuyệt đối KHÔNG bóp độ phân giải hay ép bitrate!
- Sử dụng giao thức **Resumable Direct Upload** của Meta Graph API (`rupload.facebook.com`), truyền tải trực tiếp từ máy:
  1. Khởi tạo: `POST /{ig_user_id}/media` với `media_type: "REELS"`, `upload_type: "resumable"`.
  2. Upload trực tiếp file từ ổ cứng:
     `curl -4 -s -X POST -H "Authorization: OAuth <token>" -H "offset: 0" -H "file_size: <size>" -H "Content-Type: application/octet-stream" -T "<file>" "<upload_url>"`
  3. Kiểm tra container `status_code == "FINISHED"` rồi xuất bản qua `/{ig_user_id}/media_publish`.
- *Lưu ý thời lượng Meta Graph API:* Reels yêu cầu độ dài <= 90s. Nếu video dài hơn 90s, dùng `ffmpeg -y -i <goc> -t 89 -c copy <file_89s>` để cắt đúng 89s mà **KHÔNG render lại**, bảo toàn nguyên vẹn 100% độ phân giải 4K gốc!

### C. 🧵 Threads (CHUẨN VIDEO SẮC NÉT ULTRA-HD THEO ĐÚNG API META):
- **Quy chuẩn kỹ thuật Meta Threads API:**
  + **Độ phân giải tối đa:** Chiều ngang tối đa là **1920px** (chuẩn dọc tối ưu: **1080x1920 (9:16)**; tuyệt đối không gửi video > 1920px bề ngang vì máy chủ Meta sẽ tự động báo lỗi `ERROR`).
  + **Chất lượng hình ảnh:** Tuyệt đối KHÔNG nén xuống mức thấp (như 900 kbps - 1.1 Mbps làm video bị mờ). Luôn xuất bản ở **bitrate cao 5.5 - 7.5 Mbps** (`-b:v 6500k -maxrate 7000k -c:v h264_videotoolbox` hoặc CRF 18), bảo toàn độ sắc nét căng mịn, màu sắc trung thực trên màn hình điện thoại.
  + **Cấu trúc tệp:** Bắt buộc đặt `moov` atom ở đầu tệp (`-movflags +faststart`), không chứa Edit Lists (`edts`).
  + **CDN & Kích thước:** Tối ưu file dưới 100 MB để tải siêu tốc lên CDN `https://uguu.se/upload.php` trong 5 giây, giúp máy chủ Meta crawler nạp dữ liệu tức thì mà không gặp lỗi ngắt kết nối.
  + **Giới hạn Caption:** Tham số `text` trên Threads API tối đa **500 ký tự** (luôn tối ưu nội dung cô đọng kèm hashtags dưới 500 ký tự).

### D. 📖 Facebook Story & Instagram Story:
- **Facebook Story:** Xuất bản qua `/{page_id}/video_stories` trực tiếp qua `curl -T`.
- **Instagram Story:** Cắt đúng 59 giây đầu bằng `ffmpeg -y -i <goc> -t 59 -c copy <story_59s>` (chuẩn Meta Story tối đa 60.0s, giữ nguyên chất lượng gốc bằng `-c copy`) và tải lên bằng Resumable Upload trực tiếp.

---

## 💬 4. QUY TRÌNH GẮN LINK SHOPEE AFFILIATE TỰ ĐỘNG CHUẨN SEO
1. Đọc danh sách tất cả link rút gọn từ file CSV (cột `Liên kết chuyển đổi`).
2. Tự động chuẩn bị danh sách comment theo mẫu luân phiên:
   - Bình luận 1: `Link sản phẩm ở đây: <URL 1>`
   - Bình luận 2: `Link xem và mua hàng ngay tại đây nè: <URL 2>`
   - Bình luận 3: `Link sản phẩm ở đây nha mọi người: <URL 3>`
   - Bình luận 4: `Link sản phẩm ở đây, mọi người ủng hộ nhé: <URL 4>`
   - Bình luận 5+: `Link sản phẩm: <URL 5...>`
3. Đăng tuần tự tất cả các bình luận trên vào:
   - YouTube Shorts / Video (qua `youtube.commentThreads().insert`)
   - Facebook Reels (qua `/{video_id}/comments`)
   - Instagram Reels (qua `/{media_id}/comments`)
   - Threads (qua `reply_to_id` với `threads_publish`)

---

## 📊 5. BÁO CÁO KẾT QUẢ CHO NGƯỜI DÙNG
Sau khi hoàn tất, luôn xuất bảng tổng hợp đầy đủ các đường dẫn xem trực tiếp (Live Links):
1. 🔴 Link YouTube Shorts
2. 🔷 Link Facebook Reels & Facebook Story Video ID
3. 📸 Link Instagram Reels & Instagram Story ID
4. 🧵 Link Threads bài viết
5. Danh sách các Link Affiliate đã gắn

---

## 🚀 6. CHIẾN LƯỢC VIẾT TIÊU ĐỀ, MÔ TẢ & HASHTAGS VIRAL (BẮT BUỘC ÁP DỤNG)
Tuyệt đối KHÔNG đặt tiêu đề khô khan kiểu `Review [Tên sản phẩm]`. Luôn áp dụng 1 trong 3 công thức giật Hook:
1. **Công thức So sánh / Listicle (Ưu tiên số 1):** `So Sánh [3-6-9 Mẫu] [Tên sản phẩm]: Loại Nào Đáng Mua / Ngọt Nhất? #Shorts`
2. **Công thức Hoài nghi / Cảnh báo:** `[Tên sản phẩm] Có Thực Sự Tốt / Bền Như Lời Đồn? Test Thực Tế #Shorts` hoặc `Đừng Mua [Sản phẩm] Nếu Chưa Biết Điều Này!`
3. **Công thức Nỗi đau / Giải pháp:** `[Cách giải quyết nỗi đau] Với [Tên sản phẩm] Giá Rẻ #Shorts`
- **Mô tả (Description):** Câu đầu tiên luôn là Hook đánh trúng tâm lý người xem (vd: *"Nước nhà tắm quá yếu? Test ngay vòi xịt tăng áp..."*), tiếp theo là lời kêu gọi Like/Follow và toàn bộ danh sách Link Shopee Affiliate.
- **Hashtags:** `#<brand_name_no_space> #Shorts #Reels #reviewgiadung #xuhuong #fyp #trending` + các thẻ tag ngách liên quan trực tiếp đến sản phẩm.

---

## ⚡ 7. QUY TRÌNH PHẢN HỒI NHANH KHÔNG NGHẼN CHAT (NON-BLOCKING ASYNC)
Để người dùng không phải chờ đợi trong khung chat khi upload các file 4K dung lượng lớn (> 1 GB):
1. **Phản hồi ngay trong 5 giây đầu tiên**:
   - Trích xuất link từ CSV.
   - Soạn thảo và hiển thị ngay cho người dùng:
     + 🏷️ **Tiêu đề (Title)** chuẩn SEO
     + 📝 **Mô tả & Hashtags**
     + 💬 **Danh sách toàn bộ bình luận Affiliate**
   - Kích hoạt script đăng tải chạy ngầm (Background Task / Daemon).
   - Kết thúc lượt phản hồi ngay lập tức để giải phóng khung chat, người dùng có thể yêu cầu đăng video tiếp theo ngay!
2. **Theo dõi và kiểm tra kết quả**:
   - Script chạy ngầm sẽ tự động ghi nhật ký và lưu các link live vào `POST/scratch/publish_results_<brand>.json` và `walkthrough.md`.
   - Khi người dùng hỏi "đăng xong chưa", "link đâu", bot chỉ cần đọc file kết quả và báo ngay danh sách link hoàn tất.
