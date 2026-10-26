import os
import sys
import time
import json
import requests
import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"c:\Affiliate\post1\POST"
sys.path.insert(0, BASE_DIR)

from uploaders.facebook_uploader import FacebookReelsUploader
from uploaders.threads_uploader import ThreadsAPIUploader
from uploaders.youtube_uploader import YouTubeShortsUploader

# 1. Cấu hình Kênh & File
brand_key = "dung_roi_moi_noi"
with open(os.path.join(BASE_DIR, "config", "brands.json"), "r", encoding="utf-8") as f:
    brands = json.load(f)

b_data = brands[brand_key]
brand_name = b_data["name"]

video_path = r"c:\Affiliate\Dùng Rồi Mới Nói\Video_việt_hóa\video chưa đăng\chảo nướng.mp4"
excel_path = r"c:\Affiliate\Dùng Rồi Mới Nói\Link customed\Facebook\Chảo nướng điện.xlsx"
comment_txt_path = r"c:\Affiliate\post1\comment.txt"

if not os.path.exists(video_path):
    print(f"❌ Không tìm thấy video: {video_path}")
    sys.exit(1)

# 2. Đọc template comment từ comment.txt
with open(comment_txt_path, "r", encoding="utf-8") as f:
    templates = [line.strip() for line in f if line.strip()]

# 3. Đọc link sản phẩm từ Excel
wb = openpyxl.load_workbook(excel_path)
sheet = wb.active

products = []
for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
    if i > 1 and len(row) > 2 and row[2]:
        p_name = str(row[1]).strip() if row[1] else "Sản phẩm"
        p_link = str(row[2]).strip()
        products.append({"name": p_name, "link": p_link})

print(f"======================================================================")
print(f"🚀 TỰ ĐỘNG ĐĂNG BÀI 4 NỀN TẢNG: {brand_name.upper()}")
print(f"📁 Video: {video_path}")
print(f"🔗 Số lượng link sản phẩm: {len(products)}")
print(f"======================================================================")

# 4. Chuẩn bị danh sách comment tách riêng từng link với mẫu comment.txt
comments_list = []
for idx, p in enumerate(products):
    template = templates[idx % len(templates)]
    if not template.endswith(" ") and not template.endswith(":"):
        template += " "
    comments_list.append(f"{template} {p['link']}")

title = "Chảo Nướng Điện Không Khói Chống Dính Tiện Lợi Cho Gia Đình ✨"
main_link = products[0]["link"] if products else ""

caption_fb = (
    f"Ăn đồ nướng tại nhà cực nhàn với chiếc chảo nướng điện chống dính này nha cả nhà! "
    f"Gia nhiệt nhanh, không khói, dễ dàng vệ sinh sau khi ăn ✨\n\n"
    f"🛒 Mua chính hãng giá ưu đãi tại: {main_link}\n\n"
    f"#DùngRồiMớiNói #ChảoNướngĐiện #ĐồGiaDụng #GiaDụngThôngMinh #ReviewDoGiaDung"
)

caption_general = (
    f"Ăn đồ nướng tại nhà cực nhàn với chiếc chảo nướng điện chống dính này nha cả nhà! "
    f"Gia nhiệt nhanh, không khói, dễ dàng vệ sinh sau khi ăn ✨\n"
    f"Link sắm chảo chính hãng mình để sẵn dưới bình luận nha 👇\n\n"
    f"#DùngRồiMớiNói #ChảoNướngĐiện #ĐồGiaDụng #GiaDụngThôngMinh"
)

results = {}

# ==================== 1. FACEBOOK REELS ====================
print("\n▶️ 1/4. Đang đăng Facebook Reels...")
try:
    fb_cfg = b_data["facebook"]
    fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
    res_fb = fb_uploader.upload_reel(
        video_path=video_path,
        title=title,
        caption=caption_fb,
        comment_text=comments_list
    )
    if res_fb and res_fb.get("reel_url"):
        results["Facebook"] = res_fb.get("reel_url")
        print(f"✅ Facebook Reels: {res_fb.get('reel_url')}")
    else:
        results["Facebook"] = "Thất bại"
except Exception as e:
    print(f"❌ Lỗi Facebook: {e}")
    results["Facebook"] = f"Lỗi: {e}"

# ==================== 2. YOUTUBE SHORTS ====================
print("\n▶️ 2/4. Đang đăng YouTube Shorts & Comment...")
try:
    yt_cfg = b_data["youtube"]
    token_file = os.path.join(BASE_DIR, yt_cfg["token_file"])
    yt_uploader = YouTubeShortsUploader(token_file=token_file)
    if yt_uploader.authenticate():
        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=f"{title} #shorts",
            description=caption_general,
            tags=["shorts", "chao_nuong", "dungroimoinoi", "review"],
            comment_text=None # Đăng riêng comment để kiểm soát chắc chắn 100%
        )
        if res_yt and res_yt.get("video_id"):
            vid = res_yt.get("video_id")
            results["YouTube"] = res_yt.get("shorts_url")
            print(f"✅ Đã tải lên YouTube: {res_yt.get('shorts_url')}")
            
            # Đăng comment YouTube chắc chắn
            print(f"💬 [YouTube] Đang comment {len(comments_list)} link affiliate...")
            for idx, c in enumerate(comments_list, 1):
                try:
                    time.sleep(2)
                    yt_uploader.youtube.commentThreads().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "videoId": vid,
                                "topLevelComment": {
                                    "snippet": {
                                        "textOriginal": c
                                    }
                                }
                            }
                        }
                    ).execute()
                    print(f"  ✅ Đã thêm bình luận YouTube {idx}: '{c[:45]}...'")
                except Exception as ce:
                    print(f"  ⚠️ Lỗi comment YouTube {idx}: {ce}")
        else:
            results["YouTube"] = "Thất bại"
    else:
        results["YouTube"] = "Lỗi xác thực Token"
except Exception as e:
    print(f"❌ Lỗi YouTube: {e}")
    results["YouTube"] = f"Lỗi: {e}"

# ==================== 3. INSTAGRAM REELS ====================
print("\n▶️ 3/4. Đang đăng Instagram Reels...")
try:
    ig_cfg = b_data["instagram"]
    ig_token = ig_cfg["access_token"]
    ig_user_id = ig_cfg["ig_user_id"]
    
    # Upload qua Catbox CDN trước để Meta tải về
    print("⏳ Tải video lên CDN cho Instagram...")
    with open(video_path, "rb") as f:
        r_cdn = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=120)
    
    if r_cdn.status_code == 200 and r_cdn.text.startswith("http"):
        cdn_url = r_cdn.text.strip()
        print(f"  CDN URL: {cdn_url}")
        
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={"media_type": "REELS", "video_url": cdn_url, "caption": caption_general, "access_token": ig_token},
            timeout=30
        ).json()
        
        container_id = init_res.get("id")
        if container_id:
            print(f"  Container ID: {container_id}. Đang đợi Instagram xử lý...")
            for i in range(30):
                time.sleep(5)
                st_res = requests.get(
                    f"https://graph.facebook.com/v19.0/{container_id}",
                    params={"fields": "status_code,status", "access_token": ig_token},
                    timeout=15
                ).json()
                st_code = st_res.get("status_code")
                if st_code == "FINISHED":
                    print("  ✅ Container Instagram đã sẵn sàng!")
                    break
            
            # Xuất bản bài viết
            pub_res = requests.post(
                f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": ig_token},
                timeout=30
            ).json()
            
            if "id" in pub_res:
                media_id = pub_res["id"]
                results["Instagram"] = f"Media ID: {media_id}"
                print(f"✅ ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG! Media ID: {media_id}")
                
                print("💬 Đang đăng bình luận Instagram...")
                for idx, c in enumerate(comments_list, 1):
                    time.sleep(2)
                    c_res = requests.post(
                        f"https://graph.facebook.com/v19.0/{media_id}/comments",
                        data={"message": c, "access_token": ig_token},
                        timeout=20
                    ).json()
                    print(f"  ✅ Đã thêm bình luận Instagram {idx}!")
            else:
                results["Instagram"] = f"Lỗi xuất bản: {pub_res}"
        else:
            results["Instagram"] = f"Lỗi container: {init_res}"
    else:
        results["Instagram"] = "Không upload được CDN"
except Exception as e:
    print(f"❌ Lỗi Instagram: {e}")
    results["Instagram"] = f"Lỗi: {e}"

# ==================== 4. THREADS VIDEO ====================
print("\n▶️ 4/4. Đang đăng Threads Video...")
try:
    th_cfg = b_data["threads"]
    th_uploader = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
    res_th = th_uploader.upload_video_thread(
        video_path=video_path,
        caption=caption_general
    )
    if res_th and res_th.get("id"):
        post_id = res_th.get("id")
        permalink = res_th.get("permalink", f"https://www.threads.com/post/{post_id}")
        results["Threads"] = permalink
        print(f"✅ ĐÃ ĐĂNG THREADS THÀNH CÔNG: {permalink}")
        
        print("💬 [Threads] Đang đăng từng reply link affiliate...")
        for idx, c in enumerate(comments_list, 1):
            try:
                time.sleep(2)
                th_uploader.publish_reply(post_id=post_id, text=c)
                print(f"  ✅ Threads reply {idx} thành công!")
            except Exception as e:
                print(f"  ⚠️ Threads reply {idx} lỗi: {e}")
    else:
        results["Threads"] = "Thất bại"
except Exception as e:
    print(f"❌ Lỗi Threads: {e}")
    results["Threads"] = f"Lỗi: {e}"

print("\n" + "="*70)
print(f"🎉 TỔNG KẾT BÀI ĐĂNG KÊNH {brand_name.upper()} (CHẢO NƯỚNG.MP4):")
for platform, res in results.items():
    print(f"- {platform}: {res}")
print("="*70)
