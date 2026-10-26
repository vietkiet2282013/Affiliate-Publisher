# Affiliate-Publisher 🚀

> **Hệ thống Quản lý, Đăng tải Đa Nền tảng (YouTube Shorts, Facebook Reels, Instagram Reels, Threads) & Dashboard Tối Ưu Tự Động (AI Cứu Flop, Auto Thumbnail Sync) cho 10 Kênh Affiliate.**

---

## 📌 Tính Năng Nổi Bật

1. **Dashboard Đăng Đa Kênh Tập Trung**:
   - Quản lý đồng thời **10 Kênh / Thương hiệu** trên 1 cổng duy nhất (`http://localhost:5000`).
   - Hỗ trợ đăng tải cùng lúc hoặc hẹn giờ lên **4 Nền tảng**:
     - ▶️ **YouTube Shorts** (API v3 Resumable Upload + Ghim Comment Shopee tự động)
     - 📘 **Facebook Reels** (Graph API chunked upload + Ghim bình luận link mua hàng)
     - 📸 **Instagram Reels** (Meta Graph API Container + Polling trạng thái)
     - 🧵 **Threads** (Meta Threads API video/carousel)
2. **AI Cứu Video Flop (Tự động 24h & Thủ công)**:
   - Tự động quét các video sau 24h xuất bản nếu lượt xem thấp (< 200 views).
   - Tự động dùng AI (Google Gemini) viết lại Tiêu đề, Mô tả, Hashtag hấp dẫn hơn.
   - Cập nhật trực tiếp lên video Facebook & YouTube (tối đa 3 lần sau mỗi 24h).
   - Session Drawer bên phải hiển thị chi tiết số lượng video đã quét, so sánh tiêu đề cũ - mới và link xem trực tiếp.
3. **Đồng Bộ Thumbnail Tự Động từ YouTube sang Facebook**:
   - Nhận diện thumbnail sắc nét chất lượng cao từ YouTube Shorts (`sardefault.jpg` 768x1365 hoặc `maxresdefault.jpg`).
   - Tự động cập nhật làm ảnh bìa cho Facebook Reel thông qua Facebook Graph API.
4. **Hệ Thống Phân Phối Link Affiliate Shopee Tự Động**:
   - Quản lý Master Excel / Google Sheets, tự động trích xuất mã Shopee, tự ghim comment và phân bổ link cho từng tập/video.

---

## 💻 Hướng Dẫn Cài Đặt & Chạy Local (Trên Máy Mới)

### 1. Yêu Cầu Hệ Thống
- **Hệ điều hành**: Windows 10/11 (khuyên dùng) hoặc macOS / Linux.
- **Python**: Phiên bản **Python 3.10** hoặc **Python 3.11** (khuyên dùng Python 3.11).
- **Git**: Đã cài đặt Git trên máy.

### 2. Cài Đặt Mã Nguồn & Thư Viện

Mở Terminal / PowerShell và thực hiện:

```bash
# 1. Clone source code về máy
git clone https://github.com/vietkiet2282013/Affiliate-Publisher.git
cd Affiliate-Publisher

# 2. Tạo môi trường ảo Python (Khuyên dùng)
python -m venv .venv

# 3. Kích hoạt môi trường ảo
# Trên Windows:
.venv\Scripts\activate
# Trên macOS / Linux:
# source .venv/bin/activate

# 4. Nâng cấp pip và cài đặt thư viện phụ thuộc
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Cấu Hình Tài Khoản & API Keys

- **Cấu hình các Kênh (Brands)**:
  Tệp cấu hình chính nằm tại: `POST/config/brands.json`
  Khai báo danh sách kênh, Page ID, Instagram Account ID, Access Token Meta, và đường dẫn thư mục video tương ứng.
- **Tài khoản Google / YouTube API**:
  Đặt tệp xác thực OAuth `client_secret.json` vào thư mục gốc hoặc thư mục `POST/`. Các token đăng nhập OAuth2 cho từng kênh sẽ được lưu trong `POST/credentials/youtube_tokens/`.
- **Cấu hình Gemini AI (Dùng cho tính năng Cứu Flop)**:
  Tạo tệp `.env` hoặc cấu hình biến môi trường:
  ```env
  GEMINI_API_KEY=your_gemini_api_key_here
  ```

### 4. Khởi Động Dashboard

Cách 1: Chạy trực tiếp bằng lệnh Python:
```bash
python app.py --port 5000
```

Cách 2: Trên Windows, nhấp đúp vào tệp batch:
```text
CHAY_DASHBOARD.bat
```

Sau khi khởi động thành công, mở trình duyệt truy cập:
👉 **`http://localhost:5000`**

---

## 🤖 PROMPT MẪU CHO AI AGENT (Dùng khi setup máy mới)

> Khi bạn clone project này sang một máy tính mới và muốn AI (như Antigravity, Cursor, Claude Code, Copilot, ChatGPT CLI,...) tự động kiểm tra, cài đặt thư viện và khởi động Dashboard luôn mà không cần bạn gõ lệnh thủ công, hãy sao chép và dán prompt dưới đây vào cửa sổ chat của AI:

```markdown
Tôi vừa clone repository Affiliate-Publisher về máy tính này.
Nhiệm vụ của bạn:
1. Kiểm tra môi trường Python trên máy (yêu cầu Python 3.10 hoặc 3.11).
2. Tạo virtual environment (.venv) nếu chưa có, kích hoạt nó và cài đặt toàn bộ dependencies từ `requirements.txt`.
3. Kiểm tra các tệp cấu hình cần thiết:
   - `POST/config/brands.json`
   - Tệp `.env` hoặc API key Gemini (hỏi tôi nếu cần bổ sung).
   - Thư mục `POST/credentials/youtube_tokens/` và `POST/credentials/tiktok_tokens/`.
4. Khởi động Flask server trên port 5000 (`python app.py --port 5000` hoặc chạy `CHAY_DASHBOARD.bat`).
5. Kiểm tra kết nối `http://127.0.0.1:5000/api/all_tasks` để đảm bảo Dashboard đã sẵn sàng hoạt động, sau đó báo link truy cập cho tôi.
```

---

## 📂 Cấu Trúc Thư Mục Chính

```text
Affiliate-Publisher/
├── app.py                      # Core Flask backend server & API endpoints
├── fetch_analytics.py          # Bộ phân tích dữ liệu, đối soát video đa kênh & đồng bộ thumbnail
├── auto_rescue_flop.py         # Module AI quét và cứu video flop tự động
├── CHAY_DASHBOARD.bat          # File khởi động nhanh dashboard trên Windows
├── TỰ_ĐỘNG_CỨU_FLOP.bat        # File chạy tự động cứu flop (dùng cho Task Scheduler)
├── requirements.txt            # Danh sách thư viện Python cần thiết
├── templates/
│   └── index.html              # Giao diện Dashboard quản trị đa kênh, Drawer & Analytics
├── POST/
│   ├── config/
│   │   ├── brands.json         # Danh sách 10 kênh và cấu hình tokens
│   │   ├── flop_settings.json  # Cấu hình tiêu chí video flop
│   │   └── optimized_flop_videos.json # Lịch sử tối ưu video bằng AI
│   ├── credentials/            # Thư mục chứa token YouTube & TikTok
│   └── uploaders/              # Module đăng tải: YouTube, Facebook, Instagram, Threads
└── README.md                   # Tài liệu hướng dẫn sử dụng
```

---

## 📜 Giấy Phép & Lưu Ý
- **Lưu ý bảo mật**: Không commit video, file media dung lượng lớn, hoặc tệp Access Token nhạy cảm lên repository công khai.
- Dự án phục vụ mục đích tự động hóa quy trình Affiliate Marketing đa kênh.
