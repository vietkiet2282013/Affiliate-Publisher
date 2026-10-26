import os
import sys
import json
import random
import openpyxl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"c:\Affiliate\post1\POST"
sys.path.insert(0, BASE_DIR)

from uploaders.facebook_uploader import FacebookReelsUploader
from uploaders.instagram_uploader import InstagramReelsUploader
from uploaders.threads_uploader import ThreadsAPIUploader
from uploaders.youtube_uploader import YouTubeShortsUploader

# 1. Config Kênh
brand_key = "cham_da_tiet_kiem"
with open(os.path.join(BASE_DIR, "config", "brands.json"), "r", encoding="utf-8") as f:
    brands = json.load(f)

b_data = brands[brand_key]
brand_name = b_data["name"]

# 2. File & Metadata
video_path = r"c:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\video chưa đăng\5.mp4"
excel_path = r"C:\Affiliate\Chăm Da Tiết Kiệm\Link customed\Facebook\cây lăn massage mắt.xlsx"
comment_txt_path = r"c:\Affiliate\post1\comment.txt"

# 3. Đọc template comment
with open(comment_txt_path, "r", encoding="utf-8") as f:
    templates = [line.strip() for line in f if line.strip()]

# 4. Đọc sản phẩm & link từ Excel
wb = openpyxl.load_workbook(excel_path)
sheet = wb.active

products = []
for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
    if i > 1 and len(row) > 2 and row[2]:
        p_name = str(row[1]).strip() if row[1] else "Sản phẩm"
        p_link = str(row[2]).strip()
        products.append({"name": p_name, "link": p_link})

# Chuẩn bị danh sách comment tách riêng từng link với mẫu comment.txt
comments_list = []
for idx, p in enumerate(products):
    template = templates[idx % len(templates)]
    if not template.endswith(" ") and not template.endswith(":"):
        template += " "
    comments_list.append(f"{template} {p['link']}")

title = "Cây Lăn Massage Mắt Giảm Thâm Quầng & Nâng Cơ Da Mặt ✨"

caption_general = (
    f"Chăm da quanh mắt và nâng cơ mặt cực đơn giản tại nhà với cây lăn massage mắt này nha chị em! ✨\n"
    f"Giúp thư giãn, giảm mỏi mắt và mờ quầng thâm hiệu quả.\n"
    f"Link sắm đồ mình để sẵn dưới bình luận nha cả nhà 👇\n\n"
    f"#ChămDaTiếtKiệm #CâyLănMassageMắt #GuaSha #SkincareTips"
)

results = {}

print("\n" + "="*70)
print(f"🚀 HOÀN THIỆN ĐĂNG BÀI BỔ SUNG CHO YOUTUBE & INSTAGRAM ({brand_name.upper()})")
print("="*70)

# B. YOUTUBE SHORTS
try:
    print("\n▶️ Đang đăng bổ sung YouTube Shorts...")
    yt_cfg = b_data["youtube"]
    token_file = os.path.join(BASE_DIR, yt_cfg["token_file"])
    yt_uploader = YouTubeShortsUploader(token_file=token_file)
    if yt_uploader.authenticate():
        res_yt = yt_uploader.upload_short(
            video_path=video_path,
            title=f"{title} #shorts",
            description=caption_general,
            tags=["shorts", "massagemat", "chamdatietkiem", "review"],
            comment_text=comments_list
        )
        if res_yt and res_yt.get("shorts_url"):
            results["YouTube"] = res_yt.get("shorts_url")
            print(f"✅ YouTube Shorts thành công: {res_yt.get('shorts_url')}")
        else:
            results["YouTube"] = "Thất bại"
    else:
        results["YouTube"] = "Lỗi xác thực Token"
except Exception as e:
    print(f"❌ Lỗi YouTube: {e}")
    results["YouTube"] = f"Lỗi: {e}"

# C. INSTAGRAM REELS (Dùng CDN Link để đăng ổn định với video lớn)
try:
    print("\n▶️ Đang đăng bổ sung Instagram Reels...")
    ig_cfg = b_data["instagram"]
    ig_token = ig_cfg["access_token"]
    ig_user_id = ig_cfg["ig_user_id"]
    
    # Upload qua Catbox CDN trước
    import requests
    print("⏳ Tải video lên CDN trực tiếp cho Instagram...")
    with open(video_path, "rb") as f:
        r_cdn = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=120)
    
    if r_cdn.status_code == 200 and r_cdn.text.startswith("http"):
        cdn_url = r_cdn.text.strip()
        print(f"  CDN URL: {cdn_url}")
        
        # Khởi tạo container bằng video_url
        init_res = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={"media_type": "REELS", "video_url": cdn_url, "caption": caption_general, "access_token": ig_token},
            timeout=30
        ).json()
        
        container_id = init_res.get("id")
        if container_id:
            import time
            print(f"  Container ID: {container_id}. Đợi Instagram xử lý video...")
            for _ in range(30):
                time.sleep(5)
                st_res = requests.get(
                    f"https://graph.facebook.com/v19.0/{container_id}",
                    params={"fields": "status_code,status", "access_token": ig_token},
                    timeout=15
                ).json()
                st_code = st_res.get("status_code")
                if st_code == "FINISHED":
                    break
            
            pub_res = requests.post(
                f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                data={"creation_id": container_id, "access_token": ig_token},
                timeout=30
            ).json()
            
            if "id" in pub_res:
                media_id = pub_res["id"]
                results["Instagram"] = f"Media ID: {media_id}"
                print(f"✅ Instagram Reel thành công! Media ID: {media_id}")
                
                # Comment
                print("💬 Đang đăng bình luận Instagram...")
                for idx, c in enumerate(comments_list, 1):
                    time.sleep(2)
                    requests.post(
                        f"https://graph.facebook.com/v19.0/{media_id}/comments",
                        data={"message": c, "access_token": ig_token},
                        timeout=20
                    )
            else:
                results["Instagram"] = f"Lỗi xuất bản: {pub_res}"
        else:
            results["Instagram"] = f"Lỗi container: {init_res}"
    else:
        results["Instagram"] = "Không tạo được CDN link"
except Exception as e:
    print(f"❌ Lỗi Instagram: {e}")
    results["Instagram"] = f"Lỗi: {e}"

print("\n" + "="*70)
print("KẾT QUẢ BỔ SUNG:")
for platform, res in results.items():
    print(f"- {platform}: {res}")
print("="*70)
