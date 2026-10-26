import json, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

targets = ["cham_da_tiet_kiem", "quan_ao_gia_hoi", "yeu_da_hon_bo"]

for bkey in targets:
    b = brands[bkey]
    pid = b["facebook"]["page_id"]
    tok = b["facebook"]["access_token"]
    print(f"\n--- Checking Facebook permission for {b['name']} (Page ID: {pid}) ---")
    
    # 1. Check me/page info
    r = requests.get(f"https://graph.facebook.com/v19.0/{pid}?fields=id,name&access_token={tok}").json()
    print("Page info:", r)

    # 2. Check video_reels init session (dry test start)
    init_res = requests.post(
        f"https://graph.facebook.com/v19.0/{pid}/video_reels",
        data={"upload_phase": "start", "access_token": tok}
    ).json()
    print("Video reels start test:", init_res)
