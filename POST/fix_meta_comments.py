import json, sys, os, time, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def log(msg):
    print(msg, flush=True)

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

# 1. FIX FACEBOOK REELS COMMENTS
fb_tasks = [
    {
        "brand": "dung_roi_moi_noi",
        "video_id": "1754560939103233",
        "old_comment_id": "122113003653449291_1444308374234492",
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/gQGvzP0pK",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/qjh8IONUN"
        ]
    },
    {
        "brand": "goc_tap_luyen",
        "video_id": "1440270634662126",
        "old_comment_id": "122113060635463317_1092455849866411",
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1Lfw6rREwj",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/2qUjtcLWu8"
        ]
    },
    {
        "brand": "review_that_viec_that",
        "video_id": "1141805144912390",
        "old_comment_id": "122111734569448850_1075561298529123",
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/6L4c46ccHn",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6q0sf1aiGu"
        ]
    },
    {
        "brand": "cham_cong_nghe",
        "video_id": "937712392267212",
        "old_comment_id": "122114431473469868_2321831948565291",
        "comments": [
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/3B7aHuStDh",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/1gImV9YbGW"
        ]
    }
]

log("=== SỬA BÌNH LUẬN TRÊN FACEBOOK REELS ===")
for task in fb_tasks:
    bkey = task["brand"]
    vid = task["video_id"]
    old_cid = task["old_comment_id"]
    tok = brands[bkey]["facebook"]["access_token"]
    name = brands[bkey]["name"]
    log(f"\n[{name}] Video {vid}:")

    # Xóa comment cũ
    try:
        del_res = requests.delete(f"https://graph.facebook.com/v19.0/{old_cid}?access_token={tok}", timeout=10).json()
        log(f"  🗑️ Xóa comment cũ ({old_cid}): {del_res}")
    except Exception as e:
        log(f"  ⚠️ Lỗi xóa comment cũ: {e}")

    # Đăng từng comment riêng lẻ
    for idx, ctext in enumerate(task["comments"], 1):
        try:
            time.sleep(1)
            c_res = requests.post(
                f"https://graph.facebook.com/v19.0/{vid}/comments",
                data={"message": ctext, "access_token": tok},
                timeout=10
            ).json()
            log(f"  ✅ Đã đăng comment {idx}: '{ctext}' (ID: {c_res.get('id')})")
        except Exception as e:
            log(f"  ❌ Lỗi đăng comment {idx}: {e}")

# 2. FIX INSTAGRAM REELS COMMENTS
log("\n=== SỬA BÌNH LUẬN TRÊN INSTAGRAM REELS ===")
b_cdtk = brands["cham_da_tiet_kiem"]
ig_user_id = b_cdtk["instagram"]["ig_user_id"]
ig_tok = b_cdtk["instagram"]["access_token"]
try:
    r = requests.get(f"https://graph.facebook.com/v19.0/{ig_user_id}/media?fields=id,permalink&limit=5&access_token={ig_tok}", timeout=10).json()
    cdtk_media_id = None
    for m in r.get("data", []):
        if "Ddqy-SnjKty" in m.get("permalink", ""):
            cdtk_media_id = m.get("id")
            break

    if cdtk_media_id:
        log(f"[Chăm Da Tiết Kiệm] Media ID: {cdtk_media_id}")
        # Xóa comment cũ ID 18077548022460778
        try:
            del_r = requests.delete(f"https://graph.facebook.com/v19.0/18077548022460778?access_token={ig_tok}", timeout=10).json()
            log(f"  🗑️ Xóa comment cũ IG: {del_r}")
        except Exception as e:
            log(f"  ⚠️ Lỗi xóa comment cũ IG: {e}")

        # Đăng 2 comments riêng lẻ
        for idx, ctext in enumerate([
            "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9zxzHFOeaQ",
            "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5VVWZlvEIy"
        ], 1):
            try:
                time.sleep(1)
                c_res = requests.post(
                    f"https://graph.facebook.com/v19.0/{cdtk_media_id}/comments",
                    data={"message": ctext, "access_token": ig_tok},
                    timeout=10
                ).json()
                log(f"  ✅ Đã đăng comment {idx} IG: '{ctext}' (ID: {c_res.get('id')})")
            except Exception as e:
                log(f"  ❌ Lỗi đăng comment {idx} IG: {e}")
except Exception as e:
    log(f"  ⚠️ Lỗi xử lý IG Chăm Da Tiết Kiệm: {e}")

log("\n🎉 HOÀN TẤT CẬP NHẬT TÁCH BÌNH LUẬN TRÊN FACEBOOK & INSTAGRAM!")
