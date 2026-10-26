import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders.facebook_uploader import FacebookReelsUploader
from uploaders.instagram_uploader import InstagramReelsUploader

with open(os.path.join(BASE_DIR, "config", "brands.json"), "r", encoding="utf-8") as f:
    brands = json.load(f)

print("=" * 70, flush=True)
print("🚀 BỔ SUNG REELS CÒN THIẾU: Yêu Da Hơn Bồ (Instagram) & Nói Thật Dùng Thật (Facebook)", flush=True)
print("=" * 70, flush=True)

# 1. Instagram Reel cho Yêu Da Hơn Bồ
print("\n▶️ 1. Đang đăng Instagram Reel: Yêu Da Hơn Bồ...", flush=True)
ydhb = brands["yeu_da_hon_bo"]
ig_uploader = InstagramReelsUploader(
    ig_user_id=ydhb["instagram"]["ig_user_id"],
    access_token=ydhb["instagram"]["access_token"]
)
ig_res = ig_uploader.upload_reel(
    video_path=r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\1.mp4",
    caption=(
        "Đừng để da cổ tố cáo tuổi thật! Massage kem dưỡng cổ retinol mỗi tối giúp mờ rãnh nhăn, nâng cơ săn chắc và đều màu da cực kỳ rõ rệt ✨ "
        "Chị em nào muốn có chiếc cổ thiên nga mịn màng thì tham khảo ngay link chính hãng mình để dưới cmt nhé 👇\n\n"
        "#reels #viral #fyp #yeudahonbo #skincarecommunity #neckcare #chonglaohoa #lamdep"
    ),
    comment_text=[
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8V98KopuAs",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6fhU9Rwstd"
    ]
)
if ig_res:
    print(f"🎉 THÀNH CÔNG IG Yêu Da Hơn Bồ: Media ID {ig_res.get('media_id')}", flush=True)

# 2. Facebook Reel cho Nói Thật Dùng Thật
print("\n▶️ 2. Đang đăng Facebook Reel: Nói Thật Dùng Thật...", flush=True)
ntdt = brands["noi_that_dung_that"]
fb_uploader = FacebookReelsUploader(
    page_id=ntdt["facebook"]["page_id"],
    access_token=ntdt["facebook"]["access_token"]
)
fb_res = fb_uploader.upload_reel(
    video_path=r"C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\dây sạc macsafe.mp4",
    title="Cáp Sạc MagSafe Hít Nam Châm Chân Ái Cho iPhone",
    caption=(
        "Ai dùng iPhone hay bị gãy đầu cáp sạc thì đổi sang dây sạc MagSafe từ tính này ngay nhé! "
        "Nam châm hít chặt, xoay 360 độ vừa chơi game vừa sạc không cấn tay, lại có chip ngắt an toàn chống chai pin. "
        "Review thật cho anh em tham khảo nha ✨\n\n"
        "#NóiThậtDùngThật #SạcKhôngDây #SạcTừTính #ĐồCôngNghệHay #ReviewChânThực"
    ),
    comment_text=[
        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4B07TETYNy",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/gQFIngsUN"
    ],
    scheduled_time=None  # Đăng ngay lập tức
)
if fb_res:
    print(f"🎉 THÀNH CÔNG FB Nói Thật Dùng Thật: {fb_res.get('reel_url')}", flush=True)

print("\n" + "=" * 70, flush=True)
print("🎉 HOÀN TẤT TOÀN BỘ CÁC BÀI ĐĂNG BỔ SUNG!", flush=True)
