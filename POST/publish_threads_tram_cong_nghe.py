# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import requests
import openpyxl

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

with open(r"C:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)["cham_cong_nghe"]["threads"]

user_id = cfg["user_id"]
token = cfg["access_token"]

p = r"C:\Affiliate\Trạm Công Nghệ\Link customed\Threads\đèn màn hình máy tính.xlsx"
wb = openpyxl.load_workbook(p)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
items = []
for r in rows[1:]:
    if r and len(r) > 2 and r[2]:
        name = str(r[1]).strip() if r[1] else ""
        url = str(r[2]).strip()
        items.append({"name": name, "url": url})

main_post_text = (
    "Đèn treo màn hình máy tính bảo vệ mắt chống mỏi mắt cho góc làm việc ban đêm cực sang xịn mịn! ✨\n\n"
    "🛒 Link mua 3 mẫu hot nhất:\n"
    f"1. Đèn bàn học Pixar: {items[0]['url']}\n"
    f"2. Đèn Sidohome SF301 RGB: {items[1]['url']}\n"
    f"3. Đèn Lymax L1 Plus: {items[2]['url']}\n\n"
    "(Toàn bộ link các dòng còn lại mình để dưới bình luận nhé 👇)\n"
    "#tramcongnghe #denmanhinh #desksetup"
)

print("1. Creating main Thread post...")
create_res = requests.post(
    f"https://graph.threads.net/v1.0/{user_id}/threads",
    data={
        "media_type": "TEXT",
        "text": main_post_text,
        "access_token": token
    },
    timeout=30
).json()
print("Create main post container:", create_res)

container_id = create_res["id"]
time.sleep(3)

print("2. Publishing main Thread post...")
pub_res = requests.post(
    f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
    data={"creation_id": container_id, "access_token": token},
    timeout=30
).json()
print("Publish main post:", pub_res)

post_id = pub_res.get("id")
permalink = f"https://www.threads.net/post/{post_id}"
print("Thread URL:", permalink)

templates = [
    "Link sản phẩm ở đây: ",
    "Link xem và mua hàng ngay tại đây nè: ",
    "Link sản phẩm ở đây nha mọi người: ",
    "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
    "Link sản phẩm: ",
    "Link sản phẩm ở đây cho ai cần nha: ",
    "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
    "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
    "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
    "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: "
]

print("3. Replying comments with remaining affiliate links...")
for idx, it in enumerate(items[3:], 4):
    cmt_text = f"{templates[idx % len(templates)]}\n{it['url']} ({it['name'][:45]}...)"
    r_rep = requests.post(
        f"https://graph.threads.net/v1.0/{user_id}/threads",
        data={
            "media_type": "TEXT",
            "text": cmt_text,
            "reply_to_id": post_id,
            "access_token": token
        },
        timeout=30
    ).json()
    if "id" in r_rep:
        time.sleep(2)
        requests.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
            data={"creation_id": r_rep["id"], "access_token": token},
            timeout=30
        )
        print(f"  Replied comment {idx}: {it['url']}")
    time.sleep(2)

print("🎉 Hoàn tất toàn bộ chuỗi đăng Threads và affiliate comments!")
