import json
import os
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
brands_path = os.path.join(BASE_DIR, "config", "brands.json")

with open(brands_path, "r", encoding="utf-8") as f:
    brands = json.load(f)

tokens = {
    "yeu_da_hon_bo": "THAAXS7Ru2STVBYmFQYUdFODJBaFJmTDhQZA3M3dHhuTUpkRUVHQkJmMm9QZA3VlOGswRWlEN2tHSVRPX1FFRFdjdmFWRWhzb051T3lvdldoUWtvWmQ0WFdDbHFROXJhMm5iV1B3N2wwQTEwTllWZAnVWRDlvOUUyUmwwT2tqRzB6cHNZARnV1UVRfaHk5RWhuQzgZD",
    "cham_da_tiet_kiem": "THAAXS7Ru2STVBYlpoNk5JeVhkWmtvTVd3SlFnODRmTnRjSk1ISHl2WjhpbmxhNDNKaTFWRDN0WDh6MW40RnhPZAzBicURTd0RHR3BOdEZAsZAV9fZA1FJOUQtME1DeG9QWEozcmp6MGxmZAlNMVXBMNExpMEdCUk4xVXhBTjlWUlFqdTZAXaTlXVFRwQ2FDYkFVRkkZD",
    "quan_ao_gia_hoi": "THAAXS7Ru2STVBYmI5LTZArN0JrNklTTXc2bjRfTnVwS3U3NFAyWHFnT0h1SEpnU0R1emtDeEduWVRpeDlSLWNYX2U3d0FXbDgtZA3ZAxbmZA3SUs5WngyelQ3V2lDUlB3TGhmSFV4dUpCYURtRUlvRk9UZAUJENE1LVWNaUjAzQWtMVFEzeDFaSGxkR1FkMWpVWjgZD"
}

print("=" * 70)
print("🚀 BẮT ĐẦU CẤU HÌNH VÀ KÍCH HOẠT THREADS API CHO 3 KÊNH MỚI")
print("=" * 70)

for bkey, short_token in tokens.items():
    brand_name = brands[bkey]["name"]
    print(f"\n▶️ Đang xử lý kênh: {brand_name} ({bkey})...")
    
    # 1. Đổi Short-lived token thành Long-lived token (hạn 60 ngày)
    exchange_url = "https://graph.threads.net/access_token"
    params = {
        "grant_type": "th_exchange_token",
        "client_secret": "THRDS...", # Meta handles token exchange via access_token param or direct usage
        "access_token": short_token
    }
    
    long_token = short_token
    try:
        res = requests.get(f"https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=1&access_token={short_token}", timeout=15).json()
        if "access_token" in res:
            long_token = res["access_token"]
            print("  ✅ Đã đổi thành công sang Long-lived Token 60 ngày!")
        else:
            print(f"  ℹ️ Giữ nguyên token gốc (Note: {res.get('error', {}).get('message', 'Direct Token')})")
    except Exception as e:
        print(f"  ⚠️ Không thể kết nối server đổi token, dùng token gốc: {e}")

    # 2. Truy vấn User ID Threads
    user_id = None
    username = None
    try:
        me_res = requests.get(f"https://graph.threads.net/v1.0/me?fields=id,username,threads_profile_picture_url&access_token={long_token}", timeout=15).json()
        if "id" in me_res:
            user_id = me_res["id"]
            username = me_res.get("username", brands[bkey]["threads"].get("username"))
            print(f"  ✅ Lấy thành công Threads User ID: {user_id} (Username: @{username})")
        else:
            print(f"  ❌ Lỗi lấy thông tin User ID Threads: {me_res}")
    except Exception as e:
        print(f"  ❌ Lỗi kết nối Threads Graph API: {e}")

    # 3. Cập nhật cấu hình brands.json
    if "threads" not in brands[bkey]:
        brands[bkey]["threads"] = {}
    
    brands[bkey]["threads"]["access_token"] = long_token
    if user_id:
        brands[bkey]["threads"]["user_id"] = user_id
    if username:
        brands[bkey]["threads"]["username"] = username
    
    if "threads" not in brands[bkey]["platforms"]:
        brands[bkey]["platforms"].append("threads")

# Lưu lại cấu hình mới vào brands.json
with open(brands_path, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 70)
print("🎉 ĐÃ LƯU THÀNH CÔNG TOÀN BỘ CẤU HÌNH THREADS MỚI VÀO BRANDS.JSON!")
print("=" * 80)
