"""
Bước 2 + 3: Đổi Short-Lived Token → Long-Lived Token → Page Access Token vĩnh viễn
======================================================================================
1) Gọi /oauth/access_token để đổi short-lived → long-lived user token (60 ngày)
2) Gọi /me/accounts để lấy Page Access Token vĩnh viễn cho mỗi Page
3) Tự động cập nhật brands.json
"""

import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ──────── CẤU HÌNH ────────
APP_ID = "2678374879231329"
APP_SECRET = "975ca71ab78e1676c5dd4fc356ce337f"

# Short-lived User Token mới nhất do bạn cung cấp
SHORT_LIVED_TOKEN = "EAAmD979AfWEBSjrjwTTwFZBwlcAzZAZCNU0aeOjl4ZA7kQQicCbRO2ZCPHWTCRKOZBAULmJQ79BRDiphZCiFsIGQjjYeWHH5QTg1DQ1W9A15iklaIWjUhUe0RzsH2R8NIEMwoKUZBhzZCr3A5dCly9j8HFM6DvAVsoDG07OIqfMfmHbBT3Bn6dhPZCl0ETZBjRZAK0tZBfbB8taiPMZBYFK2MTD5CE8v1WSNlt6BHQ0WZAqlBVSdtCylS7PRugk95JFT05ufBJHYTb563rTNpGHP1Kj5qV5taEZD"

BRANDS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "POST", "config", "brands.json")

# ──────── BƯỚC 2: Đổi Short-Lived → Long-Lived User Token ────────
print("=" * 70)
print("BƯỚC 2: Đổi Short-Lived User Token → Long-Lived User Token (60 ngày)")
print("=" * 70)

resp = requests.get(
    "https://graph.facebook.com/v21.0/oauth/access_token",
    params={
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": SHORT_LIVED_TOKEN,
    },
    timeout=30,
)

data = resp.json()

if "access_token" not in data:
    print(f"❌ LỖI đổi token: {json.dumps(data, indent=2, ensure_ascii=False)}")
    sys.exit(1)

long_lived_user_token = data["access_token"]
expires_in = data.get("expires_in", "không rõ")
print(f"✅ Long-Lived User Token thành công!")
print(f"   Hết hạn sau: {expires_in} giây (~{int(expires_in)//86400 if isinstance(expires_in, int) else '??'} ngày)")
print(f"   Token (50 ký tự đầu): {long_lived_user_token[:50]}...")
print()

# ──────── BƯỚC 3: Lấy Page Access Token vĩnh viễn ────────
print("=" * 70)
print("BƯỚC 3: Lấy Page Access Token VĨNH VIỄN cho tất cả Pages")
print("=" * 70)

resp2 = requests.get(
    "https://graph.facebook.com/v21.0/me/accounts",
    params={
        "access_token": long_lived_user_token,
        "fields": "id,name,access_token",
        "limit": 100,
    },
    timeout=30,
)

pages_data = resp2.json()

if "data" not in pages_data:
    print(f"❌ LỖI lấy pages: {json.dumps(pages_data, indent=2, ensure_ascii=False)}")
    sys.exit(1)

# Tạo map page_id → token
page_tokens = {}
print(f"\n📄 Tìm thấy {len(pages_data['data'])} Pages:\n")
for page in pages_data["data"]:
    page_tokens[page["id"]] = page["access_token"]
    print(f"   ✅ {page['name']} (ID: {page['id']})")
    print(f"      Token (50 ký tự đầu): {page['access_token'][:50]}...")

print()

# ──────── CẬP NHẬT brands.json ────────
print("=" * 70)
print("CẬP NHẬT brands.json với Page Access Token vĩnh viễn")
print("=" * 70)

with open(BRANDS_JSON, "r", encoding="utf-8") as f:
    brands = json.load(f)

updated_count = 0
for brand_key, brand_cfg in brands.items():
    fb_cfg = brand_cfg.get("facebook", {})
    ig_cfg = brand_cfg.get("instagram", {})
    page_id = fb_cfg.get("page_id", "")

    if page_id and page_id in page_tokens:
        new_token = page_tokens[page_id]
        old_fb = fb_cfg.get("access_token", "")[:30]
        old_ig = ig_cfg.get("access_token", "")[:30]

        # Cập nhật Facebook token
        fb_cfg["access_token"] = new_token
        # Cập nhật Instagram token (dùng chung Page token)
        if ig_cfg:
            ig_cfg["access_token"] = new_token

        updated_count += 1
        print(f"   ✅ {brand_cfg['name']} (page_id={page_id})")
        print(f"      FB:  {old_fb}... → {new_token[:30]}...")
        print(f"      IG:  {old_ig}... → {new_token[:30]}...")
    else:
        print(f"   ⚠️  {brand_cfg['name']} — page_id '{page_id}' KHÔNG tìm thấy trong danh sách Pages!")

# Ghi lại file
with open(BRANDS_JSON, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=4, ensure_ascii=False)

print(f"\n{'=' * 70}")
print(f"🎉 HOÀN TẤT! Đã cập nhật {updated_count}/10 kênh với Page Access Token VĨNH VIỄN.")
print(f"   Token này KHÔNG HẾT HẠN nếu app vẫn hoạt động và permissions không bị thu hồi.")
print(f"   File đã lưu: {BRANDS_JSON}")
print(f"{'=' * 70}")

# ──────── KIỂM TRA: Debug token để xác nhận ────────
print(f"\n🔍 KIỂM TRA: Xác nhận token vĩnh viễn...")
# Lấy 1 token bất kỳ để debug
sample_page_id = list(page_tokens.keys())[0] if page_tokens else None
if sample_page_id:
    sample_token = page_tokens[sample_page_id]
    debug_resp = requests.get(
        "https://graph.facebook.com/v21.0/debug_token",
        params={
            "input_token": sample_token,
            "access_token": f"{APP_ID}|{APP_SECRET}",
        },
        timeout=30,
    )
    debug_data = debug_resp.json().get("data", {})
    expires_at = debug_data.get("expires_at", -1)
    is_valid = debug_data.get("is_valid", False)
    token_type = debug_data.get("type", "unknown")

    print(f"   Token type: {token_type}")
    print(f"   Valid: {is_valid}")
    if expires_at == 0:
        print(f"   ⏳ Hết hạn: KHÔNG BAO GIỜ (vĩnh viễn) ✅✅✅")
    else:
        from datetime import datetime
        try:
            exp_str = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   ⏳ Hết hạn: {exp_str}")
        except:
            print(f"   ⏳ expires_at = {expires_at}")
