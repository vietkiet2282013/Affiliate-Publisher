import sys
import time
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

container_id = "18112958035944270"
ig_token = "EAAmD979AfWEBSncOL8nIXnoUbU2FjT3YdUZBH06JgYxJTZBYeZCq9ZBxM33B0L2531eIet13wXj1e92d8w2qXkXh3b4XyM4L"
ig_user_id = "17841432174052981"

# Đọc token chuẩn từ brands.json
import json
with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

ig_cfg = brands["cham_da_tiet_kiem"]["instagram"]
ig_user_id = ig_cfg["ig_user_id"]
ig_token = ig_cfg["access_token"]

comment_txt_path = r"c:\Affiliate\post1\comment.txt"
with open(comment_txt_path, "r", encoding="utf-8") as f:
    templates = [line.strip() for line in f if line.strip()]

import openpyxl
excel_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Link customed\Facebook\cây lăn massage mắt.xlsx"
wb = openpyxl.load_workbook(excel_path)
sheet = wb.active

comments_list = []
for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
    if i > 1 and len(row) > 2 and row[2]:
        p_link = str(row[2]).strip()
        template = templates[(i-2) % len(templates)]
        if not template.endswith(" ") and not template.endswith(":"):
            template += " "
        comments_list.append(f"{template} {p_link}")

print("⏳ Đang thử xuất bản lại Instagram container:", container_id)
pub_res = requests.post(
    f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
    data={"creation_id": container_id, "access_token": ig_token},
    timeout=30
).json()

print("Kết quả:", pub_res)
if "id" in pub_res:
    media_id = pub_res["id"]
    print(f"🎉 THÀNH CÔNG INSTAGRAM REEL! Media ID: {media_id}")
    for idx, c in enumerate(comments_list, 1):
        time.sleep(2)
        c_res = requests.post(
            f"https://graph.facebook.com/v19.0/{media_id}/comments",
            data={"message": c, "access_token": ig_token},
            timeout=20
        ).json()
        print(f"  Comment {idx}: {c_res}")
