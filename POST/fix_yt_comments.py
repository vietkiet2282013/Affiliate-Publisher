import json, sys, os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

# Trạm Công Nghệ: Xóa comment UgwkW4xfoCm1cGTJyAx4AaABAg và thêm 2 comment riêng
# Các kênh còn lại: thêm comment riêng nếu chưa có
tasks = [
    {
        "brand": "cham_cong_nghe",
        "video_id": "ORWjXVH7st8",
        "del_comment_id": "UgwkW4xfoCm1cGTJyAx4AaABAg",
        "comments": [
            "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/2BF364WhFb",
            "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/gQFJJcPIQ"
        ]
    },
    {
        "brand": "dung_roi_moi_noi",
        "video_id": "yVBcX5TeHh4",
        "comments": [
            "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/qjh7sA18a",
            "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/AAHNpZkW73"
        ]
    },
    {
        "brand": "goc_tap_luyen",
        "video_id": "i-lAge_9onQ",
        "comments": [
            "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/8pky46Xj96",
            "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6VNt13s92T"
        ]
    },
    {
        "brand": "review_that_viec_that",
        "video_id": "bDVIlCtMz-A",
        "comments": [
            "👉 Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/20veV4z7qA",
            "👉 Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/6q0s0WvG3m"
        ]
    }
]

print("=== SỬA & BỔ SUNG BÌNH LUẬN TRÊN YOUTUBE SHORTS ===")
for t in tasks:
    bkey = t["brand"]
    vid = t["video_id"]
    b = brands.get(bkey, {})
    tok_file = os.path.join(r"c:\Affiliate\post1\POST", b.get("youtube", {}).get("token_file", ""))
    name = b.get("name", bkey)
    print(f"\n[{name}] Video {vid}:")
    try:
        creds = Credentials.from_authorized_user_file(tok_file, ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"])
        youtube = build("youtube", "v3", credentials=creds)

        if "del_comment_id" in t:
            try:
                youtube.comments().delete(id=t["del_comment_id"]).execute()
                print(f"  🗑️ Đã xóa comment gộp cũ {t['del_comment_id']}")
            except Exception as e:
                print(f"  ⚠️ Lỗi xóa comment cũ: {e}")

        for idx, ctext in enumerate(t["comments"], 1):
            body = {
                "snippet": {
                    "videoId": vid,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": ctext
                        }
                    }
                }
            }
            res = youtube.commentThreads().insert(part="snippet", body=body).execute()
            print(f"  ✅ Đã đăng comment {idx}: '{ctext}' (ID: {res.get('id')})")
    except Exception as e:
        print(f"  ❌ Lỗi xử lý YouTube {name}: {e}")
