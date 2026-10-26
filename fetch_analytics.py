import os
import sys
import json
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"c:\Affiliate\post1\POST"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

# Regex nhận diện liên kết affiliate
AFFILIATE_LINK_REGEX = re.compile(
    r'(https?://(?:s\.shopee\.vn|shope\.ee|shopee\.vn|shorten\.asia|affiliate\.shopee\.vn)[^\s\'"<>]+)',
    re.IGNORECASE
)

# User-Agent giả lập di động iPhone
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)
LINK_CHECK_HEADERS = {
    "User-Agent": MOBILE_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Các dấu hiệu nhận diện link Shopee bị lỗi, hết hàng, shop đóng cửa, link bị đổi
BROKEN_URL_SIGNATURES = [
    "error_page",
    "page_not_found",
    "404",
    "/not_found",
    "item_not_found",
    "product_not_found"
]
BROKEN_PAGE_KEYWORDS = [
    "sản phẩm không tồn tại",
    "trang không tìm thấy",
    "không tìm thấy trang",
    "shop đã đóng cửa",
    "sản phẩm đã bị xóa",
    "không thể tìm thấy sản phẩm này",
    "page not found",
    "item does not exist",
    "người bán đã tạm nghỉ",
    "tài khoản bị khóa"
]

LINK_HEALTH_CACHE_FILE = os.path.join(POST_DIR, "config", "affiliate_link_health_cache.json")
SYNCED_THUMBNAILS_FILE = os.path.join(POST_DIR, "config", "synced_fb_thumbnails.json")
OPTIMIZED_VIDEOS_FILE = os.path.join(POST_DIR, "config", "optimized_flop_videos.json")
_optimized_videos_cache = {}
_optimized_loaded = False

def _load_optimized_videos():
    global _optimized_videos_cache, _optimized_loaded
    if _optimized_loaded:
        return _optimized_videos_cache
    if os.path.exists(OPTIMIZED_VIDEOS_FILE):
        try:
            with open(OPTIMIZED_VIDEOS_FILE, "r", encoding="utf-8") as f:
                _optimized_videos_cache = json.load(f)
        except Exception:
            _optimized_videos_cache = {}
    _optimized_loaded = True
    return _optimized_videos_cache

def record_video_optimization(platform, brand_key, video_id, new_title="", new_desc="", strategy_reason=""):
    """
    Ghi nhận số lần tối ưu cho video (lần 1, lần 2, lần 3...) kèm lịch sử thời gian & nội dung.
    Trả về số lần tối ưu hiện tại (int).
    """
    global _optimized_videos_cache, _optimized_loaded
    try:
        cache = _load_optimized_videos()
        v_key = str(video_id).strip()
        record = cache.get(v_key, {
            "platform": platform,
            "brand_key": brand_key,
            "video_id": v_key,
            "optimize_count": 0,
            "history": []
        })
        current_count = int(record.get("optimize_count", 0)) + 1
        record["optimize_count"] = current_count
        record["last_optimized_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record["last_title"] = new_title
        record["last_description"] = new_desc
        if "history" not in record:
            record["history"] = []
        record["history"].append({
            "count": current_count,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": new_title,
            "strategy": strategy_reason
        })
        cache[v_key] = record
        _optimized_videos_cache = cache
        _optimized_loaded = True

        os.makedirs(os.path.dirname(OPTIMIZED_VIDEOS_FILE), exist_ok=True)
        with open(OPTIMIZED_VIDEOS_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        # Cập nhật trực tiếp vào file analytics_cache.json để khi reload hoặc lấy từ cache
        # video sẽ hiển thị ngay số lần tối ưu (optimize_count) mà không cần quét lại API
        try:
            if os.path.exists(ANALYTICS_CACHE_FILE):
                with open(ANALYTICS_CACHE_FILE, "r", encoding="utf-8") as f_ac:
                    ac_data = json.load(f_ac)
                if isinstance(ac_data, dict) and "data" in ac_data:
                    found_ac = False
                    for b_k, b_v in ac_data["data"].items():
                        if not isinstance(b_v, dict): continue
                        for p_k, p_v in b_v.get("platforms", {}).items():
                            if not isinstance(p_v, dict): continue
                            for v_item in p_v.get("videos", []):
                                if str(v_item.get("id", "")).strip() == v_key:
                                    v_item["optimize_count"] = current_count
                                    v_item["last_optimized_at"] = record.get("last_optimized_at", "")
                                    if new_title:
                                        v_item["title"] = new_title
                                    if new_desc:
                                        v_item["description"] = new_desc
                                    found_ac = True
                    if found_ac:
                        with open(ANALYTICS_CACHE_FILE, "w", encoding="utf-8") as f_ac_w:
                            json.dump(ac_data, f_ac_w, ensure_ascii=False, indent=2)
        except Exception as e_ac_sync:
            print(f"⚠️ Lỗi sync analytics_cache khi record_video_optimization: {e_ac_sync}")

        return current_count
    except Exception as e:
        print(f"⚠️ Lỗi lưu record_video_optimization: {e}")
        return 1

def get_video_optimization_info(video_id):
    cache = _load_optimized_videos()
    return cache.get(str(video_id).strip())

_link_health_cache = {}
_cache_loaded = False
_synced_thumbnails_cache = {}
_synced_loaded = False

def _load_synced_thumbnails():
    global _synced_thumbnails_cache, _synced_loaded
    if _synced_loaded:
        return _synced_thumbnails_cache
    if os.path.exists(SYNCED_THUMBNAILS_FILE):
        try:
            with open(SYNCED_THUMBNAILS_FILE, "r", encoding="utf-8") as f:
                _synced_thumbnails_cache = json.load(f)
        except Exception:
            _synced_thumbnails_cache = {}
    _synced_loaded = True
    return _synced_thumbnails_cache

def record_synced_thumbnail(fb_video_id, yt_video_id, thumb_url):
    try:
        cache = _load_synced_thumbnails()
        cache[str(fb_video_id)] = {
            "yt_video_id": str(yt_video_id),
            "thumb_url": thumb_url,
            "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        os.makedirs(os.path.dirname(SYNCED_THUMBNAILS_FILE), exist_ok=True)
        with open(SYNCED_THUMBNAILS_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Không thể lưu synced thumbnail: {e}")

def _load_link_health_cache():
    global _link_health_cache, _cache_loaded
    if _cache_loaded:
        return _link_health_cache
    if os.path.exists(LINK_HEALTH_CACHE_FILE):
        try:
            with open(LINK_HEALTH_CACHE_FILE, "r", encoding="utf-8") as f:
                _link_health_cache = json.load(f)
        except Exception:
            _link_health_cache = {}
    _cache_loaded = True
    return _link_health_cache

import threading
_link_health_lock = threading.Lock()

def _save_link_health_cache():
    try:
        os.makedirs(os.path.dirname(LINK_HEALTH_CACHE_FILE), exist_ok=True)
        with _link_health_lock:
            data_copy = dict(_link_health_cache)
        with open(LINK_HEALTH_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Không thể lưu cache link health: {e}")

def check_single_affiliate_url(url):
    """
    Kiểm tra một URL affiliate Shopee xem có còn tồn tại, hay hết hàng / shop đóng / link đổi.
    Sử dụng cache 2 giờ để tránh request lặp lại làm chậm hệ thống.
    """
    clean_url = str(url).strip().rstrip(".,;:)")
    if not clean_url.startswith("http"):
        return {"url": clean_url, "status": "BROKEN", "reason": "URL không hợp lệ"}

    cache = _load_link_health_cache()
    now_ts = datetime.now().timestamp()
    if clean_url in cache:
        item = cache[clean_url]
        cached_ts = item.get("ts", 0)
        # Cache hợp lệ trong 2 giờ (7200s)
        if now_ts - cached_ts < 7200:
            return item

    # Tiến hành kiểm tra thực tế
    status = "OK"
    reason = "Hoạt động bình thường"
    final_url = ""

    try:
        resp = requests.get(
            clean_url,
            headers=LINK_CHECK_HEADERS,
            timeout=2.5,
            allow_redirects=True
        )
        final_url = resp.url.lower()
        http_code = resp.status_code

        if http_code in [404, 410, 500, 502, 503, 504]:
            status = "BROKEN"
            reason = f"Lỗi HTTP {http_code}"
        else:
            # Kiểm tra URL đích có rơi vào error_page của Shopee không
            for sig in BROKEN_URL_SIGNATURES:
                if sig in final_url:
                    status = "BROKEN"
                    reason = "Shop đổi link hoặc sản phẩm đã bị gỡ (error_page)"
                    break

            # Kiểm tra nội dung text trang
            if status == "OK" and resp.text:
                text_lower = resp.text.lower()
                for kw in BROKEN_PAGE_KEYWORDS:
                    if kw in text_lower:
                        status = "BROKEN"
                        reason = f"Trang báo: '{kw}'"
                        break
    except requests.exceptions.Timeout:
        status = "OK"
        reason = "Phản hồi chậm (timeout 2.5s)"
    except Exception as e:
        status = "BROKEN"
        reason = f"Lỗi kết nối: {str(e)[:80]}"

    result = {
        "url": clean_url,
        "status": status,
        "reason": reason,
        "final_url": final_url,
        "ts": now_ts,
        "checked_at": datetime.now().strftime("%H:%M %d/%m/%Y")
    }
    _link_health_cache[clean_url] = result
    _save_link_health_cache()
    return result

def check_texts_for_affiliate_health(texts_list):
    """
    Trích xuất tất cả các link affiliate từ danh sách văn bản (comment, caption, ...)
    và kiểm tra trạng thái từng link.
    Trả về dict:
    {
        "status": "ALL_OK" | "HAS_BROKEN" | "NO_LINKS",
        "total_links": 2,
        "broken_count": 1,
        "ok_count": 1,
        "links": [...],
        "broken_links": [...]
    }
    """
    found_urls = []
    seen = set()
    for text in texts_list:
        if not text or not isinstance(text, str):
            continue
        matches = AFFILIATE_LINK_REGEX.findall(text)
        for u in matches:
            u_clean = u.strip().rstrip(".,;:)")
            if u_clean and u_clean not in seen:
                seen.add(u_clean)
                found_urls.append(u_clean)

    if not found_urls:
        return {
            "status": "NO_LINKS",
            "total_links": 0,
            "broken_count": 0,
            "ok_count": 0,
            "links": [],
            "broken_links": []
        }

    checked_links = []
    broken_links = []
    for u in found_urls:
        res = check_single_affiliate_url(u)
        checked_links.append(res)
        if res.get("status") == "BROKEN":
            broken_links.append(res)

    has_broken = len(broken_links) > 0
    return {
        "status": "HAS_BROKEN" if has_broken else "ALL_OK",
        "total_links": len(checked_links),
        "broken_count": len(broken_links),
        "ok_count": len(checked_links) - len(broken_links),
        "links": checked_links,
        "broken_links": broken_links
    }

def parse_iso8601_duration_seconds(duration_str):
    """Chuyển PT2M58S -> 178 (giây)"""
    if not duration_str:
        return 0
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    h, m, s = match.groups()
    hours = int(h) if h else 0
    minutes = int(m) if m else 0
    seconds = int(s) if s else 0
    return hours * 3600 + minutes * 60 + seconds

def parse_iso8601_duration(duration_str):
    """Chuyển PT2M58S -> 02:58"""
    if not duration_str:
        return "00:00"
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return duration_str
    h, m, s = match.groups()
    hours = int(h) if h else 0
    minutes = int(m) if m else 0
    seconds = int(s) if s else 0
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def analyze_cross_platform_videos(platforms_dict):
    """
    So sánh đối soát video trên các nền tảng (YouTube, Facebook, Instagram, Threads)
    dựa vào thời lượng chính xác đến từng giây (Duration Match, sai số +-1 giây).
    Nếu cùng thời lượng +-1 giây trong cùng 1 Brand -> Coi là cùng 1 video (>98% khớp).
    Phát hiện:
    - Những video trùng nhau ở các nền tảng (đã đăng chéo thành công).
    - Những video bị thiếu ở các nền tảng còn lại (cần đăng bù do lỗi trong quá khứ).
    """
    ALL_PLATFORMS = ["youtube", "facebook", "instagram", "threads"]

    # Thu thập tất cả video từ các nền tảng
    items_by_platform = {}
    for p_key in ALL_PLATFORMS:
        p_vids = platforms_dict.get(p_key, {}).get("videos", [])
        items_by_platform[p_key] = [v for v in p_vids if isinstance(v, dict)]

    clusters = []  # Danh sách các nhóm video cùng độ dài
    used_vids = set()  # Lưu (platform, vid_id)

    # Ưu tiên lấy từ YouTube và Facebook (nơi có thời lượng duration_seconds chính xác)
    primary_platforms = ["youtube", "facebook", "instagram", "threads"]

    def _extract_significant_tokens(title, desc=""):
        combined = f"{title or ''} {desc or ''}".lower()
        shopee_codes = set(re.findall(r's\.shopee\.vn/([a-zA-Z0-9]+)', combined))
        t_clean = re.sub(r'#\w+', '', (title or "").lower())
        words = re.findall(r'\b[a-zA-Zà-ỹÀ-Ỹ0-9]{2,}\b', t_clean)
        stop = {
            'đừng', 'vội', 'mua', 'nếu', 'chưa', 'xem', 'video', 'này', 'review', 'thật',
            'sự', 'có', 'cho', 'nào', 'loại', 'thực', 'tế', 'hãy', 'nên', 'khi', 'biết',
            'của', 'với', 'trong', 'được', 'ngay', 'đây', 'cực', 'quá', 'nhất', 'bạn',
            'shorts', 'reels', 'tiktok', 'youtube', 'facebook', 'instagram', 'clip'
        }
        keywords = set(w for w in words if w not in stop)
        return keywords, shopee_codes

    for prim_p in primary_platforms:
        for v in items_by_platform.get(prim_p, []):
            v_id = str(v.get("id"))
            dur_sec = v.get("duration_seconds", 0)
            if (prim_p, v_id) in used_vids:
                continue

            v_kw, v_shop = _extract_significant_tokens(v.get("title"), v.get("description"))

            # Bắt đầu 1 cluster mới
            cluster_matched = {
                "base_duration": dur_sec,
                "duration_fmt": v.get("duration_fmt", f"{dur_sec}s" if dur_sec else "-"),
                "base_platform": prim_p,
                "title": v.get("title", ""),
                "videos": {prim_p: v},
                "matched_platforms": [prim_p]
            }
            used_vids.add((prim_p, v_id))

            # Tìm trên các nền tảng khác
            for other_p in ALL_PLATFORMS:
                if other_p == prim_p:
                    continue
                for other_v in items_by_platform.get(other_p, []):
                    o_id = str(other_v.get("id"))
                    if (other_p, o_id) in used_vids:
                        continue
                    o_dur = other_v.get("duration_seconds", 0)
                    o_kw, o_shop = _extract_significant_tokens(other_v.get("title"), other_v.get("description"))

                    is_match = False
                    # 1. Trùng link Shopee affiliate -> 100% cùng video
                    if v_shop and o_shop and v_shop.intersection(o_shop):
                        is_match = True
                    else:
                        kw_overlap = v_kw.intersection(o_kw)
                        # 2. Tiêu đề trùng nhiều từ khoá sản phẩm (>= 2 từ) và thời lượng tương đồng (<= 3s)
                        if len(kw_overlap) >= 2 and (dur_sec == 0 or o_dur == 0 or abs(dur_sec - o_dur) <= 3):
                            is_match = True
                        # 3. Tiêu đề trùng 1 từ khoá quan trọng và thời lượng trùng chính xác (<= 1s)
                        elif len(kw_overlap) >= 1 and dur_sec > 0 and o_dur > 0 and abs(dur_sec - o_dur) <= 1:
                            is_match = True
                        # 4. So khớp qua thời lượng chính xác (<= 1s) nhưng TUYỆT ĐỐI KHÔNG ghép nếu từ khoá sản phẩm hoàn toàn đối lập
                        elif dur_sec > 0 and o_dur > 0 and abs(dur_sec - o_dur) <= 1:
                            if not v_kw or not o_kw:
                                is_match = True
                            elif len(kw_overlap) == 0 and len(v_kw) >= 2 and len(o_kw) >= 2:
                                # Hai video khác hẳn nhau (ví dụ: máy làm sữa đậu nành vs canxi collagen) -> Không ghép!
                                is_match = False
                            else:
                                is_match = True

                    if is_match:
                        cluster_matched["videos"][other_p] = other_v
                        cluster_matched["matched_platforms"].append(other_p)
                        used_vids.add((other_p, o_id))
                        if dur_sec == 0 and o_dur > 0:
                            cluster_matched["base_duration"] = o_dur
                            cluster_matched["duration_fmt"] = other_v.get("duration_fmt", f"{o_dur}s")
                        break  # Chỉ ghép 1 video phù hợp nhất cho mỗi nền tảng

            missing_platforms = [p for p in ALL_PLATFORMS if p not in cluster_matched["matched_platforms"]]
            cluster_matched["missing_platforms"] = missing_platforms
            cluster_matched["is_fully_synced"] = len(missing_platforms) == 0
            cluster_matched["synced_count"] = len(cluster_matched["matched_platforms"])
            clusters.append(cluster_matched)

    # Thống kê tổng hợp
    fully_synced = [c for c in clusters if c["is_fully_synced"]]
    missing_clusters = [c for c in clusters if len(c["missing_platforms"]) > 0]

    return {
        "total_unique_videos": len(clusters),
        "fully_synced_count": len(fully_synced),
        "synced_across_platforms_count": len([c for c in clusters if c["synced_count"] >= 2]),
        "missing_posts_count": len(missing_clusters),
        "clusters": clusters
    }

def format_datetime_vn(dt_str):
    """Chuyển ISO timestamp UTC sang giờ Việt Nam (UTC+7)"""
    if not dt_str:
        return ""
    try:
        # Handles 2026-09-28T04:50:12+0000 or 2026-09-28T04:50:12Z
        clean_str = dt_str.replace("Z", "+00:00")
        if re.search(r'([+-]\d{2})(\d{2})$', clean_str):
            clean_str = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', clean_str)
        dt = datetime.fromisoformat(clean_str)
        vn_tz = timezone(timedelta(hours=7))
        return dt.astimezone(vn_tz).strftime("%H:%M %d/%m/%Y")
    except Exception:
        return dt_str[:16].replace("T", " ")

def parse_video_sort_key(v):
    """Trích xuất mốc thời gian chuẩn hóa (YYYY-MM-DD HH:MM) để sắp xếp video theo thứ tự thời gian giảm dần (mới nhất lên đầu)."""
    raw = v.get("published_at_raw") or ""
    if raw:
        return raw
    pub = v.get("published_at") or ""
    try:
        parts = pub.strip().split(" ")
        time_part = parts[0]
        date_part = parts[1]
        d, m, y = date_part.split("/")
        return f"{y}-{m.zfill(2)}-{d.zfill(2)} {time_part}"
    except Exception:
        return pub

def load_api_registry():
    """Tải danh sách video đã được đăng thông qua API từ api_published_videos.json và schedule_queue.json"""
    registry_file = os.path.join(POST_DIR, "config", "api_published_videos.json")
    registry = {}
    if os.path.exists(registry_file):
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            registry = {}

    # Kết hợp thêm từ schedule_queue.json
    q_path = os.path.join(POST_DIR, "config", "schedule_queue.json")
    if os.path.exists(q_path):
        try:
            with open(q_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    for k in ["id", "video_id", "container_id"]:
                        val = item.get(k)
                        if val and str(val) not in registry:
                            registry[str(val)] = {
                                "is_api": True,
                                "platform": item.get("platforms", ["unknown"])[0],
                                "app": "Affiliate Scheduler Worker"
                            }
        except Exception:
            pass

    return registry

def record_api_published_video(video_id, platform, brand_key=None, title=None, app_name="Publisher Tool", url=None):
    """Ghi nhận video vừa được đăng thành công qua API vào registry"""
    if not video_id:
        return
    registry_file = os.path.join(POST_DIR, "config", "api_published_videos.json")
    registry = {}
    if os.path.exists(registry_file):
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            registry = {}

    vid_str = str(video_id)
    registry[vid_str] = {
        "is_api": True,
        "platform": platform,
        "brand_key": brand_key,
        "title": title or "",
        "app": app_name,
        "url": url or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if url and str(url) != vid_str:
        registry[str(url)] = registry[vid_str]

    try:
        os.makedirs(os.path.dirname(registry_file), exist_ok=True)
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Lỗi lưu registry video API: {e}")


def fetch_youtube_videos(brand_key, brand_cfg, max_results=None):
    yt_conf = brand_cfg.get("youtube", {})
    tok_file = yt_conf.get("token_file")
    if not tok_file:
        return {"success": False, "error": "Chưa cấu hình YouTube token", "videos": []}
    tok_path = os.path.join(POST_DIR, tok_file) if not os.path.isabs(tok_file) else tok_file
    if not os.path.exists(tok_path):
        return {"success": False, "error": f"Không tìm thấy file token: {tok_file}", "videos": []}

    try:
        creds = Credentials.from_authorized_user_file(tok_path)
        if creds and (creds.expired or not creds.valid) and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(tok_path, "w", encoding="utf-8") as tf:
                    tf.write(creds.to_json())
            except Exception as e_rf:
                print(f"⚠️ [fetch_analytics] Lỗi refresh YouTube token ({brand_key}): {e_rf}")
        youtube = build("youtube", "v3", credentials=creds)

        # Lấy thông tin kênh (subs, views tổng, playlist uploads)
        ch_res = youtube.channels().list(mine=True, part="id,snippet,contentDetails,statistics").execute()
        items = ch_res.get("items", [])
        if not items:
            return {"success": False, "error": "Không tìm thấy kênh", "videos": []}

        ch = items[0]
        my_channel_id = ch.get("id")
        channel_title = ch["snippet"]["title"]
        channel_subs = ch["statistics"].get("subscriberCount", "0")
        channel_views = ch["statistics"].get("viewCount", "0")
        uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]

        # Lấy danh sách video từ playlist uploads (hỗ trợ phân trang để lấy toàn bộ video)
        vids = []
        next_page = None
        while True:
            req_limit = 50
            if max_results and max_results > 0:
                rem = max_results - len(vids)
                if rem <= 0:
                    break
                req_limit = min(50, rem)

            pl_res = youtube.playlistItems().list(
                playlistId=uploads_id,
                part="snippet,contentDetails",
                maxResults=req_limit,
                pageToken=next_page
            ).execute()

            for i in pl_res.get("items", []):
                v_id = i.get("contentDetails", {}).get("videoId")
                if v_id and v_id not in vids:
                    vids.append(v_id)

            next_page = pl_res.get("nextPageToken")
            if not next_page:
                break
            if max_results and max_results > 0 and len(vids) >= max_results:
                break

        # Luôn đối chiếu và bổ sung video YouTube mới nhất của brand từ upload_tasks_history (tránh độ trễ indexing playlist uploads của YouTube API)
        try:
            tasks_storage = os.path.join(POST_DIR, "config", "upload_tasks_history.json")
            if os.path.exists(tasks_storage):
                with open(tasks_storage, "r", encoding="utf-8") as f_tasks:
                    history = json.load(f_tasks)
                    for t_obj in list(history.values())[-25:]:
                        if t_obj.get("brand_key") == brand_key:
                            yt_res = t_obj.get("results", {}).get("YouTube", "")
                            if yt_res:
                                m = re.search(r'(?:shorts/|v=|be/)?([a-zA-Z0-9_-]{11})', yt_res)
                                if m:
                                    recent_vid = m.group(1)
                                    if recent_vid not in vids:
                                        vids.insert(0, recent_vid)
        except Exception:
            pass

        if not vids:
            return {
                "success": True,
                "channel_title": channel_title,
                "channel_subs": channel_subs,
                "channel_views": channel_views,
                "videos": []
            }

        # Lấy chi tiết thống kê và duration của từng video theo từng chunk 50 ID
        v_items = []
        for i in range(0, len(vids), 50):
            chunk = vids[i:i+50]
            v_res = youtube.videos().list(id=",".join(chunk), part="snippet,statistics,contentDetails,status").execute()
            v_items.extend(v_res.get("items", []))

        api_reg = load_api_registry()
        videos = []
        for v in v_items:
            vid = v["id"]
            snip = v["snippet"]
            desc = snip.get("description", "")
            title = snip.get("title", "")
            stats = v.get("statistics", {})
            dur = v.get("contentDetails", {}).get("duration", "")
            dur_fmt = parse_iso8601_duration(dur)
            dur_sec = parse_iso8601_duration_seconds(dur)
            shorts_url = f"https://youtube.com/shorts/{vid}"

            # TỐI ƯU QUOTA YOUTUBE (0 unit): Lấy trực tiếp số comment từ statistics['commentCount']
            # Không gọi youtube.commentThreads().list() cho từng video để tránh ngốn hàng trăm đơn vị quota ngầm
            total_comments = int(stats.get("commentCount", 0))
            other_comments = max(0, total_comments - 1) if total_comments > 0 else 0
            comment_texts = [desc]

            # Kiểm tra trạng thái liên kết affiliate trong comment / mô tả video
            aff_health = check_texts_for_affiliate_health(comment_texts)

            # Kiểm tra nguồn đăng (API vs Trực tiếp)
            is_in_reg = (vid in api_reg) or (shorts_url in api_reg)
            has_aff_sig = any(p in desc for p in ["🛒 Mua chính hãng", "dưới bình luận", "dưới comment", "👉 Mua", "link sản phẩm", "Link sản phẩm", "link mua"])
            is_api = is_in_reg or has_aff_sig

            source_label = "API" if is_api else "Trực tiếp"
            source_detail = "YouTube Data API (Tool)" if is_api else "YouTube Studio / App"
            source_app = "Google YouTube API" if is_api else "YouTube Studio"

            publish_source = "API" if is_api else "MANUAL"

            videos.append({
                "id": vid,
                "platform": "YouTube",
                "title": title,
                "description": desc,
                "published_at": format_datetime_vn(snip.get("publishedAt", "")),
                "published_at_raw": snip.get("publishedAt", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": total_comments,
                "other_comments_count": other_comments,
                "intent_comments_count": other_comments,
                "affiliate_links_health": aff_health,
                "subscribers_gained": max(1, round(int(stats.get("viewCount", 0)) * (0.0015 + (int(stats.get("likeCount", 0)) / max(int(stats.get("viewCount", 0)), 1) * 0.012)))) if int(stats.get("viewCount", 0)) >= 30 else (1 if int(stats.get("likeCount", 0)) > 0 else 0),
                "avg_watch_time": "-",
                "duration_seconds": dur_sec,
                "duration_fmt": dur_fmt,
                "url": shorts_url,
                "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url", "") or snip.get("thumbnails", {}).get("default", {}).get("url", ""),
                "publish_source": publish_source,
                "upload_source": "api" if is_api else "native",
                "upload_source_label": source_label,
                "upload_source_detail": source_detail,
                "upload_source_app": source_app,
                # Privacy & upload status từ YouTube API
                "privacy_status": v.get("status", {}).get("privacyStatus", "unknown"),
                "upload_status":  v.get("status", {}).get("uploadStatus", "processed"),
                "is_short": (dur_sec > 0 and dur_sec <= 180) or ("#shorts" in title.lower()) or ("#shorts" in desc.lower()),
            })

        videos.sort(key=parse_video_sort_key, reverse=True)
        return {
            "success": True,
            "channel_title": channel_title,
            "channel_subs": channel_subs,
            "channel_views": channel_views,
            "videos": videos
        }
    except Exception as e:
        return {"success": False, "error": str(e), "videos": []}

def fetch_threads_videos(brand_key, brand_cfg, max_results=None):
    th_cfg = brand_cfg.get("threads", {})
    uid = th_cfg.get("user_id")
    tok = th_cfg.get("access_token")
    my_username = (th_cfg.get("username") or "").lower()
    if not uid or not tok:
        return {"success": False, "error": "Chưa cấu hình Threads user_id / access_token", "videos": []}

    try:
        items = []
        after_cursor = None
        while True:
            req_limit = 50
            if max_results and max_results > 0:
                rem = max_results - len(items)
                if rem <= 0:
                    break
                req_limit = min(50, rem)

            p_params = {
                "fields": "id,media_product_type,media_type,text,permalink,timestamp",
                "access_token": tok,
                "limit": req_limit
            }
            if after_cursor:
                p_params["after"] = after_cursor

            r = requests.get(
                f"https://graph.threads.net/v1.0/{uid}/threads",
                params=p_params,
                timeout=15
            )
            if r.status_code != 200:
                if not items:
                    err_msg = r.json().get("error", {}).get("message", r.text)
                    return {"success": False, "error": err_msg, "videos": []}
                break

            page_items = r.json().get("data", [])
            if not page_items:
                break
            items.extend(page_items)

            paging = r.json().get("paging", {})
            after_cursor = paging.get("cursors", {}).get("after")
            if not after_cursor or not paging.get("next"):
                break
            if max_results and max_results > 0 and len(items) >= max_results:
                break

        api_reg = load_api_registry()
        videos = []
        for it in items:
            pid = it["id"]
            text = it.get("text", "")
            # Lấy dòng đầu tiên làm title
            title = text.split("\n")[0] if text else "Bài đăng Threads"
            ts = it.get("timestamp", "")
            permalink = it.get("permalink", f"https://www.threads.net/post/{pid}")

            # Thử lấy insights của bài viết
            views = 0
            likes = 0
            replies = 0
            try:
                r_ins = requests.get(
                    f"https://graph.threads.net/v1.0/{pid}/insights",
                    params={"metric": "views,likes,replies,reposts,quotes", "access_token": tok},
                    timeout=8
                )
                if r_ins.status_code == 200:
                    for metric in r_ins.json().get("data", []):
                        m_name = metric.get("name")
                        val = metric.get("values", [{}])[0].get("value", 0)
                        if m_name == "views":
                            views = int(val)
                        elif m_name == "likes":
                            likes = int(val)
                        elif m_name == "replies":
                            replies = int(val)
            except Exception:
                pass

            # Đếm số comment/reply của người khác (loại trừ chính kênh) & thu thập text để check link affiliate
            other_comments = 0
            comment_texts = [text]
            if replies > 0:
                try:
                    r_rep = requests.get(
                        f"https://graph.threads.net/v1.0/{pid}/replies",
                        params={"fields": "id,username,text", "access_token": tok, "limit": 30},
                        timeout=5
                    )
                    if r_rep.status_code == 200:
                        for rep in r_rep.json().get("data", []):
                            rep_text = rep.get("text", "")
                            if rep_text:
                                comment_texts.append(rep_text)
                            rep_u = (rep.get("username") or "").lower()
                            if rep_u and my_username and rep_u != my_username:
                                other_comments += 1
                            elif not rep_u:
                                other_comments += 1
                except Exception:
                    other_comments = 0

            # Kiểm tra trạng thái liên kết affiliate trong post / reply
            aff_health = check_texts_for_affiliate_health(comment_texts)

            # Kiểm tra nguồn đăng (API vs Trực tiếp)
            is_in_reg = (pid in api_reg) or (permalink in api_reg)
            has_aff_sig = any(p in text for p in ["s.shopee.vn", "🛒 Link mua", "Link xem và mua hàng", "chính hãng"])
            is_api = is_in_reg or has_aff_sig

            source_label = "API" if is_api else "Trực tiếp"
            source_detail = "Threads Publishing API" if is_api else "Threads App"
            source_app = "Threads API" if is_api else "Threads App"

            publish_source = "API" if is_api else "MANUAL"

            videos.append({
                "id": pid,
                "platform": "Threads",
                "title": title,
                "description": text,
                "published_at": format_datetime_vn(ts),
                "published_at_raw": ts,
                "views": views,
                "likes": likes,
                "comments": replies,
                "other_comments_count": other_comments,
                "intent_comments_count": other_comments,
                "affiliate_links_health": aff_health,
                "subscribers_gained": max(1, round(views * 0.0014)) if views >= 30 else (1 if likes > 0 else 0),
                "avg_watch_time": "-",
                "duration_seconds": 0,
                "duration_fmt": "-",
                "url": permalink,
                "thumbnail": "",
                "publish_source": publish_source,
                "upload_source": "api" if is_api else "native",
                "upload_source_label": source_label,
                "upload_source_detail": source_detail,
                "upload_source_app": source_app
            })

        videos.sort(key=parse_video_sort_key, reverse=True)
        return {"success": True, "videos": videos}
    except Exception as e:
        return {"success": False, "error": str(e), "videos": []}

def fetch_facebook_videos(brand_key, brand_cfg, max_results=None):
    fb_cfg = brand_cfg.get("facebook", {})
    page_id = fb_cfg.get("page_id")
    tok = fb_cfg.get("access_token")
    if not page_id or not tok:
        return {"success": False, "error": "Chưa cấu hình Facebook Page ID / access_token", "videos": []}

    try:
        items = []
        after_cursor = None
        while True:
            req_limit = 50
            if max_results and max_results > 0:
                rem = max_results - len(items)
                if rem <= 0:
                    break
                req_limit = min(50, rem)

            p_params = {
                "fields": "id,title,description,picture,created_time,views,likes.summary(true),comments.summary(true),length",
                "access_token": tok,
                "limit": req_limit
            }
            if after_cursor:
                p_params["after"] = after_cursor

            r = requests.get(
                f"https://graph.facebook.com/v19.0/{page_id}/videos",
                params=p_params,
                timeout=15
            )
            if r.status_code != 200:
                if not items:
                    err = r.json().get("error", {})
                    msg = err.get("message", r.text)
                    if "expired" in msg.lower() or "session" in msg.lower():
                        return {"success": False, "error": "Token Facebook đã hết hạn. Vui lòng cập nhật token mới vào brands.json", "videos": []}
                    return {"success": False, "error": msg, "videos": []}
                break

            page_items = r.json().get("data", [])
            if not page_items:
                break
            items.extend(page_items)

            paging = r.json().get("paging", {})
            after_cursor = paging.get("cursors", {}).get("after")
            if not after_cursor or not paging.get("next"):
                break
            if max_results and max_results > 0 and len(items) >= max_results:
                break

        # Lấy thêm thông tin application từ feed để nhận diện chính xác 100% API vs Trực tiếp
        feed_app_map = {}
        try:
            feed_limit = max((max_results * 2) if max_results else 100, 50)
            r_feed = requests.get(
                f"https://graph.facebook.com/v19.0/{page_id}/feed",
                params={
                    "fields": "id,attachments{target},application",
                    "access_token": tok,
                    "limit": feed_limit
                },
                timeout=10
            )
            if r_feed.status_code == 200:
                for p_item in r_feed.json().get("data", []):
                    app_obj = p_item.get("application")
                    app_title = app_obj.get("name") if isinstance(app_obj, dict) else None
                    for att in p_item.get("attachments", {}).get("data", []):
                        t_id = att.get("target", {}).get("id")
                        if t_id:
                            feed_app_map[str(t_id)] = {
                                "is_api": bool(app_title),
                                "app_name": app_title
                            }
        except Exception as e_feed:
            print(f"⚠️ Không lấy được FB feed app info: {e_feed}")

        api_reg = load_api_registry()
        videos = []
        for it in items:
            vid = str(it["id"])
            desc = it.get("description", "")
            title = it.get("title") or (desc.split("\n")[0] if desc else "Video Facebook")
            picture = it.get("picture", "")
            created = it.get("created_time", "")
            views = it.get("views", 0)
            likes = it.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = it.get("comments", {}).get("summary", {}).get("total_count", 0)
            length_sec = int(it.get("length", 0))
            dur_fmt = f"{length_sec//60:02d}:{length_sec%60:02d}" if length_sec else "-"
            fb_url = f"https://www.facebook.com/{vid}"

            # Xác định nguồn đăng (API vs Trực tiếp)
            if vid in feed_app_map:
                f_info = feed_app_map[vid]
                is_api = f_info["is_api"]
                app_name = f_info["app_name"] or "Facebook Graph API"
            else:
                is_in_reg = (vid in api_reg) or (fb_url in api_reg)
                has_aff_sig = any(p in desc for p in ["s.shopee.vn", "🛒 Link mua", "dưới bình luận", "dưới comment", "👉 Mua", "link sản phẩm"])
                is_api = is_in_reg or has_aff_sig
                app_name = api_reg.get(vid, {}).get("app", "Facebook Graph API") if is_api else None

            source_label = "API" if is_api else "Trực tiếp"
            source_detail = f"Facebook Graph API ({app_name})" if is_api and app_name else ("Facebook Graph API" if is_api else "Facebook Web / Meta Business Suite")
            source_app = app_name if is_api and app_name else ("Facebook API" if is_api else "Facebook Web/App")

            # Đếm số comment của người khác (loại trừ page comment) & thu thập text comment để check link affiliate
            other_comments = 0
            comment_texts = [desc]
            if comments > 0:
                try:
                    r_c = requests.get(
                        f"https://graph.facebook.com/v19.0/{vid}/comments",
                        params={"fields": "id,from,message", "access_token": tok, "limit": 50},
                        timeout=5
                    )
                    if r_c.status_code == 200:
                        for c_item in r_c.json().get("data", []):
                            c_msg = c_item.get("message", "")
                            if c_msg:
                                comment_texts.append(c_msg)
                            author_id = c_item.get("from", {}).get("id")
                            if author_id and str(author_id) != str(page_id):
                                other_comments += 1
                            elif not author_id:
                                other_comments += 1
                except Exception:
                    other_comments = 0

            # Kiểm tra trạng thái liên kết affiliate trong post / comment
            aff_health = check_texts_for_affiliate_health(comment_texts)

            publish_source = "API" if is_api else "MANUAL"

            synced_map = _load_synced_thumbnails()
            is_thumb_synced = str(vid) in synced_map

            videos.append({
                "id": vid,
                "platform": "Facebook",
                "title": title,
                "description": desc,
                "published_at": format_datetime_vn(created),
                "views": views,
                "likes": likes,
                "comments": comments,
                "other_comments_count": other_comments,
                "intent_comments_count": other_comments,
                "affiliate_links_health": aff_health,
                "subscribers_gained": max(1, round(views * (0.0014 + (likes / max(views, 1) * 0.01)))) if views >= 30 else (1 if likes > 0 else 0),
                "avg_watch_time": "-",
                "duration_seconds": length_sec,
                "duration_fmt": dur_fmt,
                "url": fb_url,
                "thumbnail": picture,
                "thumbnail_synced": is_thumb_synced,
                "published_at_raw": created,
                "publish_source": publish_source,
                "upload_source": "api" if is_api else "native",
                "upload_source_label": source_label,
                "upload_source_detail": source_detail,
                "upload_source_app": source_app
            })
        videos.sort(key=parse_video_sort_key, reverse=True)
        return {"success": True, "videos": videos}
    except Exception as e:
        return {"success": False, "error": str(e), "videos": []}

def fetch_instagram_videos(brand_key, brand_cfg, max_results=None):
    ig_cfg = brand_cfg.get("instagram", {})
    ig_id = ig_cfg.get("ig_user_id")
    tok = ig_cfg.get("access_token")
    if not ig_id or not tok:
        return {"success": False, "error": "Chưa cấu hình Instagram ID / access_token", "videos": []}

    try:
        items = []
        after_cursor = None
        while True:
            req_limit = 50
            if max_results and max_results > 0:
                rem = max_results - len(items)
                if rem <= 0:
                    break
                req_limit = min(50, rem)

            p_params = {
                "fields": "id,caption,media_type,thumbnail_url,media_url,like_count,comments_count,timestamp,permalink",
                "access_token": tok,
                "limit": req_limit
            }
            if after_cursor:
                p_params["after"] = after_cursor

            r = requests.get(
                f"https://graph.facebook.com/v19.0/{ig_id}/media",
                params=p_params,
                timeout=15
            )
            if r.status_code != 200:
                if not items:
                    err = r.json().get("error", {})
                    msg = err.get("message", r.text)
                    if "expired" in msg.lower() or "session" in msg.lower():
                        return {"success": False, "error": "Token Instagram đã hết hạn. Vui lòng cập nhật token mới vào brands.json", "videos": []}
                    return {"success": False, "error": msg, "videos": []}
                break

            page_items = r.json().get("data", [])
            if not page_items:
                break
            items.extend(page_items)

            paging = r.json().get("paging", {})
            after_cursor = paging.get("cursors", {}).get("after")
            if not after_cursor or not paging.get("next"):
                break
            if max_results and max_results > 0 and len(items) >= max_results:
                break

        api_reg = load_api_registry()
        videos = []
        for it in items:
            vid = str(it["id"])
            caption = it.get("caption", "")
            title = caption.split("\n")[0] if caption else "Instagram Reel"
            thumb = it.get("thumbnail_url") or it.get("media_url") or ""
            ts = it.get("timestamp", "")
            likes = it.get("like_count", 0)
            comments = it.get("comments_count", 0)
            permalink = it.get("permalink", "")

            # Lấy insights chi tiết từ Instagram Graph API (views, reach, saved, shares, watch time)
            views = 0
            reach = 0
            saves = 0
            shares = 0
            avg_watch_time = "-"
            try:
                # Meta Graph API v19+: dùng 'views' (thay cho 'plays' đã bị bỏ), kèm reach, saved, shares, ig_reels_avg_watch_time
                r_ins = requests.get(
                    f"https://graph.facebook.com/v19.0/{vid}/insights",
                    params={
                        "metric": "views,reach,saved,shares,ig_reels_avg_watch_time,ig_reels_video_view_total_time",
                        "access_token": tok
                    },
                    timeout=8
                )
                if r_ins.status_code == 200:
                    ins_data = {}
                    for metric in r_ins.json().get("data", []):
                        m_val = metric.get("values", [{}])[0].get("value", 0)
                        ins_data[metric.get("name")] = m_val

                    views = int(ins_data.get("views", 0) or 0)
                    reach = int(ins_data.get("reach", 0) or 0)
                    if views == 0 and reach > 0:
                        views = reach
                    saves = int(ins_data.get("saved", 0) or 0)
                    shares = int(ins_data.get("shares", 0) or 0)

                    wt_ms = ins_data.get("ig_reels_avg_watch_time", 0)
                    if wt_ms and int(wt_ms) > 0:
                        avg_watch_time = f"{round(int(wt_ms) / 1000.0, 1)}s"
                else:
                    # Fallback cho bài đăng thường (Photo / Carousel / Video cũ)
                    r_ins_fb = requests.get(
                        f"https://graph.facebook.com/v19.0/{vid}/insights",
                        params={"metric": "impressions,reach,saved", "access_token": tok},
                        timeout=5
                    )
                    if r_ins_fb.status_code == 200:
                        for metric in r_ins_fb.json().get("data", []):
                            m_name = metric.get("name")
                            m_val = int(metric.get("values", [{}])[0].get("value", 0) or 0)
                            if m_name in ["impressions", "reach"] and views == 0:
                                views = m_val
                            if m_name == "reach":
                                reach = m_val
                            elif m_name == "saved":
                                saves = m_val
            except Exception:
                pass

            # Xác định nguồn đăng (API vs Trực tiếp)
            is_in_reg = (vid in api_reg) or (permalink in api_reg)
            has_aff_sig = any(p in caption for p in ["s.shopee.vn", "🛒 Link mua", "Link xem và mua hàng", "chính hãng", "dưới bio", "mua tại bio", "👉 Mua"])
            is_api = is_in_reg or has_aff_sig

            source_label = "API" if is_api else "Trực tiếp"
            source_detail = "Instagram Graph API (Tool)" if is_api else "Instagram App / Meta Business Suite"
            source_app = "Instagram API" if is_api else "Instagram App"

            # Đếm số comment của người khác (loại trừ tài khoản Instagram của kênh) & thu thập text comment để check link affiliate
            other_comments = 0
            comment_texts = [caption]
            if comments > 0:
                try:
                    r_c = requests.get(
                        f"https://graph.facebook.com/v19.0/{vid}/comments",
                        params={"fields": "id,from,username,text", "access_token": tok, "limit": 30},
                        timeout=5
                    )
                    if r_c.status_code == 200:
                        for c_item in r_c.json().get("data", []):
                            c_txt = c_item.get("text", "")
                            if c_txt:
                                comment_texts.append(c_txt)
                            c_from_id = str(c_item.get("from", {}).get("id", ""))
                            if c_from_id and c_from_id != str(ig_id):
                                other_comments += 1
                            elif not c_from_id:
                                other_comments += 1
                except Exception:
                    other_comments = 0

            # Kiểm tra trạng thái liên kết affiliate trong caption / comment
            aff_health = check_texts_for_affiliate_health(comment_texts)

            publish_source = "API" if is_api else "MANUAL"

            videos.append({
                "id": vid,
                "platform": "Instagram",
                "title": title,
                "description": caption,
                "published_at": format_datetime_vn(ts),
                "views": views,
                "reach": reach,
                "saves": saves,
                "shares": shares,
                "likes": likes,
                "comments": comments,
                "other_comments_count": other_comments,
                "intent_comments_count": other_comments,
                "affiliate_links_health": aff_health,
                "subscribers_gained": max(1, round(views * (0.0015 + (likes / max(views, 1) * 0.012)))) if views >= 30 else (1 if likes > 0 else 0),
                "avg_watch_time": avg_watch_time,
                "duration_seconds": 0,
                "duration_fmt": "-",
                "url": permalink,
                "thumbnail": thumb,
                "published_at_raw": ts,
                "publish_source": publish_source,
                "upload_source": "api" if is_api else "native",
                "upload_source_label": source_label,
                "upload_source_detail": source_detail,
                "upload_source_app": source_app
            })
        videos.sort(key=parse_video_sort_key, reverse=True)
        return {"success": True, "videos": videos}
    except Exception as e:
        return {"success": False, "error": str(e), "videos": []}

def fetch_inbox_messages(brand_key, brand_cfg):
    """
    Quét hộp thư tin nhắn riêng (DM/Inbox) trên Facebook Messenger và Instagram Direct.
    Xác định các cuộc trò chuyện mà khách nhắn tin nhưng kênh CHƯA phản hồi (unreplied).
    Lưu ý: Threads API hiện tại chưa hỗ trợ endpoint đọc tin nhắn riêng (DM).
    """
    fb_cfg = brand_cfg.get("facebook", {})
    page_id = fb_cfg.get("page_id")
    tok = fb_cfg.get("access_token")
    b_name = brand_cfg.get("name", brand_key)

    inbox_res = {
        "total_conversations": 0,
        "unread_count": 0,
        "unreplied_count": 0,
        "unreplied_messages": [],
        "threads_note": "Threads API của Meta hiện chưa cung cấp endpoint tin nhắn riêng (DM)."
    }

    if not page_id or not tok:
        return inbox_res

    url_conv = f"https://graph.facebook.com/v19.0/{page_id}/conversations"

    # 1. Quét Facebook Page Inbox
    try:
        r_fb = requests.get(
            url_conv,
            params={
                "access_token": tok,
                "fields": "id,unread_count,updated_time,participants,messages.limit(3){id,message,from,created_time}"
            },
            timeout=8
        )
        if r_fb.status_code == 200:
            fb_convs = r_fb.json().get("data", [])
            inbox_res["total_conversations"] += len(fb_convs)
            for c in fb_convs:
                unread = int(c.get("unread_count", 0))
                inbox_res["unread_count"] += unread
                msgs = c.get("messages", {}).get("data", [])
                if msgs:
                    last_msg = msgs[0]
                    sender_id = last_msg.get("from", {}).get("id")
                    sender_name = last_msg.get("from", {}).get("name", "Khách hàng Facebook")
                    # Nếu tin nhắn cuối cùng gửi đến không phải từ chính Fanpage -> Chưa rep!
                    if sender_id and str(sender_id) != str(page_id):
                        inbox_res["unreplied_count"] += 1
                        inbox_res["unreplied_messages"].append({
                            "platform": "Facebook",
                            "conversation_id": c.get("id"),
                            "sender_name": sender_name,
                            "sender_id": sender_id,
                            "last_message": last_msg.get("message", "(Tin nhắn đa phương tiện / hình ảnh)"),
                            "created_time": format_datetime_vn(last_msg.get("created_time", "")),
                            "unread": unread > 0,
                            "chat_link": f"https://business.facebook.com/latest/inbox/all?asset_id={page_id}&nav_ref=bm_message_inbox"
                        })
    except Exception as e:
        print(f"⚠️ Lỗi đọc FB inbox ({brand_key}): {e}")

    # 2. Quét Instagram Direct qua Page
    try:
        r_ig = requests.get(
            url_conv,
            params={
                "access_token": tok,
                "platform": "instagram",
                "fields": "id,unread_count,updated_time,participants,messages.limit(3){id,message,from,created_time}"
            },
            timeout=8
        )
        if r_ig.status_code == 200:
            ig_convs = r_ig.json().get("data", [])
            inbox_res["total_conversations"] += len(ig_convs)
            for c in ig_convs:
                unread = int(c.get("unread_count", 0))
                inbox_res["unread_count"] += unread
                msgs = c.get("messages", {}).get("data", [])
                if msgs:
                    last_msg = msgs[0]
                    sender_id = last_msg.get("from", {}).get("id")
                    sender_name = last_msg.get("from", {}).get("name") or last_msg.get("from", {}).get("username", "Khách hàng Instagram")
                    if sender_id and str(sender_id) != str(page_id):
                        inbox_res["unreplied_count"] += 1
                        inbox_res["unreplied_messages"].append({
                            "platform": "Instagram",
                            "conversation_id": c.get("id"),
                            "sender_name": sender_name,
                            "sender_id": sender_id,
                            "last_message": last_msg.get("message", "(Tin nhắn đa phương tiện / hình ảnh)"),
                            "created_time": format_datetime_vn(last_msg.get("created_time", "")),
                            "unread": unread > 0,
                            "chat_link": f"https://business.facebook.com/latest/inbox/instagram?asset_id={page_id}&nav_ref=bm_message_inbox"
                        })
    except Exception as e:
        print(f"⚠️ Lỗi đọc IG inbox ({brand_key}): {e}")

    return inbox_res

def fetch_single_channel_data(b_key, b_cfg, selected_platform=None, limit=None):
    """Quét dữ liệu đầy đủ cho 1 kênh (brand) qua các nền tảng và hộp thư."""
    b_name = b_cfg.get("name", b_key)
    sel_p = selected_platform.strip().lower() if selected_platform and isinstance(selected_platform, str) else None
    ch_data = {
        "name": b_name,
        "folder": b_cfg.get("folder", ""),
        "platforms": {},
        "inbox": fetch_inbox_messages(b_key, b_cfg)
    }

    # 1. YouTube
    if not sel_p or sel_p == "youtube":
        ch_data["platforms"]["youtube"] = fetch_youtube_videos(b_key, b_cfg, max_results=limit)

    # 2. Threads
    if not sel_p or sel_p == "threads":
        ch_data["platforms"]["threads"] = fetch_threads_videos(b_key, b_cfg, max_results=limit)

    # 3. Facebook
    if not sel_p or sel_p == "facebook":
        ch_data["platforms"]["facebook"] = fetch_facebook_videos(b_key, b_cfg, max_results=limit)

    # 4. Instagram
    if not sel_p or sel_p == "instagram":
        ch_data["platforms"]["instagram"] = fetch_instagram_videos(b_key, b_cfg, max_results=limit)

    # 5. Đối soát video trùng / thiếu trên các nền tảng dựa trên thời lượng (Duration Match +-1s)
    try:
        # Nếu chỉ quét riêng lẻ 1 nền tảng (ví dụ chỉ Facebook), kết hợp với dữ liệu các nền tảng còn lại từ cache (nếu có)
        # để đảm bảo thuật toán đối soát luôn có YouTube để so khớp và lấy Thumbnail!
        platforms_for_sync = dict(ch_data["platforms"])
        if sel_p:
            cached_all = load_cached_analytics()
            if cached_all and isinstance(cached_all, dict) and "data" in cached_all:
                cached_brand = cached_all["data"].get(b_key, {})
                cached_plats = cached_brand.get("platforms", {})
                for other_p, other_data in cached_plats.items():
                    if other_p not in platforms_for_sync and other_p != sel_p:
                        platforms_for_sync[other_p] = other_data

        ch_data["cross_platform_sync"] = analyze_cross_platform_videos(platforms_for_sync)
    except Exception as e_sync:
        print(f"⚠️ Lỗi analyze_cross_platform_videos ({b_key}): {e_sync}")
        ch_data["cross_platform_sync"] = {
            "total_unique_videos": 0,
            "synced_across_platforms_count": 0,
            "missing_posts_count": 0,
            "clusters": []
        }
    return b_key, ch_data

def fetch_all_channels_data(brands_dict, selected_brand=None, selected_platform=None, limit=None):
    results = {}
    sel_b = selected_brand.strip().lower() if selected_brand and isinstance(selected_brand, str) else None

    target_brands = {}
    if sel_b:
        for k, v in brands_dict.items():
            if k.lower() == sel_b:
                target_brands[k] = v
                break
    else:
        target_brands = brands_dict

    # Chạy đa luồng song song cho các kênh (tối đa 6 workers) để tốc độ nhanh gấp 4 - 6 lần
    max_workers = min(len(target_brands), 6) if target_brands else 1
    if max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(fetch_single_channel_data, b_k, b_c, selected_platform, limit)
                for b_k, b_c in target_brands.items()
            ]
            for fut in as_completed(futures):
                try:
                    b_k, ch_d = fut.result()
                    results[b_k] = ch_d
                except Exception as e_fut:
                    print(f"⚠️ Lỗi fetch luồng kênh: {e_fut}")
    else:
        for b_k, b_c in target_brands.items():
            try:
                b_k, ch_d = fetch_single_channel_data(b_k, b_c, selected_platform, limit)
                results[b_k] = ch_d
            except Exception as e_seq:
                print(f"⚠️ Lỗi fetch kênh {b_k}: {e_seq}")

    return results

# ─────────────────────────────────────────────────────────────
# BACKGROUND ANALYTICS CACHE (INSTANT DASHBOARD LOADING)
# ─────────────────────────────────────────────────────────────
ANALYTICS_CACHE_FILE = os.path.join(POST_DIR, "config", "analytics_cache.json")

def load_cached_analytics():
    """Đọc dữ liệu thống kê từ file cache cục bộ (phản hồi tức thì <0.05s)."""
    if not os.path.exists(ANALYTICS_CACHE_FILE):
        return None
    try:
        with open(ANALYTICS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Lỗi đọc analytics cache: {e}")
        return None

def save_cached_analytics(data, duration_sec=0):
    """Ghi đè dữ liệu thống kê vào file cache cục bộ kèm mốc thời gian."""
    try:
        # Luôn enrich optimize_count từ file optimized_flop_videos.json trước khi lưu
        try:
            opt_cache = _load_optimized_videos()
            if opt_cache and isinstance(data, dict):
                for b_k, b_v in data.items():
                    if not isinstance(b_v, dict): continue
                    for p_k, p_v in b_v.get("platforms", {}).items():
                        if not isinstance(p_v, dict): continue
                        for vid_item in p_v.get("videos", []):
                            v_id_str = str(vid_item.get("id", "")).strip()
                            if v_id_str in opt_cache:
                                opt_rec = opt_cache[v_id_str]
                                vid_item["optimize_count"] = opt_rec.get("optimize_count", 0)
                                vid_item["last_optimized_at"] = opt_rec.get("last_optimized_at", "")
                                if opt_rec.get("last_title"):
                                    vid_item["title"] = opt_rec["last_title"]
        except Exception as e_opt_enrich_cache:
            print(f"⚠️ Lỗi enrich optimize_count trong save_cached_analytics: {e_opt_enrich_cache}")
        os.makedirs(os.path.dirname(ANALYTICS_CACHE_FILE), exist_ok=True)
        now_dt = datetime.now()
        payload = {
            "cached_at": now_dt.strftime("%H:%M:%S %d/%m/%Y"),
            "cached_timestamp": now_dt.timestamp(),
            "refresh_duration_seconds": round(duration_sec, 2),
            "data": data
        }
        with open(ANALYTICS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return payload
    except Exception as e:
        print(f"⚠️ Lỗi lưu analytics cache: {e}")
        return None

def refresh_analytics_cache_job(brands_dict, limit=None):
    """Tác vụ ngầm quét toàn bộ các kênh và lưu vào file cache."""
    import time
    start_t = time.time()
    print(f"🔄 [Cache Worker] Bắt đầu tự động quét và làm mới số liệu toàn bộ kênh...")
    fresh_data = fetch_all_channels_data(brands_dict, limit=limit)
    elapsed = time.time() - start_t
    saved = save_cached_analytics(fresh_data, duration_sec=elapsed)
    print(f"✅ [Cache Worker] Đã cập nhật cache thành công trong {elapsed:.1f}s! ({len(fresh_data)} kênh)")
    return saved

# ─────────────────────────────────────────────────────────────
# UPDATE VIDEO METADATA (YOUTUBE, FACEBOOK, INSTAGRAM)
# ─────────────────────────────────────────────────────────────
def update_youtube_video(brand_cfg, video_id, title=None, description=None, thumbnail_path=None):
    yt_conf = brand_cfg.get("youtube", {})
    tok_file = yt_conf.get("token_file")
    if not tok_file:
        return {"success": False, "message": "Chưa cấu hình YouTube token"}
    tok_path = os.path.join(POST_DIR, tok_file) if not os.path.isabs(tok_file) else tok_file
    if not os.path.exists(tok_path):
        return {"success": False, "message": f"Không tìm thấy file token: {tok_file}"}
    try:
        creds = Credentials.from_authorized_user_file(tok_path)
        if creds and (creds.expired or not creds.valid) and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(tok_path, "w", encoding="utf-8") as tf:
                    tf.write(creds.to_json())
            except Exception as e_rf:
                print(f"⚠️ [fetch_analytics update_youtube_video] Lỗi refresh token: {e_rf}")
        youtube = build("youtube", "v3", credentials=creds)

        # 1. Update snippet (title, description)
        if title is not None or description is not None:
            v_get = youtube.videos().list(id=video_id, part="snippet").execute()
            items = v_get.get("items", [])
            if not items:
                return {"success": False, "message": "Không tìm thấy video trên YouTube"}
            snippet = items[0]["snippet"]
            if title is not None and title.strip():
                snippet["title"] = title.strip()
            if description is not None:
                snippet["description"] = description
            youtube.videos().update(
                part="snippet",
                body={"id": video_id, "snippet": snippet}
            ).execute()

        # 2. Update thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            from googleapiclient.http import MediaFileUpload
            media_body = MediaFileUpload(thumbnail_path, mimetype="image/jpeg", resumable=True)
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=media_body
            ).execute()

        return {"success": True, "message": "Cập nhật video YouTube thành công!"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi cập nhật YouTube: {str(e)}"}

def update_facebook_video(brand_cfg, video_id, title=None, description=None, thumbnail_path=None):
    fb_cfg = brand_cfg.get("facebook", {})
    tok = fb_cfg.get("access_token")
    if not tok:
        return {"success": False, "message": "Chưa cấu hình Facebook access_token"}

    try:
        data = {}
        if title is not None and title.strip():
            data["title"] = title.strip()
        if description is not None:
            data["description"] = description

        # 1. Update text metadata
        if data:
            r = requests.post(
                f"https://graph.facebook.com/v19.0/{video_id}",
                data={**data, "access_token": tok},
                timeout=15
            )
            res_json = r.json()
            if not res_json.get("success", False) and "error" in res_json:
                return {"success": False, "message": res_json.get("error", {}).get("message", "Lỗi update FB video")}

        # 2. Update thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, "rb") as thumb_f:
                r_thumb = requests.post(
                    f"https://graph.facebook.com/v19.0/{video_id}/thumbnails",
                    data={"access_token": tok, "is_preferred": "true"},
                    files={"source": thumb_f},
                    timeout=20
                )
                res_th = r_thumb.json()
                if "error" in res_th:
                    return {"success": False, "message": f"Đã đổi text, nhưng lỗi đổi thumbnail FB: {res_th.get('error', {}).get('message')}"}

        return {"success": True, "message": "Cập nhật video Facebook thành công!"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi cập nhật Facebook: {str(e)}"}

def get_best_youtube_thumbnail_bytes(yt_video_id):
    """
    Trích xuất thumbnail nét và đúng tỷ lệ dọc 9:16 (sardefault.jpg 768x1365) của YouTube Shorts
    hoặc maxresdefault.jpg (1280x720) cho video ngang.
    Chấp nhận cả URL đầy đủ (ví dụ https://www.youtube.com/shorts/c9YfAEeS_UU) hoặc Video ID thô.
    """
    if not yt_video_id:
        return None, "", "image/jpeg"

    # Trích xuất 11 ký tự Video ID sạch
    raw_str = str(yt_video_id).strip()
    m_id = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/vi\/)?([a-zA-Z0-9_-]{11})', raw_str)
    vid = m_id.group(1) if m_id else raw_str

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # 1. Thử trực tiếp các URL tĩnh chất lượng cao từ CDN YouTube (cực nhanh, không lo bị chặn HTML)
    static_candidates = [
        f"https://i.ytimg.com/vi/{vid}/sardefault.jpg",    # Shorts dọc 9:16 nét nhất (768x1365)
        f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", # HD 1280x720
        f"https://i.ytimg.com/vi/{vid}/sddefault.jpg",     # 640x480
        f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",     # 480x360
        f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg",     # 320x180
    ]
    for u in static_candidates:
        try:
            r = requests.get(u, headers=headers, timeout=4)
            # YouTube CDN trả về ảnh rỗng ~1097 bytes khi ảnh không tồn tại
            if r.status_code == 200 and len(r.content) > 2000:
                ct = r.headers.get("Content-Type", "image/jpeg").lower()
                mime = "image/jpeg" if ("jpeg" in ct or "jpg" in ct) else "image/png"
                return r.content, u, mime
        except Exception:
            continue

    # 2. Fallback: Quét HTML trang Shorts nếu link tĩnh có chữ ký bảo vệ (token/sqp)
    shorts_url = f"https://www.youtube.com/shorts/{vid}"
    try:
        import html as _html
        r_page = requests.get(shorts_url, headers=headers, timeout=5)
        if r_page.status_code == 200:
            page_html = r_page.text
            matches = re.findall(r'(https://[^\s"\'\\<>]*(?:ytimg\.com|ggpht\.com)[^\s"\'\\<>]*sardefault\.jpg[^\s"\'\\<>]*)', page_html)
            for m in matches:
                clean_url = _html.unescape(m).replace("&amp;", "&")
                try:
                    r_img = requests.get(clean_url, headers=headers, timeout=5)
                    if r_img.status_code == 200 and len(r_img.content) > 15000:
                        return r_img.content, clean_url, "image/jpeg"
                except Exception:
                    continue

            og_match = re.search(r'<meta property="og:image" content="([^"]+)"', page_html)
            if og_match:
                og_url = _html.unescape(og_match.group(1)).replace("&amp;", "&")
                try:
                    r_og = requests.get(og_url, headers=headers, timeout=5)
                    if r_og.status_code == 200 and len(r_og.content) > 5000:
                        return r_og.content, og_url, "image/jpeg"
                except Exception:
                    pass
    except Exception as e:
        print(f"⚠️ Lỗi quét Shorts page fallback ({vid}): {e}")

    return None, "", "image/jpeg"

def sync_youtube_thumbnail_to_facebook(brand_cfg, fb_video_id, yt_video_id):
    """
    Tải thumbnail chất lượng cao từ YouTube và cập nhật sang video Facebook qua Graph API (1-Click).
    Ưu tiên lấy ảnh dọc sắc nét sardefault.jpg (768x1365) của YouTube Shorts,
    fallback sang maxresdefault.jpg.
    """
    fb_cfg = brand_cfg.get("facebook", {})
    tok = fb_cfg.get("access_token")
    if not tok:
        return {"success": False, "message": "Chưa cấu hình Facebook access_token"}

    img_bytes, selected_url, content_type = get_best_youtube_thumbnail_bytes(yt_video_id)

    if not img_bytes:
        return {"success": False, "message": f"Không thể tải thumbnail từ YouTube ({yt_video_id})"}

    import tempfile
    temp_thumb_path = None
    try:
        # 1. Tải thumbnail về file vật lý tạm trên máy tính
        ext = ".jpg" if "jpeg" in (content_type or "") or "jpg" in (content_type or "") else ".png"
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tf.write(img_bytes)
        tf.close()
        temp_thumb_path = tf.name

        # 2. Upload thẳng file ảnh vật lý từ máy lên Facebook Graph API /thumbnails
        with open(temp_thumb_path, "rb") as f_thumb:
            files = {
                "source": (os.path.basename(temp_thumb_path), f_thumb, content_type or "image/jpeg")
            }
            data = {
                "access_token": tok,
                "is_preferred": "true"
            }
            
            # Thử với video ID gốc hoặc clean ID (bỏ tiền tố page_ nếu có)
            target_ids = [str(fb_video_id).strip()]
            if "_" in str(fb_video_id):
                target_ids.append(str(fb_video_id).split("_")[-1])

            res_th = None
            last_err = ""
            for vid_target in target_ids:
                f_thumb.seek(0)
                try:
                    r_fb = requests.post(
                        f"https://graph.facebook.com/v19.0/{vid_target}/thumbnails",
                        data=data,
                        files=files,
                        timeout=25
                    )
                    res_th = r_fb.json()
                    if "error" not in res_th:
                        break
                    else:
                        last_err = res_th.get("error", {}).get("message", "Lỗi Meta API")
                except Exception as _e_req:
                    last_err = str(_e_req)

            if res_th and "error" in res_th:
                m_id = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/vi\/)?([a-zA-Z0-9_-]{11})', yt_video_id)
                clean_id = m_id.group(1) if m_id else yt_video_id
                return {
                    "success": False,
                    "message": f"Facebook từ chối cập nhật thumbnail: {last_err}",
                    "youtube_thumb_url": selected_url,
                    "download_url": f"/api/video/download-yt-thumbnail?yt_video_id={clean_id}"
                }

        # Lưu lại trạng thái đã đồng bộ thumbnail
        record_synced_thumbnail(fb_video_id, yt_video_id, selected_url)

        m_id = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/vi\/)?([a-zA-Z0-9_-]{11})', yt_video_id)
        clean_id = m_id.group(1) if m_id else yt_video_id

        return {
            "success": True,
            "message": "Đã tải thumbnail về máy và cập nhật lên video Facebook thành công!",
            "youtube_thumb_url": selected_url,
            "download_url": f"/api/video/download-yt-thumbnail?yt_video_id={clean_id}"
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi xử lý file thumbnail hoặc gọi Meta API: {str(e)}"}
    finally:
        if temp_thumb_path and os.path.exists(temp_thumb_path):
            try:
                os.remove(temp_thumb_path)
            except Exception:
                pass

def update_instagram_post(brand_cfg, media_id, caption=None, comment_text=None):
    """
    Instagram Graph API:
    - Không hỗ trợ đổi thumbnail của Reel đã đăng.
    - Không hỗ trợ sửa caption qua API công khai (chỉ xem và xoá).
    - HỖ TRỢ: Đăng thêm comment / ghim link affiliate vào phần bình luận!
    """
    ig_cfg = brand_cfg.get("instagram", {})
    tok = ig_cfg.get("access_token")
    if not tok:
        return {"success": False, "message": "Chưa cấu hình Instagram access_token"}

    try:
        if comment_text and comment_text.strip():
            # Thêm bình luận vào bài Reel Instagram
            r = requests.post(
                f"https://graph.facebook.com/v19.0/{media_id}/comments",
                data={"message": comment_text.strip(), "access_token": tok},
                timeout=15
            )
            rj = r.json()
            if "id" in rj:
                return {"success": True, "message": "Đã thêm bình luận mới vào Instagram Reel thành công!"}
            else:
                return {"success": False, "message": rj.get("error", {}).get("message", "Lỗi gửi comment Instagram")}
        else:
            return {
                "success": False,
                "message": "Instagram Graph API chính thức của Meta không cho phép bên thứ 3 sửa Caption/Thumbnail video đã đăng. Bạn có thể sử dụng chức năng Đăng Bình Luận / Link để ghim tương tác!"
            }
    except Exception as e:
        return {"success": False, "message": f"Lỗi Instagram: {str(e)}"}

if __name__ == "__main__":
    with open(os.path.join(POST_DIR, "config", "brands.json"), encoding="utf-8") as f:
        brands = json.load(f)
    print("Testing fetch for noi_that_dung_that...")
    res = fetch_all_channels_data(brands, selected_brand="noi_that_dung_that", limit=3)
    print(json.dumps(res, ensure_ascii=False, indent=2))

