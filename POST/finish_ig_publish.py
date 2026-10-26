# -*- coding: utf-8 -*-
import sys
import time
import requests
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

brands_file = r"c:\Affiliate\post1\POST\config\brands.json"
with open(brands_file, "r", encoding="utf-8") as f:
    brands = json.load(f)

b = brands["setup_phong_xinh"]
ig_id = b["instagram"]["ig_user_id"]
token = b["instagram"]["access_token"]
cid = "18103199633110178"

print(f"Đang xuất bản container {cid} lên Instagram...")
pub_res = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media_publish", data={"creation_id": cid, "access_token": token}).json()
print("Kết quả xuất bản:", pub_res)

if "id" in pub_res:
    media_id = pub_res["id"]
    media_info = requests.get(f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink&access_token={token}").json()
    permalink = media_info.get("permalink", f"https://www.instagram.com/reel/{media_id}")
    print(f"🎉 LINK INSTAGRAM REELS: {permalink}")
    
    links_file = r"C:\Affiliate\Setup Phòng Xinh\Link customed\Instagram\Tập 1_copy_nhanh.txt"
    with open(links_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip().startswith("http")]
    
    print(f"💬 Bắt đầu đăng {len(lines)} bình luận affiliate lên Instagram...")
    for idx, link in enumerate(lines):
        cm_res = requests.post(
            f"https://graph.facebook.com/v19.0/{media_id}/comments",
            data={"message": f"Món {idx+1}: {link}", "access_token": token}
        ).json()
        cid_comment = cm_res.get("id")
        print(f"   -> Đã comment món {idx+1}/{len(lines)}: {cid_comment}")
        time.sleep(1.5)
    print("DONE INSTAGRAM!")
