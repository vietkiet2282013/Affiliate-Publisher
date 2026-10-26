# -*- coding: utf-8 -*-
"""
Script xác thực lại kênh YouTube (Cấp mới token OAuth2) cho bất kỳ kênh nào trong hệ thống.
Đặc biệt dùng khi:
- Kênh cũ bị khóa/chết và bạn đã tạo kênh mới cùng tài khoản Google.
- Token hết hạn hoặc mất quyền truy cập.
"""

import os
import sys
import json
import argparse
import socket
import webbrowser

# Force IPv4
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _getaddrinfo_ipv4

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def reauth_channel(brand_key: str = "noi_that_dung_that"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    post_dir = os.path.join(base_dir, "POST")
    client_secret_file = os.path.join(post_dir, "client_secret.json")
    
    if not os.path.exists(client_secret_file):
        # Fallback to post1 root
        client_secret_file = os.path.join(base_dir, "client_secret.json")

    if not os.path.exists(client_secret_file):
        print(f"❌ Không tìm thấy file client_secret.json tại: {client_secret_file}")
        return False

    brands_file = os.path.join(post_dir, "config", "brands.json")
    brand_name = brand_key
    if os.path.exists(brands_file):
        try:
            with open(brands_file, "r", encoding="utf-8") as bf:
                bdata = json.load(bf)
                brand_name = bdata.get(brand_key, {}).get("name", brand_key)
        except Exception:
            pass

    token_dir = os.path.join(post_dir, "credentials", "youtube_tokens")
    os.makedirs(token_dir, exist_ok=True)
    token_file = os.path.join(token_dir, f"{brand_key}.json")

    print("\n" + "=" * 65)
    print(f"🔑 TIẾN TRÌNH XÁC THỰC KÊNH YOUTUBE MỚI: {brand_name.upper()}")
    print("=" * 65)
    print(f"📁 File client_secret: {os.path.basename(client_secret_file)}")
    print(f"📁 File token sẽ lưu: {token_file}")

    # Sao lưu token cũ nếu có
    if os.path.exists(token_file):
        bak_file = f"{token_file}.bak"
        try:
            import shutil
            shutil.copy2(token_file, bak_file)
            print(f"📦 Đã sao lưu token cũ sang: {os.path.basename(bak_file)}")
            os.remove(token_file)
        except Exception as _e_bak:
            print(f"⚠️ Không thể sao lưu file token cũ: {_e_bak}")

    print("\n👉 HƯỚNG DẪN CÁC BƯỚC THỰC HIỆN TRÊN TRÌNH DUYỆT:")
    print("  1. Trình duyệt sẽ tự động mở trang đăng nhập Google OAuth.")
    print("  2. Chọn đúng tài khoản Google (email quản lý các kênh).")
    print("  3. ⚠️ QUAN TRỌNG NHẤT: Khi Google hiện danh sách 'Chọn kênh hoặc tài khoản thương hiệu',")
    print(f"     hãy bấm CHỌN KÊNH '{brand_name}' MỚI!")
    print("  4. Bấm 'Tiếp tục' / 'Cho phép' (Allow) để cấp quyền tải video lên YouTube.")
    print("=" * 65 + "\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_file,
            SCOPES
        )
        # prompt='select_account consent' bắt buộc Google hiển thị màn hình chọn kênh / tài khoản
        creds = flow.run_local_server(
            port=0,
            prompt="select_account consent",
            authorization_prompt_message="🌐 Đang chờ bạn chọn kênh và cấp quyền trên trình duyệt..."
        )

        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        print(f"\n✅ ĐÃ LƯU TOKEN YOUTUBE MỚI THÀNH CÔNG VÀO:")
        print(f"   👉 {token_file}")

        # Thử lấy thông tin kênh vừa xác thực
        try:
            yt = build("youtube", "v3", credentials=creds)
            res = yt.channels().list(part="snippet,statistics", mine=True).execute()
            items = res.get("items", [])
            if items:
                ch = items[0]
                ch_title = ch.get("snippet", {}).get("title", "")
                ch_id = ch.get("id", "")
                custom_url = ch.get("snippet", {}).get("customUrl", "")
                subs = ch.get("statistics", {}).get("subscriberCount", "0")
                print("\n🎉 THÔNG TIN KÊNH YOUTUBE ĐÃ KẾT NỐI THÀNH CÔNG:")
                print(f"   📺 Tên kênh: {ch_title}")
                print(f"   🆔 Channel ID: {ch_id}")
                if custom_url:
                    print(f"   🔗 Link: https://youtube.com/{custom_url}")
                print(f"   👥 Người đăng ký: {subs}")
            else:
                print("ℹ️ Đã kết nối token thành công! (Chưa lấy được chi tiết kênh)")
        except Exception as _e_ch:
            print(f"ℹ️ Token đã hợp lệ! (Lưu ý: {_e_ch})")

        print("\n🚀 BÂY GIỜ BẠN CÓ THỂ:")
        print("   1. Vào web http://localhost:5000/")
        print(f"   2. Tại mục kênh '{brand_name}', bấm '🚀 Đăng kênh này'.")
        print("   3. Video sẽ được tải trực tiếp lên KÊNH YOUTUBE MỚI!")
        print("=" * 65 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ Lỗi xác thực kênh: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xác thực lại kênh YouTube cho hệ thống Affiliate")
    parser.add_argument("--brand", default="noi_that_dung_that", help="Mã brand (mặc định: noi_that_dung_that)")
    args = parser.parse_args()
    reauth_channel(args.brand)
