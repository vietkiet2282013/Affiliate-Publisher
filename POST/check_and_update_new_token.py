# -*- coding: utf-8 -*-
import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

new_token = "EAAmD979AfWEBSvIUvuEFX2ZC39rsATmBPBsSRZC6zZAIjPYQKZAEURWEnQgTDgVWkZAZBPJ6tZAs87kpLwheOPtYk6VEHYjNtgX983Ou0XG8cU3S8Hw47bYdwo8otBOr82QXQFfWWsJ9tDZCfMOE4n6xKxiwZC9w87Chj49uTEdqTwv5qTJFAkwnwFxCzctRnRIGrgT8l4OwwXVuYXEYT8i2crgl6R8lxA7OoQ04l7Imz2MJ4rV7ZBoPijnZBJHQicXLfLN2a9ZBCZAIPGSOUP9tKfFaZA"

# 1. Kiểm tra me/permissions
perm_res = requests.get(f"https://graph.facebook.com/v19.0/me/permissions?access_token={new_token}").json()
print("=== PERMISSIONS ===")
for p in perm_res.get("data", []):
    print(f"  {p.get('permission')}: {p.get('status')}")

# 2. Lấy danh sách trang me/accounts
acc_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?limit=100&access_token={new_token}").json()
pages = acc_res.get("data", [])
print(f"\n=== SỐ TRANG LẤY ĐƯỢC: {len(pages)} ===")
page_dict = {}
for p in pages:
    print(f"  - {p.get('name')} | Page ID: {p.get('id')}")
    page_dict[p.get("id")] = p

# 3. Cập nhật brands.json
brands_path = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_path, "r", encoding="utf-8") as f:
    brands = json.load(f)

print("\n=== KIỂM TRA & CẬP NHẬT TỪNG KÊNH ===")
for bkey, bval in brands.items():
    fb_id = bval.get("facebook", {}).get("page_id")
    if fb_id in page_dict:
        page_info = page_dict[fb_id]
        page_token = page_info["access_token"]
        bval["facebook"]["access_token"] = page_token
        print(f"✅ {bval.get('name')}: Đã có Page Access Token riêng!")
        
        # Test quyền Reels trên trang
        test_reel = requests.post(f"https://graph.facebook.com/v19.0/{fb_id}/video_reels", data={
            "upload_phase": "start",
            "access_token": page_token
        }).json()
        if "video_id" in test_reel:
            print(f"   🎉 Quyền Reels Facebook OK (video_id: {test_reel['video_id']})")
        else:
            print(f"   ⚠️ Lỗi test Reels FB: {test_reel.get('error', {}).get('message')}")
            
        # Kiểm tra IG Business Account
        ig_res = requests.get(f"https://graph.facebook.com/v19.0/{fb_id}?fields=instagram_business_account&access_token={page_token}").json()
        ig_acc = ig_res.get("instagram_business_account", {})
        if ig_acc and "id" in ig_acc:
            ig_id = ig_acc["id"]
            if "instagram" not in bval:
                bval["instagram"] = {}
            bval["instagram"]["ig_user_id"] = ig_id
            bval["instagram"]["access_token"] = page_token
            print(f"   📸 IG Business ID: {ig_id} -> Đã đồng bộ token IG!")
        else:
            if "instagram" in bval and "ig_user_id" in bval["instagram"]:
                bval["instagram"]["access_token"] = page_token
                print(f"   📸 Dùng Page Token cho IG ID có sẵn: {bval['instagram']['ig_user_id']}")
    else:
        print(f"❌ {bval.get('name')} (Page ID: {fb_id}): KHÔNG có trong token này!")

# Ghi lại brands.json
with open(brands_path, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=4, ensure_ascii=False)

print("\n🎉 Đã cập nhật xong brands.json!")
