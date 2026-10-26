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

video_url = "https://files.catbox.moe/xkvv0f.mp4"

caption = (
    "Góc setup phòng xinh và giải pháp an toàn tuyệt đối cho bé yêu và thú cưng! "
    "Chi tiết các món phụ kiện xinh xắn mình ghim dưới comment nhé 👇✨\n\n"
    "#setupphongxinh #decor #roomdecor #homedecor #cats #thucung #viral"
)

print(f"Bắt đầu khởi tạo Reel Instagram với URL: {video_url}")
c_res = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media", data={
    "media_type": "REELS",
    "video_url": video_url,
    "caption": caption,
    "access_token": token
}).json()
print("Kết quả tạo container:", c_res)

if "id" in c_res:
    cid = c_res["id"]
    for i in range(40):
        time.sleep(5)
        st = requests.get(f"https://graph.facebook.com/v19.0/{cid}", params={"fields": "status_code,status", "access_token": token}).json()
        status = st.get("status_code")
        print(f"[{i+1}/40] Trạng thái: {status}")
        if status == "FINISHED":
            print("Video đã sẵn sàng! Đang xuất bản lên Instagram...")
            pub_res = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media_publish", data={"creation_id": cid, "access_token": token}).json()
            print("Kết quả xuất bản:", pub_res)
            if "id" in pub_res:
                media_id = pub_res["id"]
                
                # Lấy permalink
                media_info = requests.get(f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink&access_token={token}").json()
                permalink = media_info.get("permalink", f"https://www.instagram.com/reel/{media_id}")
                print(f"🎉 LINK INSTAGRAM REELS: {permalink}")
                
                # Đăng các comment link riêng biệt
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
            break
        elif status == "ERROR":
            print("❌ Lỗi xử lý:", st)
            break
