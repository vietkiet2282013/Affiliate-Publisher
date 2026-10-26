import requests
import json
import time
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

video_url = "https://files.catbox.moe/nobz39.mp4"
with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

th_cfg = brands["dung_roi_moi_noi"]["threads"]
create_url = f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads"
payload = {
    "media_type": "VIDEO",
    "video_url": video_url,
    "text": "Ăn đồ nướng tại nhà cực nhàn với chiếc chảo nướng điện chống dính này nha cả nhà! ✨\nLink mua chính hãng mình để dưới bình luận nha 👇\n\n#DùngRồiMớiNói #ChảoNướngĐiện #ĐồGiaDụng",
    "access_token": th_cfg["access_token"]
}
res = requests.post(create_url, data=payload, timeout=30).json()
print("Direct Threads create container:", res)

if "id" in res:
    c_id = res["id"]
    print("Container created:", c_id, ". Đang chờ Threads xử lý video...")
    for i in range(40):
        time.sleep(5)
        st = requests.get(
            f"https://graph.threads.net/v1.0/{c_id}",
            params={"fields": "status,error_message", "access_token": th_cfg["access_token"]},
            timeout=20
        ).json()
        print(f"Trạng thái ({i+1}):", st.get("status"))
        if st.get("status") == "FINISHED":
            pub = requests.post(
                f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                data={"creation_id": c_id, "access_token": th_cfg["access_token"]},
                timeout=30
            ).json()
            print("🎉 THREADS PUBLISHED:", pub)
            
            # Post replies
            if "id" in pub:
                post_id = pub["id"]
                comment_txt_path = r"c:\Affiliate\post1\comment.txt"
                with open(comment_txt_path, "r", encoding="utf-8") as cf:
                    templates = [line.strip() for line in cf if line.strip()]
                import openpyxl
                excel_path = r"c:\Affiliate\Dùng Rồi Mới Nói\Link customed\Facebook\Chảo nướng điện.xlsx"
                wb = openpyxl.load_workbook(excel_path)
                sheet = wb.active
                comments_list = []
                for idx_r, row in enumerate(sheet.iter_rows(values_only=True), 1):
                    if idx_r > 1 and len(row) > 2 and row[2]:
                        p_link = str(row[2]).strip()
                        tmpl = templates[(idx_r-2) % len(templates)]
                        if not tmpl.endswith(" ") and not tmpl.endswith(":"):
                            tmpl += " "
                        comments_list.append(f"{tmpl} {p_link}")
                
                print("💬 Đang reply link affiliate lên Threads...")
                for idx_c, c in enumerate(comments_list, 1):
                    time.sleep(2)
                    cr = requests.post(
                        f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads",
                        data={"media_type": "TEXT", "text": c, "reply_to_id": post_id, "access_token": th_cfg["access_token"]},
                        timeout=30
                    ).json()
                    if "id" in cr:
                        requests.post(
                            f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                            data={"creation_id": cr["id"], "access_token": th_cfg["access_token"]},
                            timeout=30
                        )
                        print(f"  ✅ Threads reply {idx_c} thành công!")
            break
