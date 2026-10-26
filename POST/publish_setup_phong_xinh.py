# -*- coding: utf-8 -*-
"""
Tự động đăng video Tập 1 lên 4 nền tảng cho kênh 'Setup Phòng Xinh':
1. YouTube Shorts: Đăng công khai + ghim & bình luận từng link Shopee riêng biệt
2. Threads: Đăng bài kèm video (qua URL) + bình luận từng link affiliate riêng biệt
3. Facebook Reels: Thử đăng Reel (kèm 1 link ở caption) + bình luận từng link
4. Instagram Reels: Thử đăng Reel + bình luận từng link
"""

import os
import sys
import time
import json
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from uploaders import (
    FacebookReelsUploader,
    YouTubeShortsUploader,
    InstagramReelsUploader,
    ThreadsAPIUploader
)

def parse_copy_nhanh(file_path):
    """Trích xuất danh sách (label, link) từ file copy nhanh."""
    items = []
    if not os.path.exists(file_path):
        return items
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    current_label = ""
    for line in lines:
        if line.startswith("==="):
            continue
        if line.startswith("👉") or line.startswith("🛒") or line.startswith("✨") or line.startswith("🔗"):
            current_label = line
        elif line.startswith("http://") or line.startswith("https://"):
            items.append(line)
            current_label = ""
    return items

def upload_to_catbox(file_path):
    print("Uploading video to Catbox for public CDN URL...")
    url = "https://catbox.moe/user/api.php"
    with open(file_path, 'rb') as f:
        files = {'fileToUpload': f}
        data = {'reqtype': 'fileupload'}
        r = requests.post(url, files=files, data=data, timeout=240)
        if r.status_code == 200 and r.text.startswith('http'):
            cdn_url = r.text.strip()
            print(f"Catbox CDN: {cdn_url}")
            return cdn_url
    print(f"Catbox failed: {r.status_code} - {r.text}")
    return None

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU ĐĂNG VIDEO TẬP 1 - SETUP PHÒNG XINH TRÊN 4 NỀN TẢNG")
    print("=" * 70)

    video_path = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\1.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy video: {video_path}")
        return

    # Load brand config
    brands_cfg_path = os.path.join(BASE_DIR, "config", "brands.json")
    with open(brands_cfg_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    brand_key = "setup_phong_xinh"
    brand_data = brands[brand_key]

    links_base = r"C:\Affiliate\Setup Phòng Xinh\Link customed"
    yt_links = parse_copy_nhanh(os.path.join(links_base, "YouTube", "Tập 1_copy_nhanh.txt"))
    fb_links = parse_copy_nhanh(os.path.join(links_base, "Facebook", "Tập 1_copy_nhanh.txt"))
    ig_links = parse_copy_nhanh(os.path.join(links_base, "Instagram", "Tập 1_copy_nhanh.txt"))
    th_links = parse_copy_nhanh(os.path.join(links_base, "Threads", "Tập 1_copy_nhanh.txt"))

    print(f"📊 Đã tải links: YT={len(yt_links)}, FB={len(fb_links)}, IG={len(ig_links)}, TH={len(th_links)}")

    results = {}

    # ----------------------------------------------------
    # 1. YOUTUBE SHORTS
    # ----------------------------------------------------
    # YouTube Shorts đã đăng thành công trước đó
    results["youtube"] = "https://youtube.com/shorts/f_jggDr7ojA"
    print(f"\n🔴 [1/4] YOUTUBE SHORTS ĐÃ ĐĂNG: {results['youtube']}")

    # ----------------------------------------------------
    # 2. THREADS
    # ----------------------------------------------------
    print("\n🧵 [2/4] ĐĂNG LÊN THREADS...")
    th_caption = (
        "Boss nhà bạn hay nghịch ngợm lục tủ? Thử ngay chốt khóa an toàn siêu tiện lợi này nha! "
        "Vừa gọn đẹp cho góc phòng xinh vừa bảo vệ các bé tối đa 🐾✨\n\n"
        "Link từng món mình để ở các comment bên dưới nhé 👇\n\n"
        "#setupphongxinh #decorphong #meo #thucung #giadungtienich"
    )
    try:
        th_cfg = brand_data["threads"]
        th_uploader = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
        th_video = r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\1_threads.mp4"
        if not os.path.exists(th_video):
            th_video = video_path
        th_res = th_uploader.upload_video_thread(
            video_path=th_video,
            caption=th_caption
        )
        if th_res and "id" in th_res:
            post_id = th_res["id"]
            th_url = th_res.get("permalink", f"https://www.threads.net/@setupphongxinh/post/{post_id}")
            results["threads"] = th_url
            print(f"✅ Threads post thành công: {th_url}")
            
            # Comment từng link riêng biệt (reply to post_id)
            print(f"💬 Bắt đầu đăng {len(th_links)} comment link lên Threads...")
            for idx, link_item in enumerate(th_links):
                try:
                    reply_text = f"Món {idx + 1}: {link_item}"
                    th_uploader.publish_reply(post_id=post_id, text=reply_text)
                    print(f"   -> Đã comment link {idx + 1}/{len(th_links)}")
                    time.sleep(1.5)
                except Exception as err:
                    print(f"   -> Lỗi comment link {idx + 1}: {err}")
        else:
            results["threads"] = f"Lỗi: {th_res}"
    except Exception as e:
        results["threads"] = f"Lỗi ngoại lệ: {e}"
        print(f"❌ Threads error: {e}")

    # ----------------------------------------------------
    # 3. FACEBOOK REELS
    # ----------------------------------------------------
    print("\n🔵 [3/4] ĐĂNG LÊN FACEBOOK REELS...")
    main_fb_link = "https://s.shopee.vn/50ZJQNuvif"
    fb_title = "Dây Chốt Khóa Đa Năng Cực Tiện Cho Phòng Xinh"
    fb_caption = (
        f"Góc phòng xinh gọn gàng, an toàn tuyệt đối với chốt khóa tủ lạnh & ngăn kéo đa năng! "
        f"Ai cần mua chốt khóa chính hãng bấm ngay link này nhé 👉 {main_fb_link}\n\n"
        f"Trọn bộ phụ kiện và đồ chơi cho mèo cưng mình ghim từng link bên dưới bình luận nha 👇\n\n"
        f"#SetupPhongXinh #DecorPhong #GiaDungThongMinh #ThuCung #MeoYeu"
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
            results["facebook"] = "Thất bại (Token Meta Graph API có thể đã hết hạn)"
    except Exception as e:
        results["facebook"] = f"Lỗi: {e}"
        print(f"❌ Facebook error: {e}")

    # ----------------------------------------------------
    # 4. INSTAGRAM REELS
    # ----------------------------------------------------
    print("\n🟣 [4/4] ĐĂNG LÊN INSTAGRAM REELS...")
    ig_caption = (
        "Góc setup phòng xinh và giải pháp an toàn tuyệt đối cho bé yêu và thú cưng! "
        "Chi tiết các món phụ kiện xinh xắn mình ghim dưới comment nhé 👇✨\n\n"
        "#setupphongxinh #decor #roomdecor #homedecor #cats #thucung #viral"
    )
    ig_comment_payload = "\n".join(ig_links) if ig_links else ""

    try:
        ig_cfg = brand_data["instagram"]
        ig_uploader = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_cfg["access_token"])
        ig_res = ig_uploader.upload_reel(
            video_path=video_path,
            caption=ig_caption,
            comment_text=ig_comment_payload
        )
        if ig_res:
            results["instagram"] = ig_res.get("reel_url")
            print(f"✅ Instagram Reels thành công: {results['instagram']}")
        else:
            results["instagram"] = "Thất bại (Token Meta Graph API có thể đã hết hạn)"
    except Exception as e:
        results["instagram"] = f"Lỗi: {e}"
        print(f"❌ Instagram error: {e}")

    # ----------------------------------------------------
    # KẾT QUẢ TỔNG HỢP
    # ----------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 BÁO CÁO KẾT QUẢ ĐĂNG BÀI - SETUP PHÒNG XINH (TẬP 1):")
    for k, v in results.items():
        print(f"- {k.upper()}: {v}")
    print("=" * 70)

    # Lưu kết quả ra file json
    out_file = os.path.join(BASE_DIR, "config", "setup_phong_xinh_ep1_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
