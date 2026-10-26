import json
import os
import sys
import time
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config", "brands.json"), "r", encoding="utf-8") as f:
    brands = json.load(f)

ydhb = brands["yeu_da_hon_bo"]
ig_user_id = ydhb["instagram"]["ig_user_id"]
access_token = ydhb["instagram"]["access_token"]
video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\1.mp4"

caption = (
    "Đừng để da cổ tố cáo tuổi thật! Massage kem dưỡng cổ retinol mỗi tối giúp mờ rãnh nhăn, nâng cơ săn chắc và đều màu da cực kỳ rõ rệt ✨ "
    "Chị em nào muốn có chiếc cổ thiên nga mịn màng thì tham khảo ngay link chính hãng mình để dưới cmt nhé 👇\n\n"
    "#reels #viral #fyp #yeudahonbo #skincarecommunity #neckcare #chonglaohoa #lamdep"
)

comments = [
    "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8V98KopuAs",
    "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6fhU9Rwstd"
]

print("1. Đang tải video lên Catbox để lấy CDN URL...", flush=True)
with open(video_path, "rb") as f:
    r = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": (os.path.basename(video_path), f, "video/mp4")},
        timeout=180
    )
cdn_url = r.text.strip()
print(f"  ✅ CDN URL: {cdn_url}", flush=True)

if not cdn_url.startswith("http"):
    print("❌ Upload Catbox thất bại:", cdn_url, flush=True)
    sys.exit(1)

print("2. Đang tạo container Instagram Reel với video_url...", flush=True)
init_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
payload = {
    "media_type": "REELS",
    "video_url": cdn_url,
    "caption": caption,
    "access_token": access_token
}
c_res = requests.post(init_url, data=payload, timeout=30).json()
print("  Kết quả tạo container:", c_res, flush=True)

container_id = c_res.get("id")
if not container_id:
    print("❌ Lỗi tạo container IG:", c_res, flush=True)
    sys.exit(1)

print(f"3. Đang đợi Meta transcode video từ container {container_id}...", flush=True)
for i in range(30):
    time.sleep(5)
    st_res = requests.get(
        f"https://graph.facebook.com/v19.0/{container_id}?fields=status_code,status&access_token={access_token}",
        timeout=15
    ).json()
    st_code = st_res.get("status_code")
    print(f"  ⏳ Lần {i+1}: {st_code}", flush=True)
    if st_code == "FINISHED":
        break
    if st_code == "ERROR":
        print("❌ Lỗi xử lý IG:", st_res, flush=True)
        sys.exit(1)

print("4. Đang xuất bản Instagram Reel...", flush=True)
pub_res = requests.post(
    f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
    data={"creation_id": container_id, "access_token": access_token},
    timeout=30
).json()
print("  Kết quả xuất bản:", pub_res, flush=True)
media_id = pub_res.get("id")
if not media_id:
    print("❌ Xuất bản thất bại:", pub_res, flush=True)
    sys.exit(1)

# Lấy permalink
p_res = requests.get(f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink&access_token={access_token}").json()
permalink = p_res.get("permalink", f"https://www.instagram.com/reel/{media_id}/")
print(f"🎉 ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG: {permalink}", flush=True)

print("5. Đang đăng 2 bình luận riêng biệt...", flush=True)
for idx, c in enumerate(comments, 1):
    time.sleep(2)
    c_out = requests.post(
        f"https://graph.facebook.com/v19.0/{media_id}/comments",
        data={"message": c, "access_token": access_token},
        timeout=20
    ).json()
    print(f"  ✅ Đã thêm bình luận {idx}: '{c}' (ID: {c_out.get('id')})", flush=True)

print("=" * 70, flush=True)
print("🎉 HOÀN TẤT ĐĂNG INSTAGRAM REEL CHO YÊU DA HƠN BỒ!", flush=True)
