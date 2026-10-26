import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user_token = "EAAmD979AfWEBSmFmKELRPw79yaXT1ULIVEXeJiIFfAC84gw0zWZA7dRWcdakUHxzTMMgGz7vy7v7QbvtuRA2EUQ85Oa6gYhurxBpvWM0BZBZC30UhDqZA1g0ZCZAtextNzMfEy78koxG7lYAMnHNYE2hIMSJwhCgGYMfErdSeTlu5DGqrREAfuqKFZAZAZAlvSJDEOsbpEKdZB5oL9O2XvwwdRgdAzZBSjRTejvyNT1QDYkIGyQZAULZBwtgbfyDxSZC3nqVyU8WHPl0rZA7ik62R9jDa3p"

url = "https://graph.facebook.com/v19.0/me/accounts"
params = {"access_token": user_token, "limit": 100}

res = requests.get(url, params=params).json()

if "error" in res:
    print("LOI lay Page Token tu User Token:")
    print(json.dumps(res["error"], indent=2, ensure_ascii=False))
else:
    pages = res.get("data", [])
    print(f"User Token hop le! Lay duoc {len(pages)} Page Tokens:")
    page_map = {}
    for p in pages:
        p_name = p.get("name")
        p_id = p.get("id")
        p_token = p.get("access_token")
        page_map[p_id] = {"name": p_name, "token": p_token}
        print(f"- Page: {p_name} | ID: {p_id} | Token: {p_token[:25]}...")

    # Cap nhat vao brands.json
    brands_path = r"c:\Affiliate\post1\POST\config\brands.json"
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    updated_count = 0
    for b_key, b_info in brands.items():
        fb_info = b_info.get("facebook", {})
        ig_info = b_info.get("instagram", {})
        pid = str(fb_info.get("page_id", "")).strip()

        if pid in page_map:
            new_p_token = page_map[pid]["token"]
            fb_info["access_token"] = new_p_token
            if ig_info:
                ig_info["access_token"] = new_p_token
            updated_count += 1
            print(f"  -> Da cap nhat token cho brand: {b_info.get('name')} (Page ID: {pid})")

    with open(brands_path, "w", encoding="utf-8") as f:
        json.dump(brands, f, indent=4, ensure_ascii=False)

    print(f"\nDa cap nhat thanh cong {updated_count}/10 kenh trong brands.json!")
