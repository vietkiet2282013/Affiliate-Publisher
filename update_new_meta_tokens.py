import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

new_user_token = "EAAmD979AfWEBSmTAb1LmAM878z6CpZCPJvVUMiP3WptK59wcZASyLCGuxXcigMUMxOF507bQ93yBQd8dolQAcEXkrMZAKqhAZAwVpHchzwHvyo9P7MFai70KbWgmZChkaFyzhZB2YS0x0xpSZBmZCL8ZCujYTwvRKkAepzUGaRMj6qgZBmX0c6X32YPGfnLo90rgLOGSNjTHEziOY1HtgH59bcTff4iYBE69tcLCXBhrrFHHcpZBQaPOOBZC7UW1P4IdOGgZAPnuhqsQSE1ZCo9SMcNVpX"

print("1. Kiểm tra User Token mới...")
debug_url = f"https://graph.facebook.com/v19.0/debug_token"
# Hoặc gọi thẳng me
me_url = f"https://graph.facebook.com/v19.0/me?access_token={new_user_token}"
res_me = requests.get(me_url).json()
print("Thông tin User:", res_me)

# Lấy danh sách Pages & Page Access Tokens
accounts_url = f"https://graph.facebook.com/v19.0/me/accounts"
params = {
    "access_token": new_user_token,
    "fields": "id,name,access_token,instagram_business_account{id,username}",
    "limit": 100
}
res_acc = requests.get(accounts_url, params=params).json()

if "error" in res_acc:
    print("❌ Lỗi lấy danh sách Fanpage:", res_acc["error"])
    sys.exit(1)

pages = res_acc.get("data", [])
print(f"\n✅ Lấy thành công {len(pages)} Fanpages:")

page_map = {}
for p in pages:
    p_id = str(p.get("id"))
    p_name = p.get("name")
    p_tok = p.get("access_token")
    ig_biz = p.get("instagram_business_account", {})
    ig_id = str(ig_biz.get("id")) if ig_biz else None
    ig_user = ig_biz.get("username") if ig_biz else None

    page_map[p_id] = {
        "name": p_name,
        "token": p_tok,
        "ig_id": ig_id,
        "ig_user": ig_user
    }
    print(f"  📄 [Page {p_id}] {p_name} | IG ID: {ig_id} ({ig_user})")

# Cập nhật vào brands.json
brands_path = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_path, "r", encoding="utf-8") as f:
    brands = json.load(f)

updated_fb = 0
updated_ig = 0

for b_key, b_info in brands.items():
    fb_info = b_info.get("facebook", {})
    ig_info = b_info.get("instagram", {})

    pid = str(fb_info.get("page_id", "")).strip()

    if pid in page_map:
        item = page_map[pid]
        fb_info["access_token"] = item["token"]
        updated_fb += 1

        if ig_info:
            ig_info["access_token"] = item["token"]
            if item.get("ig_id") and not ig_info.get("ig_user_id"):
                ig_info["ig_user_id"] = item["ig_id"]
            updated_ig += 1

        print(f"  ✅ Đã cập nhật token cho kênh: {b_info.get('name')} (Page ID: {pid})")
    else:
        print(f"  ⚠️ Không tìm thấy Page ID {pid} trong token mới của bạn!")

with open(brands_path, "w", encoding="utf-8") as f:
    json.dump(brands, f, indent=4, ensure_ascii=False)

print(f"\n🎉 HOÀN TẤT: Đã cập nhật {updated_fb}/10 Facebook Pages và {updated_ig}/10 Instagram Accounts!")
