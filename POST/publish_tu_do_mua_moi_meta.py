# -*- coding: utf-8 -*-
"""
Đăng video 2.mp4 lên Facebook Reels và Instagram Reels cho thương hiệu Tủ Đồ Mùa Mới
- Kèm link affiliate chính trong caption Facebook
- Bình luận tách riêng biệt từng link cho cả Facebook và Instagram
"""

import os
import sys
import json
import time
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import FacebookReelsUploader, InstagramReelsUploader

def parse_copy_nhanh(file_path):
    items = []
    if not os.path.exists(file_path):
        return items
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]
    for line in lines:
        if line.startswith("http://") or line.startswith("https://"):
            items.append(line)
    return items

def upload_catbox(file_path):
    print("Uploading to Catbox CDN for Instagram...")
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=180)
        if r.status_code == 200 and r.text.startswith("http"):
            print(f"Catbox CDN: {r.text.strip()}")
            return r.text.strip()
    except Exception as e:
        print(f"Catbox error: {e}")
    return None

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU ĐĂNG FACEBOOK & INSTAGRAM REELS - TỦ ĐỒ MÙA MỚI (TẬP 1, 2.mp4)")
    print("=" * 70)

    video_path = r"C:\Affiliate\Tủ Đồ Mùa Mới\video_việt_hóa\2.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "tu_do_mua_moi"
    brand_data = brands[brand_key]

    links_base = r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed"
    fb_links = parse_copy_nhanh(os.path.join(links_base, "Facebook", "Tập 1_copy_nhanh.txt"))
    ig_links = parse_copy_nhanh(os.path.join(links_base, "Instagram", "Tập 1_copy_nhanh.txt"))

    print(f"📊 Đã tải links: FB={len(fb_links)}, IG={len(ig_links)}")

    results = {}

    # 1. FACEBOOK REELS
    print("\n🔵 [1/2] ĐĂNG LÊN FACEBOOK REELS...")
    main_fb_link = "https://s.shopee.vn/1BMXaR9EVX"
    fb_title = "Outfit Đi Chơi Cực Xinh Phối Cùng Giày Sneaker Đức"
    fb_caption = (
        f"Gợi ý outfit mùa mới vừa năng động vừa tôn dáng cho các nàng diện đi chơi, đi dạo phố! "
        f"Đôi sneaker CAMEL CROWN phối đồ siêu đỉnh mình để link ở đây nha 👉 {main_fb_link}\n\n"
        f"Toàn bộ áo cardigan và phụ kiện phối trong clip mình ghim chi tiết từng link bên dưới bình luận nhé 👇\n\n"
        f"#TuDoMuaMoi #OutfitDep #PhoiDoXinh #Sneaker #ShopeeHaul #ThoiTrangNu"
    )
    fb_comment_payload = "\n".join(fb_links) if fb_links else ""

    try:
        fb_cfg = brand_data["facebook"]
        fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
        fb_res = fb_uploader.upload_reel(
            video_path=video_path,
            title=fb_title,
            caption=fb_caption,
            comment_text=fb_comment_payload
        )
        if fb_res:
            results["facebook"] = fb_res.get("reel_url")
            print(f"✅ Facebook Reels thành công: {results['facebook']}")
        else:
            results["facebook"] = "Thất bại khi upload Facebook"
    except Exception as e:
        results["facebook"] = f"Lỗi: {e}"
        print(f"❌ Facebook error: {e}")

    # 2. INSTAGRAM REELS
    print("\n🟣 [2/2] ĐĂNG LÊN INSTAGRAM REELS...")
    ig_caption = (
        "Gợi ý outfit đi chơi cực xinh mùa mới! Tôn dáng, trẻ trung mà cực dễ phối đồ ✨ "
        "Chi tiết link giày và từng món đồ mình ghim đầy đủ dưới bình luận nha 👇\n\n"
        "#tudomuamoi #outfitoftheday #fashion #ootd #style #viral #reels"
    )

    try:
        ig_cfg = brand_data["instagram"]
        token = ig_cfg["access_token"]
        ig_id = ig_cfg["ig_user_id"]

        cdn_url = upload_catbox(video_path)
        if cdn_url:
            print(f"Tạo container Reel Instagram với CDN: {cdn_url}")
            c_res = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media", data={
                "media_type": "REELS",
                "video_url": cdn_url,
                "caption": ig_caption,
                "access_token": token
            }, timeout=30).json()

            if "id" in c_res:
                cid = c_res["id"]
                for i in range(40):
                    time.sleep(5)
                    st = requests.get(f"https://graph.facebook.com/v19.0/{cid}", params={"fields": "status_code,status", "access_token": token}).json()
                    status = st.get("status_code")
                    print(f"  ⏳ Trạng thái ({i+1}/40): {status}")
                    if status == "FINISHED":
                        print("Video sẵn sàng! Xuất bản lên Instagram...")
                        pub_res = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media_publish", data={"creation_id": cid, "access_token": token}).json()
                        if "id" in pub_res:
                            media_id = pub_res["id"]
                            media_info = requests.get(f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink&access_token={token}").json()
                            permalink = media_info.get("permalink", f"https://www.instagram.com/reel/{media_id}")
                            results["instagram"] = permalink
                            print(f"✅ Instagram Reels thành công: {permalink}")

                            # Bình luận từng link
                            print(f"💬 Bắt đầu đăng {len(ig_links)} bình luận affiliate lên Instagram...")
                            for idx, link in enumerate(ig_links):
                                cm_res = requests.post(
                                    f"https://graph.facebook.com/v19.0/{media_id}/comments",
                                    data={"message": f"Món {idx+1}: {link}", "access_token": token}
                                ).json()
                                print(f"   -> Đã comment món {idx+1}/{len(ig_links)}: {cm_res.get('id')}")
                                time.sleep(1.5)
                        else:
                            results["instagram"] = f"Lỗi publish: {pub_res}"
                        break
                    elif status == "ERROR":
                        results["instagram"] = f"Lỗi xử lý video: {st}"
                        break
            else:
                results["instagram"] = f"Lỗi tạo container: {c_res}"
        else:
            results["instagram"] = "Lỗi upload CDN Catbox"
    except Exception as e:
        results["instagram"] = f"Lỗi: {e}"
        print(f"❌ Instagram error: {e}")

    print("\n" + "=" * 70)
    print("📊 BÁO CÁO KẾT QUẢ TỦ ĐỒ MÙA MỚI:")
    for k, v in results.items():
        print(f"- {k.upper()}: {v}")
    print("=" * 70)

if __name__ == "__main__":
    main()
