import json, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

fb_reels = [
    ("dung_roi_moi_noi", "1754560939103233"),
    ("goc_tap_luyen", "1440270634662126"),
    ("review_that_viec_that", "1141805144912390"),
    ("cham_cong_nghe", "937712392267212"),
]

for bkey, vid in fb_reels:
    tok = brands[bkey]["facebook"]["access_token"]
    name = brands[bkey]["name"]
    r = requests.get(f"https://graph.facebook.com/v19.0/{vid}/comments?fields=id,message&access_token={tok}").json()
    print(f"\n[{name}] Video {vid}:")
    for c in r.get("data", []):
        cid = c["id"]
        msg = c.get("message", "")
        print(f"  Comment {cid}: {repr(msg[:50])}")
        # Nếu comment chứa cả 2 link (có 2 dòng 'http') thì xóa bỏ comment gộp này
        if msg.count("http") > 1:
            print(f"    -> Đang xóa comment gộp: {cid}")
            del_r = requests.delete(f"https://graph.facebook.com/v19.0/{cid}?access_token={tok}").json()
            print(f"    Kết quả xóa: {del_r}")
            if not del_r.get("success"):
                # Thử với id sau dấu gạch dưới
                if "_" in cid:
                    short_cid = cid.split("_")[-1]
                    del_r2 = requests.delete(f"https://graph.facebook.com/v19.0/{short_cid}?access_token={tok}").json()
                    print(f"    Thử xóa short_cid {short_cid}: {del_r2}")
