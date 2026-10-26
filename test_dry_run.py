import os
import sys
import json
import requests

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BRANDS_CONFIG_PATH = os.path.join("c:\\post1", "POST", "config", "brands.json")
CLIENT_SECRET_PATH = os.path.join("c:\\post1", "POST", "client_secret.json")

def test_facebook(brand_name, fb_data):
    page_id = fb_data.get("page_id")
    token = fb_data.get("access_token")
    if not page_id or not token:
        return False, "Thiếu page_id hoặc access_token"
    try:
        url = f"https://graph.facebook.com/v21.0/{page_id}?fields=id,name&access_token={token}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if "error" in data:
            return False, f"FB Error: {data['error'].get('message')}"
        return True, f"OK (Page: {data.get('name')})"
    except Exception as e:
        return False, str(e)

def test_instagram(brand_name, ig_data):
    ig_id = ig_data.get("ig_user_id")
    token = ig_data.get("access_token")
    if not ig_id or not token:
        return False, "Thiếu ig_user_id hoặc access_token"
    try:
        url = f"https://graph.facebook.com/v21.0/{ig_id}?fields=id,username&access_token={token}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if "error" in data:
            return False, f"IG Error: {data['error'].get('message')}"
        return True, f"OK (User: {data.get('username')})"
    except Exception as e:
        return False, str(e)

def test_threads(brand_name, th_data):
    token = th_data.get("access_token")
    if not token:
        return False, "Thiếu access_token"
    try:
        url = f"https://graph.threads.net/v1.0/me?fields=id,username&access_token={token}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if "error" in data:
            return False, f"Threads Error: {data['error'].get('message')}"
        return True, f"OK (User: {data.get('username')})"
    except Exception as e:
        return False, str(e)

def test_youtube(brand_name, yt_data):
    rel_path = yt_data.get("token_file")
    if not rel_path:
        return False, "Thiếu token_file"
    token_path = os.path.join("c:\\post1", "POST", rel_path)
    if not os.path.exists(token_path):
        return False, f"File không tồn tại: {token_path}"
    
    try:
        SCOPES = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl"
        ]
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds.valid:
            pass
        elif creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_path, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception as e:
                return False, f"Lỗi refresh token (có thể đã hết hạn / bị thu hồi): {e}"
        else:
            return False, "Token không hợp lệ và không thể refresh"

        youtube = build("youtube", "v3", credentials=creds)
        request = youtube.channels().list(part="snippet", mine=True)
        response = request.execute()
        items = response.get("items", [])
        if items:
            title = items[0].get("snippet", {}).get("title", "Unknown")
            return True, f"OK (Channel: {title})"
        return True, "OK (Xác thực thành công, không tìm thấy channel)"
    except Exception as e:
        return False, f"YouTube Error: {e}"

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70, flush=True)
    print("🔍 KIỂM TRA TÍNH HỢP LỆ CỦA CREDENTIALS & TOKENS TOÀN BỘ 7 KÊNH", flush=True)
    print("=" * 70, flush=True)

    if not os.path.exists(BRANDS_CONFIG_PATH):
        print(f"❌ Không tìm thấy brands.json tại {BRANDS_CONFIG_PATH}", flush=True)
        sys.exit(1)

    with open(BRANDS_CONFIG_PATH, "r", encoding="utf-8") as f:
        brands = json.load(f)

    results = []

    for brand_key, brand_info in brands.items():
        name = brand_info.get("name", brand_key)
        print(f"\n🏷️  Kênh: {name} ({brand_key})", flush=True)
        
        # Test Facebook
        fb_ok, fb_msg = test_facebook(brand_key, brand_info.get("facebook", {}))
        print(f"   🔷 Facebook:  {'✅' if fb_ok else '❌'} {fb_msg}", flush=True)
        
        # Test Instagram
        ig_ok, ig_msg = test_instagram(brand_key, brand_info.get("instagram", {}))
        print(f"   📸 Instagram: {'✅' if ig_ok else '❌'} {ig_msg}", flush=True)

        # Test Threads
        th_ok, th_msg = test_threads(brand_key, brand_info.get("threads", {}))
        print(f"   🧵 Threads:   {'✅' if th_ok else '❌'} {th_msg}", flush=True)

        # Test YouTube
        yt_ok, yt_msg = test_youtube(brand_key, brand_info.get("youtube", {}))
        print(f"   🔴 YouTube:   {'✅' if yt_ok else '❌'} {yt_msg}", flush=True)

        results.append({
            "brand": name,
            "facebook": fb_ok,
            "instagram": ig_ok,
            "threads": th_ok,
            "youtube": yt_ok
        })

    print("\n" + "=" * 70, flush=True)
    print("📊 TỔNG KẾT BẢNG TRẠNG THÁI:", flush=True)
    all_passed = True
    for r in results:
        status_line = f"- {r['brand']}: "
        checks = []
        for plat in ["facebook", "instagram", "threads", "youtube"]:
            if r[plat]:
                checks.append(f"{plat.capitalize()} ✅")
            else:
                checks.append(f"{plat.capitalize()} ❌")
                all_passed = False
        print(status_line + ", ".join(checks), flush=True)

    if all_passed:
        print("\n🎉 TOÀN BỘ CREDENTIALS ĐÃ HỢP LỆ VÀ SẴN SÀNG XUẤT BẢN!", flush=True)
    else:
        print("\nℹ️ Lưu ý: Các token bị lỗi / hết hạn cần được cấp lại hoặc đăng nhập qua trình duyệt khi xuất bản.", flush=True)

if __name__ == "__main__":
    main()
