import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders.facebook_uploader import FacebookReelsUploader

with open(os.path.join(BASE_DIR, "config", "brands.json"), "r", encoding="utf-8") as f:
    brands = json.load(f)

channels_to_publish = [
    {
        "brand_key": "cham_da_tiet_kiem",
        "video_path": r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\3.mp4",
        "title": "Bí Quyết Da Căng Mịn Tiết Kiệm Tại Nhà",
        "caption": (
            "Không cần đi spa tốn kém, em sủi bọt Biodance Bubble Booster kết hợp mặt nạ Collagen này giúp da căng mướt, cấp ẩm sâu cả ngày dài! Chị em thử ngay nha ✨\n\n"
            "#ChămDaTiếtKiệm #Biodance #SkincareHànQuốc #PhụcHồiDa #DưỡngẨmDa"
        ),
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/AUuFsAMkZV",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2Vrv0G6vRe"
        ]
    },
    {
        "brand_key": "quan_ao_gia_hoi",
        "video_path": r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\1.mp4",
        "title": "Mẫu Áo Khoác Cardigan Len Mỏng Nhẹ Chuẩn Gu Hàn Quốc",
        "caption": (
            "Item không thể thiếu trong tủ đồ mùa này của các nàng chính là em cardigan len mỏng nhẹ này nha! "
            "Form rộng thoải mái che khuyết điểm cực tốt, chất len mềm dịu không lo dặm ngứa. "
            "Phối với chân váy hay quần suông đều xinh xỉu ✨ Link sắm đồ giá hời mình để dưới bình luận nhé 👇\n\n"
            "#QuầnÁoGiáHời #ÁoCardigan #Thờitrangnữ #GợiÝPhốiĐồ #OOTDVietnam"
        ),
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/4B0CPnbxgg",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/LnTqkqYT3"
        ]
    },
    {
        "brand_key": "yeu_da_hon_bo",
        "video_path": r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\1.mp4",
        "title": "Tuyệt Chiêu Xóa Nếp Nhăn Vùng Cổ Đơn Giản Tại Nhà",
        "caption": (
            "Chăm mặt kỹ đến đâu mà bỏ quên vùng cổ là dễ bị già trước tuổi lắm nha các nàng! "
            "Cứu cánh cho những ai có đường ngấn cổ sâu hay da chùng nhão là em kem dưỡng cổ retinol này đây. "
            "Chất kem mỏng nhẹ thấm nhanh, kết hợp massage nâng cơ mỗi ngày là cổ căng mịn thấy rõ ✨ "
            "Link mua chính hãng mình ghim dưới comment nhé 👇\n\n"
            "#YêuDaHơnBồ #KemCổ #MẹoChămDa #LàmĐẹpMỗiNgày #SkincareTips"
        ),
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/80CrjtroBl",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6q0uLkwFYe"
        ]
    }
]

print("=" * 70, flush=True)
print("🚀 BẮT ĐẦU ĐĂNG FACEBOOK REELS CHO 3 KÊNH: Chăm Da Tiết Kiệm, Quần Áo Giá Hời, Yêu Da Hơn Bồ", flush=True)
print("=" * 70, flush=True)

results = []

for ch in channels_to_publish:
    bkey = ch["brand_key"]
    bdata = brands[bkey]
    name = bdata["name"]
    fb_cfg = bdata["facebook"]
    
    print(f"\n▶️ Đang xử lý: {name} (Page ID: {fb_cfg['page_id']})...", flush=True)
    uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
    res = uploader.upload_reel(
        video_path=ch["video_path"],
        title=ch["title"],
        caption=ch["caption"],
        comment_text=ch["comments"],
        scheduled_time=None  # Đăng công khai ngay lập tức
    )
    if res and res.get("reel_url"):
        print(f"🎉 THÀNH CÔNG: {name} -> {res.get('reel_url')}", flush=True)
        results.append({"name": name, "brand_key": bkey, "url": res.get("reel_url"), "status": "SUCCESS"})
    else:
        print(f"❌ THẤT BẠI: {name}", flush=True)
        results.append({"name": name, "brand_key": bkey, "status": "FAILED"})

print("\n" + "=" * 70, flush=True)
print("TỔNG KẾT KẾT QUẢ ĐĂNG BÀI FACEBOOK REELS:", flush=True)
for r in results:
    print(f"- {r['name']}: {r.get('url', 'Thất bại')}", flush=True)
print("=" * 70, flush=True)
