import json
import os
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config", "brands.json"), "r", encoding="utf-8") as f:
    brands = json.load(f)

# YouTube Shorts mapped IDs
yt_map = {
    "cham_da_tiet_kiem": "https://youtube.com/shorts/H9sEGsHNzEU",
    "dung_roi_moi_noi": "https://youtube.com/shorts/yVBcX5TeHh4",
    "goc_tap_luyen": "https://youtube.com/shorts/i-lAge_9onQ",
    "noi_that_dung_that": "https://youtube.com/shorts/tBDx54E8DqM",
    "review_that_viec_that": "https://youtube.com/shorts/bDVIlCtMz-A",
    "quan_ao_gia_hoi": "https://youtube.com/shorts/6XOPCBM_yRc",
    "cham_cong_nghe": "https://youtube.com/shorts/ORWjXVH7st8",
    "yeu_da_hon_bo": "https://youtube.com/shorts/mOt2y-PBV8s"
}

# Facebook Reels mapped IDs
fb_map = {
    "cham_da_tiet_kiem": "https://www.facebook.com/reel/1831407488170848",
    "dung_roi_moi_noi": "https://www.facebook.com/reel/1754560939103233",
    "goc_tap_luyen": "https://www.facebook.com/reel/1440270634662126",
    "review_that_viec_that": "https://www.facebook.com/reel/1141805144912390",
    "quan_ao_gia_hoi": "https://www.facebook.com/reel/1020692827692517",
    "cham_cong_nghe": "https://www.facebook.com/reel/937712392267212",
    "yeu_da_hon_bo": "https://www.facebook.com/reel/971115309353914"
}

print("=" * 80)
print("BÁO CÁO TOÀN DIỆN LINK ĐÃ ĐĂNG TRÊN 4 NỀN TẢNG (YOUTUBE, FB, IG, THREADS)")
print("=" * 80)

for bkey, bcfg in brands.items():
    if bkey not in [
        "cham_da_tiet_kiem", "dung_roi_moi_noi", "goc_tap_luyen",
        "noi_that_dung_that", "review_that_viec_that", "quan_ao_gia_hoi",
        "cham_cong_nghe", "yeu_da_hon_bo"
    ]:
        continue

    bname = bcfg.get("name", bkey)
    print(f"\n🏷️ THƯƠNG HIỆU: {bname.upper()}")

    # 1. YouTube
    yt_url = yt_map.get(bkey, "Chưa đăng")
    print(f"  🔴 YouTube Shorts: {yt_url}")

    # 2. Facebook
    fb_url = fb_map.get(bkey, "Chưa đăng")
    print(f"  🔷 Facebook Reels: {fb_url}")

    # 3. Instagram
    ig_cfg = bcfg.get("instagram", {})
    ig_id = ig_cfg.get("ig_user_id")
    ig_tok = ig_cfg.get("access_token")
    ig_url = "Chưa có bài mới"
    if ig_id and ig_tok:
        try:
            r = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}/media?fields=id,permalink,timestamp,media_type&limit=1&access_token={ig_tok}", timeout=10).json()
            if "data" in r and len(r["data"]) > 0:
                ig_url = r["data"][0].get("permalink", "N/A")
        except Exception as e:
            ig_url = f"Lỗi truy vấn: {e}"
    print(f"  📸 Instagram Reels: {ig_url}")

    # 4. Threads
    th_cfg = bcfg.get("threads", {})
    th_tok = th_cfg.get("access_token")
    th_url = "Chưa có bài mới / Không khả dụng"
    if th_tok:
        try:
            r = requests.get(f"https://graph.threads.net/v1.0/me/threads?fields=id,permalink,timestamp&limit=1&access_token={th_tok}", timeout=10).json()
            if "data" in r and len(r["data"]) > 0:
                th_url = r["data"][0].get("permalink", "N/A")
        except Exception as e:
            th_url = f"Lỗi truy vấn: {e}"
    elif not th_tok:
        th_url = "Chưa cấu hình Threads API Token"
    print(f"  🧵 Threads:        {th_url}")
