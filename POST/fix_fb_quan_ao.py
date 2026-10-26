# -*- coding: utf-8 -*-
import requests
import json
import sys
import openpyxl
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 1. Đọc đúng file comment.txt
with open(r"C:\Affiliate\post1\comment.txt", "r", encoding="utf-8") as f:
    templates = [l.strip() for l in f if l.strip()]

# 2. Đọc đúng file Excel Quần Áo Giá Hời Facebook Tập 2
wb = openpyxl.load_workbook(r"C:\Affiliate\Quần Áo Giá Hời\Link customed\Facebook\Tập 2.xlsx")
sheet = wb.active
rows = list(sheet.iter_rows(values_only=True))[1:]
links = [r[2].strip() for r in rows if r and len(r) >= 3 and str(r[2]).strip().startswith("http")]

print(f"Số lượng link chuẩn Quần Áo Giá Hời cần đăng: {len(links)}")
for idx, l in enumerate(links, 1):
    print(f"  {idx}. {l}")

with open(r"C:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

page_token = brands["quan_ao_gia_hoi"]["facebook"]["access_token"]
reel_id = "1815958699577391"

# 3. Lấy comment cũ và xóa hết
old_c = requests.get(f"https://graph.facebook.com/v19.0/{reel_id}/comments", params={"access_token": page_token, "limit": 50}).json()
old_items = old_c.get("data", [])
print(f"\nTìm thấy {len(old_items)} comment cũ cần xóa.")
for c in old_items:
    cid = c["id"]
    r_del = requests.delete(f"https://graph.facebook.com/v19.0/{cid}", params={"access_token": page_token}).json()
    print(f"  🗑️ Đã xóa comment {cid}: {r_del}")
    time.sleep(1)

# 4. Đăng lại dàn comment đúng 100%
print("\n🚀 Đang đăng lại dàn comment Facebook chuẩn xác theo comment.txt...")
for idx, link in enumerate(links):
    prefix = templates[idx % len(templates)]
    if not prefix.endswith(" "):
        prefix += " "
    msg = f"{prefix}{link}"
    r_post = requests.post(f"https://graph.facebook.com/v19.0/{reel_id}/comments", data={"message": msg, "access_token": page_token}).json()
    print(f"  ✅ Đã đăng comment {idx+1}: {msg} -> ID: {r_post.get('id')}")
    time.sleep(2)

print("\n🎉 Hoàn tất sửa bình luận Facebook cho Quần Áo Giá Hời!")
