import json, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

# Facebook Reels
fb_reels = [
    ("dung_roi_moi_noi", "1754560939103233"),
    ("goc_tap_luyen", "1440270634662126"),
    ("review_that_viec_that", "1141805144912390"),
    ("cham_cong_nghe", "937712392267212"),
]

print("=== 1. KIỂM TRA BÌNH LUẬN TRÊN FACEBOOK REELS ===")
for bkey, vid in fb_reels:
    b = brands.get(bkey, {})
    tok = b.get("facebook", {}).get("access_token")
    url = f"https://graph.facebook.com/v19.0/{vid}/comments?fields=id,message,from,created_time&access_token={tok}"
    try:
        r = requests.get(url).json()
        print(f"\n[{b.get('name')}] Video {vid}:")
        comments = r.get("data", [])
        if not comments:
            print("  (Chưa có comment hoặc rỗng)")
        for c in comments:
            print(f"  Comment ID: {c.get('id')}")
            print(f"  Content:\n{c.get('message')}\n")
    except Exception as e:
        print(f"  Lỗi: {e}")

print("\n=== 2. KIỂM TRA BÌNH LUẬN TRÊN INSTAGRAM ===")
for bkey in ["cham_da_tiet_kiem", "dung_roi_moi_noi", "goc_tap_luyen", "noi_that_dung_that", "review_that_viec_that", "quan_ao_gia_hoi", "cham_cong_nghe", "yeu_da_hon_bo"]:
    b = brands.get(bkey, {})
    ig_id = b.get("instagram", {}).get("ig_user_id")
    tok = b.get("instagram", {}).get("access_token")
    if not ig_id or not tok:
        continue
    try:
        r = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}/media?fields=id,caption,permalink,comments{{id,text,timestamp}}&limit=2&access_token={tok}").json()
        data = r.get("data", [])
        for m in data:
            comments = m.get("comments", {}).get("data", [])
            if comments:
                print(f"\n[{b.get('name')}] IG Reel: {m.get('permalink')}")
                for c in comments:
                    print(f"  Comment ID: {c.get('id')}")
                    print(f"  Text:\n{c.get('text')}\n")
    except Exception as e:
        print(f"  Lỗi IG {bkey}: {e}")
