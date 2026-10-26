# -*- coding: utf-8 -*-
"""
Tự động đăng video 'bình đun nước mang đi du lịch.mp4' cho thương hiệu 'Dùng Rồi Mới Nói' lên:
1. Instagram Reels (+ 4 comments link Shopee Affiliate)
2. Threads (+ 4 comments link Shopee Affiliate)
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
        brand = json.load(f)["dung_roi_moi_noi"]

    video_url = "https://files.catbox.moe/7rw2ds.mp4"

    # ==========================================
    # 1. ĐĂNG INSTAGRAM REELS
    # ==========================================
    ig_id = brand["instagram"]["ig_user_id"]
    ig_tok = brand["instagram"]["access_token"]
    ig_caption = (
        "Đi du lịch, công tác hay để bàn làm việc mà có em máy đun nước tức thì 3 giây này thì chuẩn bài luôn cả nhà ơi! "
        "Bấm nút 3 giây là có nước sôi pha sữa, trà, cà phê chuẩn nhiệt độ 🔥\n\n"
        "Chi tiết từng mẫu máy đun nước mình ghim link bên dưới bình luận nhé 👇\n\n"
        "#reels #viral #fyp #dungroimoinoi #maydunnuoc #binhdunnuoc #tiendung"
    )
    ig_links = [
        "https://s.shopee.vn/2gBLJfHKWL",
        "https://s.shopee.vn/3B7buaFQVS",
        "https://s.shopee.vn/30oBiHG3qR",
        "https://s.shopee.vn/2BF4ikJEXI"
    ]
    templates = [
        "Link sản phẩm ở đây: ",
        "Link sản phẩm: ",
        "Link sản phẩm ở đây nha mọi người: ",
        "Link sản phẩm ở đây, mọi người ủng hộ nhé: "
    ]

    print("==================================================")
    print("📸 1. ĐĂNG INSTAGRAM REELS - DÙNG RỒI MỚI NÓI")
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
        "Đi du lịch hay làm việc mà có em máy đun nước tức thì 3 giây này siêu tiện lợi luôn! Nóng ngay sau 3s pha sữa, trà cực chuẩn ✨\n\n"
        "🛒 Sắm ngay máy đun nước mini chính hãng:\n"
        "👉 https://s.shopee.vn/20veWRJrsH\n\n"
        "#dungroimoinoi #maydunnuoc #skincare #thietbigiadung"
    )
    th_links = [
        "https://s.shopee.vn/20veWRJrsH",
        "https://s.shopee.vn/2Vrv7MHxrO",
        "https://s.shopee.vn/2LYUv3IbCN",
        "https://s.shopee.vn/1VzNvWLltE"
    ]

    print("\n==================================================")
    print("🧵 2. ĐĂNG THREADS - DÙNG RỒI MỚI NÓI")
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

    print("\n🎉🎉 TẤT CẢ ĐÃ HOÀN THÀNH CHO KÊNH DÙNG RỒI MỚI NÓI!")

if __name__ == "__main__":
    main()
