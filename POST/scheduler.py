import os
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import time
import json
import re
import datetime
import requests
from typing import Dict, Any, List, Optional

from uploaders import (
    FacebookReelsUploader,
    InstagramReelsUploader,
    YouTubeShortsUploader,
    TikTokPlaywrightUploader,
    TikTokAPIUploader,
    ThreadsAPIUploader
)

import threading

QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/schedule_queue.json")
_queue_file_lock = threading.Lock()

def load_queue() -> List[Dict[str, Any]]:
    with _queue_file_lock:
        if not os.path.exists(QUEUE_FILE):
            return []
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

def save_queue(queue_data: List[Dict[str, Any]]):
    with _queue_file_lock:
        os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=4, ensure_ascii=False)

def add_schedule_task(
    brand_key: str,
    video_path: str,
    title: str,
    caption: str,
    comment: str,
    platforms: List[str],
    scheduled_datetime: str,  # Định dạng: "YYYY-MM-DD HH:MM" hoặc "HH:MM"
    product_keyword: str = "Kéo cắt gà"
) -> Dict[str, Any]:
    """
    Thêm một tác vụ đăng video vào hàng đợi hẹn giờ
    """
    now = datetime.datetime.now()
    try:
        if len(scheduled_datetime.strip()) <= 5 and ":" in scheduled_datetime:
            # Chỉ có giờ: "19:30"
            hour, minute = map(int, scheduled_datetime.strip().split(":"))
            target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)
        else:
            # Có cả ngày giờ: "2026-08-23 19:30"
            target_dt = datetime.datetime.strptime(scheduled_datetime.strip(), "%Y-%m-%d %H:%M")
    except Exception as e:
        print(f"❌ Định dạng thời gian hẹn không hợp lệ: {scheduled_datetime} ({e})")
        return {}

    timestamp = int(target_dt.timestamp())
    task_id = f"task_{int(time.time())}"
    task = {
        "id": task_id,
        "brand_key": brand_key,
        "video_path": os.path.abspath(video_path),
        "title": title,
        "caption": caption,
        "comment": comment,
        "platforms": platforms,
        "scheduled_time_str": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "scheduled_timestamp": timestamp,
        "product_keyword": product_keyword,
        "status": "PENDING"
    }

    queue = load_queue()
    queue.append(task)
    save_queue(queue)

    print("\n" + "="*60)
    print(f"⏰ ĐÃ LÊN LỊCH THÀNH CÔNG CHO VIDEO!")
    print(f"📅 Thời gian xuất bản: {task['scheduled_time_str']}")
    print(f"📁 Video: {os.path.basename(video_path)}")
    print(f"🌐 Nền tảng: {', '.join(platforms)}")
    print("="*60)
    return task

FB_APP_ID = "2678374879231329"
FB_APP_SECRET = "975ca71ab78e1676c5dd4fc356ce337f"

def refresh_meta_token_if_needed(brand_data: dict, brand_key: str, platform: str, brands_path: str) -> str:
    """Kiểm tra và tự động gia hạn Meta token (Instagram/Facebook) trước khi upload hẹn giờ."""
    try:
        import requests
        cur_token = brand_data.get(platform, {}).get("access_token", "")
        if not cur_token:
            return cur_token
        # Kiểm tra token
        debug_url = "https://graph.facebook.com/v19.0/debug_token"
        r_debug = requests.get(debug_url, params={"input_token": cur_token, "access_token": cur_token}, timeout=10)
        token_valid = True
        expires_at = 0
        if r_debug.status_code == 200:
            dbg_data = r_debug.json().get("data", {})
            token_valid = dbg_data.get("is_valid", False)
            expires_at = dbg_data.get("expires_at", 0)

        now_ts = int(time.time())
        # Nếu token không hợp lệ hoặc sắp hết hạn trong 24h
        if not token_valid or (expires_at and expires_at > 0 and (expires_at - now_ts < 86400)):
            print(f"🔄 [Scheduler] Token {platform} cho '{brand_key}' sắp/đã hết hạn. Đang tự động gia hạn...", flush=True)
            resp_ex = requests.get(
                "https://graph.facebook.com/v21.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": FB_APP_ID,
                    "client_secret": FB_APP_SECRET,
                    "fb_exchange_token": cur_token,
                },
                timeout=20
            )
            ex_data = resp_ex.json()
            new_tok = ex_data.get("access_token")
            if new_tok:
                # Cập nhật brands.json
                with open(brands_path, "r", encoding="utf-8") as f:
                    all_b = json.load(f)
                all_b[brand_key][platform]["access_token"] = new_tok
                if platform == "facebook" and "instagram" in all_b[brand_key]:
                    all_b[brand_key]["instagram"]["access_token"] = new_tok
                with open(brands_path, "w", encoding="utf-8") as f:
                    json.dump(all_b, f, indent=4, ensure_ascii=False)
                brand_data[platform]["access_token"] = new_tok
                print(f"  ✅ [Scheduler] Đã gia hạn token Meta thành công!", flush=True)
                return new_tok
    except Exception as e:
        print(f"  ⚠️ [Scheduler] Không thể refresh token Meta: {e}", flush=True)
    return brand_data.get(platform, {}).get("access_token", "")

def run_scheduled_worker():
    """
    Tiến trình chạy ngầm quét hàng đợi và xuất bản video đúng giờ hẹn.
    Hỗ trợ cả status PENDING và PENDING_WINDOWS_SCHEDULER.
    Track kết quả từng platform riêng biệt.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    brands_path = os.path.join(base_dir, "config/brands.json")

    # Các trạng thái hợp lệ để worker xử lý
    VALID_PENDING = {"PENDING", "PENDING_WINDOWS_SCHEDULER"}

    print("🚀 Bắt đầu trình chạy ngầm Hẹn giờ Đăng bài (Scheduler Worker)...")
    print(f"📋 Đang theo dõi queue: {QUEUE_FILE}")
    print(f"⏰ Thời gian hiện tại: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        # Reload brands mỗi vòng lặp để cập nhật token mới
        try:
            with open(brands_path, "r", encoding="utf-8") as f:
                brands = json.load(f)
        except Exception as e:
            print(f"⚠️ Lỗi đọc brands.json: {e}")
            time.sleep(10)
            continue

        queue = load_queue()
        now_ts = int(time.time())
        updated = False

        for task in queue:
            task_status = task.get("status", "")
            if task_status in VALID_PENDING and now_ts >= task.get("scheduled_timestamp", 0):
                # Xử lý riêng tác vụ bình luận Facebook hẹn giờ
                if task.get("type") == "fb_scheduled_comment":
                    vid_target = task.get("video_id")
                    t_token = task.get("access_token")
                    c_list = task.get("comments") or []
                    if isinstance(c_list, str):
                        c_list = [c_list]
                    print(f"\n{'='*60}")
                    print(f"⏰ [HẸN GIỜ COMMENT FB] Tác vụ: {task['id']} | Video ID: {vid_target}")
                    print(f"💬 Đang gửi {len(c_list)} bình luận affiliate vào Facebook Reel...")
                    all_c_ok = True
                    for c_idx, c_msg in enumerate(c_list, 1):
                        posted = False
                        for attempt in range(1, 4):
                            try:
                                time.sleep(2)
                                res_c = requests.post(
                                    f"https://graph.facebook.com/v19.0/{vid_target}/comments",
                                    data={"message": c_msg, "access_token": t_token},
                                    timeout=25
                                ).json()
                                if "id" in res_c:
                                    print(f"  ✅ Đã bình luận FB #{c_idx}: '{c_msg[:45]}...' (ID: {res_c['id']})")
                                    posted = True
                                    break
                                else:
                                    print(f"  ⚠️ Thử gửi comment #{c_idx} lần {attempt}: {res_c}")
                            except Exception as e_c:
                                print(f"  ⚠️ Lỗi gửi comment FB #{c_idx} lần {attempt}: {e_c}")
                            time.sleep(3)
                        if not posted:
                            all_c_ok = False
                    task["status"] = "SUCCESS" if all_c_ok else "FAILED"
                    task["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{'='*60}")
                    updated = True
                    continue

                try:
                    title_safe = task.get('title', 'N/A')[:50]
                except Exception:
                    title_safe = 'N/A'
                print(f"\n{'='*60}")
                print(f"⏰ [ĐẾN GIỜ HẸN] Tác vụ: {task['id']}")
                print(f"📝 Tiêu đề: {title_safe}")
                print(f"🏷️ Thương hiệu: {task.get('brand_key', 'N/A')}")
                print(f"🌐 Nền tảng: {', '.join(task.get('platforms', []))}")
                print(f"{'='*60}")

                brand_key = task["brand_key"]
                brand_data = brands.get(brand_key, {})
                video_path = task["video_path"]
                title = task.get("title", "")
                caption = task.get("caption", "")
                comment = task.get("comment", "")
                platforms = task.get("platforms", [])

                # Kiểm tra video tồn tại
                if not os.path.exists(video_path):
                    print(f"❌ Không tìm thấy video: {video_path}")
                    task["status"] = "FAILED"
                    task["error"] = f"Video không tồn tại: {video_path}"
                    task["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updated = True
                    continue

                # Track kết quả từng platform
                platform_results = {}
                has_failure = False

                # 1. YouTube Shorts
                if "youtube" in platforms:
                    try:
                        yt_cfg = brand_data.get("youtube", {})
                        yt_token = yt_cfg.get("token_file", "")
                        yt_token_path = os.path.join(base_dir, yt_token) if not os.path.isabs(yt_token) else yt_token
                        yt = YouTubeShortsUploader(token_file=yt_token_path)
                        res = yt.upload_short(video_path=video_path, title=title, description=caption, comment_text=comment)
                        if res and res.get("success"):
                            platform_results["youtube"] = {"status": "SUCCESS", "url": res.get("shorts_url", "")}
                            print(f"✅ YouTube: {res.get('shorts_url', 'OK')}")
                        else:
                            platform_results["youtube"] = {"status": "FAILED", "error": "Upload trả về None"}
                            has_failure = True
                            print(f"❌ YouTube: Upload thất bại")
                    except Exception as e:
                        platform_results["youtube"] = {"status": "FAILED", "error": str(e)}
                        has_failure = True
                        print(f"⚠️ Lỗi hẹn giờ YouTube: {e}")

                # 2. Facebook Reels
                if "facebook" in platforms:
                    try:
                        fb_cfg = brand_data.get("facebook", {})
                        fb = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])
                        res = fb.upload_reel(video_path=video_path, title=title, caption=caption, comment_text=comment)
                        if res and res.get("success"):
                            platform_results["facebook"] = {"status": "SUCCESS", "url": res.get("reel_url", "")}
                            print(f"✅ Facebook: {res.get('reel_url', 'OK')}")
                        else:
                            platform_results["facebook"] = {"status": "FAILED", "error": "Upload trả về None"}
                            has_failure = True
                            print(f"❌ Facebook: Upload thất bại")
                    except Exception as e:
                        platform_results["facebook"] = {"status": "FAILED", "error": str(e)}
                        has_failure = True
                        print(f"⚠️ Lỗi hẹn giờ Facebook: {e}")

                # Delay giữa các platform để tránh rate limit CDN
                if platform_results:
                    time.sleep(5)

                # 3. Instagram Reels
                if "instagram" in platforms:
                    try:
                        ig_token = refresh_meta_token_if_needed(brand_data, brand_key, "instagram", brands_path)
                        ig_cfg = brand_data.get("instagram", {})
                        ig = InstagramReelsUploader(ig_user_id=ig_cfg["ig_user_id"], access_token=ig_token or ig_cfg.get("access_token", ""))
                        ig_caption = f"{title}\n\n{caption}" if title else caption
                        res = ig.upload_reel(video_path=video_path, caption=ig_caption, comment_text=comment)
                        if res and res.get("success"):
                            m_id = res.get("media_id", "")
                            permalink = res.get("permalink") or (f"https://www.instagram.com/reel/{m_id}/" if m_id else "")
                            platform_results["instagram"] = {
                                "status": "SUCCESS",
                                "media_id": m_id,
                                "permalink": permalink,
                                "url": permalink
                            }
                            print(f"✅ Instagram: {permalink or m_id}")
                        else:
                            platform_results["instagram"] = {"status": "FAILED", "error": "Upload trả về None"}
                            has_failure = True
                            print(f"❌ Instagram: Upload thất bại")
                    except Exception as e:
                        platform_results["instagram"] = {"status": "FAILED", "error": str(e)}
                        has_failure = True
                        print(f"⚠️ Lỗi hẹn giờ Instagram: {e}")

                # Delay trước Threads
                if "threads" in platforms and ("instagram" in platforms or "facebook" in platforms):
                    time.sleep(5)

                # 4. Threads
                if "threads" in platforms:
                    try:
                        th_cfg = brand_data.get("threads", {})
                        if th_cfg.get("user_id") and th_cfg.get("access_token"):
                            th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
                            res = th.upload_video_thread(video_path=video_path, caption=caption, comment_link=comment)
                            if res and res.get("success"):
                                permalink = res.get("permalink", "")
                                platform_results["threads"] = {"status": "SUCCESS", "permalink": permalink, "url": permalink}
                                print(f"✅ Threads: {permalink or 'OK'}")
                            else:
                                platform_results["threads"] = {"status": "FAILED", "error": "Upload trả về None"}
                                has_failure = True
                                print(f"❌ Threads: Upload thất bại")
                        else:
                            platform_results["threads"] = {"status": "SKIPPED", "error": "Thiếu user_id/access_token"}
                            print(f"⚠️ Threads: Thiếu cấu hình cho '{brand_key}'")
                    except Exception as e:
                        platform_results["threads"] = {"status": "FAILED", "error": str(e)}
                        has_failure = True
                        print(f"⚠️ Lỗi hẹn giờ Threads: {e}")

                # 5. TikTok
                if "tiktok" in platforms:
                    try:
                        tk = TikTokAPIUploader()
                        tk.upload_to_inbox(video_path=video_path, caption=caption)
                        platform_results["tiktok"] = {"status": "SUCCESS"}
                        print(f"✅ TikTok: Upload thành công")
                    except Exception as e:
                        platform_results["tiktok"] = {"status": "FAILED", "error": str(e)}
                        has_failure = True
                        print(f"⚠️ Lỗi hẹn giờ TikTok: {e}")

                # Cập nhật kết quả
                task["platform_results"] = platform_results
                task["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if has_failure:
                    task["status"] = "COMPLETED_WITH_ERRORS"
                    failed_platforms = [p for p, r in platform_results.items() if r.get("status") == "FAILED"]
                    print(f"\n⚠️ Tác vụ {task['id']} hoàn tất với LỖI tại: {', '.join(failed_platforms)}")
                else:
                    task["status"] = "COMPLETED"
                    print(f"\n🎉 Tác vụ {task['id']} hoàn tất THÀNH CÔNG trên tất cả nền tảng!")

                # Tự động đồng bộ ngay vào cache thống kê và upload_tasks_history.json
                try:
                    succ_results = {}
                    for p_k, p_res in platform_results.items():
                        if p_res.get("status") == "SUCCESS":
                            p_label = "YouTube" if p_k == "youtube" else ("Facebook" if p_k == "facebook" else ("Instagram" if p_k == "instagram" else ("Threads" if p_k == "threads" else p_k.capitalize())))
                            succ_results[p_label] = p_res.get("permalink") or p_res.get("url") or p_res.get("media_id") or "OK"

                    # Cập nhật upload_tasks_history.json nếu có parent task ID
                    t_raw_id = task.get("id", "")
                    parent_tid = t_raw_id.replace("task_ig_", "").replace("task_th_", "")
                    history_file = os.path.join(os.path.dirname(__file__), "config", "upload_tasks_history.json")
                    if os.path.exists(history_file) and parent_tid:
                        try:
                            with open(history_file, "r", encoding="utf-8") as _hf:
                                _hist = json.load(_hf)
                            if parent_tid in _hist:
                                _target_t = _hist[parent_tid]
                                _t_res = _target_t.setdefault("results", {})
                                for _pl, _u in succ_results.items():
                                    _t_res[_pl] = _u
                                with open(history_file, "w", encoding="utf-8") as _hf:
                                    json.dump(_hist, _hf, ensure_ascii=False, indent=2)
                        except Exception as _eh:
                            print(f"⚠️ Lỗi update upload_tasks_history từ scheduler: {_eh}")

                    if succ_results:
                        from app import inject_task_into_analytics_cache
                        sched_sync_task = {
                            "brand_key": brand_key,
                            "title": title,
                            "caption": caption,
                            "results": succ_results
                        }
                        inject_task_into_analytics_cache(sched_sync_task)
                except Exception:
                    pass

                updated = True

                # Delay giữa các task để tránh quá tải
                time.sleep(10)

        if updated:
            save_queue(queue)

        time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        run_scheduled_worker()
    else:
        print("Sử dụng: python scheduler.py --worker")
