import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Nếu file youtube_auth_helper.py nằm trong thư mục POST/ thì BASE_DIR chính là thư mục POST
POST_DIR = BASE_DIR if os.path.basename(BASE_DIR).lower() == "post" else os.path.join(BASE_DIR, "POST")
BRANDS_FILE = os.path.join(POST_DIR, "config", "brands.json")
CLIENT_SECRET_FILE = os.path.join(POST_DIR, "client_secret.json")

def main():
    print("=" * 65)
    print("🔐 CÔNG CỤ XÁC THỰC VÀ CẤP TOKEN YOUTUBE OAUTH2")
    print("   (Hỗ trợ dán link vào Profile AdsPower tương ứng)")
    print("=" * 65)

    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ Không tìm thấy client_secret.json tại: {CLIENT_SECRET_FILE}")
        sys.exit(1)

    with open(BRANDS_FILE, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_keys = list(brands.keys())
    print("\n👉 CHỌN KÊNH/THƯƠNG HIỆU CẦN ĐĂNG NHẬP XÁC THỰC:")
    for idx, key in enumerate(brand_keys, 1):
        print(f"  [{idx}] {brands[key]['name']} ({key})")

    choice = input(f"\n👉 Nhập số (1-{len(brand_keys)}): ").strip()
    try:
        brand_key = brand_keys[int(choice) - 1]
    except Exception:
        print("❌ Lựa chọn không hợp lệ!")
        sys.exit(1)

    brand_data = brands[brand_key]
    token_rel_path = brand_data.get("youtube", {}).get("token_file", f"credentials/youtube_tokens/{brand_key}.json")
    token_full_path = os.path.join(POST_DIR, token_rel_path)

    print(f"\n🎯 Đang thiết lập cho kênh: {brand_data['name']}")
    print(f"📁 File token sẽ được lưu tại: {token_full_path}")

    # Chế độ xác thực
    print("\n👉 CHỌN PHƯƠNG THỨC XÁC THỰC:")
    print("  [1] Tự động mở trình duyệt mặc định (Local Server)")
    print("  [2] Copy link xác thực để dán thủ công vào AdsPower Profile (Khuyên dùng khi dùng AdsPower)")
    mode = input("👉 Nhập lựa chọn (1-2) [mặc định 2]: ").strip() or "2"

    if mode == "1":
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
    else:
        # Sử dụng flow console / redirect uri http://localhost:8080 hoặc lấy auth url
        # Dùng redirect_uri = 'urn:ietf:wg:oauth:2.0:oob' hoặc 'http://localhost:8080/'
        # Google hiện tại chuẩn hóa redirect_uri='http://localhost:8080/'
        # Flow run_local_server với open_browser=False
        port = 8080
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            SCOPES,
            redirect_uri=f"http://localhost:{port}/"
        )
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

        print("\n" + "=" * 65)
        print("🔗 HÃY COPY ĐƯỜNG DẪN DƯỚI ĐÂY:")
        print(auth_url)
        print("=" * 65)
        print(f"\n👉 Các bước thực hiện:")
        print(f"  1. Mở cửa sổ AdsPower (Profile tương ứng với kênh {brand_data['name']}).")
        print(f"  2. Dán link trên vào thanh địa chỉ và bấm Enter.")
        print(f"  3. Đăng nhập tài khoản Google và cho phép các quyền truy cập YouTube.")
        print(f"  4. Trình duyệt trên AdsPower sẽ chuyển hướng về http://localhost:{port}/?code=...")
        print("     (Nếu trình duyệt AdsPower báo trang không thể tải được, bạn chỉ cần copy toàn bộ đường link trên thanh địa chỉ URL đó)")
        print("\n👉 Dán toàn bộ URL chuyển hướng hoặc mã 'code=' vào đây:")
        
        callback_url = input("Link/Code: ").strip()
        if not callback_url:
            print("❌ Chưa nhập dữ liệu xác thực!")
            sys.exit(1)

        if "code=" in callback_url:
            import urllib.parse
            parsed = urllib.parse.urlparse(callback_url)
            params = urllib.parse.parse_qs(parsed.query)
            auth_code = params.get("code", [None])[0] or callback_url.split("code=")[-1].split("&")[0]
        else:
            auth_code = callback_url

        flow.fetch_token(code=auth_code)
        creds = flow.credentials

    os.makedirs(os.path.dirname(token_full_path), exist_ok=True)
    with open(token_full_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"\n✅ ĐÃ XÁC THỰC THÀNH CÔNG VÀ LƯU TOKEN CHO KÊNH: {brand_data['name']}")
    print(f"🎉 Giờ đây hệ thống có thể đăng video lên kênh này qua YouTube API v3 tự động!")

if __name__ == "__main__":
    main()
