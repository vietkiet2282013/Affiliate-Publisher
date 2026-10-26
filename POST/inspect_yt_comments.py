import json, sys, os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

yt_shorts = [
    ("cham_da_tiet_kiem", "H9sEGsHNzEU"),
    ("dung_roi_moi_noi", "yVBcX5TeHh4"),
    ("goc_tap_luyen", "i-lAge_9onQ"),
    ("noi_that_dung_that", "tBDx54E8DqM"),
    ("review_that_viec_that", "bDVIlCtMz-A"),
    ("quan_ao_gia_hoi", "6XOPCBM_yRc"),
    ("cham_cong_nghe", "ORWjXVH7st8"),
    ("yeu_da_hon_bo", "mOt2y-PBV8s")
]

print("=== KIỂM TRA BÌNH LUẬN TRÊN YOUTUBE SHORTS ===")
for bkey, vid in yt_shorts:
    b = brands.get(bkey, {})
    tok_file = os.path.join(r"c:\Affiliate\post1\POST", b.get("youtube", {}).get("token_file", ""))
    if not os.path.exists(tok_file):
        continue
    try:
        creds = Credentials.from_authorized_user_file(tok_file, ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"])
        youtube = build("youtube", "v3", credentials=creds)
        res = youtube.commentThreads().list(part="snippet", videoId=vid, maxResults=10).execute()
        items = res.get("items", [])
        print(f"\n[{b.get('name')}] Video https://youtube.com/shorts/{vid}:")
        if not items:
            print("  (Không có comment)")
        for it in items:
            c_id = it.get("id")
            snip = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            print(f"  Comment ID: {c_id}")
            print(f"  Text: {snip.get('textOriginal')}")
    except Exception as e:
        print(f"  [{b.get('name')}] Lỗi query YT: {e}")
