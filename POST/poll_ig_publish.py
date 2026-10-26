import requests
import json
import time
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

cid = "18111743662944270"
user_token = "EAAmD979AfWEBSvIUvuEFX2ZC39rsATmBPBsSRZC6zZAIjPYQKZAEURWEnQgTDgVWkZAZBPJ6tZAs87kpLwheOPtYk6VEHYjNtgX983Ou0XG8cU3S8Hw47bYdwo8otBOr82QXQFfWWsJ9tDZCfMOE4n6xKxiwZC9w87Chj49uTEdqTwv5qTJFAkwnwFxCzctRnRIGrgT8l4OwwXVuYXEYT8i2crgl6R8lxA7OoQ04l7Imz2MJ4rV7ZBoPijnZBJHQicXLfLN2a9ZBCZAIPGSOUP9tKfFaZA"

r = requests.get(
    "https://graph.facebook.com/v19.0/me/accounts",
    params={"access_token": user_token, "fields": "name,id,access_token,instagram_business_account"}
)
p = r.json()["data"][0]
ig = p["instagram_business_account"]["id"]
page_token = p["access_token"]

while True:
    st = requests.get(
        f"https://graph.facebook.com/v19.0/{cid}",
        params={"fields": "id,status_code,status", "access_token": page_token}
    ).json()
    print("Status:", st, flush=True)
    if st.get("status_code") == "FINISHED":
        pub = requests.post(
            f"https://graph.facebook.com/v19.0/{ig}/media_publish",
            data={"creation_id": cid, "access_token": page_token}
        ).json()
        print("Publish Res:", pub, flush=True)
        if "id" in pub:
            mid = pub["id"]
            c_res = requests.post(
                f"https://graph.facebook.com/v19.0/{mid}/comments",
                data={"message": "Link sắm dầu dưỡng La Mer chính hãng: https://s.shopee.vn/W6vCL7rpo", "access_token": page_token}
            ).json()
            print("Comment Res:", c_res, flush=True)
            p_res = requests.get(
                f"https://graph.facebook.com/v19.0/{mid}",
                params={"fields": "permalink", "access_token": page_token}
            ).json()
            print("Permalink:", p_res, flush=True)
        break
    elif st.get("status_code") == "ERROR":
        print("Error:", st, flush=True)
        break
    time.sleep(10)
