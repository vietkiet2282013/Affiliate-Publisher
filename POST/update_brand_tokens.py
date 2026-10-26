import json
import os
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user_token = "EAAmD979AfWEBSlPUkm4tM3GaaqQHKl6fbMopFBDPdNHvQrZAf6wvGwjsKa9ZBj4ZA5ZA1NNcLBroXb6kFpLCvxYtMQiDb4zNMyL2H9yv1bZBzZA5rWhVRRZAwOmO9KIzgafBKZCLm83nz6v3Odw3iGUWMp8PIwmByuvZBZANgl2ZBlRdHq8wDOiJ1ziZBPnaUrZAPJTDVpwUuLZBZAH1Ey42SUI5ullTTOSLF1R7KNWLqXudeCY73YPbWvZC8CLoAzsHkVmZB1uO6ZBFplz3HNUsRnUvvB1rtS"

brands_file = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_file, "r", encoding="utf-8") as f:
    brands = json.load(f)

# 1. Fetch accounts
res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?limit=100&access_token={user_token}").json()
pages = res.get("data", [])
print(f"Lấy được {len(pages)} trang từ User Token mới.")

page_map = {p["id"]: p for p in pages}

for bkey, bval in brands.items():
    fb_id = bval.get("facebook", {}).get("page_id")
    if fb_id and fb_id in page_map:
        p_info = page_map[fb_id]
        new_tok = p_info["access_token"]
        old_tok = bval["facebook"].get("access_token", "")
        bval["facebook"]["access_token"] = new_tok
        print(f"✅ Đã cập nhật FB token cho [{bval.get('name')}] (Page ID: {fb_id})")

        # Kiểm tra instagram_business_account
        try:
            ig_check = requests.get(f"https://graph.facebook.com/v19.0/{fb_id}?fields=instagram_business_account&access_token={new_tok}").json()
            ig_acc = ig_check.get("instagram_business_account", {})
            if ig_acc and "id" in ig_acc:
                ig_id = ig_acc["id"]
                if "instagram" not in bval:
                    bval["instagram"] = {}
                bval["instagram"]["ig_user_id"] = ig_id
                bval["instagram"]["access_token"] = new_tok
                print(f"   📸 Tìm thấy IG Business ID: {ig_id} -> Đã đồng bộ token IG!")
            else:
                # Nếu không có IG gắn kèm qua API này, vẫn giữ ig_user_id cũ nhưng thử dùng token mới nếu cùng app
                pass
        except Exception as e:
            print(f"   ⚠️ Lỗi check IG cho {fb_id}: {e}")

# Lưu lại brands.json
with open(brands_file, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=4, ensure_ascii=False)

print("\n🎉 Đã lưu cấu hình mới vào brands.json thành công!")
