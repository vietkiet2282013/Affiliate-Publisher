# -*- coding: utf-8 -*-
"""
Chỉ đăng Instagram Reels cho thương hiệu 'Dùng Rồi Mới Nói'
Video: máy đun nước tức thời 3 giây (bình đun nước mang đi du lịch.mp4)
Kèm 4 bình luận link Shopee Affiliate lấy từ:
C:\Affiliate\Dùng Rồi Mới Nói\Link customed\Instagram\máy đun nước tức thời 3 giây.xlsx
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
    print("📸 ĐĂNG INSTAGRAM REELS - DÙNG RỒI MỚI NÓI")
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

    print("\n🎉 HOÀN THÀNH ĐĂNG INSTAGRAM CHO DÙNG RỒI MỚI NÓI!")

if __name__ == "__main__":
    main()
