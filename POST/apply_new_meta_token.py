# -*- coding: utf-8 -*-
import json
import os
import sys
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

user_token = "EAAmD979AfWEBSrLkqs3ql74Aq7uQ9yJzfe4udglzufH0CPW96pcdvHbXRZAiJt9IUGjURZCMg6myGm2l8tPzI9qYnLOqwyAWBvTTwHQAFxElI2VH6HqOJySKNFP0Hj5kL4NXHeUYFDN6P9ikgAlcYuTbQvluUnzntZAwLYsIRQrwNmHA75ZAzZARyobRs6PZC9FIasYZCoWZA0slPuZBMGzZB8ePCnS3mQWoFZA9wwIaY3qIZCg4o7jKmC64f0DldK5YwuTmyDVzX0so2ZA7HyYZBAr09l"

brands_file = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_file, "r", encoding="utf-8") as f:
    brands = json.load(f)

# 1. Fetch accounts
res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?limit=100&access_token={user_token}").json()
pages = res.get("data", [])
print(f"Lấy được {len(pages)} trang từ User Token mới:")
for p in pages:
    print(f"  - {p.get('name')} (ID: {p.get('id')})")

page_map = {p["id"]: p for p in pages}

for bkey, bval in brands.items():
    fb_id = bval.get("facebook", {}).get("page_id")
    if fb_id and fb_id in page_map:
        p_info = page_map[fb_id]
        new_tok = p_info["access_token"]
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
                if "instagram" in bval and "ig_user_id" in bval["instagram"]:
                    bval["instagram"]["access_token"] = new_tok
                    print(f"   📸 Đồng bộ token mới cho IG ID sẵn có: {bval['instagram']['ig_user_id']}")
        except Exception as e:
            print(f"   ⚠️ Lỗi check IG cho {fb_id}: {e}")

# Lưu lại brands.json
with open(brands_file, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=4, ensure_ascii=False)

print("\n🎉 Đã cập nhật thành công toàn bộ Token cho brands.json!")
