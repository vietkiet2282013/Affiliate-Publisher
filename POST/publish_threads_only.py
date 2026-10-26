import json
import requests
import time
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

b = json.load(open(r"c:\Affiliate\post1\POST\config\brands.json", encoding="utf-8"))["tu_do_mua_moi"]["threads"]
cdn = "https://files.catbox.moe/41lmx4.mp4"

th_caption = (
    "Mùa lạnh tới rồi, mọi người thích phối đồ theo tone màu nào nhất trong 4 set này? 🤔\n"
    "1. Xanh navy + Trắng tiểu thư\n"
    "2. Trắng + Xám thanh lịch\n"
    "3. Nâu camel + Xám ấm áp\n"
    "4. Đen + Xám điệu đà\n\n"
    "Mình để sẵn link mua từng món dưới cmt cho ai cần nhé 👇 #tudomuamoi #phoidothudong #outfitmuadong #thoitrangnu"
)

th_comments = [
    "1. Áo khoác dạ tweed cúc đồng Kimee MA344: https://s.shopee.vn/50ZGt1OYJF",
    "2. Giày thể thao CAMEL CROWN: https://s.shopee.vn/5AsgLmtw9W",
    "3. Quần kaki ống cong cạp cao Tuma: https://s.shopee.vn/6L4djvpUmt",
    "4. Quần short da lộn DoA Stu Q8: https://s.shopee.vn/6AlDXcq87o",
    "5. Giày Mickey retro 7cm: https://s.shopee.vn/6VO3wEorRu",
    "6. Set đầm hai dây kèm cardigan Cara: https://s.shopee.vn/7AdkjSmK66",
    "7. Áo cardigan dệt kim mỏng: https://s.shopee.vn/5VVWkOsfTc"
]

print("1. Tạo container Threads...")
r = requests.post(f"https://graph.threads.net/v1.0/{b['user_id']}/threads", data={
    "media_type": "VIDEO",
    "video_url": cdn,
    "text": th_caption,
    "access_token": b["access_token"]
}, timeout=30).json()
print("Kết quả tạo container:", r)

cid = r.get("id")
if cid:
    print(f"2. Chờ Threads xử lý container {cid}...")
    for i in range(30):
        time.sleep(5)
        st = requests.get(f"https://graph.threads.net/v1.0/{cid}", params={"fields": "status,error_message", "access_token": b["access_token"]}).json()
        print(f"  ⏳ Lần {i+1}: {st.get('status')}")
        if st.get("status") == "FINISHED":
            print("  ✅ Video đã xử lý xong!")
            break
        if st.get("status") == "ERROR":
            print("  ❌ Lỗi:", st)
            sys.exit(1)
            
    print("3. Xuất bản bài viết Threads...")
    pub = requests.post(f"https://graph.threads.net/v1.0/{b['user_id']}/threads_publish", data={
        "creation_id": cid,
        "access_token": b["access_token"]
    }).json()
    print("Kết quả xuất bản:", pub)
    tid = pub.get("id")
    if tid:
        p_res = requests.get(f"https://graph.threads.net/v1.0/{tid}", params={"fields": "permalink", "access_token": b["access_token"]}).json()
        permalink = p_res.get("permalink", f"https://www.threads.net/post/{tid}")
        print(f"🎉 THREADS THÀNH CÔNG: {permalink}")
        
        print("4. Bắn từng comment link vào Threads...")
        for idx, ctext in enumerate(th_comments, 1):
            time.sleep(2)
            try:
                rep_c = requests.post(
                    f"https://graph.threads.net/v1.0/{b['user_id']}/threads",
                    data={
                        "media_type": "TEXT",
                        "text": ctext,
                        "reply_to_id": tid,
                        "access_token": b["access_token"]
                    },
                    timeout=20
                ).json()
                rep_cid = rep_c.get("id")
                if rep_cid:
                    pub_rep = requests.post(
                        f"https://graph.threads.net/v1.0/{b['user_id']}/threads_publish",
                        data={"creation_id": rep_cid, "access_token": b["access_token"]},
                        timeout=20
                    ).json()
                    print(f"  ✅ Đã reply comment Threads {idx}: (ID: {pub_rep.get('id')})")
            except Exception as e:
                print(f"  ⚠️ Lỗi reply {idx}: {e}")
