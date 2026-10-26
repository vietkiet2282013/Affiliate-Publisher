# 🚀 Facebook Reels Uploader (Python)

Chương trình tự động hoá quy trình tải video lên **Facebook Reels** (dành cho Fanpage và Trang cá nhân chuyên nghiệp) sử dụng **Meta Graph API (Facebook Reels Publishing API)** chính thức.

---

## 📂 Danh sách các file trong thư mục

- [`index.ipynb`](file:///Users/nguyendinhthe/post/index.ipynb) / [`index..ipynb `](file:///Users/nguyendinhthe/post/index..ipynb ): Jupyter Notebook chứa mã nguồn đầy đủ, có thể chạy trực tiếp từng bước trong IDE/Jupyter.
- [`reels_uploader.py`](file:///Users/nguyendinhthe/post/reels_uploader.py): Module Python độc lập chứa Class `FacebookReelsUploader` với đầy đủ tính năng.
- [`main.py`](file:///Users/nguyendinhthe/post/main.py): Giao diện dòng lệnh CLI (hỗ trợ cả gõ lệnh `--video` hoặc nhập tương tác).
- [`.env.example`](file:///Users/nguyendinhthe/post/.env.example): Mẫu file cấu hình lưu trữ `PAGE_ID` và `PAGE_ACCESS_TOKEN`.

---

## 🛠️ Hướng dẫn cài đặt

Mở Terminal và chạy lệnh sau để cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

---

## 📖 Hướng dẫn lấy `PAGE_ID` và `PAGE_ACCESS_TOKEN`

Để đăng được video lên Facebook Reels, bạn cần 2 thông tin:

### 1. Lấy `PAGE_ID` (ID Fanpage)
1. Mở Facebook và chuyển sang Fanpage của bạn.
2. Vào mục **Giới thiệu (About)** -> **Thông tin chi tiết về Trang** -> Sao chép **ID Trang (Page ID)**.
3. Hoặc bạn có thể thấy trực tiếp ID này trên URL của trình duyệt.

### 2. Lấy `PAGE_ACCESS_TOKEN` (Có đủ quyền đăng video)
1. Truy cập [Meta for Developers - Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Tại mục **Facebook App**, chọn App của bạn (hoặc bấm *Tạo ứng dụng* nếu chưa có).
3. Tại ô **User or Page**, chọn **Page Access Token** của Fanpage bạn muốn đăng.
4. Tại mục **Add a Permission**, thêm các quyền sau:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `publish_video`
5. Bấm **Generate Access Token** và bấm đồng ý cấp quyền.
6. *(Khuyên dùng)* Để lấy **Token vĩnh viễn (Long-lived Token)** không bị hết hạn sau 1 tiếng:
   - Truy cập [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/).
   - Dán Token vừa lấy -> Bấm **Debug** -> Kéo xuống cuối trang và bấm **Extend Access Token** để nhận Token dài hạn/vĩnh viễn cho Page.

---

## 🎯 Cách sử dụng

### Cách 1: Chạy trực tiếp trong Jupyter Notebook
Mở file [`index.ipynb`](file:///Users/nguyendinhthe/post/index.ipynb) trong IDE:
1. Điền `PAGE_ID` và `PAGE_ACCESS_TOKEN` vào ô cấu hình.
2. Điền đường dẫn file video `VIDEO_PATH` và `CAPTION`.
3. Bấm **Run All** hoặc chạy từng cell từ trên xuống dưới.

### Cách 2: Chạy qua dòng lệnh (CLI)
```bash
# Chạy tương tác (chương trình sẽ hỏi từng bước):
python main.py

# Hoặc truyền trực tiếp tham số:
python main.py --video "duong_dan_video.mp4" --caption "Video hot #reels #viral" --page-id "123456" --token "EAAB..."
```
