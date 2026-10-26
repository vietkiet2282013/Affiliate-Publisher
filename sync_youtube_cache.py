import sys
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(r"c:\Affiliate\post1")
sys.stdout.reconfigure(encoding="utf-8")

from fetch_analytics import (
    fetch_youtube_videos,
    analyze_cross_platform_videos,
    save_cached_analytics,
    load_cached_analytics,
    _load_optimized_videos,
    ANALYTICS_CACHE_FILE
)

def sync_youtube_cache_all():
    brands_path = r"c:\Affiliate\post1\POST\config\brands.json"
    with open(brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)

    print(f"🔄 Bắt đầu quét làm mới dữ liệu YouTube trực tiếp từ API cho toàn bộ {len(brands)} kênh...", flush=True)
    t0 = time.time()

    # Load existing cache to preserve other platforms (Facebook, Instagram, Threads)
    cached_obj = load_cached_analytics()
    if not cached_obj or not isinstance(cached_obj, dict) or "data" not in cached_obj:
        print("⚠️ Cache hiện tại trống hoặc hỏng, tạo mới dict...")
        cache_data = {}
    else:
        cache_data = cached_obj["data"]

    # ThreadPool fetch for YouTube
    youtube_results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_youtube_videos, b_k, b_c): b_k
            for b_k, b_c in brands.items()
        }
        for fut in as_completed(futures):
            b_k = futures[fut]
            try:
                res = fut.result()
                youtube_results[b_k] = res
                vids = res.get("videos", [])
                top = vids[0] if vids else {}
                print(f"✅ [{b_k}] Lấy thành công {len(vids)} video YouTube | Top 1: {top.get('id')} ({top.get('published_at')}) Views={top.get('views')}", flush=True)
            except Exception as e:
                print(f"❌ [{b_k}] Lỗi khi quét YouTube: {e}", flush=True)

    # Merge YouTube results into cache_data
    for b_k, b_c in brands.items():
        if b_k not in cache_data:
            cache_data[b_k] = {
                "name": b_c.get("name", b_k),
                "folder": b_c.get("folder", ""),
                "platforms": {},
                "inbox": {"total_unread": 0, "messages": []}
            }
        
        if b_k in youtube_results:
            cache_data[b_k]["platforms"]["youtube"] = youtube_results[b_k]
        
        # Cập nhật đối soát đăng chéo cross_platform_sync
        try:
            cache_data[b_k]["cross_platform_sync"] = analyze_cross_platform_videos(cache_data[b_k].get("platforms", {}))
        except Exception as e_c:
            print(f"⚠️ Lỗi cross_platform_sync ({b_k}): {e_c}")

    elapsed = time.time() - t0
    save_cached_analytics(cache_data, duration_sec=elapsed)
    print(f"\n🎉 ĐÃ CẬP NHẬT THÀNH CÔNG CACHE CHO TOÀN BỘ KÊNH TRONG {elapsed:.1f} GIÂY!", flush=True)

if __name__ == "__main__":
    sync_youtube_cache_all()
