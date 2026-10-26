# -*- coding: utf-8 -*-
"""
Script tự động đăng lại tất cả các video bị lỗi trên từng nền tảng tương ứng:
- YouTube Shorts: Trạm Công Nghệ, Yêu Da Hơn Bồ
- Threads Video: Trạm Công Nghệ, Yêu Da Hơn Bồ, Nói Thật Dùng Thật, Review Thật Việc Thật, Quần Áo Giá Hời, Tủ Đồ Mùa Mới
- Instagram Reels: Cả 10 kênh (áp dụng cơ chế cắt tự động 89s nếu >90s và multi-CDN Video URL)
"""

import os
import sys
import time
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "POST"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app import load_brands, parse_link_file, load_comment_templates, format_affiliate_comments, BRAND_DEFAULT_HASHTAGS
from uploaders.youtube_uploader import YouTubeShortsUploader
from uploaders.threads_uploader import ThreadsAPIUploader
from uploaders.instagram_uploader import InstagramReelsUploader

TASKS_TO_REUPLOAD = [
    {
        "brand_key": "cham_cong_nghe",
        "video_path": r"C:\Affiliate\Trạm Công Nghệ\video_việt_hóa\video chưa đăng\mic-tramcongnghe.mp4",
        "link_file": r"C:\Affiliate\Trạm Công Nghệ\Link customed\Instagram\mic thu âm không dây.csv",
        "title": "Micro thu âm không dây Moma Lark A2 giảm tiếng ồn AI cho vlogger #Shorts",
        "caption": "Micro thu âm không dây Moma Lark A2 giảm tiếng ồn AI cực đỉnh cho vlogger. Xem chi tiết và link mua sản phẩm dưới bình luận nhé!",
        "youtube_tags": ["MomaLarkA2", "MicroKhongDay", "GiamTiengOnAI", "MicChoVlogger", "ReviewCongNghe", "Shorts", "Trending"],
        "platforms": ["youtube", "threads", "instagram"]
    },
    {
        "brand_key": "yeu_da_hon_bo",
        "video_path": r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\video chưa đăng\10.mp4",
        "link_file": r"C:\Affiliate\Yêu Da Hơn Bồ\Link customed\Instagram\Tập 8.csv",
        "title": "Mặt nạ ngủ thuần chay Evoluderm bổ sung Collagen dưỡng da căng bóng #Shorts",
        "caption": "Mặt nạ ngủ thiên nhiên thuần chay Evoluderm bổ sung Collagen cho làn da căng mọng. Xem chi tiết và link mua sản phẩm dưới bình luận nhé!",
        "youtube_tags": ["MatNaColagen", "Evoluderm", "ChamSocDa", "DuongAm", "Skincare", "ReviewMyPham", "Shorts", "Trending"],
        "platforms": ["youtube", "threads", "instagram"]
    },
    {
        "brand_key": "noi_that_dung_that",
        "video_path": r"C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\video chưa đăng\kê điện thoại đa năng.mp4",
        "link_file": r"C:\Affiliate\Nói Thật Dùng Thật\Link customed\Instagram\kê điện thoại silicon.csv",
        "title": "Giá đỡ điện thoại silicon đa năng uốn cong tự do mọi hình dạng",
        "caption": "Giá đỡ điện thoại silicon đa năng có thể uốn cong tự do mọi góc độ. Xem chi tiết và link mua dưới bình luận!",
        "platforms": ["threads", "instagram"]
    },
    {
        "brand_key": "review_that_viec_that",
        "video_path": r"C:\Affiliate\Review Thật Việc Thật\video_việt_hóa\video chưa đăng\máy hút bụi.mp4",
        "link_file": r"C:\Affiliate\Review Thật Việc Thật\Link customed\Facebook\máy hút bụi đa năng.csv",
        "title": "Máy hút bụi cầm tay AUX không dây đa năng lực hút siêu mạnh",
        "caption": "Máy hút bụi cầm tay AUX không dây đa năng tiện lợi dọn dẹp nhà cửa. Xem chi tiết và link mua dưới bình luận!",
        "platforms": ["threads", "instagram"]
    },
    {
        "brand_key": "quan_ao_gia_hoi",
        "video_path": r"C:\Affiliate\Quần Áo Giá Hời\video_việt_hóa\video chưa đăng\6.mp4",
        "link_file": r"C:\Affiliate\Quần Áo Giá Hời\Link customed\Facebook\Tập 6.csv",
        "title": "Set đồ nữ áo hai dây phối giả áo trong tay ngắn quần ống suông",
        "caption": "Set đồ nữ áo hai dây phối giả áo trong tay ngắn quần ống suông cạp ren hack dáng cực xinh. Xem link mua dưới bình luận!",
        "platforms": ["threads", "instagram"]
    },
    {
        "brand_key": "tu_do_mua_moi",
        "video_path": r"C:\Affiliate\Tủ Đồ Mùa Mới\video_việt_hóa\video chưa đăng\9.mp4",
        "link_file": r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\Facebook\Tập 9.csv",
        "title": "Top mẫu giày dép nữ mùa hè cực xinh hack dáng phong cách Hàn Quốc",
        "caption": "Gợi ý những mẫu giày dép nữ xinh xắn mùa hè hack dáng. Xem link mua dưới bình luận!",
        "platforms": ["threads"]  # Instagram đã đăng thành công: https://www.instagram.com/reel/Dd9IpsXlWff/
    },
    {
        "brand_key": "setup_phong_xinh",
        "video_path": r"C:\Affiliate\Setup Phòng Xinh\Video_việt_hóa\video chưa đăng\7.mp4",
        "link_file": r"C:\Affiliate\Setup Phòng Xinh\Link customed\Instagram\Tập 7.csv",
        "title": "Bàn học và làm việc di động có bánh xe nâng hạ thông minh",
        "caption": "Bàn học và làm việc di động có bánh xe tiện lợi. Xem link mua dưới bình luận!",
        "platforms": ["instagram"]
    },
    {
        "brand_key": "goc_tap_luyen",
        "video_path": r"C:\Affiliate\Góc Tập Luyện\video_việt_hóa\video chưa đăng\8.mp4",
        "link_file": r"C:\Affiliate\Góc Tập Luyện\Link customed\Instagram\Tập 12.csv",
        "title": "Máy trượt tuyết máy tập cơ sàn chậu làm đẹp dáng chân tại nhà",
        "caption": "Thiết bị tập thể dục tại nhà máy trượt tuyết tập cơ sàn chậu. Xem link mua dưới bình luận!",
        "platforms": ["instagram"]
    },
    {
        "brand_key": "dung_roi_moi_noi",
        "video_path": r"C:\Affiliate\Dùng Rồi Mới Nói\Video_việt_hóa\video chưa đăng\găng tay thực phẩm.mp4",
        "link_file": r"C:\Affiliate\Dùng Rồi Mới Nói\Link customed\Instagram\Găng tay thực phẩm.csv",
        "title": "Găng tay thực phẩm cao su nitrile cao cấp dẻo dai tiện ích gia đình",
        "caption": "Găng tay cao su thực phẩm dẻo dai tiện ích làm bếp. Xem link mua dưới bình luận!",
        "platforms": ["instagram"]
    },
    {
        "brand_key": "cham_da_tiet_kiem",
        "video_path": r"C:\Affiliate\Chăm Da Tiết Kiệm\Video_việt_hóa\video chưa đăng\8.mp4",
        "link_file": r"C:\Affiliate\Chăm Da Tiết Kiệm\Link customed\Facebook\tinh chất whoo bichup.csv",
        "title": "Tinh chất tự sinh chống lão hóa The Whoo Bichup phục hồi da căng mọng",
        "caption": "Tinh chất phục hồi chống lão hóa da The Whoo Bichup. Xem link mua dưới bình luận!",
        "platforms": ["instagram"]
    }
]

def main():
    brands = load_brands()
    templates = load_comment_templates()
    results_summary = []

    print("=" * 80)
    print("🚀 BẮT ĐẦU TIẾN TRÌNH ĐĂNG LẠI CÁC VIDEO & NỀN TẢNG BỊ LỖI")
    print(f"Tổng số kênh cần xử lý: {len(TASKS_TO_REUPLOAD)}")
    print("=" * 80)

    for idx, item in enumerate(TASKS_TO_REUPLOAD, 1):
        b_key = item["brand_key"]
        b_cfg = brands.get(b_key, {})
        b_name = b_cfg.get("name", b_key)
        v_path = item["video_path"]
        link_file = item["link_file"]
        platforms = item["platforms"]
        title = item["title"]
        caption = item["caption"]

        print(f"\n[{idx}/{len(TASKS_TO_REUPLOAD)}] 🎯 XỬ LÝ KÊNH: {b_name} ({b_key})")
        print(f"  📁 Video: {os.path.basename(v_path)}")
        print(f"  🌐 Nền tảng cần đăng lại: {', '.join(platforms)}")

        # Đọc danh sách sản phẩm & chuẩn bị bình luận
        products = []
        if os.path.exists(link_file):
            try:
                products = parse_link_file(link_file)
                print(f"  🔗 Đã đọc {len(products)} sản phẩm từ {os.path.basename(link_file)}")
            except Exception as e:
                print(f"  ⚠️ Lỗi đọc file link: {e}")

        comments_list = format_affiliate_comments(products, b_key, templates)

        brand_res = {"brand": b_name, "video": os.path.basename(v_path)}

        # 1. YOUTUBE SHORTS
        if "youtube" in platforms:
            print(f"\n  ▶️ [1/3] Đang đăng lên YouTube Shorts: {b_name}...")
            try:
                yt_cfg = b_cfg.get("youtube", {})
                token_file = yt_cfg.get("token_file", "")
                full_token_path = os.path.join(r"c:\Affiliate\post1\POST", token_file)
                uploader_yt = YouTubeShortsUploader(token_file=full_token_path)
                
                tags = item.get("youtube_tags", ["Shorts", "Review", "Trending"])
                res_yt = uploader_yt.upload_short(
                    video_path=v_path,
                    title=title,
                    description=caption,
                    tags=tags,
                    comment_text=comments_list
                )
                if res_yt and res_yt.get("shorts_url"):
                    url = res_yt.get("shorts_url")
                    print(f"  ✅ YouTube Shorts THÀNH CÔNG: {url}")
                    brand_res["YouTube"] = url
                else:
                    print("  ❌ YouTube Shorts thất bại!")
                    brand_res["YouTube"] = "Thất bại"
            except Exception as e:
                print(f"  ❌ Lỗi YouTube: {e}")
                brand_res["YouTube"] = f"Lỗi: {e}"

        # 2. THREADS VIDEO
        if "threads" in platforms:
            print(f"\n  ▶️ [2/3] Đang đăng lên Threads Video: {b_name}...")
            try:
                th_cfg = b_cfg.get("threads", {})
                uploader_th = ThreadsAPIUploader(
                    threads_user_id=th_cfg.get("user_id", ""),
                    access_token=th_cfg.get("access_token", "")
                )
                res_th = uploader_th.upload_video_thread(
                    video_path=v_path,
                    caption=caption
                )
                if res_th and res_th.get("id"):
                    post_id = res_th.get("id")
                    permalink = res_th.get("permalink", f"https://www.threads.com/post/{post_id}")
                    print(f"  ✅ Threads Video THÀNH CÔNG: {permalink}")
                    brand_res["Threads"] = permalink

                    # Reply bình luận affiliate
                    print(f"  💬 Đang đăng {len(comments_list)} comment affiliate lên Threads...")
                    for c_idx, c in enumerate(comments_list, 1):
                        try:
                            time.sleep(2)
                            uploader_th.publish_reply(post_id=post_id, text=c)
                            print(f"    ✅ Threads reply {c_idx} thành công!")
                        except Exception as ce:
                            print(f"    ⚠️ Threads reply {c_idx} lỗi: {ce}")
                else:
                    print("  ❌ Threads Video thất bại!")
                    brand_res["Threads"] = "Thất bại"
            except Exception as e:
                print(f"  ❌ Lỗi Threads: {e}")
                brand_res["Threads"] = f"Lỗi: {e}"

        # 3. INSTAGRAM REELS
        if "instagram" in platforms:
            print(f"\n  ▶️ [3/3] Đang đăng lên Instagram Reels: {b_name}...")
            try:
                ig_cfg = b_cfg.get("instagram", {})
                uploader_ig = InstagramReelsUploader(
                    ig_user_id=ig_cfg.get("ig_user_id", ""),
                    access_token=ig_cfg.get("access_token", "")
                )
                res_ig = uploader_ig.upload_reel(
                    video_path=v_path,
                    caption=f"{title}\n\n{caption}",
                    comment_text=comments_list
                )
                if res_ig and res_ig.get("reel_url"):
                    url = res_ig.get("reel_url")
                    print(f"  ✅ Instagram Reels THÀNH CÔNG: {url}")
                    brand_res["Instagram"] = url
                elif res_ig and res_ig.get("media_id"):
                    url = f"https://www.instagram.com/reel/{res_ig.get('media_id')}"
                    print(f"  ✅ Instagram Reels THÀNH CÔNG: {url}")
                    brand_res["Instagram"] = url
                else:
                    print("  ❌ Instagram Reels thất bại!")
                    brand_res["Instagram"] = "Thất bại"
            except Exception as e:
                print(f"  ❌ Lỗi Instagram: {e}")
                brand_res["Instagram"] = f"Lỗi: {e}"

        results_summary.append(brand_res)
        print("-" * 60)
        time.sleep(3)

    print("\n" + "=" * 80)
    print("🎉 TỔNG KẾT TOÀN BỘ KẾT QUẢ ĐĂNG LẠI:")
    print("=" * 80)
    print(json.dumps(results_summary, indent=2, ensure_ascii=False))

    # Lưu kết quả ra file để xem lại
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reupload_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Kết quả đã được lưu tại: {out_file}")

if __name__ == "__main__":
    main()
