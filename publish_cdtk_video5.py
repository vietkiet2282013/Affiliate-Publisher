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

print(f"📌 Kênh: {brand_name} ({brand_key})")
print(f"🎬 Video: {video_path}")
print(f"🔗 Số lượng sản phẩm/link: {len(products)}")

# Chuẩn bị danh sách comment tách riêng từng link với mẫu comment.txt
comments_list = []
for idx, p in enumerate(products):
    template = templates[idx % len(templates)]
    # Đảm bảo template kết thúc có khoảng trắng nếu cần
    if not template.endswith(" ") and not template.endswith(":"):
        template += " "
    comments_list.append(f"{template} {p['link']}")

title = "Cây Lăn Massage Mắt Giảm Thâm Quầng & Nâng Cơ Da Mặt ✨"
main_link = products[0]["link"] if products else ""

caption_fb = (
    f"Chăm da quanh mắt và nâng cơ mặt cực đơn giản tại nhà với cây lăn massage mắt này nha chị em! ✨\n"
    f"Giúp thư giãn, giảm mỏi mắt và mờ quầng thâm hiệu quả.\n\n"
    f"🛒 Sắm ngay chính hãng tại: {main_link}\n\n"
    f"#ChămDaTiếtKiệm #CâyLănMassageMắt #GuaSha #SkincareTips #LàmĐẹpMỗiNgày"
)

caption_general = (
    f"Chăm da quanh mắt và nâng cơ mặt cực đơn giản tại nhà với cây lăn massage mắt này nha chị em! ✨\n"
    f"Giúp thư giãn, giảm mỏi mắt và mờ quầng thâm hiệu quả.\n"
    f"Link sắm đồ mình để sẵn dưới bình luận nha cả nhà 👇\n\n"
    f"#ChămDaTiếtKiệm #CâyLănMassageMắt #GuaSha #SkincareTips"
)

results = {}

print("\n" + "="*70)
print(f"🚀 ĐĂNG VIDEO 5.MP4 LÊN 4 NỀN TẢNG CHO KÊN {brand_name.upper()}")
print("="*70)

# A. FACEBOOK REELS
try:
    print("\n▶️ 1/4. Đang đăng Facebook Reels...")
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
        print(f"✅ Facebook Reel thành công: {res_fb.get('reel_url')}")
    else:
        results["Facebook"] = "Thất bại"
except Exception as e:
    print(f"❌ Lỗi Facebook: {e}")
    results["Facebook"] = f"Lỗi: {e}"

# B. YOUTUBE SHORTS
try:
    print("\n▶️ 2/4. Đang đăng YouTube Shorts...")
    yt_cfg = b_data["youtube"]
    token_file = os.path.join(BASE_DIR, yt_cfg["token_file"])
    yt_uploader = YouTubeShortsUploader(token_file=token_file)
    if yt_uploader.authenticate():
        res_yt = yt_uploader.upload_shorts(
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

# C. INSTAGRAM REELS
try:
    print("\n▶️ 3/4. Đang đăng Instagram Reels...")
    ig_cfg = b_data["instagram"]
    ig_uploader = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
    res_ig = ig_uploader.upload_reel(
        video_path=video_path,
        caption=caption_general,
        comment_text=comments_list
    )
    if res_ig and res_ig.get("media_id"):
        results["Instagram"] = f"Media ID: {res_ig.get('media_id')}"
        print(f"✅ Instagram Reel thành công: Media ID {res_ig.get('media_id')}")
    else:
        results["Instagram"] = "Thất bại"
except Exception as e:
    print(f"❌ Lỗi Instagram: {e}")
    results["Instagram"] = f"Lỗi: {e}"

# D. THREADS VIDEO
try:
    print("\n▶️ 4/4. Đang đăng Threads Video...")
    th_cfg = b_data["threads"]
    th_uploader = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
    res_th = th_uploader.upload_video_thread(
        video_path=video_path,
        caption=caption_general
    )
    if res_th and res_th.get("id"):
        post_id = res_th.get("id")
        permalink = res_th.get("permalink", f"https://www.threads.net/post/{post_id}")
        results["Threads"] = permalink
        print(f"✅ Threads Video thành công: {permalink}")

        # Post replies
        print("💬 [Threads] Đang đăng từng reply link affiliate...")
        for idx, c in enumerate(comments_list, 1):
            try:
                import time
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
print("TỔNG KẾT BÀI ĐĂNG KÊNH CHĂM DA TIẾT KIỆM (5.MP4):")
for platform, res in results.items():
    print(f"- {platform}: {res}")
print("="*70)
