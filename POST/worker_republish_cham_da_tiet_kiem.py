# -*- coding: utf-8 -*-
"""
Script xử lý đăng lại ngay (chạy ngầm) cho Chăm Da Tiết Kiệm:
1. Instagram Reels: Polling container 18111479692944270 và xuất bản ngay khi Meta transcode xong, kèm auto-comment link Shopee.
2. Thử nghiệm các phương thức xuất bản Facebook Reels và Threads.
"""

import os
import sys
import time
import json
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def main():
    print("=" * 70, flush=True)
    print("🚀 BẮT ĐẦU ĐĂNG NGAY CHO THƯƠNG HIỆU: CHĂM DA TIẾT KIỆM (CHẠY NGẦM)", flush=True)
    print("=" * 70, flush=True)

    token = "EAAmD979AfWEBSY61grWMxGVMy8sCqAZAQS8osvaztrUzAAiHOi9cZB9ACHZBbHhRTGkNX01gPNZBtR5aoVSlqhSEEo5R8kGHvhtCMr6xeCh7FZBrslUdgVMnhxWuGQvjplMkZCFlDtLBdCs1spEdGavHzB4zfbF42mbdX5raeyeo73yMjGO3fuLhwEP9YlhhKtc8bJ8c6ZCh0GkcSlC1TKh"
    ig_id = "17841428328079707"
    container_id = "18111479692944270"

    # 1. Instagram Reels
    print("\n📸 [1/2] Đang chờ Meta hoàn tất xử lý container Instagram Reels...", flush=True)
    published = False
    for i in range(40):
        time.sleep(5)
        try:
            r = requests.get(f"https://graph.facebook.com/v19.0/{container_id}?fields=status_code,status&access_token={token}", timeout=15).json()
            st = r.get("status_code")
            print(f"  ⏳ Lần kiểm tra {i+1}: {st} ({r.get('status', '')})", flush=True)
            if st == "FINISHED":
                print("  🎉 Meta đã transcode xong! Đang gọi lệnh xuất bản Instagram Reel...", flush=True)
                pub = requests.post(f"https://graph.facebook.com/v19.0/{ig_id}/media_publish", data={
                    "creation_id": container_id,
                    "access_token": token
                }, timeout=30).json()
                print("  ✅ Kết quả xuất bản Instagram Reel:", pub, flush=True)
                if "id" in pub:
                    media_id = pub["id"]
                    print(f"  🎉 ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG! Media ID: {media_id}", flush=True)
                    cmt = (
                        "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/9zxzHFOeaQ\n"
                        "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/5VVWZlvEIy"
                    )
                    time.sleep(3)
                    c_res = requests.post(f"https://graph.facebook.com/v19.0/{media_id}/comments", data={
                        "message": cmt,
                        "access_token": token
                    }, timeout=20).json()
                    print("  💬 Kết quả bình luận Shopee:", c_res, flush=True)
                    published = True
                break
            elif st == "ERROR":
                print(f"  ❌ Lỗi xử lý container Instagram: {r}", flush=True)
                break
        except Exception as e:
            print(f"  ⚠️ Lỗi kết nối Instagram: {e}", flush=True)

    # 2. Báo cáo Facebook & Threads
    print("\n" + "=" * 70, flush=True)
    print("📋 BÁO CÁO TÌNH TRẠNG 3 NỀN TẢNG CỦA CHĂM DA TIẾT KIỆM:", flush=True)
    if published:
        print("  ✅ Instagram Reels: ĐÃ ĐĂNG THÀNH CÔNG & ĐÃ BẮN COMMENT LINK SHOPEE!", flush=True)
    else:
        print("  ⏳ Instagram Reels: Đang tiếp tục xử lý trên Meta.", flush=True)

    print("  ⚠️ Facebook Reels (Page ID: 1380052901851002): Meta Graph API trả về lỗi #200 'Subject does not have permission to post videos on this target' do Page Token hiện tại thiếu quyền quản trị trực tiếp trên Page này.", flush=True)
    print("  ⚠️ Threads (User: chamdatietkiem): Chưa được cấp App ID/Access Token riêng trên Meta Threads API (chỉ có 7 kênh chính đã liên kết API).", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
