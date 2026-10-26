# -*- coding: utf-8 -*-
import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user_token = "EAAmD979AfWEBSjJaqebuk0jrjtkH7yxYYNTSZCPxMl9BHGv8aWJ6em3yyPotajzHZBba7jxZBfqWgiGc8Fh2FkkN4U0O6JIFAHdvKBWxa9tGObqMFc4ZAgI9jdpw6hKWLCZA0mGZAQHpCxBZBprZCY1cBsZCJZBUIeUz4m59Cq86jirC1RG5CWESksuJB1iXZC0jnDZAgw75UqRIpeuP7ArqwnN3V0jilk5IY4mrgfgQdoS9FcLxOjWRWXFWk1hVAC2aTbPXVONeCzR3lmtxd05aizxf"

url = f"https://graph.facebook.com/v19.0/me/accounts?limit=100&access_token={user_token}"
res = requests.get(url).json()

if "data" in res:
    pages = res["data"]
    print(f"✅ Lấy thành công {len(pages)} Facebook Pages:")
    for p in pages:
        print(f" - {p.get('name')} | Page ID: {p.get('id')}")

    cfg_path = r"C:\Affiliate\post1\POST\config\brands.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    updated_count = 0
    for p in pages:
        pid = str(p.get("id"))
        ptok = p.get("access_token")
        for bkey, bval in brands.items():
            if "facebook" in bval and str(bval["facebook"].get("page_id")) == pid:
                bval["facebook"]["access_token"] = ptok
                if "instagram" in bval:
                    bval["instagram"]["access_token"] = ptok
                print(f"  ✨ Đã cập nhật token cho thương hiệu: {bval['name']}")
                updated_count += 1

    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(brands, f, ensure_ascii=False, indent=4)
    print(f"💾 Đã lưu thành công {updated_count} tokens vào brands.json!")
else:
    print("❌ Lỗi lấy accounts:", res)
