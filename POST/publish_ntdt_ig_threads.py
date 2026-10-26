# -*- coding: utf-8 -*-
"""
Tự động đăng video 'cạo lông mèo.mp4' cho thương hiệu 'Nói Thật Dùng Thật' lên:
1. Instagram Reels (+ 8 comments link Shopee Affiliate)
2. Threads (+ 8 comments link Shopee Affiliate)
"""

import os
import sys
import json
import time
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"

def main():
    cfg_path = os.path.join(POST_DIR, "config", "brands.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        brand = json.load(f)["noi_that_dung_that"]

    video_url = "https://files.catbox.moe/oq7krt.mp4"

    templates = [
        "Link sản phẩm ở đây: ",
        "Link sản phẩm: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: ",
        "Link xem và mua hàng ngay tại đây nè: ",
        "Link sản phẩm ở đây cho ai cần nha: ",
        "Mọi người xem chi tiết và đặt hàng tại link này nhé: ",
        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: "
    ]

    # ==========================================
    # 1. ĐĂNG INSTAGRAM REELS
    # ==========================================
    ig_id = brand["instagram"]["ig_user_id"]
    ig_tok = brand["instagram"]["access_token"]
    ig_caption = (
        "Chiếc lược chải lông cạo lông mèo thần thánh lấy sạch lông rụng mà "
        "boss cực kỳ mê luôn nha cả nhà! Giúp nhà cửa luôn sạch sẽ thơm tho ✨\n\n"
        "Link sắm các loại lược chải lông chính hãng mình ghim ở bình luận nhé 👇\n\n"
        "#reels #viral #fyp #noithatdungthat #luocchailongmeo #thucung #chomeo"
    )
    ig_links = [
        "https://s.shopee.vn/6L4c3DKcLg",
        "https://s.shopee.vn/5q8LSIMWMf",
        "https://s.shopee.vn/9zxuPx6euY",
        "https://s.shopee.vn/9V1dp28YvX",
        "https://s.shopee.vn/8KpgQtD0IO",
        "https://s.shopee.vn/2LYTHrZqTJ",
        "https://s.shopee.vn/1VzMIKd1AE",
        "https://s.shopee.vn/gQFIngBr9"
    ]

    print("==================================================")
    print("📸 1. ĐĂNG INSTAGRAM REELS - NÓI THẬT DÙNG THẬT")
    print("==================================================")
    ig_create = requests.post(
        f"https://graph.facebook.com/v19.0/{ig_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": ig_caption,
            "access_token": ig_tok
        },
        timeout=30
    ).json()
    print("Container ID:", ig_create)

    if "id" in ig_create:
        cid = ig_create["id"]
        for i in range(40):
            time.sleep(5)
            st = requests.get(
                f"https://graph.facebook.com/v19.0/{cid}",
                params={"fields": "status_code,status", "access_token": ig_tok},
                timeout=20
            ).json()
            print(f"  Trạng thái IG ({i+1}/40): {st.get('status_code')}")
            if st.get("status_code") == "FINISHED":
                pub = requests.post(
                    f"https://graph.facebook.com/v19.0/{ig_id}/media_publish",
                    data={"creation_id": cid, "access_token": ig_tok},
                    timeout=30
                ).json()
                print(f"  🎉 ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG! ID: {pub.get('id')}")

                mid = pub.get("id")
                if mid:
                    for idx, l in enumerate(ig_links):
                        time.sleep(2)
                        c_txt = f"{templates[idx % len(templates)]}{l}"
                        c_res = requests.post(
                            f"https://graph.facebook.com/v19.0/{mid}/comments",
                            data={"message": c_txt, "access_token": ig_tok},
                            timeout=20
                        ).json()
                        print(f"    ✅ Đã thêm comment IG {idx+1}: {c_res.get('id')}")
                break
            elif st.get("status_code") == "ERROR":
                print(f"  ❌ Lỗi xử lý IG: {st}")
                break

    # ==========================================
    # 2. ĐĂNG THREADS
    # ==========================================
    th_id = brand["threads"]["user_id"]
    th_tok = brand["threads"]["access_token"]
    th_caption = (
        "Chiếc lược chải lông cạo lông mèo thần thánh lấy sạch lông rụng cực đỉnh! Giúp boss dễ chịu mà nhà cửa không lo dính lông rụng ✨\n\n"
        "🛒 Sắm ngay lược chải lông mèo chính hãng:\n"
        "👉 https://s.shopee.vn/6VO2FWJz0j\n\n"
        "#noithatdungthat #luocchailongmeo #thucung"
    )
    th_links = [
        "https://s.shopee.vn/6VO2FWJz0j",
        "https://s.shopee.vn/5LC4rNOQNa",
        "https://s.shopee.vn/AAHKcG61Zb",
        "https://s.shopee.vn/905NE7ASwS",
        "https://s.shopee.vn/8V96dCCMxR",
        "https://s.shopee.vn/2BF35YaToI",
        "https://s.shopee.vn/1Lfw61deVD",
        "https://s.shopee.vn/W6p6UgpC8"
    ]

    print("\n==================================================")
    print("🧵 2. ĐĂNG THREADS - NÓI THẬT DÙNG THẬT")
    print("==================================================")
    th_create = requests.post(
        f"https://graph.threads.net/v1.0/{th_id}/threads",
        data={
            "media_type": "VIDEO",
            "video_url": video_url,
            "text": th_caption,
            "access_token": th_tok
        },
        timeout=30
    ).json()
    print("Container ID:", th_create)

    if "id" in th_create:
        tcid = th_create["id"]
        for i in range(40):
            time.sleep(5)
            st = requests.get(
                f"https://graph.threads.net/v1.0/{tcid}",
                params={"fields": "status,error_message", "access_token": th_tok},
                timeout=20
            ).json()
            print(f"  Trạng thái Threads ({i+1}/40): {st.get('status')}")
            if st.get("status") == "FINISHED":
                pub = requests.post(
                    f"https://graph.threads.net/v1.0/{th_id}/threads_publish",
                    data={"creation_id": tcid, "access_token": th_tok},
                    timeout=30
                ).json()
                print(f"  🎉 ĐÃ ĐĂNG THREADS THÀNH CÔNG! ID: {pub.get('id')}")

                tid = pub.get("id")
                if tid:
                    for idx, l in enumerate(th_links):
                        time.sleep(2)
                        c_txt = f"{templates[idx % len(templates)]}{l}"
                        c_create = requests.post(
                            f"https://graph.threads.net/v1.0/{th_id}/threads",
                            data={
                                "media_type": "TEXT",
                                "text": c_txt,
                                "reply_to_id": tid,
                                "access_token": th_tok
                            },
                            timeout=20
                        ).json()
                        if "id" in c_create:
                            c_pub = requests.post(
                                f"https://graph.threads.net/v1.0/{th_id}/threads_publish",
                                data={"creation_id": c_create["id"], "access_token": th_tok},
                                timeout=20
                            ).json()
                            print(f"    ✅ Đã thêm comment Threads {idx+1}: {c_pub.get('id')}")
                break
            elif st.get("status") == "ERROR":
                print(f"  ❌ Lỗi xử lý Threads: {st}")
                break

    print("\n🎉🎉 TẤT CẢ ĐÃ HOÀN THÀNH CHO KÊNH NÓI THẬT DÙNG THẬT!")

if __name__ == "__main__":
    main()
