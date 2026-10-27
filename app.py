import os

import sys

import time

import json

import uuid

import csv

import re

import random

import threading

import requests

import openpyxl

from datetime import datetime, timezone, timedelta

from google.oauth2.credentials import Credentials

from google.auth.transport.requests import Request

from flask import Flask, render_template, request, jsonify, send_file

from collections import OrderedDict



sys.stdout.reconfigure(encoding="utf-8", errors="replace")



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_parent_cand = os.path.dirname(BASE_DIR.rstrip("/\\"))
if os.path.exists(os.path.join(_parent_cand, "Affiliate")):
    AFFILIATE_ROOT = os.path.join(_parent_cand, "Affiliate")
else:
    AFFILIATE_ROOT = _parent_cand

POST_DIR = os.path.join(BASE_DIR, "POST")

sys.path.insert(0, POST_DIR)



from uploaders.facebook_uploader import FacebookReelsUploader

from uploaders.threads_uploader import ThreadsAPIUploader

from uploaders.youtube_uploader import YouTubeShortsUploader

from fetch_analytics import (

    record_video_optimization,

    get_video_optimization_info,

    _load_optimized_videos,

    fetch_all_channels_data,

    update_youtube_video,

    update_facebook_video,

    update_instagram_post,

    record_api_published_video,

    load_cached_analytics,

    save_cached_analytics,

    refresh_analytics_cache_job,

    sync_youtube_thumbnail_to_facebook,

    get_best_youtube_thumbnail_bytes

)



from advanced_analytics import (

    enrich_video_metrics, calculate_ad_score, analyze_intent_comments,

    get_publish_source_comparison, get_channel_audience_analytics

)





app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

app.config['TEMPLATES_AUTO_RELOAD'] = True



# Lưu tiến trình tất cả tác vụ (hỗ trợ nhiều task song song & lưu bền vững ra đĩa)

tasks = OrderedDict()

cancelled_tasks = set()

MAX_TASKS_HISTORY = 1000  # Giữ lại tối đa 1000 task gần nhất

TASKS_STORAGE_PATH = os.path.join(POST_DIR, "config", "upload_tasks_history.json")



def load_persisted_tasks():

    global tasks

    if os.path.exists(TASKS_STORAGE_PATH):

        try:

            with open(TASKS_STORAGE_PATH, "r", encoding="utf-8") as f:

                data = json.load(f)

                for k, v in data.items():

                    # Tự động chuẩn hóa link Instagram nếu còn ở dạng "Media ID: ..."

                    res = v.get("results")

                    if isinstance(res, dict) and "Instagram" in res:

                        ig_val = str(res.get("Instagram") or "").strip()

                        if "Media ID:" in ig_val or (ig_val.isdigit() and len(ig_val) >= 10):

                            m = re.search(r'(\d{10,})', ig_val)

                            if m:

                                res["Instagram"] = f"https://www.instagram.com/reel/{m.group(1)}/"

                    tasks[k] = v

        except Exception as e:

            print(f"⚠️ Không thể đọc {TASKS_STORAGE_PATH}: {e}")



def save_persisted_tasks():

    try:

        os.makedirs(os.path.dirname(TASKS_STORAGE_PATH), exist_ok=True)

        with open(TASKS_STORAGE_PATH, "w", encoding="utf-8") as f:

            # Chỉ lưu 50 task mới nhất

            items = list(tasks.items())[-MAX_TASKS_HISTORY:]

            json.dump(dict(items), f, ensure_ascii=False, indent=2)

    except Exception as e:

        print(f"⚠️ Không thể lưu {TASKS_STORAGE_PATH}: {e}")



load_persisted_tasks()



def inject_task_into_analytics_cache(task):

    """

    Tự động đồng bộ ngay lập tức video vừa đăng thành công vào analytics_cache.json

    để người dùng mở tab Thống kê là thấy ngay lập tức mà không cần chờ quét ngầm.

    """

    if not task:

        return

    brand_key = task.get("brand_key")

    if not brand_key:

        return

    results = task.get("results", {})

    if not results:

        return



    try:

        from fetch_analytics import load_cached_analytics, save_cached_analytics, parse_video_sort_key

        cached_obj = load_cached_analytics()

        if not cached_obj or not isinstance(cached_obj, dict) or "data" not in cached_obj:

            return



        cache_data = cached_obj["data"]

        if brand_key not in cache_data:

            return



        brand_data = cache_data[brand_key]

        platforms = brand_data.setdefault("platforms", {})

        now_dt = datetime.now()

        now_str = now_dt.strftime("%H:%M %d/%m/%Y")

        now_iso = now_dt.isoformat()

        title = task.get("title") or task.get("params", {}).get("title") or task.get("video_name") or "Video mới đăng"

        caption = task.get("caption") or task.get("params", {}).get("caption") or ""



        # 1. YouTube

        yt_res = results.get("YouTube", "")

        if yt_res and ("youtube.com" in yt_res or "youtu.be" in yt_res or len(yt_res.strip()) == 11):

            m = re.search(r'(?:shorts/|v=|be/)?([a-zA-Z0-9_-]{11})', yt_res)

            yt_id = m.group(1) if m else yt_res.strip()

            yt_plat = platforms.setdefault("youtube", {"success": True, "videos": []})

            vids = yt_plat.setdefault("videos", [])

            if not any(v.get("id") == yt_id for v in vids):

                vids.insert(0, {

                    "id": yt_id,

                    "platform": "YouTube",

                    "title": title + (" #Shorts" if "#shorts" not in title.lower() else ""),

                    "description": caption,

                    "published_at": now_str,

                    "published_at_raw": now_iso,

                    "views": 0,

                    "likes": 0,

                    "comments": 0,

                    "other_comments_count": 0,

                    "intent_comments_count": 0,

                    "subscribers_gained": "Theo kênh",

                    "avg_watch_time": "-",

                    "duration_seconds": 0,

                    "duration_fmt": "-",

                    "url": f"https://youtube.com/shorts/{yt_id}",

                    "thumbnail": f"https://i.ytimg.com/vi/{yt_id}/hqdefault.jpg",

                    "publish_source": "API",

                    "upload_source": "api",

                    "upload_source_label": "API",

                    "upload_source_detail": "YouTube Data API (Tool)",

                    "upload_source_app": "Google YouTube API",

                    "privacy_status": "public",

                    "upload_status": "processed",

                    "is_short": True,

                    "status": "published"

                })



        # 2. Facebook

        fb_res = results.get("Facebook", "")

        if fb_res and ("facebook.com" in fb_res or fb_res.isdigit()):

            m = re.search(r'(\d+)', fb_res)

            fb_id = m.group(1) if m else fb_res.strip()

            fb_plat = platforms.setdefault("facebook", {"success": True, "videos": []})

            vids = fb_plat.setdefault("videos", [])

            if not any(v.get("id") == fb_id for v in vids):

                vids.insert(0, {

                    "id": fb_id,

                    "platform": "Facebook",

                    "title": title,

                    "description": caption,

                    "published_at": now_str,

                    "published_at_raw": now_iso,

                    "views": 0,

                    "likes": 0,

                    "comments": 0,

                    "other_comments_count": 0,

                    "intent_comments_count": 0,

                    "subscribers_gained": "-",

                    "avg_watch_time": "-",

                    "duration_seconds": 0,

                    "duration_fmt": "-",

                    "url": fb_res if fb_res.startswith("http") else f"https://www.facebook.com/reel/{fb_id}",

                    "thumbnail": "",

                    "publish_source": "API",

                    "upload_source": "api",

                    "upload_source_label": "API",

                    "upload_source_detail": "Facebook Graph API (Tool)",

                    "upload_source_app": "Facebook API",

                    "status": "published"

                })



        # 3. Instagram

        ig_res = results.get("Instagram", "")

        if ig_res and ("instagram.com" in ig_res or "Media ID:" in ig_res or ig_res.isdigit()):

            m = re.search(r'(\d+)', ig_res)

            ig_id = m.group(1) if m else ig_res.strip()

            ig_url = ig_res if ig_res.startswith("http") else f"https://www.instagram.com/reel/{ig_id}/"

            ig_plat = platforms.setdefault("instagram", {"success": True, "videos": []})

            vids = ig_plat.setdefault("videos", [])

            if not any(v.get("id") == ig_id or v.get("url") == ig_url for v in vids):

                vids.insert(0, {

                    "id": ig_id,

                    "platform": "Instagram",

                    "title": title,

                    "description": caption,

                    "published_at": now_str,

                    "published_at_raw": now_iso,

                    "views": 0,

                    "likes": 0,

                    "comments": 0,

                    "other_comments_count": 0,

                    "intent_comments_count": 0,

                    "subscribers_gained": "-",

                    "avg_watch_time": "-",

                    "duration_seconds": 0,

                    "duration_fmt": "-",

                    "url": f"https://www.instagram.com/reel/{ig_id}/",

                    "thumbnail": "",

                    "publish_source": "API",

                    "upload_source": "api",

                    "upload_source_label": "API",

                    "upload_source_detail": "Instagram Graph API (Tool)",

                    "upload_source_app": "Instagram API",

                    "status": "published"

                })



        # 4. Threads

        th_res = results.get("Threads", "")

        if th_res and ("threads" in th_res or th_res.isdigit()):

            m = re.search(r'post/([a-zA-Z0-9_-]+)', th_res)

            th_id = m.group(1) if m else th_res.strip()

            th_plat = platforms.setdefault("threads", {"success": True, "videos": []})

            vids = th_plat.setdefault("videos", [])

            if not any(v.get("id") == th_id or v.get("url") == th_res for v in vids):

                vids.insert(0, {

                    "id": th_id,

                    "platform": "Threads",

                    "title": title,

                    "description": caption,

                    "published_at": now_str,

                    "published_at_raw": now_iso,

                    "views": 0,

                    "likes": 0,

                    "comments": 0,

                    "other_comments_count": 0,

                    "intent_comments_count": 0,

                    "subscribers_gained": "-",

                    "avg_watch_time": "-",

                    "duration_seconds": 0,

                    "duration_fmt": "-",

                    "url": th_res if th_res.startswith("http") else f"https://www.threads.net/post/{th_id}",

                    "thumbnail": "",

                    "publish_source": "API",

                    "upload_source": "api",

                    "upload_source_label": "API",

                    "upload_source_detail": "Threads Publishing API",

                    "upload_source_app": "Threads API",

                    "status": "published"

                })



        # Sắp xếp lại các video theo thời gian xuất bản mới nhất lên đầu

        for p_name, p_obj in platforms.items():

            if isinstance(p_obj, dict) and "videos" in p_obj:

                p_obj["videos"].sort(key=parse_video_sort_key, reverse=True)



        save_cached_analytics(cache_data, duration_sec=cached_obj.get("refresh_duration_seconds", 0))

        print(f"⚡ [Analytics Cache] Đã đồng bộ video mới đăng của {brand_key} vào cache tức thì!")

    except Exception as e_inj:

        print(f"⚠️ Lỗi inject_task_into_analytics_cache: {e_inj}")



BRANDS_CONFIG_PATH = os.path.join(POST_DIR, "config", "brands.json")

COMMENT_TXT_PATH = os.path.join(BASE_DIR, "comment.txt")



# BẢNG HASHTAG MẶC ĐỊNH CHO TỪNG KÊNH THEO CHUẨN SEO

BRAND_DEFAULT_HASHTAGS = {

    "noi_that_dung_that": [

        "Nói Thật Dùng Thật", "Noi That Dung That", "review đồ gia dụng", "do gia dung thong minh",

        "đồ gia dụng thông minh", "gia dụng tiện ích", "do dung gia dinh", "test đồ gia dụng",

        "review chân thật", "có nên mua", "trải nghiệm thực tế", "mẹo vặt gia đình",

        "đồ gia dụng shopee", "Shorts", "review gia dụng shorts"

    ],

    "yeu_da_hon_bo": [

        "Yêu Da Hơn Bồ", "Yeu Da Hon Bo", "yeudahonbo", "skincare", "chăm sóc da",

        "cham soc da", "skincare routine", "góc làm đẹp", "da căng bóng", "phục hồi da",

        "chống lão hóa", "dưỡng ẩm", "review mỹ phẩm", "tips làm đẹp", "mỹ phẩm chính hãng",

        "Shorts", "vlog làm đẹp"

    ],

    "review_that_viec_that": [

        "Review Thật Việc Thật", "Review That Viec That", "review đồ gia dụng", "test đồ gia dụng",

        "đồ gia dụng thông minh", "gia dụng tiện ích", "trải nghiệm thực tế", "đánh giá thực tế",

        "đồ dùng gia đình", "shorts", "review", "affiliate", "trending"

    ],

    "dung_roi_moi_noi": [

        "Dùng Rồi Mới Nói", "Dung Roi Moi Noi", "review đồ gia dụng", "test đồ gia dụng",

        "đồ gia dụng thông minh", "gia dụng tiện ích", "đồ dùng thông minh", "trải nghiệm thực tế",

        "đánh giá chân thật", "shorts", "review", "affiliate", "trending"

    ],

    "setup_phong_xinh": [

        "Setup Phòng Xinh", "Setup Phong Xinh", "setup bàn làm việc", "decor phòng ngủ",

        "đồ setup thông minh", "nội thất thông minh", "decor phòng trọ", "góc làm việc đẹp",

        "review đồ decor", "bàn nâng hạ", "shorts", "review", "affiliate", "trending"

    ],

    "cham_da_tiet_kiem": [

        "Chăm Da Tiết Kiệm", "Cham Da Tiet Kiem", "skincare tiết kiệm", "chăm sóc da tiết kiệm",

        "skincare bình dân", "skincare học sinh sinh viên", "mỹ phẩm ngon bổ rẻ",

        "chăm sóc da tại nhà", "review mỹ phẩm", "shorts", "review", "affiliate", "trending"

    ],

    "goc_tap_luyen": [

        "Góc Tập Luyện", "Goc Tap Luyen", "dụng cụ tập gym", "đồ tập thể dục tại nhà",

        "review đồ tập", "giảm cân tại nhà", "dụng cụ đốt mỡ", "thiết bị tập luyện",

        "tập gym tại nhà", "shorts", "review", "affiliate", "trending"

    ],

    "tu_do_mua_moi": [

        "Tủ Đồ Mùa Mới", "Tu Do Mua Moi", "thời trang nữ", "phối đồ nữ", "review quần áo nữ",

        "gợi ý phối đồ", "outfit đẹp", "haul quần áo shopee", "style hàn quốc",

        "shorts", "review", "affiliate", "trending"

    ],

    "cham_cong_nghe": [

        "Trạm Công Nghệ", "Tram Cong Nghe", "đồ công nghệ hữu ích", "phụ kiện công nghệ",

        "review đồ công nghệ", "đồ chơi công nghệ", "thiết bị thông minh", "công nghệ tiện ích",

        "shorts", "review", "affiliate", "trending"

    ],

    "quan_ao_gia_hoi": [

        "Quần Áo Giá Hời", "Quan Ao Gia Hoi", "quần áo nữ giá rẻ", "thời trang nữ giá hời",

        "review quần áo nữ", "haul quần áo shopee", "săn sale quần áo", "phối đồ nữ giá rẻ",

        "shorts", "review", "affiliate", "trending"

    ]

}



def load_brands():

    with open(BRANDS_CONFIG_PATH, "r", encoding="utf-8") as f:

        return json.load(f)



def load_comment_templates():

    if os.path.exists(COMMENT_TXT_PATH):

        with open(COMMENT_TXT_PATH, "r", encoding="utf-8") as f:

            lines = [line.strip() for line in f if line.strip()]

            if lines:

                return lines

    return [

        "Link sản phẩm ở đây cho ai cần nha: ",

        "Link sp mình mua ở đây nhé, mọi người tham khảo nha: ",

        "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",

        "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",

        "Link sản phẩm ở đây: "

    ]



def format_affiliate_comments(products, brand_key, comment_templates=None):

    """

    Tạo nội dung bình luận affiliate theo đúng chuẩn 5 mẫu câu người dùng yêu cầu:

    1. Link sản phẩm ở đây cho ai cần nha: <link>

    2. Link sp mình mua ở đây nhé, mọi người tham khảo nha: <link>

    3. Link săn deal/mua hàng chính hãng ở đây nha cả nhà: <link>

    4. Mình để sẵn link mua hàng ở đây cho mọi người nè: <link>

    5. Link sản phẩm ở đây: <link>

    Nếu có nhiều hơn link sản phẩm thì lặp lại tuần tự theo vòng tròn (idx % len(templates)).

    """

    if not products:

        return []



    if not comment_templates:

        comment_templates = load_comment_templates()



    if not comment_templates:

        comment_templates = [

            "Link sản phẩm ở đây cho ai cần nha: ",

            "Link sp mình mua ở đây nhé, mọi người tham khảo nha: ",

            "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",

            "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",

            "Link sản phẩm ở đây: "

        ]



    # Deduplicate sản phẩm theo link để đảm bảo mỗi link affiliate chỉ xuất hiện đúng 1 lần duy nhất

    seen_links = set()

    unique_products = []

    for p in products:

        raw_lnk = (p.get("link") or "").strip()

        clean_lnk = raw_lnk.rstrip("/?#&").lower()

        if clean_lnk and clean_lnk not in seen_links:

            seen_links.add(clean_lnk)

            unique_products.append(p)

    products = unique_products



    if not products:

        return []



    # Định dạng từng comment riêng biệt tuần tự theo đúng 5 mẫu câu yêu cầu

    comments = []

    seen_cmts = set()

    for idx, p in enumerate(products):

        link = p.get("link", "").strip()

        if not link:

            continue

        prefix = comment_templates[idx % len(comment_templates)].strip()

        if not (prefix.endswith(":") or prefix.endswith(" ") or prefix.endswith("!") or prefix.endswith(".")):

            prefix += ":"

        c_str = f"{prefix} {link}".strip()

        if c_str not in seen_cmts:

            seen_cmts.add(c_str)

            comments.append(c_str)



    return comments



def get_existing_yt_comments(youtube_service, video_id):

    """Lấy danh sách các bình luận và link affiliate đã có trên video YouTube để chống trùng lặp."""

    existing_texts = set()

    existing_links = set()

    if not youtube_service or not video_id:

        return existing_texts, existing_links

    try:

        threads_res = youtube_service.commentThreads().list(

            part="snippet",

            videoId=video_id,

            maxResults=100

        ).execute()

        for item in threads_res.get("items", []):

            top_snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})

            t_text = (top_snippet.get("textOriginal") or top_snippet.get("textDisplay") or "").strip()

            if t_text:

                existing_texts.add(t_text.lower())

                for u in re.findall(r'https?://[^\s<>"]+', t_text):

                    existing_links.add(u.rstrip("/?#&").lower())

    except Exception as _e_list:

        print(f"ℹ️ Không thể đọc comment hiện có trên video YouTube {video_id}: {_e_list}")

    return existing_texts, existing_links



def is_duplicate_yt_comment(comment_text, existing_texts, existing_links):

    """Kiểm tra xem nội dung comment hoặc link affiliate trong comment đã tồn tại trên video chưa."""

    if not comment_text:

        return False

    c_lower = comment_text.strip().lower()

    if c_lower in existing_texts:

        return True

    urls = [u.rstrip("/?#&").lower() for u in re.findall(r'https?://[^\s<>"]+', comment_text)]

    if urls and any(u in existing_links for u in urls):

        return True

    return False



# ──────── PROACTIVE TOKEN REFRESH ────────

YOUTUBE_SCOPES = [

    "https://www.googleapis.com/auth/youtube.upload",

    "https://www.googleapis.com/auth/youtube.force-ssl",

    "https://www.googleapis.com/auth/youtube.readonly"

]

FB_APP_ID = "2678374879231329"

FB_APP_SECRET = "975ca71ab78e1676c5dd4fc356ce337f"



def ensure_valid_tokens(brand_key, platform):

    """

    Proactive Token Refresh: Tự động kiểm tra và làm mới token trước khi upload:

    - YouTube: Kiểm tra expiry hoặc creds.expired. Nếu token hết hạn hoặc còn dưới 24h,

      tự động refresh qua Request() và ghi đè token mới vào file json của brand.

    - Meta (Facebook/Instagram): Kiểm tra token qua GET /debug_token hoặc GET /{id}.

      Nếu token còn dưới 24h hoặc bị invalid, tự động trigger script gia hạn token dài hạn (fb_exchange_token).

    """

    brands = load_brands()

    brand_cfg = brands.get(brand_key, {})

    if not brand_cfg:

        return {"success": False, "message": f"Không tìm thấy brand: {brand_key}"}



    plat = platform.lower().strip()



    # 1. YOUTUBE TOKEN REFRESH

    if plat == "youtube":

        yt_cfg = brand_cfg.get("youtube", {})

        tok_file = yt_cfg.get("token_file")

        if not tok_file:

            return {"success": False, "message": f"Chưa cấu hình YouTube token_file cho kênh {brand_key}"}



        tok_path = os.path.join(POST_DIR, tok_file) if not os.path.isabs(tok_file) else tok_file

        if not os.path.exists(tok_path):

            return {"success": False, "message": f"Không tìm thấy file token YouTube: {tok_path}"}



        try:

            creds = Credentials.from_authorized_user_file(tok_path)

            needs_refresh = False



            # Kiểm tra thời gian hết hạn (expiry)

            if creds.expiry:

                now_utc = datetime.now(timezone.utc)

                exp_dt = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry.tzinfo is None else creds.expiry

                # Nếu hết hạn hoặc còn hiệu lực dưới 24 giờ

                if exp_dt - now_utc < timedelta(hours=24):

                    needs_refresh = True

            elif creds.expired:

                needs_refresh = True



            if needs_refresh or (creds.expired and creds.refresh_token):

                print(f"🔄 [YouTube Token] Token kênh {brand_key} sắp/đã hết hạn (<24h). Đang tự động làm mới...")

                creds.refresh(Request())

                with open(tok_path, "w", encoding="utf-8") as tf:

                    tf.write(creds.to_json())

                print(f"  ✅ [YouTube Token] Đã làm mới token thành công và cập nhật vào {os.path.basename(tok_path)}!")

                return {"success": True, "refreshed": True, "message": "Token YouTube đã được làm mới thành công"}

            return {"success": True, "refreshed": False, "message": "Token YouTube còn hiệu lực"}

        except Exception as e:

            print(f"  ⚠️ [YouTube Token] Lỗi kiểm tra/refresh token cho {brand_key}: {e}")

            return {"success": False, "message": f"Lỗi refresh token YouTube: {e}"}



    # 2. META TOKEN (FACEBOOK / INSTAGRAM)

    elif plat in ["facebook", "instagram"]:

        target_cfg = brand_cfg.get(plat, {})

        cur_token = target_cfg.get("access_token")

        target_id = target_cfg.get("page_id") if plat == "facebook" else target_cfg.get("ig_user_id")



        if not cur_token or not target_id:

            return {"success": False, "message": f"Chưa cấu hình token hoặc ID cho {plat} kênh {brand_key}"}



        try:

            # Kiểm tra thời hạn token qua debug_token hoặc graph API

            debug_url = "https://graph.facebook.com/v19.0/debug_token"

            r_debug = requests.get(debug_url, params={"input_token": cur_token, "access_token": cur_token}, timeout=10)

            token_valid = True

            expires_at = None



            if r_debug.status_code == 200:

                dbg_data = r_debug.json().get("data", {})

                token_valid = dbg_data.get("is_valid", False)

                expires_at = dbg_data.get("expires_at", 0)  # 0 nghĩa là token không bao giờ hết hạn (vĩnh viễn)



            # Nếu token có hạn (expires_at > 0) và còn dưới 24h (hoặc không hợp lệ)

            now_ts = int(time.time())

            if not token_valid or (expires_at and expires_at > 0 and (expires_at - now_ts < 86400)):

                print(f"🔄 [Meta Token] Token {plat} kênh {brand_key} sắp hết hạn (<24h). Đang gia hạn fb_exchange_token...")

                

                # Gọi fb_exchange_token đổi token dài hạn

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

                    # Nếu là Facebook page token, lấy Page Access Token vĩnh viễn qua /me/accounts

                    page_id = brand_cfg.get("facebook", {}).get("page_id")

                    updated_token = new_tok

                    try:

                        r_acc = requests.get(

                            "https://graph.facebook.com/v21.0/me/accounts",

                            params={"access_token": new_tok, "fields": "id,name,access_token", "limit": 100},

                            timeout=20

                        )

                        if r_acc.status_code == 200:

                            for p_acc in r_acc.json().get("data", []):

                                if str(p_acc.get("id")) == str(page_id):

                                    updated_token = p_acc.get("access_token", new_tok)

                                    break

                    except Exception:

                        pass



                    # Cập nhật brands.json

                    brands[brand_key][plat]["access_token"] = updated_token

                    if plat == "facebook" and "instagram" in brands[brand_key]:

                        # Instagram thường dùng chung Page Access Token

                        brands[brand_key]["instagram"]["access_token"] = updated_token



                    with open(BRANDS_CONFIG_PATH, "w", encoding="utf-8") as f:

                        json.dump(brands, f, indent=4, ensure_ascii=False)



                    print(f"  ✅ [Meta Token] Đã gia hạn và cập nhật token cho kênh {brand_key}!")

                    return {"success": True, "refreshed": True, "message": "Token Meta đã được gia hạn"}

                else:

                    print(f"  ⚠️ [Meta Token] Không thể gia hạn token: {ex_data}")

            return {"success": True, "refreshed": False, "message": "Token Meta còn hiệu lực"}

        except Exception as e:

            print(f"  ⚠️ [Meta Token] Lỗi kiểm tra token {plat} cho {brand_key}: {e}")

            return {"success": False, "message": f"Lỗi Meta token check: {e}"}



    return {"success": True, "message": f"Nền tảng {plat} không cần refresh token đặc biệt"}



_SHORT_URL_NAME_CACHE = {}



def extract_product_name_from_url(url):

    """Trích xuất tên sản phẩm từ đường dẫn Shopee gốc nếu file không có cột tên, hỗ trợ tự động giải mã link rút gọn s.shopee.vn/shp.ee"""

    if not url:

        return ""

    if url in _SHORT_URL_NAME_CACHE:

        return _SHORT_URL_NAME_CACHE[url]

    try:

        import urllib.parse

        parsed = urllib.parse.urlparse(url)

        host = (parsed.netloc or "").lower()

        path = parsed.path

        parts = [p for p in path.split('/') if p]



        # 1. Nếu là link rút gọn Shopee (s.shopee.vn, shp.ee), giải mã redirect để lấy URL gốc

        if any(sh in host for sh in ["s.shopee.vn", "shp.ee"]):

            try:

                import urllib.request

                req = urllib.request.Request(

                    url,

                    headers={

                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

                    }

                )

                with urllib.request.urlopen(req, timeout=3.5) as resp:

                    final_url = resp.geturl()

                    if final_url and "shopee.vn" in final_url and final_url != url:

                        parsed_final = urllib.parse.urlparse(final_url)

                        final_parts = [p for p in parsed_final.path.strip("/").split("/") if p]

                        if final_parts:

                            final_slug = final_parts[0]

                            if "-i." in final_slug:

                                final_slug = final_slug.split("-i.")[0]

                            decoded_name = urllib.parse.unquote(final_slug).replace("-", " ").strip()

                            if decoded_name and not decoded_name.startswith("http") and len(decoded_name) > 3:

                                _SHORT_URL_NAME_CACHE[url] = decoded_name

                                return decoded_name

            except Exception as _e_resolve:

                pass



        # 2. Xử lý URL Shopee gốc thông thường

        if parts:

            slug = parts[0]

            if '-i.' in slug:

                slug = slug.split('-i.')[0]

            decoded = urllib.parse.unquote(slug).replace('-', ' ').strip()

            if decoded and not decoded.startswith("http"):

                _SHORT_URL_NAME_CACHE[url] = decoded

                return decoded

    except Exception:

        pass

    return ""



# ─────────────────────────────────────────────────────────────────────────────

# CẤU HÌNH & HELPER SHOPEE BATCH CUSTOM LINKS & NỀN TẢNG

# ─────────────────────────────────────────────────────────────────────────────



# Bảng mapping chuẩn Sub_id3 theo từng kênh

CHANNEL_SUB_ID3 = {

    "noi_that_dung_that": "noithatdungthat",

    "dung_roi_moi_noi": "dungroimoinoi",

    "review_that_viec_that": "reviewthatt",

    "setup_phong_xinh": "setupphongxinh",

    "tu_do_mua_moi": "tudomuamoi",

    "cham_cong_nghe": "tramcongnghe",

    "goc_tap_luyen": "goctapluyen",

    "cham_da_tiet_kiem": "chamdatietkiem",

    "quan_ao_gia_hoi": "quanaogiahoi",

    "yeu_da_hon_bo": "yeudahonbo"

}



# 7 Nền tảng chuẩn theo cấu trúc Batch Custom Links Shopee

BATCH_CUSTOM_PLATFORMS = [

    "facebook",

    "instagram",

    "threads",

    "shopeevideo",

    "zalovideo",

    "pinterest",

    "youtube"

]



def remove_accents_str(input_str: str) -> str:

    """Xóa dấu tiếng Việt, chuyển về ký tự ASCII không dấu"""

    if not input_str:

        return ""

    import unicodedata

    nfkd_form = unicodedata.normalize('NFKD', input_str)

    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])



def normalize_platform_name(val: str) -> str:

    """Chuẩn hóa tên nền tảng từ Sub_id1 hoặc tên cột/folder sang mã chuẩn"""

    if not val:

        return ""

    v = str(val).strip().lower()

    if any(k in v for k in ["facebook", "fb", "reels"]):

        return "facebook"

    if any(k in v for k in ["youtube", "yt", "shorts"]):

        return "youtube"

    if any(k in v for k in ["instagram", "ig", "insta"]):

        return "instagram"

    if any(k in v for k in ["threads", "th"]):

        return "threads"

    if any(k in v for k in ["shopeevideo", "shopee video", "shopee_video"]):

        return "shopeevideo"

    if any(k in v for k in ["zalovideo", "zalo video", "zalo_video", "zalo"]):

        return "zalovideo"

    if any(k in v for k in ["pinterest", "pin"]):

        return "pinterest"

    return v



def detect_platform_from_path(file_path: str) -> str:

    """Tự động nhận diện nền tảng nếu file nằm trong folder mang tên nền tảng (Link customed\\Facebook, ...)"""

    if not file_path:

        return ""

    fp_lower = file_path.lower().replace("/", "\\")

    if "\\facebook\\" in fp_lower or "\\facebook " in fp_lower or fp_lower.endswith("\\facebook"):

        return "facebook"

    if "\\youtube\\" in fp_lower or "\\youtube " in fp_lower or fp_lower.endswith("\\youtube"):

        return "youtube"

    if "\\instagram\\" in fp_lower or "\\instagram " in fp_lower or fp_lower.endswith("\\instagram"):

        return "instagram"

    if "\\threads\\" in fp_lower or "\\threads " in fp_lower or fp_lower.endswith("\\threads"):

        return "threads"

    if "\\shopee video\\" in fp_lower or "\\shopeevideo\\" in fp_lower:

        return "shopeevideo"

    if "\\zalo video\\" in fp_lower or "\\zalovideo\\" in fp_lower:

        return "zalovideo"

    if "\\pinterest\\" in fp_lower:

        return "pinterest"

    return ""



def make_sub_id2(url: str, idx: int = 1, prefix: str = None, video_name: str = None) -> str:

    """

    Tạo mã Sub_id2 chuẩn Shopee Affiliate (chữ, số không dấu, tối đa 20 ký tự, e.g. okhoaso1, okhoaso2).

    Ưu tiên: prefix người dùng nhập > slug tên sản phẩm trích xuất từ link gốc > tên video > sp{idx}.

    """

    if prefix:

        p_clean = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(prefix).lower())

        if p_clean:

            return f"{p_clean[:14]}{idx}"

    try:

        import urllib.parse

        parsed = urllib.parse.urlparse(url)

        path = parsed.path.strip('/')

        parts = [p for p in path.split('/') if p]

        if parts:

            slug = parts[0]

            if '-i.' in slug:

                slug = slug.split('-i.')[0]

            decoded_slug = urllib.parse.unquote(slug)

            words = decoded_slug.replace('-', ' ').split()[:3]

            short_str = ''.join(words)

            slug_clean = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(short_str).lower())

            if slug_clean:

                return f"{slug_clean[:14]}{idx}"

    except Exception:

        pass

    if video_name:

        v_clean = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(video_name).lower())

        if v_clean:

            return f"{v_clean[:14]}{idx}"

    return f"sp{idx}"



def get_brand_sub_id3(brand_key: str) -> str:

    """Lấy Sub_id3 theo cấu hình của kênh, fallback sang slug không dấu của brand_key"""

    if brand_key in CHANNEL_SUB_ID3:

        return CHANNEL_SUB_ID3[brand_key]

    return re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(brand_key).lower())



def get_brand_key_from_sub_id3(sub_id3: str) -> str:

    """Tìm brand_key từ Sub_id3 trong file Shopee Batch Custom Links"""

    if not sub_id3:

        return ""

    s_clean = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(sub_id3).lower())

    for k, v in CHANNEL_SUB_ID3.items():

        if v.lower() == s_clean:

            return k

        if re.sub(r'[^a-zA-Z0-9]', '', k.lower()) == s_clean:

            return k

    return ""



# ─── BỘ CHỈ MỤC & TÌM KIẾM SẢN PHẨM AFFILIATE TỪ KHO LINK CŨ ───

_AFFILIATE_CATALOG_CACHE = {"timestamp": 0, "items": []}



def build_affiliate_catalog(force_refresh=False):

    """

    Quét và lập chỉ mục toàn bộ sản phẩm affiliate từ:

    1. C:\\Affiliate\\Tổng hợp Link Affiliate (tất cả các Batch 1, Batch 2,...)

    2. C:\\Affiliate\\<Brand>\\Link customed và các thư mục video có file AffiliateBatchCustomLinks*.csv

    3. upload_tasks_history.json

    Trả về danh sách các sản phẩm kèm tên, sub_id2, sub_id3, brand_key, và bảng link theo platform.

    """

    now = time.time()

    if not force_refresh and _AFFILIATE_CATALOG_CACHE["items"] and (now - _AFFILIATE_CATALOG_CACHE["timestamp"] < 30):

        return _AFFILIATE_CATALOG_CACHE["items"]



    import urllib.parse

    catalog = []

    seen_dict = {}



    def _extract_name_from_url(url, fallback=""):

        if not url:

            return fallback

        slug = url.split("?")[0].split("shopee.vn/")[-1]

        if "-i." in slug:

            slug = slug.split("-i.")[0]

        decoded = urllib.parse.unquote(slug).replace("-", " ").strip()

        return decoded if decoded and not decoded.startswith("http") and len(decoded) > 2 else fallback



    # 1. Quét C:\Affiliate\Tổng hợp Link Affiliate

    tong_hop = os.path.join(AFFILIATE_ROOT, "Tổng hợp Link Affiliate")

    if os.path.exists(tong_hop):

        for root, dirs, files in os.walk(tong_hop):

            for f in files:

                ext = os.path.splitext(f)[1].lower()

                if ext in [".csv", ".xlsx"] and ("affiliatebatchcustomlinks" in f.lower() or "master" in f.lower()):

                    fp = os.path.join(root, f)

                    try:

                        if ext == ".csv":

                            with open(fp, "r", encoding="utf-8-sig", errors="ignore") as cf:

                                reader = csv.DictReader(cf)

                                for row in reader:

                                    orig = (row.get("Liên kết gốc") or "").strip()

                                    conv = (row.get("Liên kết chuyển đổi") or "").strip()

                                    sub1 = (row.get("Sub_id1") or "").strip().lower()

                                    sub2 = (row.get("Sub_id2") or "").strip()

                                    sub3 = (row.get("Sub_id3") or "").strip().lower()

                                    if orig and conv:

                                        p_name = _extract_name_from_url(orig, sub2)

                                        bkey = get_brand_key_from_sub_id3(sub3)

                                        k = (orig, sub2, sub3)

                                        if k not in seen_dict:

                                            item = {

                                                "name": p_name,

                                                "orig": orig,

                                                "sub2": sub2,

                                                "sub3": sub3,

                                                "brand_key": bkey,

                                                "platforms": {}

                                            }

                                            if sub1:

                                                item["platforms"][sub1] = conv

                                            seen_dict[k] = item

                                            catalog.append(item)

                                        else:

                                            if sub1:

                                                seen_dict[k]["platforms"][sub1] = conv

                    except Exception:

                        pass



    # 2. Quét các kênh trong C:\Affiliate

    try:

        brands = load_brands()

        for bk, bcfg in brands.items():

            b_folder = bcfg.get("folder") or bk

            b_dir = os.path.join(AFFILIATE_ROOT, b_folder)

            if not os.path.exists(b_dir):

                continue

            for root, dirs, files in os.walk(b_dir):

                if "video_douyin" in root.lower():

                    continue

                for f in files:

                    if f.lower().endswith(".csv") and "affiliatebatchcustomlinks" in f.lower():

                        fp = os.path.join(root, f)

                        try:

                            with open(fp, "r", encoding="utf-8-sig", errors="ignore") as cf:

                                reader = csv.DictReader(cf)

                                for row in reader:

                                    orig = (row.get("Liên kết gốc") or row.get("Link Shopee") or "").strip()

                                    conv = (row.get("Liên kết chuyển đổi") or row.get("Link Shopee") or "").strip()

                                    sub1 = (row.get("Sub_id1") or "").strip().lower()

                                    sub2 = (row.get("Sub_id2") or "").strip()

                                    sub3 = (row.get("Sub_id3") or "").strip().lower() or get_brand_sub_id3(bk)

                                    name_col = (row.get("Tên sản phẩm") or "").strip()

                                    p_name = name_col or _extract_name_from_url(orig, sub2)

                                    if orig and conv:

                                        k = (orig, sub2, sub3)

                                        if k not in seen_dict:

                                            item = {

                                                "name": p_name,

                                                "orig": orig,

                                                "sub2": sub2,

                                                "sub3": sub3,

                                                "brand_key": bk,

                                                "platforms": {}

                                            }

                                            if sub1:

                                                item["platforms"][sub1] = conv

                                            seen_dict[k] = item

                                            catalog.append(item)

                                        else:

                                            if sub1:

                                                seen_dict[k]["platforms"][sub1] = conv

                        except Exception:

                            pass

    except Exception:

        pass



    # 3. Quét upload_tasks_history.json

    history_path = os.path.join(POST_DIR, "config", "upload_tasks_history.json")

    if os.path.exists(history_path):

        try:

            with open(history_path, "r", encoding="utf-8", errors="ignore") as hf:

                history = json.load(hf)

                for tid, t in history.items():

                    bk = (t.get("brand_key") or "").strip().lower()

                    params = t.get("params", {})

                    prods = params.get("products", [])

                    for p in prods:

                        name = p.get("name") or ""

                        link = p.get("link") or ""

                        link_goc = p.get("link_goc") or ""

                        plat = (p.get("platform") or "").strip().lower()

                        sub2 = p.get("sub_id2") or ""

                        p_name = _extract_name_from_url(link_goc, name or sub2)

                        if not p_name or len(p_name) < 3 or p_name.startswith("http"):

                            p_name = name or "Sản phẩm chính hãng"

                        if link:

                            k = (link_goc or link, sub2, bk)

                            if k not in seen_dict:

                                item = {

                                    "name": p_name,

                                    "orig": link_goc,

                                    "sub2": sub2,

                                    "sub3": bk,

                                    "brand_key": bk,

                                    "platforms": {}

                                }

                                if plat:

                                    item["platforms"][plat] = link

                                else:

                                    item["platforms"]["general"] = link

                                seen_dict[k] = item

                                catalog.append(item)

                            else:

                                if plat:

                                    seen_dict[k]["platforms"][plat] = link

        except Exception:

            pass



    _AFFILIATE_CATALOG_CACHE["timestamp"] = now

    _AFFILIATE_CATALOG_CACHE["items"] = catalog

    return catalog



def compute_product_similarity(query: str, target_name: str, sub2: str = "", query_brand: str = "", target_brand: str = "") -> int:

    """

    Tính điểm độ tương đồng giữa tên sản phẩm do AI nhận diện và sản phẩm trong kho (thang điểm 0 - 100).

    """

    if not query or not target_name:

        return 0



    q_norm = remove_accents_str(query).strip().lower()

    t_norm = remove_accents_str(target_name).strip().lower()

    s2_norm = remove_accents_str(sub2).strip().lower()



    if not q_norm or not t_norm:

        return 0



    # 1. Khớp chuỗi con trực tiếp (Exact substring containment)

    score = 0

    if q_norm == t_norm:

        score = 100

    elif q_norm in t_norm:

        # Nếu cụm từ nhận diện nằm trọn trong tên sản phẩm đầy đủ

        score = 95

    elif t_norm in q_norm:

        score = 90

    else:

        # 2. So khớp tập từ khóa (Token matching)

        q_tokens = set(re.findall(r'[a-z0-9]+', q_norm))

        t_tokens = set(re.findall(r'[a-z0-9]+', t_norm))



        stop_words = {

            'cho', 'va', 'cua', 'co', 'o', 'la', 'nhung', 'cac', 'thi', 'loai',

            'mau', 'chat', 'lieu', 'cao', 'cap', 'chinh', 'hang', 'tien', 'loi',

            'chong', 'giup', 'tot', 'rat', 'sieu', 'chuan', 'dep', 'hot'

        }

        q_sig = q_tokens - stop_words

        t_sig = t_tokens - stop_words



        if not q_sig:

            q_sig = q_tokens

        if not t_sig:

            t_sig = t_tokens



        common = q_sig & t_sig

        if not common:

            # Kiểm tra xem có từ nào trong q_tokens xuất hiện trong sub2 không

            sub2_hit = any(len(tok) >= 3 and tok in s2_norm for tok in q_sig)

            return 30 if sub2_hit else 0



        # Nếu toàn bộ từ quan trọng của query nằm trong target

        if q_sig.issubset(t_sig):

            score = 90

        else:

            ratio = len(common) / len(q_sig)

            score = int(ratio * 80)



        # Thưởng điểm nếu sub2 khớp

        for tok in q_sig:

            if len(tok) >= 3 and tok in s2_norm:

                score += 10

                break



    # 3. Ưu tiên kênh cùng thương hiệu (Brand bias bonus)

    if query_brand and target_brand:

        q_b_clean = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(query_brand).lower())

        t_b_clean = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(target_brand).lower())

        q_sub3 = CHANNEL_SUB_ID3.get(query_brand, "").lower()

        if q_b_clean == t_b_clean or (q_sub3 and q_sub3 == t_b_clean):

            score += 10



    return min(score, 100)



def find_best_matching_products(detected_product_names: list, brand_key: str = None, min_score: int = 45) -> list:

    """

    Tìm kiếm và đối soát các sản phẩm do Gemini phát hiện trực tiếp trong file

    DANH_SACH_LINK_GOC_VA_RUT_GON_<CHANNEL>.xlsx của kênh đó.

    Trả về cả Link Gốc Shopee và Link Rút Gọn tương ứng của sản phẩm.

    """

    if not detected_product_names:

        return []



    try:

        import sys

        if r"C:\Affiliate" not in sys.path:

            sys.path.append(r"C:\Affiliate")

        from link_tracker_sync import match_products_in_channel_file

        return match_products_in_channel_file(brand_key, detected_product_names, min_score=min_score)

    except Exception as _e_match:

        print(f"⚠️ Lỗi khi match_products_in_channel_file({brand_key}): {_e_match}")

        return []



def get_platform_comments(products, target_platform, brand_key, comment_templates=None):

    """

    Lấy danh sách bình luận affiliate theo đúng chuẩn 5 mẫu câu,

    nếu products có gắn platform (từ Sub_id1 hoặc thư mục customed) thì lọc CHÍNH XÁC link của nền tảng đó.

    Nếu không có sản phẩm nào cho nền tảng đó (ví dụ file chung không chia nền tảng), fallback về toàn bộ products.

    """

    if not products:

        return []

    

    norm_target = normalize_platform_name(target_platform)

    has_platform_info = any(bool(p.get("platform")) for p in products)

    

    if has_platform_info:

        matched_products = [

            p for p in products 

            if normalize_platform_name(p.get("platform")) == norm_target

        ]

        if matched_products:

            return format_affiliate_comments(matched_products, brand_key, comment_templates)

    

    # Fallback nếu không có platform tag hoặc không có link nào khớp: dùng toàn bộ products

    return format_affiliate_comments(products, brand_key, comment_templates)



def parse_link_file(file_path):

    """Hỗ trợ đọc cả file .xlsx và .csv linh hoạt, tự động nhận diện cấu trúc file Shopee Affiliate Batch Links (kèm Sub_id1 nền tảng)"""

    products = []

    if not os.path.exists(file_path):

        return products



    file_plat_fallback = detect_platform_from_path(file_path)



    if file_path.lower().endswith(".csv"):

        encodings = ["utf-8-sig", "utf-8", "cp1258", "latin1"]

        for enc in encodings:

            try:

                with open(file_path, "r", encoding=enc) as f:

                    reader = list(csv.reader(f))

                    if not reader:

                        continue

                    header = [str(c or "").strip().lower() for c in reader[0]]

                    name_col, link_col, goc_col = None, None, None

                    sub1_col, sub2_col, sub3_col = None, None, None



                    # 1. Quét tìm vị trí cột dựa trên tiêu đề

                    for idx, col_name in enumerate(header):

                        if any(k in col_name for k in ["chuyển đổi", "chuyen doi", "affiliate", "rút gọn", "rut gon", "short"]):

                            link_col = idx

                        elif any(k in col_name for k in ["liên kết gốc", "lien ket goc", "link gốc", "link goc", "shopee gốc"]):

                            goc_col = idx

                        elif any(k in col_name for k in ["tên", "ten", "title", "product"]):

                            name_col = idx

                        elif any(k in col_name for k in ["sub_id1", "sub1", "nền tảng", "nen tang", "platform"]):

                            sub1_col = idx

                        elif any(k in col_name for k in ["sub_id2", "sub2"]):

                            sub2_col = idx

                        elif any(k in col_name for k in ["sub_id3", "sub3"]):

                            sub3_col = idx



                    # 2. Xử lý từng dòng dữ liệu

                    for i, row in enumerate(reader[1:], 2):

                        if not any(row):

                            continue

                        

                        target_link = ""

                        target_name = ""

                        link_goc = ""

                        sub_id1_val = ""

                        sub_id2_val = ""



                        # Nếu đã xác định được cột qua header

                        if link_col is not None and len(row) > link_col and row[link_col].strip():

                            target_link = row[link_col].strip()

                        if goc_col is not None and len(row) > goc_col and row[goc_col].strip():

                            link_goc = row[goc_col].strip()

                        if name_col is not None and len(row) > name_col and row[name_col].strip():

                            target_name = row[name_col].strip()

                        if sub1_col is not None and len(row) > sub1_col and row[sub1_col].strip():

                            sub_id1_val = row[sub1_col].strip()

                        if sub2_col is not None and len(row) > sub2_col and row[sub2_col].strip():

                            sub_id2_val = row[sub2_col].strip()



                        # Nếu chưa tìm thấy cột từ header, tự động quét từng ô trong row để tìm link affiliate (s.shopee.vn)

                        if not target_link:

                            for c in row:

                                c_str = str(c or "").strip()

                                if "s.shopee.vn" in c_str or "shp.ee" in c_str:

                                    target_link = c_str

                                    break

                                elif "shopee.vn" in c_str and not target_link:

                                    target_link = c_str



                        # Tìm link gốc shopee nếu chưa có

                        if not link_goc:

                            for c in row:

                                c_str = str(c or "").strip()

                                if "shopee.vn/" in c_str and "s.shopee.vn" not in c_str:

                                    link_goc = c_str

                                    break



                        # Nếu không có cột tên, tự động trích xuất tên sản phẩm từ link gốc

                        if not target_name and link_goc:

                            target_name = extract_product_name_from_url(link_goc)



                        if not target_name and len(row) > 1 and row[1].strip() and not row[1].strip().startswith("http"):

                            target_name = row[1].strip()



                        # Xác định platform của dòng này

                        row_platform = normalize_platform_name(sub_id1_val) or file_plat_fallback



                        if target_link:

                            products.append({

                                "name": target_name or "Sản phẩm chính hãng",

                                "link": target_link,

                                "link_goc": link_goc,

                                "platform": row_platform,

                                "sub_id1": sub_id1_val,

                                "sub_id2": sub_id2_val

                            })



                if products:

                    break

            except Exception:

                continue

    else:

        try:

            wb = openpyxl.load_workbook(file_path, data_only=True)

            sheet = wb.active

            rows = list(sheet.iter_rows(values_only=True))

            if rows:

                header = [str(c or "").strip().lower() for c in rows[0]]

                name_col, link_col, goc_col = None, None, None

                sub1_col, sub2_col, sub3_col = None, None, None



                for idx, col_name in enumerate(header):

                    if any(k in col_name for k in ["chuyển đổi", "chuyen doi", "affiliate", "rút gọn", "rut gon", "short"]):

                        link_col = idx

                    elif any(k in col_name for k in ["liên kết gốc", "lien ket goc", "link gốc", "link goc", "shopee gốc"]):

                        goc_col = idx

                    elif any(k in col_name for k in ["tên", "ten", "title", "product"]):

                        name_col = idx

                    elif any(k in col_name for k in ["sub_id1", "sub1", "nền tảng", "nen tang", "platform"]):

                        sub1_col = idx

                    elif any(k in col_name for k in ["sub_id2", "sub2"]):

                        sub2_col = idx

                    elif any(k in col_name for k in ["sub_id3", "sub3"]):

                        sub3_col = idx



                for i, row in enumerate(rows[1:], 2):

                    if not any(row):

                        continue

                    

                    target_link = ""

                    target_name = ""

                    link_goc = ""

                    sub_id1_val = ""

                    sub_id2_val = ""



                    if link_col is not None and len(row) > link_col and row[link_col]:

                        target_link = str(row[link_col]).strip()

                    if goc_col is not None and len(row) > goc_col and row[goc_col]:

                        link_goc = str(row[goc_col]).strip()

                    if name_col is not None and len(row) > name_col and row[name_col]:

                        target_name = str(row[name_col]).strip()

                    if sub1_col is not None and len(row) > sub1_col and row[sub1_col]:

                        sub_id1_val = str(row[sub1_col]).strip()

                    if sub2_col is not None and len(row) > sub2_col and row[sub2_col]:

                        sub_id2_val = str(row[sub2_col]).strip()



                    # Quét tự động nếu không khớp header

                    if not target_link:

                        for c in row:

                            c_str = str(c or "").strip()

                            if "s.shopee.vn" in c_str or "shp.ee" in c_str:

                                target_link = c_str

                                break

                            elif "shopee.vn" in c_str and not target_link:

                                target_link = c_str



                    if not link_goc:

                        for c in row:

                            c_str = str(c or "").strip()

                            if "shopee.vn/" in c_str and "s.shopee.vn" not in c_str:

                                link_goc = c_str

                                break



                    if not target_name and link_goc:

                        target_name = extract_product_name_from_url(link_goc)



                    if not target_name and len(row) > 1 and row[1] and not str(row[1]).strip().startswith("http"):

                        target_name = str(row[1]).strip()



                    row_platform = normalize_platform_name(sub_id1_val) or file_plat_fallback



                    if target_link:

                        products.append({

                            "name": target_name or "Sản phẩm chính hãng",

                            "link": target_link,

                            "link_goc": link_goc,

                            "platform": row_platform,

                            "sub_id1": sub_id1_val,

                            "sub_id2": sub_id2_val

                        })

        except Exception as e:

            print(f"⚠️ Lỗi đọc file Excel {file_path}: {e}")



    return products



def _is_direct_url_input(text: str) -> bool:

    """Kiểm tra xem input có phải là URL trực tiếp (hoặc kèm prefix nền tảng) không."""

    t = text.strip()

    if t.startswith("http://") or t.startswith("https://"):

        return True

    if ":" in t and ("http://" in t or "https://" in t):

        prefix = t.split(":", 1)[0].strip().lower()

        if prefix in ["facebook", "fb", "youtube", "yt", "shorts", "instagram", "ig", "threads", "th", "shopeevideo", "zalovideo", "pinterest", "zalo", "pin"]:

            return True

    return False



def parse_direct_urls(raw_text: str) -> list:

    """

    Parse danh sách URL affiliate dán trực tiếp vào ô File Link Sản Phẩm.

    Hỗ trợ:

    - 1 URL duy nhất

    - Nhiều URL mỗi dòng 1 URL

    - Tiền tố nền tảng (ví dụ: facebook: https://... hoặc fb: https://...)

    - URL lẫn lộn với text (tự filter ra URL)

    Trả về list[{name, link, link_goc, platform}] tương thích với parse_link_file().

    """

    products = []

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    for line in lines:

        line_lower = line.lower()

        plat = ""

        if any(k in line_lower for k in ["facebook:", "fb:", "[fb]", "[facebook]"]):

            plat = "facebook"

        elif any(k in line_lower for k in ["youtube:", "yt:", "shorts:", "[yt]", "[youtube]"]):

            plat = "youtube"

        elif any(k in line_lower for k in ["instagram:", "ig:", "[ig]", "[instagram]"]):

            plat = "instagram"

        elif any(k in line_lower for k in ["threads:", "th:", "[th]", "[threads]"]):

            plat = "threads"

        elif any(k in line_lower for k in ["shopeevideo:", "shopee video:", "[shopeevideo]"]):

            plat = "shopeevideo"

        elif any(k in line_lower for k in ["zalovideo:", "zalo:", "[zalo]"]):

            plat = "zalovideo"

        elif any(k in line_lower for k in ["pinterest:", "pin:", "[pinterest]"]):

            plat = "pinterest"



        tokens = line.split()

        for token in tokens:

            if token.startswith("http://") or token.startswith("https://"):

                url = token.strip(".,;\"'()")

                if not url:

                    continue

                name = extract_product_name_from_url(url)

                if not name or name.startswith("http"):

                    name = "Sản phẩm chính hãng"

                products.append({

                    "name": name,

                    "link": url,

                    "link_goc": url,

                    "platform": plat

                })

                break

    return products



def load_all_products_from_input(excel_input: str) -> list:

    """Đọc toàn bộ sản phẩm từ excel_input (hỗ trợ 1 file, nhiều file, URL đơn, nhiều URL, hoặc hỗn hợp nhiều dòng)"""

    if not excel_input:

        return []

    lines = [l.strip() for l in excel_input.splitlines() if l.strip()]

    if not lines:

        return []



    # 1. Nếu chỉ có 1 dòng và là file thực tế

    if len(lines) == 1 and os.path.exists(lines[0]):

        return parse_link_file(lines[0])



    # 2. Nếu tất cả các dòng đều là link trực tiếp

    if all(_is_direct_url_input(l) for l in lines):

        return parse_direct_urls(excel_input)



    # 3. Nhiều dòng hỗn hợp (vừa file vừa link trực tiếp)

    all_products = []

    for l in lines:

        if os.path.exists(l):

            try:

                all_products.extend(parse_link_file(l))

            except Exception as e:

                print(f"⚠️ Lỗi đọc file {l}: {e}")

        elif _is_direct_url_input(l):

            all_products.extend(parse_direct_urls(l))



    return all_products





def generate_seo_tags(product_names):

    """Tự động sinh 4 hashtag SEO mạnh từ tên sản phẩm"""

    # Từ phổ biến cần loại bỏ

    stop_words = {"sản", "phẩm", "cái", "chiếc", "bộ", "hộp", "gói", "chai",

                  "túi", "miếng", "viên", "cây", "và", "cho", "với", "của",

                  "từ", "đến", "trong", "ngoài", "tại", "bằng", "về",

                  "the", "a", "an", "of", "for", "with", "and", "in", "on"}



    # Gom tất cả từ khóa từ danh sách sản phẩm

    all_words = []

    for name in product_names:

        name_clean = re.sub(r'[^\w\sÀ-ỹ]', '', name, flags=re.UNICODE)

        words = [w.strip() for w in name_clean.split() if len(w.strip()) > 1

                 and w.strip().lower() not in stop_words]

        all_words.extend(words)



    # Đếm tần suất và lấy top từ khóa

    word_freq = {}

    for w in all_words:

        key = w.lower()

        word_freq[key] = word_freq.get(key, 0) + 1



    # Sắp xếp theo tần suất

    sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])



    tags = []

    # Tag 1: Tên sản phẩm đầu tiên (nguyên cụm)

    if product_names:

        first_product = re.sub(r'[^\w\sÀ-ỹ]', '', product_names[0], flags=re.UNICODE).strip()

        if first_product:

            tags.append(first_product)



    # Tag 2-4: Top từ khóa phổ biến

    for word, freq in sorted_words:

        if len(tags) >= 4:

            break

        # Tránh trùng

        if not any(word in t.lower() for t in tags):

            tags.append(word.title())



    # Bổ sung tag mặc định nếu chưa đủ 4

    defaults = ["Review", "Affiliate", "Shorts", "Trending"]

    for d in defaults:

        if len(tags) >= 4:

            break

        if d.lower() not in [t.lower() for t in tags]:

            tags.append(d)



    return tags[:4]



@app.route("/")

def index():

    brands = load_brands()

    brand_list = []

    for k, v in brands.items():

        brand_list.append({

            "key": k,

            "name": v.get("name", k),

            "folder": v.get("folder", ""),

            "platforms": v.get("platforms", ["youtube", "facebook", "instagram", "threads"]),

            "default_tags": BRAND_DEFAULT_HASHTAGS.get(k, [])

        })

    return render_template("index.html", brands=brand_list)



@app.route("/api/preview_excel", methods=["POST"])

def preview_excel():

    data = request.json or {}

    excel_path = (data.get("excel_path") or "").strip()

    if not excel_path:

        return jsonify({"success": False, "message": "Chưa có đường dẫn"}), 400



    try:

        products = load_all_products_from_input(excel_path)

        if products:

            product_names = [p["name"] for p in products]

            auto_tags = generate_seo_tags(product_names)

            return jsonify({

                "success": True,

                "count": len(products),

                "products": products,

                "auto_tags": auto_tags,

                "source": "direct_url" if _is_direct_url_input(excel_path) else "file"

            })

        return jsonify({"success": False, "message": "Không tìm thấy sản phẩm trong file hoặc link đã nhập"}), 400

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



# Quản lý chia luồng — mỗi kênh chạy thread riêng, đăng ngay không chờ

brand_locks = {}

brand_locks_mutex = threading.Lock()



# Khóa hàng đợi điều tiết riêng cho Instagram (chống nghẽn binary container & rate limit)

# Đảm bảo mỗi thời điểm chỉ có DUY NHẤT 1 video Instagram được upload lên Meta

# và tự động giãn cách an toàn 60 giây giữa các kênh.

instagram_upload_lock = threading.Lock()

last_instagram_finish_time = 0.0

INSTAGRAM_DELAY_SECONDS = 60



def get_brand_lock(brand_key):

    with brand_locks_mutex:

        if brand_key not in brand_locks:

            brand_locks[brand_key] = threading.Lock()

        return brand_locks[brand_key]



def run_upload_task(task_id, params):

    task = tasks.get(task_id)

    if not task:

        return

    task["params"] = params

    brand_key = params["brand_key"]

    brand_name = params.get("brand_name", brand_key)



    # Kiểm tra hủy ngay trước khi bắt đầu

    if task_id in cancelled_tasks:

        task["status"] = "CANCELLED"

        task["progress_detail"] = "Đã hủy bởi người dùng"

        task["logs"].append("🛑 Tác vụ đã được người dùng nhấn HỦY ĐĂNG!")

        return



    task["status"] = "RUNNING"

    task["progress_detail"] = "Khởi động..."



    try:

        _execute_upload_task(task_id, params)

    except Exception as e:

        import traceback

        traceback.print_exc()

        task["status"] = "FAILED"

        task["progress_detail"] = f"Lỗi: {e}"

        task["logs"].append(f"💥 Lỗi ngoại lệ trong quá trình đăng: {e}")

        if not task.get("failed_platforms"):

            succ = set(task.get("successful_platforms", []))

            all_p = task.get("platforms", [])

            task["failed_platforms"] = [p for p in all_p if p not in succ]





def _build_yt_title(title: str, tags: list) -> str:

    """

    Chèn 1-2 hashtag vào cuối tiêu đề YouTube.

    Luôn có #Shorts. Thêm 1 hashtag ngành nếu còn chỗ (tổng <= 100 ký tự).

    """

    base = title.strip() if title else ""

    # Lấy tag đầu tiên không phải 'shorts'/'reels' để chèn thêm

    extra_tag = ""

    for t in tags:

        t_slug = re.sub(r'\s+', '', t).strip()

        if t_slug.lower() not in ("shorts", "reels", "affiliate", "review"):

            extra_tag = f"#{t_slug}"

            break



    candidate = f"{base} {extra_tag} #Shorts".strip() if extra_tag else f"{base} #Shorts"

    # Nếu quá 100 ký tự, bỏ extra_tag

    if len(candidate) > 100:

        candidate = f"{base} #Shorts"

    return candidate[:100]





def _build_yt_description(

    description: str,

    tags: list = None,

    comments_list_yt: list = None,

    products: list = None,

    brand_key: str = None

):

    """

    Chuẩn hóa mô tả cho YouTube Shorts:

    1. Kiểm tra xem mô tả (description) đã có link Shopee Affiliate hay chưa.

    2. Nếu CHƯA CÓ:

       - Tự động lấy link sản phẩm Shopee Affiliate (ưu tiên link gắn Sub_id1 YouTube nếu có).

       - Chèn khối link sản phẩm vào mô tả theo định dạng chuẩn, giãn cách dòng thoáng đãng:

         🛒 MUA SẢN PHẨM CHÍNH HÃNG TẠI ĐÂY:

         👉 [Tên SP]: [Link Shopee]

    3. Thêm 3-5 hashtag SEO (luôn có #Shorts) ở cuối cùng của mô tả.

    Trả về tuple: (final_description, was_injected, injected_urls)

    """

    desc_clean = (description or "").strip()

    tags = tags or []



    # Bóc tách hashtag ở cuối description nếu có sẵn để chuyển xuống đáy cùng sau link affiliate

    hashtag_tail_match = re.search(r'(\n\s*#[^\n]+)+\s*$', desc_clean)

    existing_hashtags = []

    if hashtag_tail_match:

        tail_str = hashtag_tail_match.group(0).strip()

        desc_clean = desc_clean[:hashtag_tail_match.start()].strip()

        existing_hashtags = re.findall(r'#(\w+)', tail_str)



    # 1. Kiểm tra xem trong mô tả đã có link Shopee Affiliate chưa

    aff_pattern = r'(?:https?://)?(?:s\.shopee\.vn|shope\.ee|shopee\.vn|shorten\.asia|affiliate\.shopee\.vn)[^\s\'"<>]+'

    has_aff_link = bool(re.search(aff_pattern, desc_clean, flags=re.IGNORECASE))



    if not has_aff_link and products:

        for p in products:

            p_lnk = (p.get("link") or "").strip().rstrip("/?#&").lower()

            if p_lnk and p_lnk in desc_clean.lower():

                has_aff_link = True

                break

    if not has_aff_link and comments_list_yt:

        for c in comments_list_yt:

            u_matches = re.findall(r"https?://[^\s<>\"\']+", c)

            if u_matches:

                u_clean = u_matches[0].rstrip("/?#&").lower()

                if u_clean in desc_clean.lower():

                    has_aff_link = True

                    break



    was_injected = False

    injected_urls = []

    if has_aff_link:

        body_text = desc_clean

    else:

        yt_prods = []

        if products:

            has_plat_tag = any(bool(p.get("platform")) for p in products)

            if has_plat_tag:

                yt_prods = [p for p in products if normalize_platform_name(p.get("platform")) == "youtube"]

            if not yt_prods:

                yt_prods = products

        formatted_items = []

        seen_urls = set()

        if yt_prods:

            for p in yt_prods:

                raw_u = (p.get("link") or "").strip()

                if not raw_u:

                    continue

                u_key = raw_u.rstrip("/?#&").lower()

                if u_key in seen_urls:

                    continue

                seen_urls.add(u_key)

                injected_urls.append(raw_u)

                p_name = (p.get("name") or "").strip()

                if p_name and p_name.lower() not in ["sản phẩm chính hãng", "sản phẩm 1", "link sản phẩm", "sản phẩm"]:

                    formatted_items.append(f"👉 {p_name}:\n{raw_u}")

                else:

                    formatted_items.append(f"👉 Mua tại đây: {raw_u}")

        if not formatted_items and comments_list_yt:

            for c in comments_list_yt:

                c_clean = c.strip()

                if not c_clean:

                    continue

                urls = re.findall(r"https?://[^\s<>\"\']+", c_clean)

                if not urls:

                    continue

                u = urls[0]

                u_key = u.rstrip("/?#&").lower()

                if u_key in seen_urls:

                    continue

                seen_urls.add(u_key)

                injected_urls.append(u)

                prefix = c_clean.replace(u, "").strip().rstrip(":- ")

                if prefix:

                    formatted_items.append(f"👉 {prefix}:\n{u}")

                else:

                    formatted_items.append(f"👉 Mua tại đây: {u}")

        if formatted_items:

            was_injected = True

            aff_block = "🛒 MUA SẢN PHẨM CHÍNH HÃNG TẠI ĐÂY:\n\n" + "\n\n".join(formatted_items)

            body_text = f"{desc_clean}\n\n{aff_block}" if desc_clean else aff_block

        else:

            body_text = desc_clean



    # 3. Gom toàn bộ Hashtags (tối đa 4 tag nội dung + #Shorts)

    selected_tags = []

    all_raw_tags = list(existing_hashtags) + list(tags)

    for t in all_raw_tags:

        t_slug = re.sub(r'[\s\W]+', '', t, flags=re.UNICODE).strip()

        if t_slug and t_slug.lower() != "shorts":

            tag_formatted = f"#{t_slug}"

            if tag_formatted.lower() not in [x.lower() for x in selected_tags] and len(selected_tags) < 4:

                selected_tags.append(tag_formatted)

    selected_tags.append("#Shorts")

    hashtag_line = " ".join(selected_tags)

    final_desc = f"{body_text}\n\n{hashtag_line}".strip() if body_text else hashtag_line

    return final_desc, was_injected, injected_urls





def _build_ig_caption(title: str, caption: str, tags: list) -> str:

    """

    Ghép caption Instagram: title + caption + 5-8 hashtag cuối.

    Instagram cho phép đến 30 hashtag, nhưng 5-8 là optimal.

    """

    parts = []

    if title and title.strip():

        parts.append(title.strip())

    if caption and caption.strip():

        parts.append(caption.strip())



    # Chọn tối đa 8 hashtag

    selected = []

    for t in tags:

        t_slug = re.sub(r'\s+', '', t).strip()

        if t_slug and len(selected) < 7:

            selected.append(f"#{t_slug}")

    selected.append("#Reels")    # Luôn có #Reels



    if selected:

        parts.append(" ".join(selected))



    return "\n\n".join(parts)





def _save_links_as_csv(raw_url_text: str, video_path: str) -> str:

    """

    Lưu danh sách URL affiliate (dán trực tiếp) thành file CSV chuẩn

    vào cùng thư mục chứa video, tên file là AffiliateBatchCustomLinks{timestamp}.csv.

    Trả về đường dẫn file CSV vừa tạo, hoặc "" nếu lỗi.

    """

    try:

        import csv as _csv

        from datetime import datetime as _dt



        video_dir = os.path.dirname(os.path.abspath(video_path))

        timestamp  = _dt.now().strftime("%Y%m%d%H%M")

        csv_name   = f"AffiliateBatchCustomLinks{timestamp}.csv"

        csv_path   = os.path.join(video_dir, csv_name)



        # Parse URLs từ raw text

        urls = [u.strip() for u in raw_url_text.splitlines() if u.strip().startswith("http")]

        if not urls:

            return ""



        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:

            writer = _csv.writer(f)

            # Header tương thích với parse_link_file()

            writer.writerow(["Liên kết gốc", "Sub_id1", "Sub_id2", "Sub_id3", "Sub_id4", "Sub_id5",

                             "Liên kết chuyển đổi", "Lí do thất bại"])

            for url in urls:

                writer.writerow([url, "", "", "", "", "", url, ""])



        print(f"💾 Đã lưu {len(urls)} link affiliate → {csv_path}", flush=True)

        return csv_path

    except Exception as e:

        print(f"⚠️ Không thể lưu CSV link affiliate: {e}", flush=True)

        return ""





def _execute_upload_task(task_id, params):

    task = tasks[task_id]

    def task_log(msg):

        task["logs"].append(msg)

    brand_key = params["brand_key"]

    video_path = params["video_path"]

    thumbnail_path = (params.get("thumbnail_path") or "").strip()

    title = params["title"]

    caption = params["caption"]

    products = params["products"]

    platforms = params["platforms"]

    youtube_tags = params.get("youtube_tags", ["shorts", "review", "affiliate"])

    schedule_time = params.get("schedule_time")  # ISO string hoặc None



    # Xử lý hẹn giờ:

    # - Facebook/YouTube: Sử dụng API native hẹn giờ (upload ngay, platform tự publish đúng giờ)

    # - Instagram/Threads: Lưu vào scheduler queue, worker sẽ upload đúng giờ

    is_scheduled = bool(schedule_time)

    ig_threads_deferred = False  # Đánh dấu nếu IG/Threads được chuyển sang queue



    if is_scheduled:

        try:

            sched_dt = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))

            vn_tz = timezone(timedelta(hours=7))

            sched_vn = sched_dt.astimezone(vn_tz).strftime("%H:%M %d/%m/%Y")

            task["status"] = "RUNNING"

            task["schedule_display"] = sched_vn



            # FB/YouTube: upload ngay với API hẹn giờ (không cần chờ)

            has_api_schedule = any(p in platforms for p in ["facebook", "youtube"])

            # IG/Threads: chuyển sang scheduler worker

            has_local_schedule = any(p in platforms for p in ["instagram", "threads"])



            if has_api_schedule:

                task["logs"].append(f"⏰ HẸN GIỜ: FB/YouTube sẽ dùng API native schedule vào {sched_vn}")

            if has_local_schedule:

                task["logs"].append(f"⏰ HẸN GIỜ: IG/Threads sẽ được scheduler worker đăng vào {sched_vn}")

                ig_threads_deferred = True



        except Exception as e:

            task["logs"].append(f"⚠️ Lỗi parse thời gian hẹn giờ: {e}. Đăng ngay.")

            is_scheduled = False





    task["logs"].append(f"🚀 Bắt đầu đăng bài cho kênh: {params['brand_name']}")

    task["logs"].append(f"📁 Video: {video_path}")

    task["logs"].append(f"🔗 Số lượng link sản phẩm: {len(products)}")

    if youtube_tags:

        task["logs"].append(f"🏷️ YouTube Tags: {', '.join(youtube_tags)}")



    # Đọc comment templates và tạo comments_list thông minh (phân biệt 1 sp vs nhiều sp)

    templates = load_comment_templates()

    comments_list = format_affiliate_comments(products, brand_key, templates)



    # Bình luận tách biệt chuẩn theo từng nền tảng nếu file có gắn platform/Sub_id1

    comments_list_fb = get_platform_comments(products, "facebook", brand_key, templates)

    comments_list_yt = get_platform_comments(products, "youtube", brand_key, templates)

    comments_list_ig = get_platform_comments(products, "instagram", brand_key, templates)

    comments_list_th = get_platform_comments(products, "threads", brand_key, templates)



    # PROACTIVE TOKEN REFRESH: Kiểm tra và làm mới token trước khi upload

    for p_target in platforms:

        try:

            tok_check = ensure_valid_tokens(brand_key, p_target)

            if tok_check.get("refreshed"):

                task["logs"].append(f"🔄 Token {p_target.upper()} đã được tự động làm mới trước khi đăng!")

        except Exception as _e_tok:

            print(f"⚠️ Lỗi check token {p_target} cho {brand_key}: {_e_tok}")



    # Reload brands sau khi token refresh để lấy token mới nhất

    brands = load_brands()

    b_data = brands[brand_key]



    # Lấy danh sách hashtag mặc định của kênh (nếu có)

    default_tags = BRAND_DEFAULT_HASHTAGS.get(brand_key, [])

    # Ghép thêm các tag người dùng nhập từ giao diện (youtube_tags)

    combined_tags_list = []

    seen_tags = set()

    for t in (default_tags + (youtube_tags or [])):

        t_clean = t.strip()

        if t_clean and t_clean.lower() not in seen_tags:

            seen_tags.add(t_clean.lower())

            combined_tags_list.append(t_clean)



    # Chuẩn bị chuỗi hashtags Facebook — tối đa 5 tag (3 từ AI tags trước, rồi 2 default nếu còn thiếu)

    clean_fb_tags = []

    # Ưu tiên youtube_tags (từ AI) trước, tối đa 3 tag

    for t in (youtube_tags or []):

        if len(clean_fb_tags) >= 3:

            break

        clean_tag = re.sub(r'[\s\W]+', '', t, flags=re.UNICODE)

        if clean_tag:

            clean_fb_tags.append(f"#{clean_tag}")

    # Bổ sung tối đa 2 tag từ default nếu chưa đủ 5

    for t in (default_tags or []):

        if len(clean_fb_tags) >= 5:

            break

        clean_tag = re.sub(r'[\s\W]+', '', t, flags=re.UNICODE)

        slug_lower = clean_tag.lower()

        if clean_tag and not any(slug_lower in x.lower() for x in clean_fb_tags):

            clean_fb_tags.append(f"#{clean_tag}")

    fb_hashtags_str = " ".join(clean_fb_tags)



    # Xử lý Caption riêng cho Facebook Reels:

    # Tuyệt đối không gắn link Shopee/Affiliate trong Caption (tránh bị AI Meta quét bóp tương tác).

    # Chỉ giữ mô tả sạch, câu dẫn CTA về bình luận và Hashtags. Link Shopee được ghim vào Bình Luận.

    clean_caption_base = caption.strip() if caption.strip() else ""

    # Loại bỏ link affiliate / Shopee nếu người dùng có lỡ nhập vào ô Caption

    clean_caption_base = re.sub(

        r'(?:https?://)?(?:s\.shopee\.vn|shope\.ee|shopee\.vn|shorten\.asia|affiliate\.shopee\.vn)[^\s\'"<>]+',

        '',

        clean_caption_base,

        flags=re.IGNORECASE

    )

    # Loại bỏ các URL thông thường khác

    clean_caption_base = re.sub(r'https?://[^\s\'"<>]+', '', clean_caption_base)

    # Dọn dẹp câu thừa dẫn link nếu có

    clean_caption_base = re.sub(r'(?:mua ngay tại|mua chính hãng giá tốt tại|mua tại|link mua|link sp|link sản phẩm|tham khảo tại|xem tại)\s*', '', clean_caption_base, flags=re.IGNORECASE)

    clean_caption_base = re.sub(r'\s{2,}', ' ', clean_caption_base).strip()



    caption_parts = []

    if clean_caption_base:

        caption_parts.append(clean_caption_base)

    if products:

        caption_parts.append("🛒 Link mua sản phẩm chính hãng mình để ở phần bình luận bên dưới nhé! 👇")

    if fb_hashtags_str:

        caption_parts.append(fb_hashtags_str)



    caption_fb = "\n\n".join(caption_parts)



    results = {}

    completed_count = 0

    total_platforms = len(platforms)

    failed_platforms = []

    successful_platforms = []



    # Tính scheduled_time dạng Unix timestamp cho Facebook & YouTube

    fb_scheduled_ts = None

    yt_publish_at = None

    if schedule_time:

        try:

            sched_dt = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))

            now_ts = int(time.time())

            diff_sec = int(sched_dt.timestamp()) - now_ts

            # Meta Graph API & YouTube yêu cầu thời gian hẹn phải cách hiện tại tối thiểu 10 phút

            if diff_sec < 600:

                adjusted_dt = datetime.now(timezone.utc) + timedelta(minutes=15)

                adj_vn = adjusted_dt.astimezone(timezone(timedelta(hours=7))).strftime("%H:%M %d/%m/%Y")

                task["logs"].append(f"⚠️ Thời gian hẹn quá sát ({max(0, diff_sec)//60} phút). Facebook & YouTube yêu cầu tối thiểu 10 phút. Hệ thống tự động đẩy sang: {adj_vn} để API không bị từ chối!")

                sched_dt = adjusted_dt



            fb_scheduled_ts = int(sched_dt.timestamp())

            yt_publish_at = sched_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        except Exception as e_ts:

            task["logs"].append(f"⚠️ Lỗi xử lý thời gian hẹn giờ: {e_ts}")



    # 1. FACEBOOK

    if "facebook" in platforms:

        if task_id in cancelled_tasks:

            task["status"] = "CANCELLED"

            task["current_platform"] = None

            task["progress_detail"] = "Đã hủy bởi người dùng"

            task["logs"].append("🛑 Tác vụ đã được người dùng nhấn HỦY ĐĂNG!")

            return



        task["current_platform"] = "facebook"

        task["logs"].append("▶️ Đang đăng lên Facebook Reels...")

        task["progress_detail"] = "Facebook Reels"

        try:

            fb_cfg = b_data.get("facebook", {})

            fb_uploader = FacebookReelsUploader(page_id=fb_cfg["page_id"], access_token=fb_cfg["access_token"])

            res_fb = fb_uploader.upload_reel(

                video_path=video_path,

                title=title,

                caption=caption_fb,

                comment_text=comments_list_fb,

                scheduled_time=fb_scheduled_ts,

                log_cb=task_log

            )

            if res_fb and res_fb.get("reel_url"):

                results["Facebook"] = res_fb.get("reel_url")

                successful_platforms.append("facebook")

                status_msg = "(hẹn giờ)" if fb_scheduled_ts else ""

                task["logs"].append(f"✅ Facebook Reels thành công {status_msg}: {res_fb.get('reel_url')}")

                has_fb_cust = any(p.get("platform") == "facebook" for p in products)

                fb_cust_txt = " (dùng link custom Facebook)" if has_fb_cust else ""

                task["logs"].append(f"💬 Đã gán {len(comments_list_fb)} bình luận affiliate{fb_cust_txt} xuống Bình Luận (Caption giữ sạch 100% để tối ưu tương tác Facebook Reels)!")



                # Tự động share lên Facebook Story (chỉ khi đăng ngay, không hẹn giờ)

                if not fb_scheduled_ts:

                    try:

                        fb_vid_id_story = res_fb.get("video_id")

                        if fb_vid_id_story:

                            story_res = fb_uploader.share_to_story(fb_vid_id_story)

                            if story_res and story_res.get("success"):

                                task["logs"].append("📖 Đã tự động share lên Facebook Story!")

                            else:

                                task["logs"].append("⚠️ Share Facebook Story không thành công (Reel vẫn đăng bình thường).")

                    except Exception as _e_story:

                        task["logs"].append(f"⚠️ Lỗi share Facebook Story: {_e_story}")



                try:

                    record_api_published_video(

                        video_id=res_fb.get("video_id") or res_fb.get("post_id"),

                        platform="facebook",

                        brand_key=brand_key,

                        title=title,

                        app_name="Facebook Graph API (My_Post)",

                        url=res_fb.get("reel_url")

                    )

                except Exception as _e_reg:

                    print(f"⚠️ Không thể lưu registry FB: {_e_reg}")



                # Cập nhật Thumbnail tùy chỉnh cho Facebook Video nếu có

                if thumbnail_path and os.path.exists(thumbnail_path):

                    try:

                        fb_vid_id = res_fb.get("video_id") or res_fb.get("post_id")

                        if fb_vid_id:

                            with open(thumbnail_path, "rb") as thumb_f:

                                r_th = requests.post(

                                    f"https://graph.facebook.com/v19.0/{fb_vid_id}/thumbnails",

                                    data={"access_token": fb_cfg["access_token"], "is_preferred": "true"},

                                    files={"source": thumb_f},

                                    timeout=20

                                )

                                if r_th.status_code == 200:

                                    task["logs"].append("🖼️ Đã cập nhật ảnh bìa Thumbnail cho Facebook Reel thành công!")

                                else:

                                    print(f"⚠️ Lỗi update thumbnail FB: {r_th.text}")

                    except Exception as _e_th:

                        print(f"⚠️ Không thể cập nhật thumbnail FB: {_e_th}")

            else:

                err_msg = (res_fb.get("error") if isinstance(res_fb, dict) else None) or getattr(fb_uploader, "last_error", None) or "Lỗi không xác định từ Meta API"

                results["Facebook"] = f"Thất bại: {err_msg}"

                failed_platforms.append("facebook")

                task["logs"].append(f"❌ Facebook Reels thất bại! Lý do: {err_msg}")

        except Exception as e:

            results["Facebook"] = f"Lỗi: {e}"

            failed_platforms.append("facebook")

            task["logs"].append(f"❌ Lỗi Facebook: {e}")

        completed_count += 1

        task["progress"] = int(completed_count / total_platforms * 100)



    # 2. YOUTUBE SHORTS

    if "youtube" in platforms:

        if task_id in cancelled_tasks:

            task["status"] = "CANCELLED"

            task["current_platform"] = None

            task["progress_detail"] = "Đã hủy bởi người dùng"

            task["logs"].append("🛑 Tác vụ đã được người dùng nhấn HỦY ĐĂNG!")

            return



        task["current_platform"] = "youtube"

        schedule_label = " (hẹn giờ)" if yt_publish_at else ""

        task["logs"].append(f"▶️ Đang đăng lên YouTube Shorts{schedule_label} & Bình luận...")

        task["progress_detail"] = "YouTube Shorts"

        try:

            yt_cfg = b_data.get("youtube", {})

            token_file = os.path.join(POST_DIR, yt_cfg["token_file"])

            yt_uploader = YouTubeShortsUploader(token_file=token_file)

            if yt_uploader.authenticate():

                # KIỂM TRA VÀ TỰ ĐỘNG CHÈN LINK AFFILIATE VÀO MÔ TẢ YOUTUBE SHORTS

                yt_desc, yt_injected, yt_urls = _build_yt_description(

                    description=caption,

                    tags=combined_tags_list,

                    comments_list_yt=comments_list_yt,

                    products=products,

                    brand_key=brand_key

                )

                if yt_injected and yt_urls:

                    task["logs"].append(f"🔍 Kiểm tra mô tả YouTube: Chưa có link Shopee -> Tự động chèn {len(yt_urls)} link Affiliate vào Mô tả video:")

                    for u in yt_urls[:3]:

                        task["logs"].append(f"   👉 Link Shopee: {u}")

                elif not yt_injected and any(d in caption.lower() for d in ["shopee.vn", "s.shopee.vn", "shope.ee"]):

                    task["logs"].append("🔍 Kiểm tra mô tả YouTube: Đã có sẵn link Shopee Affiliate trong mô tả video.")

                else:

                    task["logs"].append("ℹ️ Kiểm tra mô tả YouTube: Không tìm thấy link Shopee affiliate để chèn.")



                res_yt = yt_uploader.upload_short(

                    video_path=video_path,

                    title=_build_yt_title(title, combined_tags_list),

                    description=yt_desc,

                    tags=combined_tags_list if combined_tags_list else ["shorts", "review", "affiliate"],

                    comment_text=None,  # Để None để upload_short không tự comment; app.py quản lý comment bên dưới kèm log và chống trùng lặp tuyệt đối

                    publish_at=yt_publish_at,

                    log_cb=task_log

                )

                if res_yt and res_yt.get("video_id"):

                    vid = res_yt.get("video_id")

                    shorts_url = res_yt.get("shorts_url")

                    results["YouTube"] = shorts_url

                    successful_platforms.append("youtube")

                    task["logs"].append(f"✅ YouTube Shorts thành công{schedule_label}: {shorts_url}")

                    if yt_injected and yt_urls:

                        task["logs"].append("🛒 Mô tả (Description) YouTube Shorts đã được tự động chèn đầy đủ link Shopee Affiliate!")

                    elif not yt_injected and any(d in caption.lower() for d in ["shopee.vn", "s.shopee.vn", "shope.ee"]):

                        task["logs"].append("🛒 Mô tả (Description) YouTube Shorts đã có sẵn link Shopee Affiliate!")

                    try:

                        record_api_published_video(

                            video_id=vid,

                            platform="youtube",

                            brand_key=brand_key,

                            title=title,

                            app_name="YouTube Data API (Tool)",

                            url=shorts_url

                        )

                    except Exception as _e_reg:

                        print(f"⚠️ Không thể lưu registry YT: {_e_reg}")



                    # Cập nhật Thumbnail cho YouTube Video nếu có

                    if thumbnail_path and os.path.exists(thumbnail_path):

                        try:

                            from googleapiclient.http import MediaFileUpload

                            media_thumb = MediaFileUpload(thumbnail_path, mimetype="image/jpeg", resumable=True)

                            yt_uploader.youtube.thumbnails().set(

                                videoId=vid,

                                media_body=media_thumb

                            ).execute()

                            task["logs"].append("🖼️ Đã cập nhật ảnh bìa Thumbnail cho YouTube Shorts thành công!")

                        except Exception as _e_yt_th:

                            print(f"⚠️ Không thể cập nhật thumbnail YouTube: {_e_yt_th}")



                    # Bình luận YouTube (CHỈ COMMENT ĐÚNG 1 CÂU ĐIỀU HƯỚNG MẶC ĐỊNH CHO TẤT CẢ 10 KÊNH - KHÔNG COMMENT LINK AFFILIATE)

                    if not yt_publish_at:

                        yt_guide_comment = "📌 Link sản phẩm mình để ở dưới phần mô tả của video nhé"

                        task["logs"].append("💬 Đang kiểm tra và đăng bình luận điều hướng lên YouTube...")

                        try:

                            existing_texts, existing_links = get_existing_yt_comments(yt_uploader.youtube, vid)

                            if yt_guide_comment.strip().lower() in existing_texts:

                                task["logs"].append("  ℹ️ Bình luận điều hướng đã tồn tại trên video (chống trùng lặp).")

                            else:

                                time.sleep(2)

                                yt_uploader.youtube.commentThreads().insert(

                                    part="snippet",

                                    body={

                                        "snippet": {

                                            "videoId": vid,

                                            "topLevelComment": {

                                                "snippet": {

                                                    "textOriginal": yt_guide_comment

                                                }

                                            }

                                        }

                                    }

                                ).execute()

                                task["logs"].append(f'  ✅ Đã đăng bình luận: "{yt_guide_comment}"')

                        except Exception as ce:

                            err_str = str(ce).lower()

                            if "quotaexceeded" in err_str or "403" in err_str or "quota" in err_str:

                                task["logs"].append("  ⚠️ YouTube API quota hết hôm nay. Link affiliate đã có sẵn trong Mô tả video.")

                            elif "commentsdisabled" in err_str or "disabled" in err_str:

                                task["logs"].append("  ⚠️ Video này đã tắt bình luận — link đã có trong Mô tả.")

                            elif "videoidrequired" in err_str or "notfound" in err_str:

                                task["logs"].append("  ⚠️ Video chưa được YouTube index xong, không thể comment ngay. Link đã có trong Mô tả.")

                            else:

                                task["logs"].append(f"  ⚠️ Bình luận YouTube: {str(ce)[:120]}")

                    else:

                        task["logs"].append("⏰ YouTube hẹn giờ: Đã bảo đảm link sản phẩm trong Mô tả (video chưa public nên chưa thể ghim comment)")

                else:

                    err_msg = (res_yt.get("error") if isinstance(res_yt, dict) else None) or getattr(yt_uploader, "last_error", None) or "Lỗi không xác định từ YouTube Data API"

                    results["YouTube"] = f"Thất bại: {err_msg}"

                    failed_platforms.append("youtube")

                    task["logs"].append(f"❌ YouTube Shorts thất bại! Lý do: {err_msg}")

            else:

                err_msg = getattr(yt_uploader, "last_error", None) or "Không thể xác thực Token OAuth2"

                results["YouTube"] = f"Lỗi xác thực: {err_msg}"

                failed_platforms.append("youtube")

                task["logs"].append(f"❌ Không xác thực được YouTube Token! Lý do: {err_msg}")

        except Exception as e:

            results["YouTube"] = f"Lỗi: {e}"

            failed_platforms.append("youtube")

            task["logs"].append(f"❌ Lỗi YouTube: {e}")

        completed_count += 1

        task["progress"] = int(completed_count / total_platforms * 100)



    # 3. THREADS VIDEO

    if "threads" in platforms:

        if task_id in cancelled_tasks:

            task["status"] = "CANCELLED"

            task["progress_detail"] = "Đã hủy bởi người dùng"

            task["logs"].append("🛑 Tác vụ đã được người dùng nhấn HỦY ĐĂNG!")

            return



        if ig_threads_deferred:

            # Hẹn giờ: lưu vào scheduler queue

            task["logs"].append("⏰ Threads: Đã lưu vào hàng đợi hẹn giờ (scheduler worker)")

            task["progress_detail"] = "Threads → Scheduler Queue"

            try:

                from POST.scheduler import load_queue as sq_load, save_queue as sq_save, QUEUE_FILE

                sq = sq_load()

                th_task = {

                    "id": f"task_th_{task_id}",

                    "brand_key": brand_key,

                    "video_path": os.path.abspath(video_path),

                    "title": title,

                    "caption": (caption or "").strip()[:490] + "..." if len((caption or "").strip()) > 500 else (caption or "").strip(),

                    "comment": "\n".join(comments_list_th),

                    "platforms": ["threads"],

                    "scheduled_time_str": sched_dt.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S") if is_scheduled else "",

                    "scheduled_timestamp": int(sched_dt.timestamp()) if is_scheduled else 0,

                    "status": "PENDING"

                }

                sq.append(th_task)

                sq_save(sq)

                results["Threads"] = f"Đã lên lịch hẹn giờ"

                successful_platforms.append("threads")

                task["logs"].append(f"  ✅ Đã thêm vào queue: {th_task['id']}")

            except Exception as e:

                results["Threads"] = f"Lỗi queue: {e}"

                failed_platforms.append("threads")

                task["logs"].append(f"  ❌ Lỗi thêm Threads vào queue: {e}")

        else:

            # Đăng ngay

            task["current_platform"] = "threads"

            task["logs"].append("▶️ Đang đăng lên Threads Video...")

            task["progress_detail"] = "Threads Video"

            try:

                th_cfg = b_data.get("threads", {})

                # Truncate caption đúng 500 ký tự trước khi truyền vào uploader

                threads_caption = str(caption or "").strip()

                if len(threads_caption) > 497:

                    threads_caption = threads_caption[:494] + "..."

                th_uploader = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])

                res_th = th_uploader.upload_video_thread(

                    video_path=video_path,

                    caption=threads_caption,

                    comment_link=comments_list_th,

                    log_cb=task_log

                )

                if res_th and res_th.get("id"):

                    post_id = res_th.get("id")

                    permalink = res_th.get("permalink", f"https://www.threads.com/post/{post_id}")

                    results["Threads"] = permalink

                    successful_platforms.append("threads")

                    task["logs"].append(f"✅ Threads Video thành công: {permalink}")

                    task["logs"].append("💬 Đã tự động reply các link affiliate trên Threads!")

                    try:

                        record_api_published_video(

                            video_id=post_id,

                            platform="threads",

                            brand_key=brand_key,

                            title=title,

                            app_name="Threads API (Tool)",

                            url=permalink

                        )

                    except Exception as _e_reg:

                        print(f"⚠️ Không thể lưu registry TH: {_e_reg}")

                else:

                    err_msg = (res_th.get("error") if isinstance(res_th, dict) else None) or getattr(th_uploader, "last_error", None) or "Lỗi không xác định từ Threads API"

                    results["Threads"] = f"Thất bại: {err_msg}"

                    failed_platforms.append("threads")

                    task["logs"].append(f"❌ Threads đăng bài thất bại! Lý do: {err_msg}")

            except Exception as e:

                results["Threads"] = f"Lỗi: {e}"

                failed_platforms.append("threads")

                task["logs"].append(f"❌ Lỗi Threads: {e}")

        completed_count += 1

        task["progress"] = int(completed_count / total_platforms * 100)



    # 4. INSTAGRAM REELS (Đăng cuối cùng sau Facebook, YouTube, Threads - giãn cách 1 phút giữa các kênh)

    if "instagram" in platforms:

        if task_id in cancelled_tasks:

            task["status"] = "CANCELLED"

            task["progress_detail"] = "Đã hủy bởi người dùng"

            task["logs"].append("🛑 Tác vụ đã được người dùng nhấn HỦY ĐĂNG!")

            return



        if ig_threads_deferred:

            # Hẹn giờ: lưu vào scheduler queue, worker sẽ upload đúng giờ

            task["logs"].append("⏰ Instagram: Đã lưu vào hàng đợi hẹn giờ (scheduler worker)")

            task["progress_detail"] = "Instagram → Scheduler Queue"

            try:

                from POST.scheduler import load_queue as sq_load, save_queue as sq_save, QUEUE_FILE

                sq = sq_load()

                ig_task = {

                    "id": f"task_ig_{task_id}",

                    "brand_key": brand_key,

                    "video_path": os.path.abspath(video_path),

                    "title": title,

                    "caption": caption,

                    "comment": "\n".join(comments_list_ig),

                    "platforms": ["instagram"],

                    "scheduled_time_str": sched_dt.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S") if is_scheduled else "",

                    "scheduled_timestamp": int(sched_dt.timestamp()) if is_scheduled else 0,

                    "status": "PENDING"

                }

                sq.append(ig_task)

                sq_save(sq)

                results["Instagram"] = f"Đã lên lịch hẹn giờ"

                successful_platforms.append("instagram")

                task["logs"].append(f"  ✅ Đã thêm vào queue: {ig_task['id']}")

            except Exception as e:

                results["Instagram"] = f"Lỗi queue: {e}"

                failed_platforms.append("instagram")

                task["logs"].append(f"  ❌ Lỗi thêm IG vào queue: {e}")

        else:

            # Đăng ngay: dùng InstagramReelsUploader với hàng đợi điều tiết an toàn 1 phút giữa các kênh

            task["logs"].append("⏳ [Instagram Queue] Đang chờ lượt điều tiết an toàn (giãn cách 1 phút giữa các kênh)...")

            task["progress_detail"] = "Instagram: Chờ lượt..."



            # Sử dụng instagram_upload_lock để đảm bảo chỉ 1 kênh đăng Instagram tại 1 thời điểm

            with instagram_upload_lock:

                global last_instagram_finish_time

                import time as _time



                # Kiểm tra hủy tác vụ trong khi chờ đến lượt

                if task_id in cancelled_tasks:

                    task["status"] = "CANCELLED"

                    task["progress_detail"] = "Đã hủy bởi người dùng"

                    task["logs"].append("🛑 Tác vụ đã được người dùng nhấn HỦY ĐĂNG trong lúc chờ Instagram!")

                    return



                # Nếu kênh trước vừa đăng xong, giãn cách an toàn 60 giây (1 phút)

                now_ts = _time.time()

                time_since_last = now_ts - last_instagram_finish_time

                if last_instagram_finish_time > 0 and time_since_last < INSTAGRAM_DELAY_SECONDS:

                    wait_sec = int(INSTAGRAM_DELAY_SECONDS - time_since_last)

                    task["logs"].append(f"⏱️ [Instagram Delay] Giãn cách an toàn {wait_sec}s để Meta xử lý xong video kênh trước...")

                    for s in range(wait_sec, 0, -5):

                        if task_id in cancelled_tasks:

                            task["status"] = "CANCELLED"

                            return

                        task["progress_detail"] = f"Instagram: Giãn cách {s}s"

                        _time.sleep(min(5, s))



                task["current_platform"] = "instagram"

                task["logs"].append("▶️ Đang đăng lên Instagram Reels...")

                task["progress_detail"] = "Instagram Reels"

                try:

                    from uploaders.instagram_uploader import InstagramReelsUploader

                    ig_cfg = b_data.get("instagram", {})

                    ig_token = ig_cfg.get("access_token", "")

                    ig_user_id = ig_cfg.get("ig_user_id", "")

                    ig_uploader = InstagramReelsUploader(ig_user_id=ig_user_id, access_token=ig_token)

                    ig_caption = _build_ig_caption(title, caption, combined_tags_list)

                    res_ig = ig_uploader.upload_reel(

                        video_path=video_path,

                        caption=ig_caption,

                        comment_text=comments_list_ig,

                        log_cb=task_log

                    )

                    if res_ig and res_ig.get("success"):

                        m_id = res_ig.get("media_id", "")

                        permalink = res_ig.get("permalink") or (f"https://www.instagram.com/reel/{m_id}/" if m_id else "")

                        results["Instagram"] = permalink or f"Media ID: {m_id}"

                        successful_platforms.append("instagram")

                        has_ig_cust = any(p.get("platform") == "instagram" for p in products)

                        ig_cust_txt = " (link custom Instagram)" if has_ig_cust else ""

                        task["logs"].append(f"✅ Instagram Reel thành công: {permalink or m_id}{ig_cust_txt}")



                        # Tự động tạo Instagram Story từ Reel vừa đăng

                        try:

                            story_res = ig_uploader.share_to_story(m_id, video_path=video_path)

                            if story_res and story_res.get("success"):

                                task["logs"].append("📖 Đã tự động tạo Instagram Story từ Reel!")

                            else:

                                task["logs"].append("⚠️ Tạo Instagram Story không thành công (Reel vẫn đăng bình thường).")

                        except Exception as _e_story:

                            task["logs"].append(f"⚠️ Lỗi tạo Instagram Story: {_e_story}")



                        try:

                            record_api_published_video(

                                video_id=m_id,

                                platform="instagram",

                                brand_key=brand_key,

                                title=title,

                                app_name="Instagram Graph API (Tool)",

                                url=permalink or ""

                            )

                        except Exception as _e_reg:

                            print(f"⚠️ Không thể lưu registry IG: {_e_reg}")

                    else:

                        err_msg = (res_ig.get("error") if isinstance(res_ig, dict) else None) or getattr(ig_uploader, "last_error", None) or "Lỗi không xác định từ Meta API"

                        results["Instagram"] = f"Thất bại: {err_msg}"

                        failed_platforms.append("instagram")

                        task["logs"].append(f"❌ Instagram Reels thất bại! Lý do: {err_msg}")

                except Exception as e:

                    results["Instagram"] = f"Lỗi: {e}"

                    failed_platforms.append("instagram")

                    task["logs"].append(f"❌ Lỗi Instagram: {e}")

                finally:

                    last_instagram_finish_time = _time.time()

        completed_count += 1

        task["progress"] = int(completed_count / total_platforms * 100)






    task["progress"] = 100

    task["current_platform"] = None

    task["results"] = results

    task["failed_platforms"] = failed_platforms

    task["successful_platforms"] = successful_platforms



    if failed_platforms:

        task["status"] = "FAILED"

        if successful_platforms:

            task["progress_detail"] = f"Lỗi {len(failed_platforms)}/{total_platforms} nền tảng ({', '.join(failed_platforms)})"

            task["logs"].append(f"⚠️ Có {len(failed_platforms)} nền tảng lỗi: {', '.join(failed_platforms)}. Hãy nhấn 'Đăng lại lỗi' để thử lại!")

        else:

            task["progress_detail"] = "Đăng thất bại hoàn toàn"

            task["logs"].append(f"❌ Toàn bộ nền tảng ({', '.join(failed_platforms)}) đều thất bại!")

    else:

        task["status"] = "COMPLETED"

        task["progress_detail"] = "Hoàn tất"

        if ig_threads_deferred:

            task["logs"].append("🎉 HOÀN TẤT! FB/YouTube đã đăng (hẹn giờ API). IG/Threads sẽ được scheduler worker đăng đúng giờ.")

        else:

            task["logs"].append("🎉 HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ĐĂNG BÀI!")



    try:

        save_persisted_tasks()

        if successful_platforms:

            inject_task_into_analytics_cache(task)

    except Exception as _e_sync_cache:

        print(f"⚠️ Lỗi lưu persisted tasks hoặc inject cache: {_e_sync_cache}")





def run_manual_adspower_task(task_id, params):

    """Worker chạy trong background thực hiện mở 4 tab và tải video lên qua AdsPower."""

    task = tasks.get(task_id)

    if not task:

        return

    task["params"] = params

    brand_key = params["brand_key"]

    brand_name = params.get("brand_name", brand_key)

    video_path = params["video_path"]

    title = params.get("title", "")

    caption = params.get("caption", "")

    platforms = params.get("platforms", ["youtube", "facebook", "instagram", "threads"])

    comments_map = params.get("comments_map", {})

    privacy = params.get("privacy", "private")



    def progress_callback(pct, msg):

        if pct is not None:

            task["progress"] = pct

        if msg:

            task["progress_detail"] = msg

            task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

            print(f"[{brand_name}] ({task.get('progress', 0)}%) {msg}")



    try:

        progress_callback(5, f"🚀 Khởi động đăng qua AdsPower cho kênh '{brand_name}' ({'Chế độ riêng tư' if privacy == 'private' else 'Chế độ công khai'})...")

        from adspower_manual_poster import AdsPowerManualPoster

        brands = load_brands()

        profile_id = brands.get(brand_key, {}).get("adspower_id")



        poster = AdsPowerManualPoster()

        poster.post_all(

            profile_id=profile_id,

            video_path=video_path,

            title=title,

            caption=caption,

            platforms=platforms,

            comments_map=comments_map,

            privacy=privacy,

            progress_cb=progress_callback

        )

        task["status"] = "COMPLETED"

        task["progress"] = 100

        task["progress_detail"] = "Đã đăng hoàn tất 4 nền tảng và bình luận link affiliate!"

        task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 Hoàn tất đăng 4 nền tảng và comment affiliate!")

        task["results"] = {

            "YouTube": "Đã xuất bản (Không công khai / Unlisted)",

            "Facebook": "Đã xuất bản Facebook Reels",

            "Instagram": "Đã xuất bản Instagram Reels",

            "Threads": "Đã xuất bản Threads"

        }

    except Exception as e:

        import traceback

        traceback.print_exc()

        task["status"] = "FAILED"

        task["progress_detail"] = f"Lỗi AdsPower: {str(e)}"

        task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Lỗi: {e}")

    finally:

        try:

            save_persisted_tasks()

        except Exception:

            pass





@app.route("/api/start_upload", methods=["POST"])

def start_upload():

    try:

        data = request.json or {}

        brand_key = data.get("brand_key")

        video_path = (data.get("video_path") or "").strip()

        excel_path = (data.get("excel_path") or "").strip()

        title = (data.get("title") or "").strip()

        caption = (data.get("caption") or "").strip()

        platforms = data.get("platforms", ["youtube", "facebook", "instagram", "threads"])

        youtube_tags = data.get("youtube_tags", [])  # Danh sách tag từ frontend

        schedule_time = (data.get("schedule_time") or "").strip()  # ISO datetime string



        if not brand_key or not video_path:

            return jsonify({"success": False, "message": "Vui lòng chọn kênh và đường dẫn video!"}), 400



        if not os.path.exists(video_path):

            return jsonify({"success": False, "message": f"Không tìm thấy file video: {video_path}"}), 400



        if not excel_path:

            return jsonify({"success": False, "message": "Bắt buộc: Vui lòng nhập đường dẫn file Excel/CSV hoặc dán link Shopee affiliate!"}), 400



        if not title:

            return jsonify({"success": False, "message": "Bắt buộc: Vui lòng nhập tiêu đề video!"}), 400



        if not caption:

            return jsonify({"success": False, "message": "Bắt buộc: Vui lòng nhập caption / mô tả cho video!"}), 400



        # Đọc sản phẩm — hỗ trợ cả file xlsx/csv lẫn URL affiliate dán trực tiếp (1 hoặc nhiều file/link)

        products = []

        if excel_path:

            try:

                products = load_all_products_from_input(excel_path)

                if _is_direct_url_input(excel_path) and products and video_path:

                    saved_csv = _save_links_as_csv(excel_path, video_path)

                    if saved_csv:

                        excel_path = saved_csv   # Cập nhật excel_path sang file CSV vừa lưu

            except Exception as e:

                return jsonify({"success": False, "message": f"Lỗi đọc file link sản phẩm: {e}"}), 400



        # Tự động lưu/cập nhật link rút gọn vừa thêm vào file danh sách tổng hợp của kênh

        try:

            import sys

            if r"C:\Affiliate" not in sys.path: sys.path.append(r"C:\Affiliate")

            from link_tracker_sync import record_published_short_links

            record_published_short_links(brand_key, excel_input=excel_path, video_path=video_path, products_list=products)

        except Exception as _e_sync:

            print(f"⚠️ Lỗi cập nhật file danh sách link: {_e_sync}")



        # Auto-gen tags nếu chưa có

        if not youtube_tags and products:

            youtube_tags = generate_seo_tags([p["name"] for p in products])



        brands = load_brands()

        brand_name = brands.get(brand_key, {}).get("name", brand_key)



        # Tính schedule display

        schedule_display = ""

        initial_status = "RUNNING"

        if schedule_time:

            try:

                sched_dt = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))

                vn_tz = timezone(timedelta(hours=7))

                schedule_display = sched_dt.astimezone(vn_tz).strftime("%H:%M %d/%m/%Y")

                initial_status = "SCHEDULED"

            except Exception:

                pass



        task_id = str(uuid.uuid4())[:8]

        tasks[task_id] = {

            "id": task_id,

            "brand_key": brand_key,

            "brand_name": brand_name,

            "status": initial_status,

            "progress": 0,

            "progress_detail": f"Hẹn giờ: {schedule_display}" if schedule_display else "Khởi tạo...",

            "created_at": datetime.now().strftime("%H:%M:%S"),

            "created_date": datetime.now().strftime("%d/%m/%Y"),

            "logs": [],

            "results": {},

            "video_path": video_path,

            "video_name": os.path.basename(video_path),

            "platforms": platforms,

            "schedule_display": schedule_display,

            "youtube_tags": youtube_tags

        }



        # Dọn dẹp task cũ nếu quá nhiều

        while len(tasks) > MAX_TASKS_HISTORY:

            tasks.popitem(last=False)



        params = {

            "brand_key": brand_key,

            "brand_name": brand_name,

            "video_path": video_path,

            "title": title or "Video Review Sản Phẩm Chất Lượng",

            "caption": caption or "Xem chi tiết và link mua sản phẩm dưới bình luận nhé!",

            "products": products,

            "platforms": platforms,

            "youtube_tags": youtube_tags,

            "schedule_time": schedule_time if schedule_time else None

        }

        tasks[task_id]["params"] = params



        t = threading.Thread(target=run_upload_task, args=(task_id, params), daemon=True)

        t.start()



        return jsonify({"success": True, "task_id": task_id})

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500





@app.route("/api/start_manual_adspower_upload", methods=["POST"])

def start_manual_adspower_upload():

    try:

        data = request.json or {}

        brand_key = data.get("brand_key")

        video_path = (data.get("video_path") or "").strip()

        title = (data.get("title") or "").strip()

        caption = (data.get("caption") or "").strip()

        excel_path = (data.get("excel_path") or "").strip()

        privacy = (data.get("privacy") or "private").strip()



        # Luôn đảm bảo cả 4 nền tảng cho chức năng Đăng thủ công

        platforms = ["youtube", "facebook", "instagram", "threads"]



        # Fallback từ channel_drafts nếu thiếu trường dữ liệu

        drafts = load_channel_drafts()

        draft = drafts.get(brand_key, {})

        if not video_path:

            video_path = (draft.get("video") or "").strip()

        if not title:

            title = (draft.get("title") or "").strip()

        if not caption:

            caption = (draft.get("caption") or "").strip()

        if not excel_path:

            excel_path = (draft.get("excel") or "").strip()



        if not brand_key or not video_path:

            return jsonify({"success": False, "message": "Vui lòng chọn kênh và video!"}), 400



        if not os.path.exists(video_path):

            return jsonify({"success": False, "message": f"Không tìm thấy video: {video_path}"}), 400



        brands = load_brands()

        brand_name = brands.get(brand_key, {}).get("name", brand_key)



        # Parse affiliate comments cho từng nền tảng

        products = []

        comments_map = {}

        if excel_path:

            try:

                products = load_all_products_from_input(excel_path)

                templates = load_comment_templates()

                comments_map = {

                    "facebook": get_platform_comments(products, "facebook", brand_key, templates),

                    "youtube": ["📌 Link sản phẩm mình để ở dưới phần mô tả của video nhé"],

                    "instagram": get_platform_comments(products, "instagram", brand_key, templates),

                    "threads": get_platform_comments(products, "threads", brand_key, templates),

                }

            except Exception as _e_cmt:

                print(f"⚠️ Lỗi phân tích affiliate links: {_e_cmt}")



        # Tự động lưu/cập nhật link rút gọn vừa thêm vào file danh sách tổng hợp (đăng thủ công)

        try:

            import sys

            if r"C:\Affiliate" not in sys.path: sys.path.append(r"C:\Affiliate")

            from link_tracker_sync import record_published_short_links

            record_published_short_links(brand_key, excel_input=excel_path, video_path=video_path, products_list=products)

        except Exception as _e_sync:

            print(f"⚠️ Lỗi cập nhật file danh sách link (thủ công): {_e_sync}")



        task_id = str(uuid.uuid4())[:8]

        tasks[task_id] = {

            "id": task_id,

            "brand_key": brand_key,

            "brand_name": brand_name,

            "status": "RUNNING",

            "progress": 5,

            "progress_detail": f"Đang kết nối AdsPower ({'Riêng tư' if privacy == 'private' else 'Công khai'})...",

            "created_at": datetime.now().strftime("%H:%M:%S"),

            "created_date": datetime.now().strftime("%d/%m/%Y"),

            "logs": [],

            "results": {},

            "video_path": video_path,

            "video_name": os.path.basename(video_path),

            "platforms": platforms,

            "is_manual": True

        }



        params = {

            "brand_key": brand_key,

            "brand_name": brand_name,

            "video_path": video_path,

            "title": title or "Review Sản Phẩm Chất Lượng",

            "caption": caption or "Xem chi tiết và link mua sản phẩm dưới bình luận nhé! #review",

            "excel_path": excel_path,

            "privacy": privacy,

            "comments_map": comments_map,

            "platforms": platforms

        }

        tasks[task_id]["params"] = params



        t = threading.Thread(target=run_manual_adspower_task, args=(task_id, params), daemon=True)

        t.start()



        return jsonify({

            "success": True,

            "task_id": task_id,

            "message": f"Đã bắt đầu đăng thủ công 4 nền tảng ({'Riêng tư' if privacy == 'private' else 'Công khai'}) và chuẩn bị comment affiliate!"

        })

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": str(e)}), 500





@app.route("/api/start_batch_upload", methods=["POST"])

def start_batch_upload():

    try:

        data = request.json or {}

        jobs = data.get("jobs", [])

        if not jobs:

            return jsonify({"success": False, "message": "Không có kênh nào được cấu hình để đăng!"}), 400



        created_task_ids = []

        brands = load_brands()



        for idx, job in enumerate(jobs):

            brand_key = job.get("brand_key")

            video_path = (job.get("video_path") or "").strip()

            excel_path = (job.get("excel_path") or "").strip()

            title = (job.get("title") or "").strip()

            caption = (job.get("caption") or "").strip()



            if not brand_key or not video_path or not excel_path or not title or not caption:

                continue

            if not os.path.exists(video_path):

                continue

            platforms = job.get("platforms", ["youtube", "facebook", "instagram", "threads"])

            youtube_tags = job.get("youtube_tags", [])

            schedule_time = (job.get("schedule_time") or "").strip()



            products = []

            if excel_path:

                try:

                    products = load_all_products_from_input(excel_path)

                    if _is_direct_url_input(excel_path) and products and video_path:

                        saved_csv = _save_links_as_csv(excel_path, video_path)

                        if saved_csv:

                            excel_path = saved_csv

                except Exception:

                    pass



            if not youtube_tags and products:

                youtube_tags = generate_seo_tags([p["name"] for p in products])



            brand_name = brands.get(brand_key, {}).get("name", brand_key)



            schedule_display = ""

            initial_status = "QUEUED"

            if schedule_time:

                try:

                    sched_dt = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))

                    vn_tz = timezone(timedelta(hours=7))

                    schedule_display = sched_dt.astimezone(vn_tz).strftime("%H:%M %d/%m/%Y")

                    initial_status = "SCHEDULED"

                except Exception:

                    pass



            task_id = str(uuid.uuid4())[:8]

            tasks[task_id] = {

                "id": task_id,

                "brand_key": brand_key,

                "brand_name": brand_name,

                "status": initial_status,

                "progress": 0,

                "progress_detail": f"Hẹn giờ: {schedule_display}" if schedule_display else "Đang chờ luồng...",

                "created_at": datetime.now().strftime("%H:%M:%S"),

                "created_date": datetime.now().strftime("%d/%m/%Y"),

                "logs": [f"📋 Đã thêm vào hàng đợi đăng bài cho kênh: {brand_name}"],

                "results": {},

                "video_path": video_path,

                "video_name": os.path.basename(video_path),

                "platforms": platforms,

                "schedule_display": schedule_display,

                "youtube_tags": youtube_tags

            }



            while len(tasks) > MAX_TASKS_HISTORY:

                tasks.popitem(last=False)



            params = {

                "brand_key": brand_key,

                "brand_name": brand_name,

                "video_path": video_path,

                "title": title or f"Review Sản Phẩm Chất Lượng - {brand_name}",

                "caption": caption or "Xem chi tiết và link mua sản phẩm dưới bình luận nhé!",

                "products": products,

                "platforms": platforms,

                "youtube_tags": youtube_tags,

                "schedule_time": schedule_time if schedule_time else None

            }

            tasks[task_id]["params"] = params



            t = threading.Thread(target=run_upload_task, args=(task_id, params), daemon=True)

            t.start()

            created_task_ids.append(task_id)



        if not created_task_ids:

            return jsonify({"success": False, "message": "Không tìm thấy file video hợp lệ nào trong các kênh đã điền!"}), 400



        return jsonify({

            "success": True,

            "message": f"Đã chia luồng an toàn và bắt đầu đăng {len(created_task_ids)} kênh!",

            "task_ids": created_task_ids,

            "count": len(created_task_ids)

        })

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500



@app.route("/api/task_status/<task_id>")

def task_status(task_id):

    if task_id not in tasks:

        return jsonify({"success": False, "message": "Không tìm thấy task"}), 404

    return jsonify({"success": True, "task": tasks[task_id]})



@app.route("/api/all_tasks")

def all_tasks():

    """Trả về tất cả các task đang chạy hoặc đã hoàn tất, tự động hợp nhất với các task hẹn giờ trong schedule_queue"""

    # Đồng bộ thêm các task hẹn giờ chưa chạy từ schedule_queue.json nếu server vừa restart

    try:

        from POST.scheduler import load_queue

        q = load_queue()

        for item in q:

            q_id = item.get("id", "")

            # Lấy task_id gốc nếu có tiền tố task_ig_ hoặc task_th_

            m_tid = q_id

            if m_tid.startswith("task_ig_"):

                m_tid = m_tid[len("task_ig_"):]

            elif m_tid.startswith("task_th_"):

                m_tid = m_tid[len("task_th_"):]



            if m_tid not in tasks and item.get("status") in ["PENDING", "PENDING_WINDOWS_SCHEDULER"]:

                brands = load_brands()

                b_name = brands.get(item.get("brand_key", ""), {}).get("name", item.get("brand_key", ""))

                tasks[m_tid] = {

                    "id": m_tid,

                    "brand_key": item.get("brand_key", ""),

                    "brand_name": b_name,

                    "status": "SCHEDULED",

                    "progress": 50,

                    "progress_detail": f"Hẹn giờ: {item.get('scheduled_time_str', '')}",

                    "created_at": item.get("scheduled_time_str", "").split(" ")[-1] if " " in item.get("scheduled_time_str", "") else "Hẹn giờ",

                    "logs": [

                        f"⏰ Đã lên lịch hẹn giờ cho {b_name}",

                        f"📁 Video: {item.get('video_path', '')}",

                        f"🌐 Nền tảng: {', '.join(item.get('platforms', []))}",

                        f"⏰ Thời gian đăng dự kiến: {item.get('scheduled_time_str', '')}"

                    ],

                    "results": {},

                    "video_path": item.get("video_path", ""),

                    "video_name": os.path.basename(item.get("video_path", "")),

                    "platforms": item.get("platforms", []),

                    "schedule_display": item.get("scheduled_time_str", "")

                }

    except Exception as e_sync:

        print(f"⚠️ Lỗi đồng bộ all_tasks với schedule_queue: {e_sync}")



    save_persisted_tasks()

    return jsonify({"success": True, "tasks": dict(tasks)})



@app.route("/api/cancel_task/<task_id>", methods=["POST"])

def cancel_task(task_id):

    """Hủy một tác vụ đang chạy hoặc đang hẹn giờ"""

    cancelled_tasks.add(task_id)

    task = tasks.get(task_id)

    if not task:

        return jsonify({"success": True, "message": f"Đã đánh dấu hủy tác vụ {task_id}"})



    task["status"] = "CANCELLED"

    task["progress_detail"] = "Đã hủy bởi người dùng"

    task["logs"].append("🛑 Người dùng đã nhấn HỦY ĐĂNG tác vụ này!")



    # Nếu task đang có trong queue hẹn giờ của worker, đổi status trong queue thành CANCELLED

    try:

        from POST.scheduler import load_queue, save_queue

        q = load_queue()

        q_updated = False

        for item in q:

            if item.get("id") in [f"task_ig_{task_id}", f"task_th_{task_id}"] and item.get("status") in ["PENDING", "PENDING_WINDOWS_SCHEDULER"]:

                item["status"] = "CANCELLED"

                item["error"] = "Đã hủy bởi người dùng"

                q_updated = True

        if q_updated:

            save_queue(q)

    except Exception as e:

        print(f"⚠️ Lỗi cập nhật queue khi hủy task: {e}")



    try:

        save_persisted_tasks()

    except Exception:

        pass



    return jsonify({"success": True, "message": f"Đã hủy tác vụ {task_id}", "task": task})



@app.route("/api/retry_failed_tasks", methods=["POST"])

def retry_failed_tasks():

    """

    Đăng lại các tiến trình hoặc nền tảng bị lỗi.

    - Nếu gửi { "task_id": "xxx" }: chỉ đăng lại task cụ thể đó.

    - Nếu không gửi: tìm tất cả các task có status == "FAILED" hoặc có failed_platforms.

    QUAN TRỌNG: CHỈ ĐĂNG LẠI CÁC NỀN TẢNG BỊ LỖI (failed_platforms), giữ nguyên và bỏ qua nền tảng đã thành công.

    """

    try:

        data = request.json or {}

        target_task_id = data.get("task_id")



        candidates = []

        if target_task_id:

            if target_task_id not in tasks:

                return jsonify({"success": False, "message": f"Không tìm thấy tác vụ #{target_task_id}"}), 404

            candidates.append((target_task_id, tasks[target_task_id]))

        else:

            for tid, t in list(tasks.items()):

                # Chỉ lấy task có lỗi hoặc thất bại và chưa được thử lại

                is_failed = t.get("status") in ["FAILED", "ERROR"]

                has_failed_plats = bool(t.get("failed_platforms"))

                is_not_retried = t.get("status") not in ["RETRIED", "RUNNING", "QUEUED"]

                if (is_failed or has_failed_plats) and is_not_retried:

                    candidates.append((tid, t))



        if not candidates:

            return jsonify({"success": False, "message": "Không có tiến trình nào bị lỗi cần đăng lại!"}), 400



        retried_tasks = []

        for tid, t in candidates:

            # Xác định các nền tảng bị lỗi

            failed_platforms = list(t.get("failed_platforms") or [])

            if not failed_platforms:

                succ = set(t.get("successful_platforms") or [])

                all_p = t.get("platforms") or (t.get("params") or {}).get("platforms") or ["facebook", "youtube", "instagram", "threads"]

                failed_platforms = [p for p in all_p if p not in succ]



            if not failed_platforms:

                continue



            params = t.get("params")

            if not params:

                params = {

                    "brand_key": t.get("brand_key"),

                    "brand_name": t.get("brand_name"),

                    "video_path": t.get("video_path") or "",

                    "title": t.get("title") or f"Review Sản Phẩm Chất Lượng - {t.get('brand_name')}",

                    "caption": t.get("caption") or "Xem chi tiết và link mua sản phẩm dưới bình luận nhé!",

                    "products": t.get("products") or [],

                    "platforms": failed_platforms,

                    "youtube_tags": t.get("youtube_tags") or [],

                    "schedule_time": None

                }



            # CHỈ ĐĂNG LẠI CÁC NỀN TẢNG BỊ LỖI

            retry_params = dict(params)

            retry_params["platforms"] = failed_platforms

            retry_params["schedule_time"] = None  # Đăng ngay khi thử lại



            # Đánh dấu task cũ thành RETRIED

            t["status"] = "RETRIED"

            t["logs"].append(f"🔁 Đã kích hoạt đăng lại cho các nền tảng lỗi: {', '.join(failed_platforms)}")



            # Tạo task mới độc lập

            new_task_id = str(uuid.uuid4())[:8]

            brand_name = retry_params.get("brand_name", retry_params.get("brand_key"))



            tasks[new_task_id] = {

                "id": new_task_id,

                "brand_key": retry_params["brand_key"],

                "brand_name": brand_name,

                "status": "QUEUED",

                "progress": 0,

                "progress_detail": f"Đăng lại ({', '.join(failed_platforms)})...",

                "created_at": datetime.now().strftime("%H:%M:%S"),

                "created_date": datetime.now().strftime("%d/%m/%Y"),

                "logs": [

                    f"🔁 ĐĂNG LẠI từ tác vụ gốc #{tid}",

                    f"🎯 Nền tảng thử lại: {', '.join(failed_platforms)} (các nền tảng đã thành công được bỏ qua)"

                ],

                "results": {},

                "video_path": retry_params.get("video_path", ""),

                "video_name": os.path.basename(retry_params.get("video_path", "")),

                "platforms": failed_platforms,

                "schedule_display": "",

                "youtube_tags": retry_params.get("youtube_tags", []),

                "params": retry_params,

                "retried_from": tid

            }



            while len(tasks) > MAX_TASKS_HISTORY:

                tasks.popitem(last=False)



            thread = threading.Thread(target=run_upload_task, args=(new_task_id, retry_params), daemon=True)

            thread.start()



            retried_tasks.append({

                "old_task_id": tid,

                "new_task_id": new_task_id,

                "brand_name": brand_name,

                "platforms": failed_platforms

            })



        if not retried_tasks:

            return jsonify({"success": False, "message": "Không tìm thấy nền tảng lỗi nào cần đăng lại!"}), 400



        return jsonify({

            "success": True,

            "message": f"Đã bắt đầu đăng lại {len(retried_tasks)} tác vụ lỗi!",

            "retried_count": len(retried_tasks),

            "retried_tasks": retried_tasks

        })

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500





def load_scheduled_tasks():

    queue_path = os.path.join(POST_DIR, "config", "schedule_queue.json")

    if os.path.exists(queue_path):

        try:

            with open(queue_path, "r", encoding="utf-8") as f:

                return json.load(f)

        except Exception:

            return []

    return []



@app.route("/api/analytics", methods=["GET"])

def get_analytics():

    """

    Fetch dữ liệu video, view, like, comment, và tự động tính Ad Decision Score & Metrics.

    Hỗ trợ Cache nền tức thì (Instant Loading <0.05s).

    Query params:

      - brand: Tên kênh cần lọc (hoặc để trống để lấy tất cả)

      - platform: Nền tảng (youtube, facebook, instagram, threads)

      - limit: Giới hạn số video mỗi nền tảng

      - force_refresh: '1' hoặc 'true' để ép quét trực tiếp từ API thay vì đọc cache

    """

    brand = request.args.get("brand", "").strip() or None

    platform = request.args.get("platform", "").strip() or None

    force_refresh = request.args.get("force_refresh", "").strip().lower() in ["1", "true", "yes"]



    try:

        limit_param = request.args.get("limit", default=None)

        limit = int(limit_param) if limit_param and int(limit_param) > 0 else None

    except Exception:

        limit = None

        

    brands = load_brands()

    cached_info = None

    data = None



    # Nếu không yêu cầu force_refresh, ưu tiên đọc từ cache nền

    if not force_refresh:

        cached_obj = load_cached_analytics()

        if cached_obj and isinstance(cached_obj, dict) and "data" in cached_obj:

            all_cached_data = cached_obj["data"]

            # Nếu có lọc theo brand cụ thể, chỉ trích xuất brand đó

            if brand:

                sel_b_lower = brand.lower()

                data = {k: v for k, v in all_cached_data.items() if k.lower() == sel_b_lower}

            else:

                data = all_cached_data



            # Tự động phục hồi nếu nền tảng/kênh được yêu cầu đang bị lỗi trong cache (loại trừ YouTube để không đốt quota)

            if brand and platform and data and platform.lower() != "youtube":

                b_val = data.get(brand, {})

                plat_val = b_val.get("platforms", {}).get(platform, {})

                if not plat_val.get("success", True) or plat_val.get("error"):

                    print(f"🔄 Cache của {brand} ({platform}) bị lỗi, kích hoạt quét mới trực tiếp để tự phục hồi...")

                    data = None



            if data is not None:

                cached_info = {

                    "is_cached": True,

                    "cached_at": cached_obj.get("cached_at", ""),

                    "cached_timestamp": cached_obj.get("cached_timestamp", 0),

                    "refresh_duration_seconds": cached_obj.get("refresh_duration_seconds", 0)

                }



    # Nếu chưa có cache hoặc người dùng yêu cầu force_refresh: quét trực tiếp

    if data is None:

        import time as _t

        _start_t = _t.time()

        data = fetch_all_channels_data(brands, selected_brand=brand, selected_platform=platform, limit=limit)

        _elapsed = _t.time() - _start_t

        # Nếu quét toàn bộ (không lọc riêng lẻ), lưu lại làm cache mới

        if not brand and not platform:

            save_cached_analytics(data, duration_sec=_elapsed)

        else:

            # Nếu người dùng bấm Ép quét mới riêng 1 brand hoặc 1 platform,

            # cập nhật đúng phần mới quét vào cache hiện có để không làm mất dữ liệu các kênh khác

            try:

                cached_obj = load_cached_analytics()

                if cached_obj and isinstance(cached_obj, dict) and "data" in cached_obj:

                    cur_cache_data = cached_obj["data"]

                    for b_k, b_v in data.items():

                        if b_k in cur_cache_data:

                            if platform:

                                cur_cache_data[b_k]["platforms"][platform] = b_v.get("platforms", {}).get(platform, {})

                            else:

                                cur_cache_data[b_k] = b_v

                            if "cross_platform_sync" in b_v:

                                cur_cache_data[b_k]["cross_platform_sync"] = b_v["cross_platform_sync"]

                    save_cached_analytics(cur_cache_data, duration_sec=_elapsed)

            except Exception as e_cache_merge:

                print(f"⚠️ Lỗi merge cache nền tảng/kênh: {e_cache_merge}")



        cached_info = {

            "is_cached": False,

            "cached_at": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),

            "cached_timestamp": datetime.now().timestamp(),

            "refresh_duration_seconds": round(_elapsed, 2)

        }



    # Đọc danh sách bài đã lên lịch (chỉ hiển thị những bài có lịch hẹn trong tương lai)

    scheduled_tasks = load_scheduled_tasks()

    now_vn = datetime.now()

    pending_tasks = []

    for t in scheduled_tasks:

        if t.get("status") in ["SCHEDULED", "PENDING_WINDOWS_SCHEDULER"]:

            sched_str = t.get("scheduled_time_str")

            if sched_str:

                try:

                    sched_dt = datetime.strptime(sched_str, "%Y-%m-%d %H:%M:%S")

                    if sched_dt <= now_vn:

                        continue

                except Exception:

                    pass

            pending_tasks.append(t)



    # Duyệt qua từng brand và platform để chuẩn hóa dữ liệu

    for b_key, b_val in data.items():

        if not isinstance(b_val, dict):

            continue

        platforms = b_val.get("platforms", {})

        

        for plat_key, plat_val in platforms.items():

            if not isinstance(plat_val, dict):

                continue

            

            # Lọc theo platform nếu có yêu cầu

            if platform and plat_key.lower() != platform.lower():

                continue



            videos = plat_val.get("videos", [])

            for v in videos:

                v["status"] = "published"

                enrich_video_metrics(v)

            

            # Tìm các task hẹn giờ thuộc về brand và platform này

            brand_scheduled_vids = []

            for t in pending_tasks:

                if t.get("brand_key") == b_key:

                    task_plats = [p.lower() for p in t.get("platforms", [])]

                    if plat_key.lower() in task_plats or any(plat_key.lower() in p for p in task_plats):

                        task_title = t.get("title") or t.get("product_keyword") or (t.get("caption", "").split("\n")[0] if t.get("caption") else "Video đã hẹn giờ")

                        sched_vid = {

                            "id": t.get("id"),

                            "platform": plat_key.capitalize(),

                            "title": task_title,

                            "published_at": t.get("scheduled_time_str") or "Lên lịch",

                            "published_at_raw": t.get("scheduled_time_str") or "",

                            "status": "scheduled",

                            "views": 0,

                            "likes": 0,

                            "comments": 0,

                            "subscribers_gained": "-",

                            "avg_watch_time": "-",

                            "duration_seconds": 0,

                            "duration_fmt": "-",

                            "url": "",

                            "thumbnail": "",

                            "upload_source": "api",

                            "upload_source_label": "API",

                            "upload_source_detail": "Lên lịch qua Tool",

                            "upload_source_app": "Affiliate Scheduler",

                            "other_comments_count": 0,

                            "intent_comments_count": 0

                        }

                        enrich_video_metrics(sched_vid)

                        brand_scheduled_vids.append(sched_vid)



            from fetch_analytics import parse_video_sort_key

            videos.sort(key=parse_video_sort_key, reverse=True)

            plat_val["videos"] = brand_scheduled_vids + videos



    # Gắn thông tin số lần tối ưu (optimize_count) cho từng video

    try:

        opt_cache = _load_optimized_videos()

        if opt_cache:

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

                        else:

                            vid_item["optimize_count"] = 0

    except Exception as e_opt_enrich:

        print(f"⚠️ Lỗi enrich optimize_count: {e_opt_enrich}")



    # Tính toán thông tin nhân khẩu học và số lượng người theo dõi toàn diện

    audience_overview = get_channel_audience_analytics(brands, brand_key=brand, raw_analytics_data=data)



    return jsonify({

        "success": True,

        "data": data,

        "audience_overview": audience_overview,

        "cache_info": cached_info,

        "youtube_quota": get_youtube_quota_details()

    })





_youtube_quota_cache = {'ts': 0, 'data': None}



def get_youtube_quota_details():

    """

    Tính toán chi tiết quota YouTube Data API v3:

    - Reset vào 00:00:00 giờ Thái Bình Dương (PT / Pacific Time).

    - Giờ Việt Nam tương ứng: 14:00 (mùa hè PDT, UTC-7) hoặc 15:00 (mùa đông PST, UTC-8).

    - Giới hạn mặc định: 10,000 units / ngày cho toàn bộ project Google Cloud.

    - Kiểm tra thực tế trạng thái hiện tại (AVAILABLE / EXCEEDED).

    """

    import time, datetime, glob, os, json

    from google.oauth2.credentials import Credentials

    from googleapiclient.discovery import build

    from googleapiclient.errors import HttpError



    now_ts = time.time()

    if _youtube_quota_cache['data'] and (now_ts - _youtube_quota_cache['ts'] < 60):

        res = dict(_youtube_quota_cache['data'])

        elapsed = int(now_ts - _youtube_quota_cache['ts'])

        sec_left = max(0, res['total_seconds_left'] - elapsed)

        res['total_seconds_left'] = sec_left

        res['hours_left'] = sec_left // 3600

        res['minutes_left'] = (sec_left % 3600) // 60

        res['seconds_left'] = sec_left % 60

        return res



    now_utc = datetime.datetime.now(datetime.timezone.utc)

    year = now_utc.year

    mar1 = datetime.datetime(year, 3, 1, 2, 0, tzinfo=datetime.timezone.utc)

    dst_start = mar1 + datetime.timedelta(days=(6 - mar1.weekday() + 7) % 7 + 7)

    nov1 = datetime.datetime(year, 11, 1, 2, 0, tzinfo=datetime.timezone.utc)

    dst_end = nov1 + datetime.timedelta(days=(6 - nov1.weekday()) % 7)



    is_dst = dst_start <= now_utc < dst_end

    pt_offset = -7 if is_dst else -8

    pt_tz_name = 'PDT (UTC-7)' if is_dst else 'PST (UTC-8)'



    tz_pt = datetime.timezone(datetime.timedelta(hours=pt_offset))

    tz_vn = datetime.timezone(datetime.timedelta(hours=7))



    now_pt = now_utc.astimezone(tz_pt)

    now_vn = now_utc.astimezone(tz_vn)



    next_midnight_pt = (now_pt + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    time_left = next_midnight_pt - now_pt

    total_seconds = max(0, int(time_left.total_seconds()))

    hours = total_seconds // 3600

    minutes = (total_seconds % 3600) // 60

    seconds = total_seconds % 60



    next_reset_vn = next_midnight_pt.astimezone(tz_vn)



    # Thử gọi 1 request cực nhẹ (1 unit) để xác thực trạng thái sống

    tok_files = glob.glob(r"C:\Affiliate\post1\POST\credentials\youtube_tokens\*.json")

    is_available = True

    error_msg = ''

    tested_token = None



    if tok_files:

        tested_token = tok_files[0]

        try:

            with open(tested_token, 'r') as f:

                t_data = json.load(f)

            creds = Credentials.from_authorized_user_info(t_data)

            youtube = build('youtube', 'v3', credentials=creds)

            youtube.channels().list(mine=True, part='id').execute()

            is_available = True

        except HttpError as he:

            err_str = str(he)

            if 'quotaExceeded' in err_str:

                is_available = False

                error_msg = 'The request cannot be completed because you have exceeded your quota.'

            else:

                error_msg = err_str

        except Exception as e:

            error_msg = str(e)



    data = {

        'status': 'AVAILABLE' if is_available else 'EXCEEDED',

        'is_available': is_available,

        'daily_limit': 10000,

        'now_vn': now_vn.strftime('%H:%M:%S %d/%m/%Y'),

        'now_pt': now_pt.strftime('%H:%M:%S %d/%m/%Y'),

        'pt_tz_name': pt_tz_name,

        'reset_time_vn': next_reset_vn.strftime('%H:%M:%S %d/%m/%Y'),

        'reset_hour_vn': next_reset_vn.strftime('%H:%M'),

        'hours_left': hours,

        'minutes_left': minutes,

        'seconds_left': seconds,

        'total_seconds_left': total_seconds,

        'error_msg': error_msg,

        'project_id': 'fir-5e3b2',

        'tested_token': os.path.basename(tested_token) if tested_token else None

    }

    _youtube_quota_cache['ts'] = now_ts

    _youtube_quota_cache['data'] = data

    return data



@app.route("/api/youtube-quota", methods=["GET"])

def get_youtube_quota_api():

    """API trả về thông tin quota YouTube hiện tại và đếm ngược thời gian refresh"""

    return jsonify({

        "success": True,

        "quota": get_youtube_quota_details()

    })



@app.route("/api/analytics/refresh-cache", methods=["POST"])

def trigger_refresh_analytics_cache():

    """Endpoint kích hoạt chạy ngầm làm mới cache thống kê"""

    brands = load_brands()

    def _bg_job():

        try:

            refresh_analytics_cache_job(brands, limit=None)

        except Exception as e_bg:

            print(f"⚠️ Lỗi refresh cache ngầm: {e_bg}")



    t = threading.Thread(target=_bg_job, daemon=True)

    t.start()

    return jsonify({

        "success": True,

        "message": "Đang chạy ngầm quét và làm mới số liệu cho toàn bộ 10 kênh..."

    })





@app.route("/api/token_quota_status", methods=["GET"])

def api_token_quota_status():

    """Lấy dữ liệu hạn mức token, quota và ngày refresh của YouTube, Meta (FB, IG), Threads."""

    try:

        force = request.args.get("force", "").lower() in ["1", "true", "yes"]

        from POST.token_quota_manager import get_token_quota_status

        data = get_token_quota_status(force_refresh=force)

        return jsonify({"success": True, "data": data})

    except Exception as e:

        return jsonify({"success": False, "error": str(e)}), 500





@app.route("/api/refresh_all_tokens", methods=["POST"])

def api_refresh_all_tokens():

    """Chạy quy trình quét và làm mới token cho toàn bộ hệ thống."""

    try:

        from POST.token_quota_manager import refresh_all_system_tokens

        res = refresh_all_system_tokens()

        return jsonify(res)

    except Exception as e:

        return jsonify({"success": False, "error": str(e)}), 500





@app.route("/api/analytics/compare-source", methods=["GET"])

def compare_publish_source():

    """

    API endpoint so sánh hiệu quả giữa video đăng qua API và video đăng bằng tay (MANUAL).

    Query params:

      - brand_key: Mã kênh (ví dụ: 'noi_that_dung_that', 'all' hoặc để trống để so sánh tất cả kênh)

      - platform: Lọc theo nền tảng (youtube, facebook, instagram, threads hoặc để trống)

      - limit: Số lượng video lấy từ mỗi nền tảng (mặc định 30)

    """

    brand_key = request.args.get("brand_key", "").strip() or request.args.get("brand", "").strip() or None

    platform = request.args.get("platform", "").strip() or None

    try:

        limit = int(request.args.get("limit", 30))

    except Exception:

        limit = 30



    try:

        brands = load_brands()

        raw_data = fetch_all_channels_data(brands, selected_brand=brand_key, selected_platform=platform, limit=limit)

        

        all_videos = []

        for b_k, b_val in raw_data.items():

            if not isinstance(b_val, dict):

                continue

            for plat_k, plat_data in b_val.get("platforms", {}).items():

                if isinstance(plat_data, dict) and plat_data.get("success"):

                    for v in plat_data.get("videos", []):

                        enrich_video_metrics(v)

                        all_videos.append(v)



        comparison = get_publish_source_comparison(all_videos)

        return jsonify({

            "success": True,

            "brand_key": brand_key or "all",

            "platform": platform or "all",

            "total_videos_analyzed": len(all_videos),

            "comparison": comparison

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e),

            "comparison": {

                "API": {"video_count": 0, "median_views": 0.0, "mean_views": 0.0, "avg_engagement_rate": 0.0, "avg_retention_rate": 0.0},

                "MANUAL": {"video_count": 0, "median_views": 0.0, "mean_views": 0.0, "avg_engagement_rate": 0.0, "avg_retention_rate": 0.0}

            }

        }), 500





# ──────── NATIVE FILE PICKER (không copy file, chỉ lấy đường dẫn gốc) ────────

import subprocess



def _open_file_dialog(title, file_filter):

    """Mở hộp thoại chọn file của Windows qua PowerShell, trả về đường dẫn gốc."""

    ps_script = f'''

Add-Type -AssemblyName System.Windows.Forms

$dlg = New-Object System.Windows.Forms.OpenFileDialog

$dlg.Title = "{title}"

$dlg.Filter = "{file_filter}"

$dlg.Multiselect = $false

if ($dlg.ShowDialog() -eq "OK") {{ $dlg.FileName }} else {{ "" }}

'''

    try:

        result = subprocess.run(

            ["powershell", "-NoProfile", "-Command", ps_script],

            capture_output=True, text=True, timeout=120

        )

        path = result.stdout.strip()

        return path if path and os.path.exists(path) else None

    except Exception as e:

        print(f"⚠️ Lỗi mở file dialog: {e}")

        return None





def _bring_media_player_to_front():

    """Đưa cửa sổ Media Player lên trên cùng màn hình ngay sau khi mở."""

    import time

    import ctypes

    from ctypes import wintypes



    user32 = ctypes.windll.user32

    DESKTOPENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)



    # Thử tìm cửa sổ trong vòng 3.5 giây

    for _ in range(12):

        time.sleep(0.3)

        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)

        media_hwnds = []



        def enum_callback(hwnd, lparam):

            length = user32.GetWindowTextLengthW(hwnd)

            if length > 0:

                buff = ctypes.create_unicode_buffer(length + 1)

                user32.GetWindowTextW(hwnd, buff, length + 1)

                t = buff.value.lower()

                if "media player" in t:

                    media_hwnds.append(hwnd)

            return True



        if hdesk:

            user32.EnumDesktopWindows(hdesk, DESKTOPENUMPROC(enum_callback), 0)

        else:

            user32.EnumWindows(DESKTOPENUMPROC(enum_callback), 0)



        if media_hwnds:

            for hwnd in media_hwnds:

                try:

                    # Bỏ qua hạn chế SetForegroundWindow của Windows bằng keybd_event Alt

                    user32.ShowWindow(hwnd, 9) # SW_RESTORE

                    user32.BringWindowToTop(hwnd)

                    user32.keybd_event(0x12, 0, 0, 0) # Alt down

                    user32.SetForegroundWindow(hwnd)

                    user32.keybd_event(0x12, 0, 2, 0) # Alt up

                    # Đặt HWND_TOPMOST tạm thời rồi hoàn tác để đảm bảo hiển thị trên mọi cửa sổ

                    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002) # HWND_TOPMOST

                    user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002) # HWND_NOTOPMOST

                except Exception:

                    pass

            break





@app.route("/api/open_video_player", methods=["POST"])

def open_video_player():

    """Mở file video trực tiếp trên máy bằng trình phát Media Player và hiển thị ngay trước màn hình."""

    data = request.get_json(silent=True) or {}

    file_path = (data.get("file_path") or "").strip().strip('"').strip("'")

    if not file_path:

        return jsonify({"success": False, "message": "Đường dẫn video trống"}), 400



    file_path = os.path.normpath(file_path)

    if not os.path.exists(file_path):

        return jsonify({"success": False, "message": f"Không tìm thấy file: {file_path}"}), 404



    try:

        # Kích hoạt mở video bằng Media Player

        os.startfile(file_path)

        # Chạy thread đẩy cửa sổ Media Player lên phía trước màn hình ngay lập tức

        import threading

        threading.Thread(target=_bring_media_player_to_front, daemon=True).start()

        return jsonify({"success": True, "message": f"Đã mở video: {os.path.basename(file_path)}"})

    except Exception as e:

        print(f"⚠️ Lỗi mở video player: {e}")

        return jsonify({"success": False, "message": str(e)}), 500





@app.route("/api/pick_video", methods=["POST"])

def pick_video():

    """Mở hộp thoại Windows chọn file video → trả về đường dẫn gốc (KHÔNG copy file)."""

    path = _open_file_dialog(

        "Chọn Video để đăng",

        "Video Files (*.mp4;*.mov;*.avi;*.mkv)|*.mp4;*.mov;*.avi;*.mkv|All Files (*.*)|*.*"

    )

    if path:

        size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)

        return jsonify({

            "success": True,

            "file_path": path,

            "file_name": os.path.basename(path),

            "size_mb": size_mb

        })

    return jsonify({"success": False, "message": "Chưa chọn file nào"})





@app.route("/api/pick_excel", methods=["POST"])

def pick_excel():

    """Mở hộp thoại Windows chọn file Excel/CSV → trả về đường dẫn gốc + parse sản phẩm."""

    path = _open_file_dialog(

        "Chọn File Link Sản Phẩm",

        "Excel/CSV (*.xlsx;*.xls;*.csv)|*.xlsx;*.xls;*.csv|All Files (*.*)|*.*"

    )

    if path:

        # Parse link sản phẩm trực tiếp từ file gốc

        try:

            products = parse_link_file(path)

            product_names = [p["name"] for p in products]

            auto_tags = generate_seo_tags(product_names)

        except Exception:

            products = []

            auto_tags = []



        return jsonify({

            "success": True,

            "file_path": path,

            "file_name": os.path.basename(path),

            "count": len(products),

            "products": products,

            "auto_tags": auto_tags

        })

    return jsonify({"success": False, "message": "Chưa chọn file nào"})





def _extract_base_key_for_pairing(filename: str) -> str:

    """

    Chuẩn hóa tên file để ghép đôi (auto-pairing) video và link sản phẩm.

    Ví dụ: 'tập 1.mp4' -> 'ep_1', 'Tập 1.xlsx' -> 'ep_1', '1.mp4' -> 'ep_1', 'bàn làm việc.mp4' -> 'bàn làm việc'

    """

    import unicodedata

    name_no_ext = os.path.splitext(filename)[0]

    norm = unicodedata.normalize("NFC", name_no_ext).lower().strip()

    norm = re.sub(r'[_\-\s]+', ' ', norm).strip()

    if re.search(r'^(?:đợt|dot)\s*\d+$', norm):

        return f"batch_{norm}"

    norm = re.sub(r'affiliatebatchcustomlinks\d*', '', norm).strip()

    norm = re.sub(r'batch custom links\s*(\(\d+\))?', '', norm).strip()

    m = re.search(r'(?:t[aậ]p|ep|part|b[àa]i)\s*(\d+)', norm)

    if m:

        return f"ep_{int(m.group(1))}"

    m2 = re.search(r'(?:^|[^\d])(\d+)(?:[^\d]|$)', norm)

    if m2:

        return f"ep_{int(m2.group(1))}"

    return norm





def is_old_batch_folder(path_or_name: str) -> bool:

    """

    Kiểm tra xem thư mục hoặc file có thuộc các đợt cũ (< đợt 4, ví dụ: đợt 1, đợt 2, đợt 3) hay không.

    Theo yêu cầu người dùng: Chỉ tính từ thư mục 'đợt 4' trở đi (đợt 4, đợt 5, đợt 6,...).

    Các đợt 1, đợt 2, đợt 3 (hoặc đợt < 4) là các đợt cũ đã đăng xong, cần loại bỏ hoàn toàn khỏi video chưa đăng.

    """

    if not path_or_name:

        return False

    import unicodedata

    norm = unicodedata.normalize("NFC", str(path_or_name)).lower().replace("\\", "/")

    # Tìm các số đợt xuất hiện trong đường dẫn (ví dụ: đợt 1, đợt 2, đợt 3, dot 1, dot 2, dot 3, đợt_1, dot_2, dot_3)

    matches = re.findall(r'(?:đợt|dot)[\s_-]*(\d+)', norm)

    for m in matches:

        try:

            if int(m) < 4:

                return True

        except ValueError:

            pass

    return False





def find_brand_viet_hoa_folder(brand_dir: str):

    """

    Tìm thư mục 'video_việt_hóa' hoặc 'video_viet_hoa' của brand.

    Thư mục này chứa toàn bộ các video (cả 'video chưa đăng' và 'video đã đăng').

    """

    if not brand_dir or not os.path.exists(brand_dir):

        return None

    import unicodedata

    candidates = []

    try:

        for d in os.listdir(brand_dir):

            full_sub = os.path.join(brand_dir, d)

            if os.path.isdir(full_sub):

                norm = unicodedata.normalize("NFC", d).lower()

                if "việt_hóa" in norm or "viet_hoa" in norm or "video_việt" in norm or "video_viet" in norm:

                    candidates.append(full_sub)

    except Exception:

        pass

    if candidates:

        return candidates[0]

    return None





def find_brand_chua_dang_folder(brand_dir: str):

    """

    Tìm thư mục 'video chưa đăng' hoặc 'video chua dang' trong thư mục của brand.

    Ưu tiên thư mục nằm trong 'video_việt_hóa' / 'video_viet_hoa' nếu có.

    """

    if not brand_dir or not os.path.exists(brand_dir):

        return None

    candidates = []

    import unicodedata

    for root, dirs, _ in os.walk(brand_dir):

        for d in dirs:

            norm = unicodedata.normalize("NFC", d).lower()

            if "chưa đăng" in norm or "chua dang" in norm:

                candidates.append(os.path.join(root, d))

    if not candidates:

        return None

    # Ưu tiên thư mục có 'việt_hóa' hoặc 'viet_hoa'

    candidates.sort(key=lambda p: (

        0 if ("việt_hóa" in unicodedata.normalize("NFC", p).lower() or "viet_hoa" in unicodedata.normalize("NFC", p).lower()) else 1,

        len(p)

    ))

    return candidates[0]





def resolve_brand_folder_path(brand_cfg: dict):

    """Tìm thư mục vật lý thực tế của brand trên ổ đĩa, xử lý sai lệch encoding tiếng Việt có dấu và ưu tiên thư mục chứa video."""

    import unicodedata

    raw_folder = (brand_cfg.get("folder") or "").strip()

    if not raw_folder:

        return None

    parent_dir = AFFILIATE_ROOT  # Thư mục gốc C:\Affiliate

    

    norm_nfc = unicodedata.normalize("NFC", raw_folder).lower()

    norm_nfd = unicodedata.normalize("NFD", raw_folder).lower()

    

    candidates = []

    try:

        for entry in os.listdir(parent_dir):

            full_entry = os.path.join(parent_dir, entry)

            if not os.path.isdir(full_entry):

                continue

            e_nfc = unicodedata.normalize("NFC", entry).lower()

            e_nfd = unicodedata.normalize("NFD", entry).lower()

            if e_nfc == norm_nfc or e_nfd == norm_nfd:

                candidates.append(full_entry)

    except Exception:

        pass



    if not candidates:

        direct = os.path.join(parent_dir, raw_folder)

        if os.path.exists(direct) and os.path.isdir(direct):

            return direct

        return None



    if len(candidates) == 1:

        return candidates[0]



    # Nếu có nhiều hơn 1 folder trùng tên (do NFD vs NFC): ưu tiên thư mục chứa video và nhiều file hơn

    def folder_score(p):

        score = 0

        try:

            sub_items = os.listdir(p)

            score += len(sub_items) * 10

            for item in sub_items:

                item_lower = unicodedata.normalize("NFC", item).lower()

                if "video" in item_lower:

                    score += 1000

                if "việt_hóa" in item_lower or "viet_hoa" in item_lower:

                    score += 500

        except Exception:

            pass

        return score



    candidates.sort(key=folder_score, reverse=True)

    return candidates[0]






@app.route("/api/debug-affiliate", methods=["GET"])
def debug_affiliate():
    return jsonify({
        "BASE_DIR": BASE_DIR,
        "AFFILIATE_ROOT": AFFILIATE_ROOT,
        "AFFILIATE_ROOT_exists": os.path.exists(AFFILIATE_ROOT),
        "AFFILIATE_ROOT_list": os.listdir(AFFILIATE_ROOT) if os.path.exists(AFFILIATE_ROOT) else [],
        "resolve_noi_that": resolve_brand_folder_path(load_brands().get("noi_that_dung_that", {}))
    })

@app.route("/api/brand-files", methods=["GET"])

def get_brand_files():

    import unicodedata, re

    """

    Quét toàn bộ thư mục video của brand (bao gồm 'Video chưa đăng' của mọi đợt và 'video đã đăng'):

    - Lọc danh sách video (.mp4, .mov) trong 'Video_việt_hóa' (cả video chưa đăng và đã đăng)

    - Lọc danh sách file excel (.xlsx, .csv) trong 'Video_việt_hóa' và thư mục 'Link customed'

    - Phân loại rõ ràng:

        + Video chưa đăng: sắp xếp theo đợt mới nhất lên đầu, số tập tăng dần

        + Video đã đăng: sắp xếp theo đợt mới nhất, tập và thời gian sửa đổi

    - Tự động ghép cặp (auto-pairing) với file link sản phẩm tương ứng

    - Đề xuất cặp file mới nhất từ video CHƯA ĐĂNG

    """

    brand_key = request.args.get("brand_key", "").strip()

    brands = load_brands()

    if brand_key not in brands:

        return jsonify({"success": False, "message": f"Không tìm thấy brand: {brand_key}"}), 404



    b_cfg = brands[brand_key]

    folder_path = resolve_brand_folder_path(b_cfg)

    if not folder_path or not os.path.exists(folder_path):

        return jsonify({

            "success": True,

            "brand_key": brand_key,

            "folder": b_cfg.get("folder", ""),

            "folder_path": folder_path,

            "chua_dang_path": None,

            "videos": [],

            "excels": [],

            "pairs": [],

            "latest_pair": None,

            "message": "Chưa tìm thấy thư mục của kênh này trên máy tính."

        })



    # Tìm thư mục 'Video_việt_hóa' của brand (chứa cả 'video chưa đăng' và 'video đã đăng')

    viet_hoa_path = find_brand_viet_hoa_folder(folder_path)

    chua_dang_path = find_brand_chua_dang_folder(folder_path)

    scan_video_dir = viet_hoa_path if viet_hoa_path and os.path.exists(viet_hoa_path) else (

        chua_dang_path if chua_dang_path and os.path.exists(chua_dang_path) else folder_path

    )



    video_files = []

    excel_files = []



    try:

        # 1. QUÉT VIDEO (.mp4, .mov) trong scan_video_dir (Bỏ qua đợt 1, 2, 3 - chỉ lấy từ đợt 4, đợt 5 trở đi)

        for root, dirs, files in os.walk(scan_video_dir):

            dirs[:] = [

                d for d in dirs 

                if d.lower() not in ["node_modules", ".git", ".venv", "__pycache__"] 

                and "douyin" not in d.lower()

                and not re.search(r'(?:đợt|dot)[\s_-]*0*([123])(?!\d)', d, re.IGNORECASE)

            ]

            for f in files:

                ext = os.path.splitext(f)[1].lower()

                if ext not in [".mp4", ".mov"]:

                    continue

                fp = os.path.join(root, f)

                # Lọc bỏ nếu đường dẫn thuộc đợt 1, đợt 2, đợt 3

                norm_full = fp.replace("\\", "/").lower()

                if re.search(r'(?:đợt|dot)[\s_-]*0*([123])(?!\d)', norm_full):

                    continue

                fp = os.path.join(root, f)

                rel = os.path.relpath(fp, scan_video_dir).replace("\\", "/")



                # Rút gọn tiền tố hiển thị cho đẹp mắt:

                # 'video chưa đăng/đợt 5/6/file.mp4' -> 'đợt 5/6/file.mp4'

                # 'video đã đăng/file.mp4' -> 'đã đăng/file.mp4'

                display_name = rel

                norm_rel = unicodedata.normalize("NFC", rel).lower()

                for prefix in ["video chưa đăng/", "video chua dang/", "video đã đăng/", "video da dang/"]:

                    if norm_rel.startswith(prefix):

                        disp_core = rel[len(prefix):]

                        if "đã đăng" in prefix or "da dang" in prefix:

                            display_name = "đã đăng/" + disp_core

                        else:

                            display_name = disp_core

                        break



                try:

                    stat = os.stat(fp)

                    mtime = stat.st_mtime

                    size_mb = round(stat.st_size / (1024 * 1024), 2)

                except Exception:

                    mtime = 0

                    size_mb = 0



                bkey = _extract_base_key_for_pairing(f)

                parent_dir_name = os.path.basename(root)

                folder_ep = _extract_base_key_for_pairing(parent_dir_name) if not parent_dir_name.lower().startswith(("đợt", "dot")) else ""



                video_files.append({

                    "name": f,

                    "rel_path": rel,

                    "display_name": display_name,

                    "full_path": fp,

                    "dir_path": root,

                    "size_mb": size_mb,

                    "mtime": mtime,

                    "base_key": bkey,

                    "folder_ep": folder_ep

                })



        # 2. QUÉT EXCEL/CSV:

        # 2a. Quét trong scan_video_dir (toàn bộ các đợt)

        scanned_excel_paths = set()

        for root, dirs, files in os.walk(scan_video_dir):

            dirs[:] = [d for d in dirs if d.lower() not in ["node_modules", ".git", ".venv", "__pycache__"] and "douyin" not in d.lower()]

            for f in files:

                if f.startswith("~$"):

                    continue

                ext = os.path.splitext(f)[1].lower()

                if ext not in [".xlsx", ".csv"]:

                    continue

                fp = os.path.join(root, f)

                rel = os.path.relpath(fp, scan_video_dir).replace("\\", "/")

                if fp in scanned_excel_paths:

                    continue

                scanned_excel_paths.add(fp)



                display_name = rel if rel != f else f



                try:

                    stat = os.stat(fp)

                    mtime = stat.st_mtime

                    size_mb = round(stat.st_size / (1024 * 1024), 2)

                except Exception:

                    mtime = 0

                    size_mb = 0



                bkey = _extract_base_key_for_pairing(f)

                parent_dir_name = os.path.basename(root)

                folder_ep = _extract_base_key_for_pairing(parent_dir_name) if not parent_dir_name.lower().startswith(("đợt", "dot")) else ""



                excel_files.append({

                    "name": f,

                    "rel_path": rel,

                    "display_name": display_name,

                    "full_path": fp,

                    "dir_path": root,

                    "size_mb": size_mb,

                    "mtime": mtime,

                    "base_key": bkey,

                    "folder_ep": folder_ep

                })



        # 2b. Quét thêm trong thư mục 'Link customed' nếu có

        customed_candidates = [

            os.path.join(folder_path, "Link customed"),

            os.path.join(os.path.dirname(folder_path), "Link customed")

        ]

        for cdir in customed_candidates:

            if os.path.exists(cdir) and os.path.isdir(cdir):

                for root, dirs, files in os.walk(cdir):

                    dirs[:] = [d for d in dirs if d.lower() not in ["node_modules", ".git", ".venv", "__pycache__"]]

                    for f in files:

                        if f.startswith("~$"):

                            continue

                        ext = os.path.splitext(f)[1].lower()

                        if ext not in [".xlsx", ".csv"]:

                            continue

                        fp = os.path.join(root, f)

                        if fp in scanned_excel_paths:

                            continue

                        scanned_excel_paths.add(fp)



                        rel = os.path.relpath(fp, folder_path).replace("\\", "/")

                        try:

                            stat = os.stat(fp)

                            mtime = stat.st_mtime

                            size_mb = round(stat.st_size / (1024 * 1024), 2)

                        except Exception:

                            mtime = 0

                            size_mb = 0



                        bkey = _extract_base_key_for_pairing(f)

                        excel_files.append({

                            "name": f,

                            "rel_path": rel,

                            "display_name": rel,

                            "full_path": fp,

                            "dir_path": root,

                            "size_mb": size_mb,

                            "mtime": mtime,

                            "base_key": bkey,

                            "folder_ep": ""

                        })

                break



    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi quét thư mục: {str(e)}"}), 500



    # 2.5. XÁC ĐỊNH TRẠNG THÁI ĐÃ ĐĂNG / CHƯA ĐĂNG CHO TỪNG VIDEO

    history_uploaded_paths = set()

    for tid, t_item in tasks.items():

        if t_item.get("brand_key") == brand_key and t_item.get("video_path"):

            st = t_item.get("status")

            if st in ["COMPLETED", "RUNNING", "SCHEDULED", "QUEUED"]:

                history_uploaded_paths.add(t_item.get("video_path").replace("\\", "/").lower().strip())



    if os.path.exists(TASKS_STORAGE_PATH):

        try:

            with open(TASKS_STORAGE_PATH, "r", encoding="utf-8") as f:

                h_data = json.load(f)

                for tid, t_item in h_data.items():

                    if t_item.get("brand_key") == brand_key and t_item.get("video_path"):

                        st = t_item.get("status")

                        if st in ["COMPLETED", "RUNNING", "SCHEDULED", "QUEUED"]:

                            history_uploaded_paths.add(t_item.get("video_path").replace("\\", "/").lower().strip())

        except Exception:

            pass



    for vf in video_files:

        vf_norm = vf["full_path"].replace("\\", "/").lower().strip()

        vf_rel_norm = unicodedata.normalize("NFC", vf["rel_path"]).lower().replace("\\", "/").strip()



        # Kiểm tra 0: Thuộc thư mục video đã đăng

        is_in_da_dang = ("video đã đăng" in vf_rel_norm or "video da dang" in vf_rel_norm or 

                         "đã đăng cho đợt cũ" in vf_rel_norm or "da dang cho dot cu" in vf_rel_norm or

                         "video đã đăng" in vf_norm or "video da dang" in vf_norm)



        # Kiểm tra 1: Trong thư mục video có file kết quả link affiliate (AffiliateBatchCustomLinks*.csv/xlsx)

        has_aff_csv = False

        dir_p = vf["dir_path"]

        try:

            for fname in os.listdir(dir_p):

                fl = fname.lower()

                if (fl.endswith(".csv") or fl.endswith(".xlsx")) and not fl.startswith("~$"):

                    if "affiliatebatchcustomlinks" in fl or "batch custom links" in fl or "batch_custom_links" in fl:

                        has_aff_csv = True

                        break

        except Exception:

            pass



        # Kiểm tra 2: Video có trong lịch sử tác vụ upload

        in_history = False

        if vf_norm in history_uploaded_paths or any(hp.endswith("/" + os.path.basename(vf_norm)) for hp in history_uploaded_paths):

            in_history = True



        if is_in_da_dang or has_aff_csv or in_history:

            vf["is_uploaded"] = True

            vf["upload_status"] = "Đã đăng"

        else:

            vf["is_uploaded"] = False

            vf["upload_status"] = "Chưa đăng"



    # Sắp xếp danh sách:

    # - Video CHƯA ĐĂNG đưa lên ĐẦU: Đợt mới nhất lên đầu (đợt 5 -> đợt 4 -> đợt 3...), trong cùng đợt thì tập nhỏ lên trước (1 -> 2 -> 3)

    # - Video ĐÃ ĐĂNG đưa xuống DƯỚI: Đợt mới nhất lên đầu, kèm các video trong 'video đã đăng'

    def _batch_sort_key(item, is_unposted=True):

        name_str = item.get("display_name", "")

        m_batch = re.search(r'(?:đợt|dot)[\s_-]*(\d+)', name_str.lower())

        batch_num = int(m_batch.group(1)) if m_batch else 0

        

        m_num = re.search(r'(?:/|\\|^)(\d+)(?:/|\\|\.mp4|\.mov|_|\s)', name_str)

        ep_num = int(m_num.group(1)) if m_num else 999

        

        if is_unposted:

            return (-batch_num, ep_num, name_str)

        else:

            return (-batch_num, ep_num, -item.get("mtime", 0), name_str)



    unposted_videos = [v for v in video_files if not v["is_uploaded"]]

    posted_videos = [v for v in video_files if v["is_uploaded"]]



    unposted_videos.sort(key=lambda x: _batch_sort_key(x, True))

    posted_videos.sort(key=lambda x: _batch_sort_key(x, False))

    sorted_video_files = unposted_videos + posted_videos



    excel_files.sort(key=lambda x: x["mtime"], reverse=True)



    # 3. AUTO-PAIRING (GHÉP CẶP VIDEO VỚI FILE LINK SẢN PHẨM)

    pairs = []

    for vf in sorted_video_files:

        matched_ef = None

        match_type = ""



        # Ưu tiên 1: Cùng thư mục con trực tiếp với video (ví dụ cùng trong đợt 4\9)

        same_dir_excels = [

            ef for ef in excel_files 

            if ef["dir_path"] == vf["dir_path"] and "batch custom links" not in ef["name"].lower()

        ]

        if same_dir_excels:

            same_dir_excels.sort(key=lambda x: (

                2 if "affiliatebatchcustomlinks" in x["name"].lower() else 1,

                1 if x["name"].lower().endswith(".csv") else 0,

                x["mtime"]

            ), reverse=True)

            matched_ef = same_dir_excels[0]

            match_type = "cùng thư mục"



        # Ưu tiên 2: Trùng base_key trong CÙNG CỤM THƯ MỤC CHA

        if not matched_ef and vf["base_key"] and len(vf["base_key"]) >= 3 and not vf["base_key"].startswith("ep_"):

            key_candidates = [

                ef for ef in excel_files 

                if ef["base_key"] and ef["base_key"] == vf["base_key"] and "link customed" not in ef["full_path"].lower()

            ]

            if key_candidates:

                key_candidates.sort(key=lambda x: (1 if x["name"].lower().endswith(".xlsx") else 0, x["mtime"]), reverse=True)

                matched_ef = key_candidates[0]

                match_type = "trùng tên file"



        # Ưu tiên 3: Tìm trong Link customed chỉ khi TÊN SẢN PHẨM THỰC CHẤT trùng nhau

        if not matched_ef and vf["base_key"] and not vf["base_key"].startswith("ep_"):

            v_stem = vf["name"].lower().split(".")[0].strip()

            if len(v_stem) >= 4 and not re.match(r'^(?:t[aậ]p\s*\d+|\d+|ep\s*\d+|part\s*\d+)$', v_stem):

                custom_matches = [

                    ef for ef in excel_files 

                    if "link customed" in ef["full_path"].lower() and v_stem in ef["name"].lower()

                ]

                if custom_matches:

                    custom_matches.sort(key=lambda x: x["mtime"], reverse=True)

                    matched_ef = custom_matches[0]

                    match_type = "link customed"



        if matched_ef:

            vf["has_matched_excel"] = True

            vf["matched_excel_name"] = matched_ef["name"]

            vf["matched_excel_path"] = matched_ef["full_path"]

            vf["match_type"] = match_type

            pairs.append({

                "video": vf,

                "excel": matched_ef,

                "pair_name": vf["display_name"],

                "match_type": match_type,

                "mtime": max(vf["mtime"], matched_ef["mtime"])

            })

        else:

            vf["has_matched_excel"] = False

            vf["matched_excel_name"] = None

            vf["matched_excel_path"] = None

            vf["match_type"] = None



    pairs.sort(key=lambda x: x["mtime"], reverse=True)



    # Đề xuất cặp file mới nhất: CHỈ đề xuất từ video CHƯA ĐĂNG

    unposted_pairs = [p for p in pairs if not p["video"].get("is_uploaded")]

    latest_pair = None

    if unposted_pairs:

        latest_pair = {

            "video_path": unposted_pairs[0]["video"]["full_path"],

            "video_name": unposted_pairs[0]["video"]["display_name"],

            "excel_path": unposted_pairs[0]["excel"]["full_path"],

            "excel_name": unposted_pairs[0]["excel"]["display_name"],

            "pair_type": "matched_pair"

        }

    elif unposted_videos:

        latest_pair = {

            "video_path": unposted_videos[0]["full_path"],

            "video_name": unposted_videos[0]["display_name"],

            "excel_path": (excel_files[0]["full_path"] if excel_files else ""),

            "excel_name": (excel_files[0]["display_name"] if excel_files else ""),

            "pair_type": "latest_files"

        }



    return jsonify({

        "success": True,

        "brand_key": brand_key,

        "folder": b_cfg.get("folder", ""),

        "folder_path": folder_path,

        "chua_dang_path": chua_dang_path,

        "videos_count": len(sorted_video_files),

        "unposted_count": len(unposted_videos),

        "uploaded_count": len(posted_videos),

        "excels_count": len(excel_files),

        "pairs_count": len(pairs),

        "videos": sorted_video_files,

        "excels": excel_files,

        "pairs": pairs,

        "latest_pair": latest_pair

    })





@app.route("/api/photo-post/trigger-manual", methods=["POST"])

def trigger_photo_post_manual():

    """

    Endpoint cho phép bấm nút test đăng bài viết dạng ảnh (Photo Post)

    ngay lập tức cho 1 kênh hoặc toàn bộ 10 kênh từ giao diện Dashboard.

    """

    try:

        data = request.json or {}

        brand_key = data.get("brand_key", "").strip()



        # Import động module daily_photo_poster

        sys.path.insert(0, os.path.join(BASE_DIR, "POST"))

        try:

            import daily_photo_poster

        except ImportError:

            from POST import daily_photo_poster



        if brand_key:

            res = daily_photo_poster.publish_daily_photo_post(brand_key)

            return jsonify(res)

        else:

            # Chạy nền cho toàn bộ kênh nếu không truyền brand_key

            def _run_all():

                daily_photo_poster.run_daily_photo_job()



            t = threading.Thread(target=_run_all, daemon=True)

            t.start()

            return jsonify({

                "success": True,

                "message": "Đã kích hoạt tiến trình đăng bài ảnh tự động cho toàn bộ 10 thương hiệu!"

            })

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi trigger photo post: {str(e)}"}), 500







@app.route("/api/analyze_video", methods=["POST"])

def analyze_video():

    """

    Phân tích video bằng Gemini API:

    - Tự động tạo 3 phương án A/B testing: Hook tò mò CTR, Lợi ích chuyển đổi, Chuẩn SEO Search

    - Tự động đề xuất 3 bộ hashtags tối ưu tương ứng

    """

    data = request.json or {}

    video_path = (data.get("video_path") or "").strip()

    excel_path = (data.get("excel_path") or "").strip()  # Nhận thêm excel_path / URL list

    brand_key = (data.get("brand_key") or "").strip()

    brand_name = ""

    if brand_key:

        try:

            brands = load_brands()

            brand_name = brands.get(brand_key, {}).get("name", "")

        except Exception:

            pass

    b_name = brand_name or brand_key or "Kênh không xác định"

    v_name = os.path.basename(video_path) if video_path else "Chưa chọn file"



    if not video_path or not os.path.exists(video_path):

        return jsonify({

            "success": False,

            "brand_key": brand_key,

            "brand_name": b_name,

            "video_path": video_path,

            "video_name": v_name,

            "message": f"Kênh [{b_name}] - Không tìm thấy file video '{v_name}' trên máy tính"

        }), 400



    # Kiểm tra kích thước file (giới hạn 20MB cho Gemini inline)

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)



    try:

        from google import genai

        from google.genai import types



        # Tìm API key từ biến môi trường hoặc file .env

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")



        if not api_key:

            # Thử đọc từ .env file

            env_path = os.path.join(BASE_DIR, ".env")

            if os.path.exists(env_path):

                with open(env_path, "r", encoding="utf-8") as ef:

                    for line in ef:

                        line = line.strip()

                        if line.startswith("GEMINI_API_KEY="):

                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

                        elif line.startswith("GOOGLE_API_KEY="):

                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")



        if not api_key:

            return jsonify({

                "success": False,

                "message": "Chưa cấu hình GEMINI_API_KEY. Hãy tạo file .env với nội dung: GEMINI_API_KEY=your_key"

            }), 400



        client = genai.Client(api_key=api_key)



        # Chuẩn bị file upload: Đảm bảo đường dẫn file và tên file thuần ASCII 100%

        # Tránh lỗi 'ascii' codec can't encode character do HTTP header X-Goog-Upload-File-Name của SDK

        import time as _time

        import tempfile

        import subprocess

        import shutil



        temp_target_path = None

        ext = os.path.splitext(video_path)[1].lower() or ".mp4"

        temp_ascii_file = os.path.join(tempfile.gettempdir(), f"gemini_vid_{int(_time.time())}_{uuid.uuid4().hex[:6]}{ext}")



        need_compress = file_size_mb > 20   # Nén sớm hơn — file > 20MB là nén

        compressed_success = False



        if need_compress:

            print(f"🎬 Đang nén video tối ưu cho AI (360p @ 2fps): {video_path} ({file_size_mb:.1f}MB) -> {temp_ascii_file}")

            cmd = [

                "ffmpeg", "-y", "-i", video_path,

                "-vf", "scale=-2:360:flags=fast_bilinear,fps=2",  # 360p 2fps: xử lý cực nhanh trên CPU, Gemini vẫn thấy rõ mọi phân cảnh & chữ trên màn hình

                "-c:v", "libx264", "-crf", "35", "-preset", "ultrafast",

                "-c:a", "aac", "-b:a", "48k",    # Audio vừa đủ cho AI nhận diện giọng nói

                temp_ascii_file

            ]

            try:

                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                new_size_mb = os.path.getsize(temp_ascii_file) / (1024 * 1024)

                print(f"✅ Nén xong! Dung lượng gửi AI chỉ còn: {new_size_mb:.1f}MB (gốc {file_size_mb:.1f}MB)")

                temp_target_path = temp_ascii_file

                compressed_success = True

            except Exception as fe:

                print(f"⚠️ Không thể nén qua ffmpeg, sao chép file với tên thuần ASCII: {fe}")



        if not compressed_success:

            # Copy sang file tạm thuần ASCII để Google SDK httpx không bị lỗi Unicode header

            shutil.copy2(video_path, temp_ascii_file)

            temp_target_path = temp_ascii_file



        upload_target = temp_target_path



        # Upload video lên Gemini (Chỉ định rõ mime_type để tránh lỗi Unknown mime type)

        import mimetypes

        guessed_type, _ = mimetypes.guess_type(video_path)

        if not guessed_type:

            guessed_type = "video/mp4"



        print(f"📤 Đang upload video lên Gemini để phân tích (mime_type: {guessed_type})...")

        try:

            video_file = client.files.upload(

                file=upload_target,

                config=types.UploadFileConfig(

                    mime_type=guessed_type,

                    display_name=f"review_video_{int(_time.time())}"

                )

            )

        finally:

            # Dọn dẹp file tạm trên máy tính ngay sau khi hoàn tất upload

            if temp_target_path and os.path.exists(temp_target_path):

                try:

                    os.remove(temp_target_path)

                except Exception:

                    pass



        # Chờ video xử lý xong — timeout 90s

        _poll_start = _time.time()

        while video_file.state.name == "PROCESSING":

            if _time.time() - _poll_start > 90:

                return jsonify({"success": False, "message": "Gemini xử lý video quá lâu (>90s). Thử lại."}), 500

            _time.sleep(3)

            video_file = client.files.get(name=video_file.name)



        if video_file.state.name == "FAILED":

            return jsonify({"success": False, "message": "Gemini không thể xử lý video này"}), 500



        brand_key = (data.get("brand_key") or "").strip()

        brand_name = ""

        if brand_key:

            brands = load_brands()

            brand_name = brands.get(brand_key, {}).get("name", "")



        # Parse danh sách sản phẩm từ excel_path hoặc URL trực tiếp để inject vào Gemini prompt

        hint_products = []

        if excel_path:

            try:

                if _is_direct_url_input(excel_path):

                    hint_products = parse_direct_urls(excel_path)

                elif os.path.exists(excel_path):

                    hint_products = parse_link_file(excel_path)

            except Exception:

                pass



        # Xây dựng đoạn context sản phẩm cho prompt

        product_context = ""

        if hint_products:

            lines = []

            for i, p in enumerate(hint_products, 1):

                name = p.get("name", "Sản phẩm chính hãng")

                link = p.get("link", "")

                lines.append(f"  {i}. {name} → {link}")

            product_context = (

                "\n\nGợi ý sản phẩm affiliate đi kèm (LƯU Ý ĐẶC BIỆT: Đây CHỈ là gợi ý đối chiếu. Video thực tế là chân lý tuyệt đối! NẾU sản phẩm xuất hiện/được review trong video KHÁC HOÀN TOÀN so với danh sách gợi ý này, bạn BẮT BUỘC phải đặt tiêu đề, mô tả và hashtag theo ĐÚNG sản phẩm thực tế trong video, TUYỆT ĐỐI KHÔNG dùng tên sản phẩm gợi ý bị sai lệch):\n"

                + "\n".join(lines)

            )



        prompt = f"""Bạn là Giám đốc Sáng tạo Nội dung và Chuyên gia SEO Affiliate hàng đầu cho các nền tảng video ngắn (YouTube Shorts, Facebook Reels, Instagram Reels, TikTok, Threads).

Nhiệm vụ: Xem kỹ toàn bộ âm thanh, hình ảnh, văn bản (on-screen text), ngữ cảnh và sản phẩm xuất hiện trong video này.

Mục tiêu: Tạo ra ĐÚNG 3 PHƯƠNG ÁN (A/B TESTING) Tiêu đề, Mô tả và Bộ Hashtags tương ứng để người dùng thử nghiệm A/B hiệu quả trên Facebook Reels và YouTube Shorts:



1. PHƯƠNG ÁN 1 (Option A) - Chiến lược: "HOOK & TÒ MÒ CỰC MẠNH (Tối ưu CTR Bùng Nổ Shorts/Reels)":

   - Nhắm đến: Tỷ lệ nhấp (CTR) và giữ chân người xem ngay trong 3 giây đầu tiên trên feed.

   - Tiêu đề: 50 - 75 ký tự, mở đầu bằng các mẫu Hook kích thích tò mò cao, cảnh báo sai lầm, so sánh ngầm hoặc đặt câu hỏi bất ngờ (Ví dụ: 'Đừng Vội Mua [Tên SP] Nếu Chưa Biết Điều Này! 🔥', 'Sự Thật Về [Tên SP] Mà Người Bán Không Nói Cho Bạn 🤔').

   - Mô tả: Nhấn mạnh chi tiết bất ngờ nhất ở 3s đầu, thúc đẩy người xem thảo luận và có Call-To-Action (CTA) xem link chi tiết ở bình luận.

   - Hashtags: 7-8 tag tập trung vào trending, viral, shorts, reels và từ khóa tò mò.



2. PHƯƠNG ÁN 2 (Option B) - Chiến lược: "NỖI ĐAU & LỢI ÍCH (Tối ưu Chuyển Đổi Đơn Hàng / Conversion)":

   - Nhắm đến: Đánh trúng nỗi đau khách hàng đang gặp phải và đưa ra sản phẩm như một giải pháp hoàn hảo (Problem - Solution).

   - Tiêu đề: 50 - 75 ký tự, nêu bật ngay công dụng giải cứu vấn đề + tên sản phẩm + lợi ích vượt trội (Ví dụ: 'Bí Quyết [Giải Quyết Vấn Đề] Gọn Nhẹ Chỉ Với [Tên SP] ✨', '[Tên SP]: Cứu Tinh Cho Ai Đang Gặp Tình Trạng Này 💡').

   - Mô tả: 2-4 câu chỉ rõ ưu điểm đáng tiền, lý do nên sở hữu ngay hôm nay + CTA rõ ràng hướng dẫn lấy mã giảm giá và link chính hãng ở bình luận/mô tả.

   - Hashtags: 7-8 tag tập trung vào ngách sản phẩm, công dụng giải pháp và từ khóa hành vi người mua hàng.



3. PHƯƠNG ÁN 3 (Option C) - Chiến lược: "CHUẨN SEO TỪ KHÓA TÌM KIẾM (Tối ưu Lên Top Đề Xuất Lâu Dài)":

   - Nhắm đến: Thuật toán YouTube Search & Facebook Search, giúp video ăn đề xuất tìm kiếm tự nhiên bền vững nhiều tháng sau khi đăng.

   - Tiêu đề: 55 - 80 ký tự, cấu trúc chuẩn mực: [Tên Sản Phẩm Chính Xác] - [Tính Năng / Model Nổi Bật] + [Đánh Giá / Hướng Dẫn Chi Tiết].

   - Mô tả: Đoạn văn phong phú từ khóa chính & từ khóa phụ ngữ cảnh sử dụng, thông số nổi bật + CTA chuẩn mực.

   - Hashtags: 7-8 tag chuẩn SEO gồm 2 tag tên sản phẩm (không dấu), 2 tag ngành hàng, 2 tag từ khóa tìm kiếm và 2 tag nền tảng.



{f'Kênh phân phối: {brand_name}' if brand_name else ''}{product_context}



QUY TẮC BẮT BUỘC:

- NỘI DUNG VIDEO LÀ CHÂN LÝ TUYỆT ĐỐI: Bạn PHẢI quan sát hình ảnh thực tế, chữ viết hiển thị và nghe lời bình trong video để nhận diện CHÍNH XÁC sản phẩm đang được giới thiệu (ví dụ: gối massage cổ vai gáy, mỹ phẩm, đồ gia dụng...).

- Gợi ý sản phẩm affiliate (nếu có): CHỈ được dùng khi sản phẩm gợi ý TRÙNG KHỚP với sản phẩm trong video. Nếu sản phẩm trong video hoàn toàn khác danh sách gợi ý (ví dụ video là gối massage nhưng gợi ý lại là củ sạc), bạn BẮT BUỘC BỎ QUA gợi ý đó và đặt tiêu đề/mô tả/hashtag theo ĐÚNG sản phẩm gối massage trong video.

- NHẬN DIỆN CÁC SẢN PHẨM TRONG VIDEO (detected_products):

  + Hãy quan sát kỹ toàn bộ video (hình ảnh, văn bản on-screen, lời thuyết minh/âm thanh) để xác định video này đang review hoặc có những sản phẩm gì xuất hiện:

    * Có video review cụ thể 1 sản phẩm.

    * Có video review nhiều sản phẩm (ví dụ top 3-5 món đồ công nghệ/gia dụng, combo phối đồ, danh sách sản phẩm yêu thích...).

    * Có video không chủ đích review sản phẩm nào, nhưng có sản phẩm hoặc vật dụng xuất hiện trong video (bạn hãy nhận diện các sản phẩm nổi bật xuất hiện trong video đó).

    * Nếu video hoàn toàn là đời sống, phong cảnh, tâm sự... không hề xuất hiện hoặc nhắc đến sản phẩm thương mại nào thì trả về mảng rỗng [].

  + Trả về mảng danh sách tên các sản phẩm này vào trường 'detected_products' (mỗi phần tử là tên sản phẩm rõ ràng, súc tích bằng tiếng Việt, ví dụ: ["Gối massage cổ vai gáy thông minh", "Củ sạc nhanh 65W GaN"]).

- Hashtags: Trả về danh sách gồm 7 đến 8 hashtags cho MỖI phương án, viết liền không dấu (slug), TUYỆT ĐỐI KHÔNG chứa ký tự '#'.

  + 2 tag đầu tiên: tên/loại sản phẩm cụ thể trong video (viết liền không dấu).

  + 2 tag tiếp theo: ngách hành vi mua sắm.

  + 2 tag nền tảng: shorts, reels.

  + 1-2 tag tên kênh/ngành hàng.

- Toàn bộ bằng tiếng Việt tự nhiên, hấp dẫn, chuẩn văn phong review affiliate hiện đại.



Hãy trả về KẾT QUẢ THEO ĐỊNH DẠNG JSON DUY NHẤT (TUYỆT ĐỐI KHÔNG bọc markdown ```json, KHÔNG có bất kỳ lời dẫn hay giải thích thừa thãi nào):

{{

  "detected_products": [

    "Tên sản phẩm 1 đang review hoặc xuất hiện trong video",

    "Tên sản phẩm 2 (nếu có nhiều sản phẩm)"

  ],

  "options": [

    {{

      "id": 1,

      "style": "Hook & Tò Mò (Tối Ưu CTR Shorts/Reels)",

      "badge": "🔥 Hook CTR Cao",

      "title": "Tiêu đề phương án 1 chứa tên SP + hook tò mò + emoji",

      "description": "Mô tả phương án 1 đánh trúng tâm lý tò mò + CTA link ở bình luận",

      "hashtags": ["tag_san_pham_1", "tag_san_pham_2", "tag_ngach_1", "tag_ngach_2", "shorts", "reels", "trending"]

    }},

    {{

      "id": 2,

      "style": "Nỗi Đau & Lợi Ích (Tối Ưu Chuyển Đổi Đơn Hàng)",

      "badge": "💰 Tăng Chuyển Đổi",

      "title": "Tiêu đề phương án 2 nêu giải pháp + tên SP + lợi ích vượt trội",

      "description": "Mô tả phương án 2 nêu ưu điểm giải quyết nỗi đau + CTA link ở bình luận",

      "hashtags": ["tag_san_pham_1", "tag_san_pham_2", "tag_ngach_1", "tag_ngach_2", "shorts", "reels", "review"]

    }},

    {{

      "id": 3,

      "style": "Chuẩn SEO Search (Tối Ưu Đề Xuất Lâu Dài)",

      "badge": "🔍 Chuẩn SEO Đề Xuất",

      "title": "Tiêu đề phương án 3 chuẩn từ khóa tìm kiếm YouTube/Facebook Search",

      "description": "Mô tả phương án 3 giàu từ khóa ngữ cảnh + CTA xem link",

      "hashtags": ["tag_san_pham_1", "tag_san_pham_2", "tag_ngach_1", "tag_ngach_2", "shorts", "reels", "seotop"]

    }}

  ]

}}"""



        # Ưu tiên các model flash ổn định cao, phản hồi siêu tốc, ít bị quá tải 503 và có quota độc lập

        video_models_to_try = [

            "gemini-3.5-flash-lite", # Siêu tốc (~0.8s), phân tích video mượt mà, quota độc lập, không bị 503

            "gemini-3.6-flash",      # Ổn định cao, phân tích sâu, hỗ trợ video chuẩn xác

            "gemini-flash-lite-latest", # Bản Flash-Lite GA ổn định nhất của Google

            "gemini-3.1-flash-lite", # Dự phòng Lite

            "gemini-3.8-flash",      # Bản cao cấp nhất

            "gemini-3.5-flash",      # Dự phòng Flash

            "gemini-3.7-flash"       # Dự phòng 3.7

        ]

        response = None

        last_api_err = None



        for v_model in video_models_to_try:

            for attempt in range(2):

                try:

                    print(f"🤖 Đang phân tích video chuẩn SEO bằng {v_model} (lần {attempt + 1})...")

                    response = client.models.generate_content(

                        model=v_model,

                        contents=[video_file, prompt]

                    )

                    if response and (response.text or "").strip():

                        print(f"✅ Model {v_model} phân tích video thành công!")

                        break

                except Exception as me:

                    err_s = str(me)

                    last_api_err = me

                    print(f"⚠️ {v_model} (lần {attempt + 1}) gặp lỗi: {err_s}")

                    # Nếu là 503 (quá tải) hoặc 429 (rate limit) thì đợi 2 giây để Google phục hồi

                    if ("503" in err_s or "UNAVAILABLE" in err_s or "429" in err_s or "RESOURCE_EXHAUSTED" in err_s) and attempt == 0:

                        _time.sleep(2)

                    else:

                        break

            if response and (response.text or "").strip():

                break



        if not response or not (response.text or "").strip():

            raw_err_s = str(last_api_err)

            if "503" in raw_err_s or "UNAVAILABLE" in raw_err_s:

                clean_msg = "Máy chủ Gemini đang quá tải tạm thời (503 UNAVAILABLE). Hệ thống đã tự động thử các model dự phòng nhưng chưa được. Vui lòng bấm 'Thử lại kênh này' sau 5-10 giây."

            elif "429" in raw_err_s or "RESOURCE_EXHAUSTED" in raw_err_s:

                clean_msg = "Đạt giới hạn số lượng yêu cầu gọi Gemini (429 Rate Limit). Vui lòng đợi 30 giây rồi thử lại."

            else:

                clean_msg = f"Không nhận được phản hồi từ AI ({raw_err_s[:150]})"

            raise Exception(clean_msg)



        result_text = (response.text or "").strip()



        # Clean markdown code block nếu có

        if result_text.startswith("```"):

            result_text = re.sub(r'^```\w*\n?', '', result_text)

            result_text = re.sub(r'\n?```$', '', result_text)



        json_match = re.search(r'\{[\s\S]*\}', result_text)

        if json_match:

            result_text = json_match.group(0)



        result = json.loads(result_text)



        # Cleanup Gemini file

        try:

            client.files.delete(name=video_file.name)

        except Exception:

            pass



        # Trích xuất danh sách sản phẩm nhận diện được trong video

        raw_products = result.get("detected_products") or []

        detected_products = []

        if isinstance(raw_products, list):

            for p in raw_products:

                if isinstance(p, str) and p.strip():

                    detected_products.append(p.strip())

                elif isinstance(p, dict) and p.get("name"):

                    detected_products.append(str(p.get("name")).strip())

        elif isinstance(raw_products, str) and raw_products.strip():

            detected_products = [x.strip() for x in raw_products.split(",") if x.strip()]



        # Chuẩn hóa danh sách options để luôn có 3 phương án hợp lệ

        raw_options = result.get("options")

        options = []

        if isinstance(raw_options, list) and len(raw_options) > 0:

            options = raw_options

        else:

            # Fallback nếu Gemini chỉ trả về dạng đơn

            options = [

                {

                    "id": 1,

                    "style": "Hook & Tò Mò (Tối Ưu CTR Shorts/Reels)",

                    "badge": "🔥 Hook CTR Cao",

                    "title": result.get("title", ""),

                    "description": result.get("description", ""),

                    "hashtags": result.get("hashtags", [])

                }

            ]



        # Đảm bảo mỗi option có đầy đủ các trường chuẩn

        badge_defaults = ["🔥 Hook CTR Cao", "💰 Tăng Chuyển Đổi", "🔍 Chuẩn SEO Đề Xuất"]

        style_defaults = [

            "Hook & Tò Mò (Tối Ưu CTR Shorts/Reels)",

            "Nỗi Đau & Lợi Ích (Tối Ưu Chuyển Đổi Đơn Hàng)",

            "Chuẩn SEO Search (Tối Ưu Đề Xuất Lâu Dài)"

        ]



        for idx, opt in enumerate(options, 1):

            if not opt.get("id"):

                opt["id"] = idx

            if not opt.get("style"):

                opt["style"] = style_defaults[idx - 1] if idx <= len(style_defaults) else f"Phương án {idx}"

            if not opt.get("badge"):

                opt["badge"] = badge_defaults[idx - 1] if idx <= len(badge_defaults) else "✨ Tối Ưu SEO"

            if not opt.get("title"):

                opt["title"] = result.get("title", "")

            if not opt.get("description"):

                opt["description"] = result.get("description", "")

            if not opt.get("hashtags"):

                opt["hashtags"] = result.get("hashtags", [])



        default_opt = options[0]



        try:

            print(f"✅ Phân tích video thành công ({len(detected_products)} sản phẩm, {len(options)} phương án A/B): {default_opt.get('title', '?')}")

        except Exception:

            pass



        # Tự động lưu nháp vào file backend để khi F5/reload trang không bị mất

        # Tự động tìm kiếm link affiliate khớp từ kho link cũ cho các sản phẩm vừa nhận diện

        matched_affiliate_products = []

        try:

            matched_affiliate_products = find_best_matching_products(detected_products, brand_key=brand_key, min_score=50)

            if matched_affiliate_products:

                print(f"🎯 Đã tự động khớp {len(matched_affiliate_products)} sản phẩm affiliate từ kho cho kênh {brand_key}")

        except Exception as _me:

            print(f"⚠️ Lỗi khớp link affiliate cho {brand_key}: {_me}")



        # Tự động lưu nháp vào file backend để khi F5/reload trang không bị mất

        if brand_key:

            try:

                cur_drafts = load_channel_drafts()

                b_draft = cur_drafts.get(brand_key, {})

                b_draft.update({

                    "video": video_path,

                    "excel": excel_path,

                    "options": options,

                    "aiOptions": options,

                    "aiSelectedIdx": 0,

                    "aiBoxVisible": True,

                    "detected_products": detected_products,

                    "aiDetectedProducts": detected_products,

                    "matched_affiliate_products": matched_affiliate_products,

                    "aiProductsBoxVisible": True,

                    "title": default_opt.get("title", ""),

                    "caption": default_opt.get("description", ""),

                    "tags": default_opt.get("hashtags", []),

                    "aiBadgeTitle": True,

                    "aiBadgeCaption": True,

                    "savedAt": int(time.time() * 1000)

                })

                cur_drafts[brand_key] = b_draft

                save_channel_drafts(cur_drafts)

            except Exception as se:

                print(f"⚠️ Lỗi lưu nháp video cho {brand_key}: {se}")



        return jsonify({

            "success": True,

            "options": options,

            "detected_products": detected_products,

            "matched_affiliate_products": matched_affiliate_products,

            "title": default_opt.get("title", ""),

            "description": default_opt.get("description", ""),

            "hashtags": default_opt.get("hashtags", [])

        })



    except ImportError:

        v_name = os.path.basename(video_path) if video_path else "Chưa chọn file"

        b_name = brand_name or brand_key or "Kênh không xác định"

        return jsonify({

            "success": False,

            "brand_key": brand_key,

            "brand_name": b_name,

            "video_path": video_path,

            "video_name": v_name,

            "message": f"Kênh [{b_name}] - Chưa cài thư viện google-genai. Chạy: python -m pip install google-genai"

        }), 500

    except json.JSONDecodeError as e:

        v_name = os.path.basename(video_path) if video_path else "Chưa chọn file"

        b_name = brand_name or brand_key or "Kênh không xác định"

        return jsonify({

            "success": False,

            "brand_key": brand_key,

            "brand_name": b_name,

            "video_path": video_path,

            "video_name": v_name,

            "message": f"Kênh [{b_name}] - Video '{v_name}': Gemini trả về định dạng JSON không hợp lệ ({str(e)})"

        }), 500

    except Exception as e:

        import traceback

        traceback.print_exc()

        v_name = os.path.basename(video_path) if video_path else "Chưa chọn file"

        b_name = brand_name or brand_key or "Kênh không xác định"

        clean_err = str(e)

        return jsonify({

            "success": False,

            "brand_key": brand_key,

            "brand_name": b_name,

            "video_path": video_path,

            "video_name": v_name,

            "message": f"Kênh [{b_name}] - Video '{v_name}': {clean_err}"

        }), 500





@app.route("/api/match_affiliate_product", methods=["POST"])

def match_affiliate_product():

    """

    API tìm kiếm link affiliate phù hợp từ kho cho sản phẩm hoặc danh sách sản phẩm do AI phát hiện.

    """

    data = request.json or {}

    brand_key = (data.get("brand_key") or "").strip()

    detected_products = data.get("detected_products") or []

    query = (data.get("query") or "").strip()

    if query and not detected_products:

        detected_products = [query]



    if not detected_products:

        return jsonify({"success": False, "message": "Chưa có tên sản phẩm cần tìm link", "matches": []}), 400



    try:

        matches = find_best_matching_products(detected_products, brand_key=brand_key, min_score=45)

        return jsonify({

            "success": True,

            "matches": matches,

            "count": len(matches)

        })

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi tìm kiếm link: {str(e)}", "matches": []}), 500







# ─────────────────────────────────────────────────────────────

# CHANNEL DRAFTS PERSISTENCE (LƯU & KHÔI PHỤC KHI F5/RELOAD)

# ─────────────────────────────────────────────────────────────

DRAFTS_FILE = os.path.join(BASE_DIR, "channel_drafts.json")



def load_channel_drafts() -> dict:

    try:

        if os.path.exists(DRAFTS_FILE):

            with open(DRAFTS_FILE, "r", encoding="utf-8") as f:

                return json.load(f)

    except Exception as e:

        print(f"⚠️ Lỗi đọc channel_drafts.json: {e}")

    return {}



def save_channel_drafts(drafts: dict):

    try:

        with open(DRAFTS_FILE, "w", encoding="utf-8") as f:

            json.dump(drafts, f, ensure_ascii=False, indent=2)

    except Exception as e:

        print(f"⚠️ Lỗi ghi channel_drafts.json: {e}")



@app.route("/api/channel_drafts", methods=["GET"])

def get_channel_drafts():

    """Lấy toàn bộ dữ liệu nháp của các kênh để khôi phục khi reload trang."""

    return jsonify({"success": True, "drafts": load_channel_drafts()})



@app.route("/api/channel_drafts", methods=["POST"])

def update_channel_drafts():

    """Cập nhật dữ liệu nháp từ frontend (tự động đồng bộ 2 chiều)."""

    data = request.json or {}

    cur_drafts = load_channel_drafts()

    if "drafts" in data and isinstance(data["drafts"], dict):

        cur_drafts.update(data["drafts"])

    elif "brand_key" in data:

        bk = data["brand_key"]

        draft_body = data.get("draft") or {}

        if draft_body:

            cur_drafts[bk] = draft_body

        elif bk in cur_drafts:

            del cur_drafts[bk]

    save_channel_drafts(cur_drafts)

    return jsonify({"success": True})



@app.route("/api/channel_drafts/<brand_key>/clear", methods=["POST"])

def clear_single_channel_draft(brand_key):

    """Xóa dữ liệu nháp của 1 kênh khi người dùng ấn nút Làm mới."""

    cur_drafts = load_channel_drafts()

    if brand_key in cur_drafts:

        del cur_drafts[brand_key]

        save_channel_drafts(cur_drafts)

    return jsonify({"success": True})



@app.route("/api/channel_drafts/clear_all", methods=["POST"])

def clear_all_channel_drafts():

    """Xóa toàn bộ nháp của cả 10 kênh."""

    save_channel_drafts({})

    return jsonify({"success": True})





# ─────────────────────────────────────────────────────────────

# AI ASSISTANT (CHAT, CODE FIX, PROMPT EDITOR LIKE ANTIGRAVITY)

# ─────────────────────────────────────────────────────────────

def get_gemini_api_key():

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key:

        env_path = os.path.join(BASE_DIR, ".env")

        if os.path.exists(env_path):

            with open(env_path, "r", encoding="utf-8") as ef:

                for line in ef:

                    line = line.strip()

                    if line.startswith("GEMINI_API_KEY="):

                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

                        break

                    elif line.startswith("GOOGLE_API_KEY="):

                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

                        break

    return api_key



@app.route("/api/ai_chat", methods=["POST"])

def ai_chat():

    """

    Trợ lý AI lập trình và sửa code trực tiếp giống Antigravity:

    - Nhận tin nhắn, ngữ cảnh file hoặc code

    - Sử dụng Gemini API (GEMINI_API_KEY)

    - Hỗ trợ xem code, giải thích, viết code, sửa lỗi

    """

    data = request.json or {}

    user_prompt = (data.get("prompt") or "").strip()

    history = data.get("history") or []  # [{role: 'user'|'model', text: '...'}]

    file_context = data.get("file_context") or ""

    selected_file = data.get("selected_file") or ""



    if not user_prompt:

        return jsonify({"success": False, "message": "Nội dung câu hỏi không được để trống"}), 400



    api_key = get_gemini_api_key()

    if not api_key:

        return jsonify({

            "success": False,

            "message": "Chưa tìm thấy GEMINI_API_KEY trong file .env hoặc biến môi trường!"

        }), 400



    try:

        from google import genai

        client = genai.Client(api_key=api_key)



        # Xây dựng system prompt định hướng chuyên gia coding giống Antigravity

        system_instruction = (

            "Bạn là Antigravity AI Code Assistant - một trợ lý lập trình chuyên sâu, thông minh và thân thiện.\n"

            "Bạn đang trực tiếp hỗ trợ nhà phát triển tại dự án Affiliate Publisher (Python Flask, JavaScript, Multi-Platform Uploaders, HTML/CSS).\n"

            "Nhiệm vụ của bạn:\n"

            "1. Phân tích lỗi, sửa code, debug, refactor hoặc viết tính năng mới theo yêu cầu của người dùng.\n"

            "2. Khi sửa code hoặc đề xuất giải pháp, luôn giải thích rõ ràng, cung cấp đoạn code chính xác, có thể copy hoặc áp dụng ngay.\n"

            "3. Trả lời bằng tiếng Việt tự nhiên, ngắn gọn, súc tích, định dạng Markdown đẹp mắt với code block (```python, ```javascript, ```html...).\n"

            "4. Nếu người dùng hỏi về phân tích video, marketing, prompt TikTok/Shorts/Reels, hãy tối ưu prompt và đưa ra gợi ý xuất sắc nhất."

        )



        full_content = ""

        if selected_file and file_context:

            full_content += f"=== NỘI DUNG FILE HIỆN TẠI ({selected_file}) ===\n```\n{file_context[:15000]}\n```\n\n"

        full_content += f"Người dùng yêu cầu:\n{user_prompt}"



        # Thử với gemini-3.8-flash và các đời 3.x

        models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.1-flash-lite"]

        reply_text = None

        last_err = None



        for m in models_to_try:

            try:

                chat_prompt = f"{system_instruction}\n\n"

                if history:

                    chat_prompt += "=== LỊCH SỬ CHAT TRƯỚC ĐÓ ===\n"

                    for h in history[-6:]:  # Lấy 6 lượt chat gần nhất

                        role = "User" if h.get("role") == "user" else "AI"

                        chat_prompt += f"{role}: {h.get('text', '')}\n"

                    chat_prompt += "\n=== LƯỢT CHAT MỚI ===\n"

                chat_prompt += full_content



                resp = client.models.generate_content(

                    model=m,

                    contents=chat_prompt

                )

                if resp and resp.text:

                    reply_text = resp.text

                    break

            except Exception as ex:

                last_err = ex

                continue



        if not reply_text:

            return jsonify({

                "success": False,

                "message": f"Không thể lấy phản hồi từ Gemini ({last_err})"

            }), 500



        return jsonify({

            "success": True,

            "reply": reply_text

        })



    except Exception as e:

        return jsonify({

            "success": False,

            "message": f"Lỗi gọi Gemini AI: {str(e)}"

        }), 500



@app.route("/api/project_files", methods=["GET"])

def get_project_files():

    """Lấy danh sách các file mã nguồn trong dự án để AI Assistant có thể đọc nhanh"""

    allowed_exts = {".py", ".html", ".js", ".css", ".json", ".txt", ".md", ".env", ".bat"}

    file_list = []

    try:

        for root, dirs, files in os.walk(BASE_DIR):

            # Bỏ qua các thư mục không cần thiết

            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "venv", ".idea", ".vscode", "node_modules", ".gemini"]]

            for f in files:

                ext = os.path.splitext(f)[1].lower()

                if ext in allowed_exts:

                    full_p = os.path.join(root, f)

                    rel_p = os.path.relpath(full_p, BASE_DIR)

                    file_list.append(rel_p)

        file_list.sort()

        return jsonify({"success": True, "files": file_list})

    except Exception as e:

        return jsonify({"success": False, "message": str(e), "files": []})



@app.route("/api/get_file_content", methods=["POST"])

def get_file_content():

    """Đọc nội dung một file trong dự án"""

    data = request.json or {}

    rel_path = (data.get("filename") or "").strip()

    if not rel_path:

        return jsonify({"success": False, "message": "Chưa cung cấp tên file"}), 400

    

    # Bảo vệ chống path traversal

    safe_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))

    if not safe_path.startswith(BASE_DIR):

        return jsonify({"success": False, "message": "Đường dẫn không hợp lệ"}), 403

    

    if not os.path.exists(safe_path):

        return jsonify({"success": False, "message": "File không tồn tại"}), 404



    try:

        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:

            content = f.read()

        return jsonify({"success": True, "filename": rel_path, "content": content})

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/api/save_file_content", methods=["POST"])

def save_file_content():

    """Lưu cập nhật code trực tiếp từ AI Code Editor"""

    data = request.json or {}

    rel_path = (data.get("filename") or "").strip()

    content = data.get("content")

    if not rel_path or content is None:

        return jsonify({"success": False, "message": "Thiếu dữ liệu"}), 400



    safe_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))

    if not safe_path.startswith(BASE_DIR):

        return jsonify({"success": False, "message": "Đường dẫn không hợp lệ"}), 403



    try:

        with open(safe_path, "w", encoding="utf-8") as f:

            f.write(content)

        return jsonify({"success": True, "message": f"Đã lưu file {rel_path} thành công!"})

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500





@app.route("/api/repost_comments", methods=["POST"])

def repost_comments():

    """

    Đăng lại link Affiliate vào phần bình luận của video đã đăng.

    Hỗ trợ: YouTube, Facebook, Instagram, Threads.

    Payload JSON:

      - platform   : "youtube" | "facebook" | "instagram" | "threads"

      - brand_key  : mã kênh

      - video_id   : ID video trên nền tảng

      - links      : list URL string (mỗi URL là 1 bình luận riêng)

      - excel_path : (tuỳ chọn) đường dẫn file .xlsx/.csv để tự parse link

    """

    try:

        data = request.json or {}

        platform   = (data.get("platform") or "").strip().lower()

        brand_key  = (data.get("brand_key") or "").strip()

        video_id   = (data.get("video_id") or "").strip()

        links      = data.get("links") or []          # list[str] — URL thô

        excel_path = (data.get("excel_path") or "").strip()



        if not platform or not brand_key:

            return jsonify({"success": False, "message": "Thiếu platform hoặc brand_key"}), 400



        # Với dry_run không cần video_id

        if not data.get("dry_run") and not video_id:

            return jsonify({"success": False, "message": "Thiếu video_id"}), 400



        brands = load_brands()

        brand_cfg = brands.get(brand_key)

        if not brand_cfg:

            return jsonify({"success": False, "message": f"Không tìm thấy cấu hình kênh: {brand_key}"}), 404



        # --- Parse sản phẩm từ Excel nếu có ---

        products = []

        if excel_path and os.path.exists(excel_path):

            try:

                products = parse_link_file(excel_path)

            except Exception as e:

                return jsonify({"success": False, "message": f"Lỗi đọc file Excel: {e}"}), 400

        elif links:

            # Dán link thủ công: mỗi URL là 1 sản phẩm tên chung

            for url in links:

                url = str(url).strip()

                if url.startswith("http"):

                    products.append({"name": "Sản phẩm chính hãng", "link": url, "link_goc": ""})



        if not products:

            return jsonify({"success": False, "message": "Không có link nào để đăng bình luận"}), 400



        # Tạo danh sách comment theo template luân phiên (ưu tiên đúng nền tảng)

        comment_list = get_platform_comments(products, platform, brand_key)

        if not comment_list:

            comment_list = format_affiliate_comments(products, brand_key)

        if not comment_list:

            return jsonify({"success": False, "message": "Không tạo được nội dung bình luận"}), 400



        # Chế độ dry_run: chỉ trả preview, không đăng thật

        if data.get("dry_run"):

            return jsonify({

                "success": True,

                "message": f"Preview {len(comment_list)} bình luận sẵn sàng.",

                "comments_preview": comment_list,

                "posted": [],

                "errors": []

            })



        posted = []

        errors = []



        # ── YouTube ──────────────────────────────────────────────────────────

        if "youtube" in platform:

            try:

                from google.auth.transport.requests import Request as GRequest

                from google.oauth2.credentials import Credentials as GCreds

                from googleapiclient.discovery import build as yt_build



                yt_cfg    = brand_cfg.get("youtube", {})

                tok_file  = yt_cfg.get("token_file", "")

                tok_path  = os.path.join(BASE_DIR, "POST", tok_file) if not os.path.isabs(tok_file) else tok_file

                yt_scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]



                creds = GCreds.from_authorized_user_file(tok_path, yt_scopes)

                if creds and creds.expired and creds.refresh_token:

                    creds.refresh(GRequest())

                    with open(tok_path, "w", encoding="utf-8") as tf:

                        tf.write(creds.to_json())



                # Chống trùng lặp comment YouTube khi repost

                existing_texts, existing_links = get_existing_yt_comments(yt_service, video_id)



                for idx, cmt in enumerate(comment_list, 1):

                    if is_duplicate_yt_comment(cmt, existing_texts, existing_links):

                        posted.append(f"YouTube #{idx} (Đã có sẵn trên video, bỏ qua)")

                        continue

                    try:

                        time.sleep(2)

                        yt_service.commentThreads().insert(

                            part="snippet",

                            body={

                                "snippet": {

                                    "videoId": video_id,

                                    "topLevelComment": {

                                        "snippet": {"textOriginal": cmt}

                                    }

                                }

                            }

                        ).execute()

                        existing_texts.add(cmt.strip().lower())

                        for u in re.findall(r'https?://[^\s<>"]+', cmt):

                            existing_links.add(u.rstrip("/?#&").lower())

                        posted.append(f"YouTube #{idx}")

                    except Exception as ce:

                        errors.append(f"YouTube #{idx}: {ce}")

            except Exception as e:

                errors.append(f"YouTube setup lỗi: {e}")



        # ── Facebook ─────────────────────────────────────────────────────────

        elif "facebook" in platform:

            fb_cfg = brand_cfg.get("facebook", {})

            tok    = fb_cfg.get("access_token", "")

            if not tok:

                return jsonify({"success": False, "message": "Chưa có Facebook access_token"}), 400

            for idx, cmt in enumerate(comment_list, 1):

                try:

                    time.sleep(2)

                    r = requests.post(

                        f"https://graph.facebook.com/v19.0/{video_id}/comments",

                        data={"message": cmt, "access_token": tok},

                        timeout=20

                    ).json()

                    if "id" in r:

                        posted.append(f"Facebook #{idx}")

                    else:

                        errors.append(f"Facebook #{idx}: {r.get('error', {}).get('message', r)}")

                except Exception as ce:

                    errors.append(f"Facebook #{idx}: {ce}")



        # ── Instagram ────────────────────────────────────────────────────────

        elif "instagram" in platform:

            ig_cfg = brand_cfg.get("instagram", {})

            tok    = ig_cfg.get("access_token", "")

            if not tok:

                return jsonify({"success": False, "message": "Chưa có Instagram access_token"}), 400

            for idx, cmt in enumerate(comment_list, 1):

                try:

                    time.sleep(2)

                    r = requests.post(

                        f"https://graph.facebook.com/v19.0/{video_id}/comments",

                        data={"message": cmt, "access_token": tok},

                        timeout=20

                    ).json()

                    if "id" in r:

                        posted.append(f"Instagram #{idx}")

                    else:

                        errors.append(f"Instagram #{idx}: {r.get('error', {}).get('message', r)}")

                except Exception as ce:

                    errors.append(f"Instagram #{idx}: {ce}")



        # ── Threads ──────────────────────────────────────────────────────────

        elif "threads" in platform:

            th_cfg  = brand_cfg.get("threads", {})

            tok     = th_cfg.get("access_token", "")

            user_id = th_cfg.get("user_id", "")

            if not tok or not user_id:

                return jsonify({"success": False, "message": "Chưa cấu hình Threads user_id / access_token"}), 400

            for idx, cmt in enumerate(comment_list, 1):

                try:

                    # Tạo reply container

                    r_create = requests.post(

                        f"https://graph.threads.net/v1.0/{user_id}/threads",

                        data={

                            "media_type": "TEXT",

                            "text": cmt,

                            "reply_to_id": video_id,

                            "access_token": tok

                        },

                        timeout=25

                    ).json()

                    if "id" not in r_create:

                        errors.append(f"Threads #{idx} tạo container lỗi: {r_create}")

                        continue

                    time.sleep(2)

                    # Publish reply

                    r_pub = requests.post(

                        f"https://graph.threads.net/v1.0/{user_id}/threads_publish",

                        data={"creation_id": r_create["id"], "access_token": tok},

                        timeout=20

                    ).json()

                    if "id" in r_pub:

                        posted.append(f"Threads #{idx}")

                    else:

                        errors.append(f"Threads #{idx} publish lỗi: {r_pub}")

                except Exception as ce:

                    errors.append(f"Threads #{idx}: {ce}")

        else:

            return jsonify({"success": False, "message": f"Nền tảng '{platform}' không hỗ trợ đăng lại comment"}), 400



        # ── Tổng kết ─────────────────────────────────────────────────────────

        total    = len(comment_list)

        ok_count = len(posted)

        if ok_count == 0:

            return jsonify({

                "success": False,

                "message": f"Đăng thất bại toàn bộ {total} bình luận.",

                "errors": errors

            })

        return jsonify({

            "success": True,

            "message": f"✅ Đã đăng {ok_count}/{total} bình luận thành công!",

            "posted": posted,

            "errors": errors,

            "comments_preview": comment_list

        })



    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500





@app.route("/api/regenerate_title_desc", methods=["POST"])

def regenerate_title_desc():

    """

    Dùng Gemini API (text-only) để gen lại Tiêu đề & Mô tả chuẩn SEO

    dựa trên tiêu đề hiện tại + tên thương hiệu + nền tảng.

    Không cần upload lại video.

    """

    try:

        data = request.json or {}

        current_title = (data.get("title") or "").strip()

        current_desc = (data.get("description") or "").strip()

        brand_key = (data.get("brand_key") or "").strip()

        platform = (data.get("platform") or "").strip()



        if not current_title and not current_desc:

            return jsonify({"success": False, "message": "Cần có tiêu đề hoặc mô tả hiện tại để gen lại"}), 400



        api_key = get_gemini_api_key()

        if not api_key:

            return jsonify({"success": False, "message": "Chưa cấu hình GEMINI_API_KEY trong file .env"}), 400



        brands = load_brands()

        brand_name = brands.get(brand_key, {}).get("name", brand_key) if brand_key else ""



        prompt = f"""Bạn là Giám đốc Sáng tạo Nội dung kiêm Chuyên gia SEO Affiliate hàng đầu, chuyên tối ưu video ngắn đạt CTR và chuyển đổi đơn hàng cao nhất trên YouTube Shorts, Facebook Reels, Instagram Reels và Threads.



Nhiệm vụ: Dựa vào thông tin video hiện có, viết lại Tiêu đề và Mô tả CHUẨN SEO — hook mạnh hơn, từ khóa tối ưu hơn, CTR cao hơn, thúc đẩy click affiliate tốt hơn.



━━━ THÔNG TIN VIDEO HIỆN TẠI ━━━

Tiêu đề hiện tại : {current_title if current_title else '(chưa có)'}

Mô tả hiện tại   : {current_desc[:400] if current_desc else '(chưa có)'}

Kênh phân phối   : {brand_name if brand_name else '(không rõ)'}

Nền tảng đăng    : {platform if platform else 'YouTube Shorts / Facebook Reels / Instagram Reels'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



Trả về DUY NHẤT chuỗi JSON hợp lệ (TUYỆT ĐỐI không bọc markdown ```json, không giải thích, không thêm bất kỳ text nào ngoài JSON):



{{

  "title": "...",

  "description": "...",

  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]

}}



━━━ QUY TẮC SEO BẮT BUỘC ━━━



【TIÊU ĐỀ — Title】

• Độ dài: 55–80 ký tự (hiển thị trọn vẹn trên mobile, không bị cắt '...' ở YouTube Shorts & Facebook Reels).

• Phải chứa TÊN HOẶC LOẠI SẢN PHẨM CỤ THỂ (ví dụ: "kính cường lực", "đệm lưng công thái học", "máy hút mụn").

• Bắt đầu bằng một trong các Hook kích thích tâm lý mạnh nhất:

  - Nỗi đau → Giải pháp : "Hết Đau Lưng Khi Ngồi Máy Tính Với Đệm Công Thái Học Này! 🔥"

  - Cảnh báo / Sốc nhẹ : "Đừng Mua Kính Cường Lực Nếu Chưa Xem Clip Này! ⚠️"

  - So sánh / Listicle  : "Test 5 Loại Kính Cường Lực iPhone: Loại Nào Xứng Đáng Nhất? 🤔"

  - Bí quyết / Hack     : "Cách Chọn Đệm Lưng Đúng Chuẩn Công Thái Học — Dân Văn Phòng Cần Biết ✨"

• CUỐI tiêu đề BẮT BUỘC chèn đúng 1 hashtag sản phẩm slug viết liền (ví dụ: "#kinhcuongluc", "#demlung") + "#Shorts". Ví dụ hoàn chỉnh: "Đừng Mua Kính Cường Lực Nếu Chưa Xem Clip Này! ⚠️ #kinhcuongluc #Shorts"

• 1–2 emoji trong câu, không spam.

• TUYỆT ĐỐI không dùng tiêu đề dạng "Review [Tên SP]" khô khan, thiếu hook.



【MÔ TẢ / CAPTION — Description】

• Cấu trúc 3 phần rõ ràng:

  1. Hook câu đầu (1 câu): Đánh thẳng vào nỗi đau hoặc lợi ích lớn nhất.

  2. Thân bài (1–2 câu): 2–3 tính năng nổi bật, lồng từ khóa phụ + ngữ cảnh người dùng.

  3. CTA dứt khoát: "Link mua chính hãng + ưu đãi mình đã ghim sẵn ở bình luận nhé! 👇"

• Sau CTA, THÊM 1 dòng trống rồi chèn 3–5 hashtag slug (ví dụ: "#kinhcuongluc #phukieniphone #reviewcongnghe #Shorts #Reels"). Đây là hashtag dành cho phần mô tả YouTube và caption Instagram.

• Tổng độ dài phần mô tả (chưa kể hashtag): 3–5 câu, tối đa 450 ký tự.

• Ngôn ngữ tiếng Việt tự nhiên, gần gũi, đúng văn phong review affiliate.



【HASHTAGS — field riêng trong JSON】

• 7–8 hashtag slug viết liền, KHÔNG chứa '#' (hệ thống tự thêm '#' khi dùng).

• Cơ cấu BẮT BUỘC:

  - Tag [0] và [1]: tên / loại sản phẩm cụ thể slug (dùng trong tiêu đề YouTube)

  - Tag [2]–[4]: ngách / hành vi mua (reviewgiadung, meovat, congthaihoc…)

  - Tag [5]–[6]: nền tảng xu hướng (shorts, reels)

  - Tag [7]: tên kênh slug nếu có (noithatdungthat, setupphongxinh…)

• Tất cả viết liền không dấu cách, không ký tự đặc biệt.



【NGÔN NGỮ】 100% tiếng Việt tự nhiên, giọng review thật — không quảng cáo lộ liễu.



CHỈ TRẢ VỀ DUY NHẤT CHUỖI JSON HỢP LỆ."""



        from google import genai

        client = genai.Client(api_key=api_key)



        models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]

        result_text = None

        last_err = None



        for model_name in models_to_try:

            try:

                resp = client.models.generate_content(model=model_name, contents=prompt)

                if resp and (resp.text or "").strip():

                    result_text = resp.text.strip()

                    break

            except Exception as me:

                last_err = me

                continue



        if not result_text:

            return jsonify({"success": False, "message": f"Gemini không phản hồi: {last_err}"}), 500



        # Clean markdown nếu Gemini vẫn bọc ```json

        if result_text.startswith("```"):

            result_text = re.sub(r'^```\w*\n?', '', result_text)

            result_text = re.sub(r'\n?```$', '', result_text.strip())



        result = json.loads(result_text.strip())

        return jsonify({

            "success": True,

            "title": result.get("title", ""),

            "description": result.get("description", ""),

            "hashtags": result.get("hashtags", [])

        })



    except json.JSONDecodeError as e:

        return jsonify({"success": False, "message": f"Gemini trả về JSON không hợp lệ: {e}"}), 500

    except ImportError:

        return jsonify({"success": False, "message": "Chưa cài google-genai. Chạy: pip install google-genai"}), 500

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi gen lại tiêu đề: {str(e)}"}), 500





@app.route("/api/analytics/ai_optimize_flop", methods=["POST"])

def ai_optimize_flop():

    """

    Dùng Gemini AI chuyên biệt để 'CỨU FLOP' cho video bị đứng view sau 24h:

    - Phân tích nguyên nhân video flop (thiếu tò mò, hook yếu, sai từ khóa, hashtag bão hòa)

    - Viết lại Tiêu đề có tỷ lệ click (CTR) cao đột phá, giật tít đánh trúng tâm lý người xem

    - Viết lại Caption/Mô tả dẫn dắt giữ chân và chốt sale affiliate

    - Bộ 7-8 Hashtag ngách mới để thuật toán phân phối lại tệp người xem mới

    """

    try:

        data = request.json or {}

        current_title = (data.get("title") or "").strip()

        current_desc = (data.get("description") or "").strip()

        brand_key = (data.get("brand_key") or "").strip()

        platform = (data.get("platform") or "").strip()

        views = data.get("views", 0)

        likes = data.get("likes", 0)

        comments = data.get("comments", 0)

        age_hours = data.get("age_hours", 24)



        if not current_title and not current_desc:

            return jsonify({"success": False, "message": "Cần có tiêu đề hoặc mô tả hiện tại của video flop"}), 400



        api_key = get_gemini_api_key()

        if not api_key:

            return jsonify({"success": False, "message": "Chưa cấu hình GEMINI_API_KEY trong file .env"}), 400



        brands = load_brands()

        brand_name = brands.get(brand_key, {}).get("name", brand_key) if brand_key else ""



        prompt = f"""Bạn là Bậc Thầy Tối Ưu Thuật Toán Video Ngắn (YouTube Shorts, Facebook Reels, TikTok) chuyên giải cứu các video bị FLOP / BỊ BÓP TƯƠNG TÁC / ĐỨNG VIEW sau 24h đăng.



NGUYÊN TẮC THUẬT TOÁN:

Khi video bị flop (ít view sau 24h), thuật toán đã dừng phân phối vì:

1. Tỷ lệ click (CTR) quá thấp do Tiêu đề nhàm chán, không kích thích tò mò hoặc đánh đúng nỗi đau.

2. Từ khóa/Hashtag quá chung chung hoặc cạnh tranh quá cao, khiến AI phân phối nhầm tệp khán giả.

3. Phần mở đầu (Hook) trong mô tả thiếu sự cấp bách hoặc tranh cãi ngầm.



NHIỆM VỤ: Hãy "TÁI SINH" lại siêu dữ liệu (Metadata) cho video này để thuật toán kích hoạt vòng thử nghiệm phân phối mới!



━━━ THÔNG TIN VIDEO BỊ FLOP ━━━

• Tiêu đề hiện tại : {current_title if current_title else '(chưa có)'}

• Mô tả hiện tại   : {current_desc[:350] if current_desc else '(chưa có)'}

• Kênh sở hữu      : {brand_name if brand_name else '(không rõ)'}

• Nền tảng         : {platform if platform else 'Facebook Reels / YouTube Shorts'}

• Thời gian đã đăng: {age_hours} giờ

• Chỉ số hiện tại  : {views} views, {likes} likes, {comments} bình luận (Bị Flop nặng)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



YÊU CẦU ĐẶC BIỆT KHI CỨU FLOP:

1. TIÊU ĐỀ (Title):

   - Tuyệt đối KHÔNG giữ cách đặt tên cũ khô khan hay theo khuôn sáo "Review..."

   - Áp dụng các công thức Viral Hook tâm lý cực mạnh:

     + Hook Nghịch lý / Gây sốc: "Tưởng Phí Tiền Hóa Ra Lại Quá Đỉnh..."

     + Hook Cảnh báo: "Ai Đang Dùng Cái Này Thì Bỏ Ngay Đi! ⚠️"

     + Hook Tò mò cực độ: "Lý Do Người Ta Giấu Không Cho Bạn Biết Mẹo Này... 🤫"

     + Hook Tiết kiệm / Tránh bẫy: "Đừng Mua Nếu Chưa Biết 1 Điều Này Về..."

   - Chiều dài: 55 - 80 ký tự (chuẩn mobile, không bị che mất chữ).

   - Thêm 1 hashtag sản phẩm ngắn gọn + #Shorts (hoặc #Reels) ở cuối.



2. MÔ TẢ / CAPTION (Description):

   - Câu đầu tiên phải kích thích tranh luận hoặc đồng cảm sâu sắc.

   - 2-3 câu ngắn nêu giải pháp & tính năng thực tế.

   - Lời kêu gọi hành động (CTA) ghim link mua hàng tự nhiên: "Link chi tiết và ưu đãi mình để sẵn dưới bình luận/bio nhé! 👇"

   - Kèm 3-5 hashtag đuôi.



3. HASHTAGS (Danh sách 7-8 tags):

   - Tránh tag quá chung chung 100M views (như #viral, #trending).

   - Hãy chọn tag ngách có tính chuyển đổi cao, tag giải quyết vấn đề, tag sản phẩm cụ thể.



4. GIẢI THÍCH CHIẾN LƯỢC (strategy_reason):

   - Tóm tắt 1-2 câu ngắn giải thích vì sao tiêu đề và cách tiếp cận mới này sẽ giúp video thoát flop và kích hoạt lại thuật toán đề xuất.



Trả về DUY NHẤT chuỗi JSON hợp lệ (KHÔNG bọc markdown ```json, không thêm chữ thừa nào ngoài JSON):

{{

  "title": "...",

  "description": "...",

  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],

  "strategy_reason": "..."

}}"""



        from google import genai

        client = genai.Client(api_key=api_key)



        models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]

        result_text = None

        last_err = None



        for model_name in models_to_try:

            try:

                resp = client.models.generate_content(model=model_name, contents=prompt)

                if resp and (resp.text or "").strip():

                    result_text = resp.text.strip()

                    break

            except Exception as me:

                last_err = me

                continue



        if not result_text:

            return jsonify({"success": False, "message": f"Gemini không phản hồi: {last_err}"}), 500



        if result_text.startswith("```"):

            result_text = re.sub(r'^```\w*\n?', '', result_text)

            result_text = re.sub(r'\n?```$', '', result_text.strip())



        result = json.loads(result_text.strip())

        return jsonify({

            "success": True,

            "title": result.get("title", ""),

            "description": result.get("description", ""),

            "hashtags": result.get("hashtags", []),

            "strategy_reason": result.get("strategy_reason", "")

        })



    except json.JSONDecodeError as e:

        return jsonify({"success": False, "message": f"Gemini trả về JSON không hợp lệ: {e}"}), 500

    except ImportError:

        return jsonify({"success": False, "message": "Chưa cài google-genai. Chạy: pip install google-genai"}), 500

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi tối ưu flop AI: {str(e)}"}), 500






@app.route("/api/analytics/optimized_flop_videos_list", methods=["GET"])
def get_optimized_flop_videos_list():
    """Lấy danh sách tất cả các video đã được quét và tối ưu bởi AI (cứu flop)."""
    try:
        from fetch_analytics import load_cached_analytics, _load_optimized_videos
        opt_cache = _load_optimized_videos()
        cached = load_cached_analytics()
        data = cached.get("data", {}) if isinstance(cached, dict) else {}
        brands_cfg = load_brands()

        enriched_list = []
        for v_id, opt in opt_cache.items():
            b_key = opt.get("brand_key", "")
            brand_name = brands_cfg.get(b_key, {}).get("name", b_key)
            p = (opt.get("platform") or "").lower()
            item = dict(opt)
            item["brand_name"] = brand_name
            
            # Khớp thông tin video từ analytics cache (views, thumbnail, url,...)
            matched = None
            if b_key in data and p in data[b_key].get("platforms", {}):
                for cv in data[b_key]["platforms"][p].get("videos", []):
                    if str(cv.get("id", "")).strip() == str(v_id).strip():
                        matched = cv
                        break
            
            if matched:
                item["views"] = matched.get("views", 0)
                item["likes"] = matched.get("likes", 0)
                item["comments"] = matched.get("comments", 0)
                item["url"] = matched.get("url", "")
                item["published_at"] = matched.get("published_at", "")
                item["thumbnail"] = matched.get("thumbnail", "")
                if not item.get("last_title"):
                    item["last_title"] = matched.get("title", "")
            else:
                item.setdefault("views", 0)
                item.setdefault("likes", 0)
                item.setdefault("comments", 0)
                item.setdefault("url", f"https://youtube.com/shorts/{v_id}" if "youtube" in p else f"https://facebook.com/reel/{v_id}")
                item.setdefault("thumbnail", "")
                item.setdefault("published_at", "")

            enriched_list.append(item)

        # Sắp xếp mới nhất lên đầu (theo thời gian tối ưu gần nhất)
        def _sort_key(x):
            return str(x.get("last_optimized_at") or "")
        enriched_list.sort(key=_sort_key, reverse=True)

        # Thống kê tổng quan
        yt_count = sum(1 for x in enriched_list if "youtube" in (x.get("platform") or "").lower())
        fb_count = sum(1 for x in enriched_list if "facebook" in (x.get("platform") or "").lower())
        round1_count = sum(1 for x in enriched_list if x.get("optimize_count") == 1)
        round2_count = sum(1 for x in enriched_list if x.get("optimize_count") == 2)
        round3_count = sum(1 for x in enriched_list if (x.get("optimize_count") or 0) >= 3)

        return jsonify({
            "success": True,
            "total": len(enriched_list),
            "stats": {
                "youtube": yt_count,
                "facebook": fb_count,
                "round1": round1_count,
                "round2": round2_count,
                "round3_or_more": round3_count
            },
            "videos": enriched_list
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/auto_flop_log", methods=["GET"])
def get_auto_flop_log():
    """Lấy log và trạng thái gần nhất của tiến trình tự động cứu flop."""
    try:
        log_file = os.path.join(AFFILIATE_ROOT, "post1", "logs", "auto_flop_rescue.log")
        recent_logs = []
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                recent_logs = [l.strip() for l in lines[-60:] if l.strip()]

        opt_cache = _load_optimized_videos()
        settings_file = os.path.join(POST_DIR, "config", "flop_settings.json")
        settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as sf:
                    settings = json.load(sf)
            except Exception:
                pass

        return jsonify({
            "success": True,
            "logs": recent_logs,
            "total_optimized_records": len(opt_cache),
            "settings": settings
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/run_auto_flop_now", methods=["POST"])
def run_auto_flop_now_endpoint():
    """Kích hoạt tiến trình tự động cứu flop ngay lập tức (chạy ngầm độc lập)."""
    try:
        import subprocess
        script_path = os.path.join(AFFILIATE_ROOT, "auto_rescue_flop.py")
        py_exe = os.path.join(AFFILIATE_ROOT, "python311", "python.exe")
        if not os.path.exists(py_exe):
            py_exe = sys.executable

        subprocess.Popen([py_exe, script_path], cwd=AFFILIATE_ROOT)
        return jsonify({
            "success": True,
            "message": "Đã kích hoạt tiến trình tự động cứu flop thành công! Tiến trình đang chạy ngầm và ghi log."
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi kích hoạt cứu flop: {str(e)}"}), 500


@app.route("/api/update_video", methods=["POST"])

def update_video():

    """

    Cập nhật Tiêu đề, Mô tả, Thumbnail cho Video trên YouTube, Facebook, hoặc Thêm comment ghim cho Instagram

    """

    try:

        platform = request.form.get("platform", "").strip().lower()

        brand_key = request.form.get("brand_key", "").strip()

        video_id = request.form.get("video_id", "").strip()

        title = request.form.get("title")

        description = request.form.get("description")

        comment_text = request.form.get("comment_text")



        if not platform or not brand_key or not video_id:

            return jsonify({"success": False, "message": "Thiếu thông tin bắt buộc (platform, brand_key, video_id)"}), 400



        brands = load_brands()

        brand_cfg = brands.get(brand_key)

        if not brand_cfg:

            return jsonify({"success": False, "message": f"Không tìm thấy cấu hình cho kênh: {brand_key}"}), 404



        # Xử lý file thumbnail tải lên nếu có

        thumbnail_path = None

        if "thumbnail" in request.files:

            thumb_file = request.files["thumbnail"]

            if thumb_file and thumb_file.filename:

                import tempfile

                ext = os.path.splitext(thumb_file.filename)[1] or ".jpg"

                temp_thumb = tempfile.NamedTemporaryFile(delete=False, suffix=ext)

                thumb_file.save(temp_thumb.name)

                temp_thumb.close()

                thumbnail_path = temp_thumb.name



        try:

            if "youtube" in platform:

                res = update_youtube_video(

                    brand_cfg=brand_cfg,

                    video_id=video_id,

                    title=title,

                    description=description,

                    thumbnail_path=thumbnail_path

                )

            elif "facebook" in platform:

                res = update_facebook_video(

                    brand_cfg=brand_cfg,

                    video_id=video_id,

                    title=title,

                    description=description,

                    thumbnail_path=thumbnail_path

                )

            elif "instagram" in platform:

                res = update_instagram_post(

                    brand_cfg=brand_cfg,

                    media_id=video_id,

                    caption=description,

                    comment_text=comment_text

                )

            else:

                return jsonify({"success": False, "message": f"Nền tảng {platform} không hỗ trợ chỉnh sửa qua API"}), 400



            # Nếu cập nhật thành công, ghi nhận tăng số lần tối ưu

            if isinstance(res, dict) and res.get("success"):

                try:

                    strategy_reason = request.form.get("strategy_reason", "")

                    opt_count = record_video_optimization(

                        platform=platform,

                        brand_key=brand_key,

                        video_id=video_id,

                        new_title=title or "",

                        new_desc=description or "",

                        strategy_reason=strategy_reason

                    )

                    res["optimize_count"] = opt_count

                except Exception as e_rec:

                    print(f"⚠️ Lỗi record_video_optimization trong update_video: {e_rec}")



            return jsonify(res)

        finally:

            if thumbnail_path and os.path.exists(thumbnail_path):

                try:

                    os.remove(thumbnail_path)

                except Exception:

                    pass

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/api/video/sync-yt-thumbnail-to-fb", methods=["POST"])

def sync_yt_thumbnail_to_fb_route():

    """

    1-Click đồng bộ Thumbnail từ YouTube sang Facebook Video.

    Payload: { "brand_key": "...", "fb_video_id": "...", "yt_video_id": "..." }

    """

    try:

        req_data = request.get_json(silent=True) or request.form

        brand_key = req_data.get("brand_key", "").strip()

        fb_video_id = req_data.get("fb_video_id", "").strip()

        yt_video_id = req_data.get("yt_video_id", "").strip()



        if not brand_key or not fb_video_id or not yt_video_id:

            return jsonify({"success": False, "message": "Thiếu tham số brand_key, fb_video_id hoặc yt_video_id"}), 400



        brands = load_brands()

        brand_cfg = brands.get(brand_key)

        if not brand_cfg:

            return jsonify({"success": False, "message": f"Không tìm thấy cấu hình cho kênh: {brand_key}"}), 404



        res = sync_youtube_thumbnail_to_facebook(

            brand_cfg=brand_cfg,

            fb_video_id=fb_video_id,

            yt_video_id=yt_video_id

        )

        return jsonify(res)

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi đồng bộ thumbnail: {str(e)}"}), 500



@app.route("/api/video/get-yt-thumbnail", methods=["GET"])

def get_yt_thumbnail_route():

    """

    Lấy thông tin và link ảnh Thumbnail nét nhất từ YouTube (hỗ trợ ID hoặc URL).

    Query: ?yt_video_id=...

    """

    try:

        yt_vid = request.args.get("yt_video_id", "").strip()

        if not yt_vid:

            return jsonify({"success": False, "message": "Thiếu tham số yt_video_id"}), 400

        

        img_bytes, selected_url, mime = get_best_youtube_thumbnail_bytes(yt_vid)

        if not selected_url or not img_bytes:

            return jsonify({"success": False, "message": f"Không thể lấy thumbnail cho video: {yt_vid}"}), 404

        

        m_id = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/vi\/)?([a-zA-Z0-9_-]{11})', yt_vid)

        clean_id = m_id.group(1) if m_id else yt_vid

        

        return jsonify({

            "success": True,

            "yt_video_id": clean_id,

            "thumbnail_url": selected_url,

            "bytes_size": len(img_bytes),

            "mime_type": mime,

            "download_url": f"/api/video/download-yt-thumbnail?yt_video_id={clean_id}"

        })

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/api/video/download-yt-thumbnail", methods=["GET"])

def download_yt_thumbnail_route():

    """

    Tải file ảnh Thumbnail chất lượng cao từ YouTube trực tiếp về máy tính (.jpg).

    Query: ?yt_video_id=...

    """

    try:

        from io import BytesIO

        yt_vid = request.args.get("yt_video_id", "").strip()

        if not yt_vid:

            return jsonify({"success": False, "message": "Thiếu tham số yt_video_id"}), 400

        

        img_bytes, selected_url, mime = get_best_youtube_thumbnail_bytes(yt_vid)

        if not img_bytes:

            return jsonify({"success": False, "message": "Không thể tải thumbnail từ YouTube"}), 404

        

        m_id = re.search(r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/vi\/)?([a-zA-Z0-9_-]{11})', yt_vid)

        clean_id = m_id.group(1) if m_id else "youtube"

        

        return send_file(

            BytesIO(img_bytes),

            mimetype=mime or "image/jpeg",

            as_attachment=True,

            download_name=f"{clean_id}_thumbnail.jpg"

        )

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



# ─────────────────────────────────────────────────────────────────────────────

# TẠO & XUẤT FILE BATCH CUSTOM LINKS (.XLSX) CHO 7 NỀN TẢNG (SHOPEE AFFILIATE)

# ─────────────────────────────────────────────────────────────────────────────



@app.route("/api/generate_batch_custom_links", methods=["POST"])

def generate_batch_custom_links():

    """

    Tạo file Batch Custom Links.xlsx đúng cấu trúc Shopee Affiliate:

    - 6 Cột chuẩn: ['Liên kết gốc', 'Sub_id1', 'Sub_id2', 'Sub_id3', 'Sub_id4', 'Sub_id5']

    - 7 Nền tảng: facebook, instagram, threads, shopeevideo, zalovideo, pinterest, youtube

    - 1 link gốc -> 7 dòng; 2 link gốc -> 14 dòng; N link -> N * 7 dòng

    - Lưu file vào: C:\\Affiliate\\<BrandFolder>\\Link gốc\\<Folder>\\Batch Custom Links.xlsx

    - Trả về đường dẫn và download_url để tự động tải về

    """

    try:

        data = request.json or {}

        brand_key = (data.get("brand_key") or "").strip()

        raw_links = data.get("links") or []

        sub2_prefix = (data.get("sub2_prefix") or "").strip()

        video_path = (data.get("video_path") or "").strip()



        if not brand_key:

            return jsonify({"success": False, "message": "Thiếu mã kênh (brand_key)"}), 400



        # Lọc danh sách link Shopee hợp lệ

        clean_links = []

        for l in raw_links:

            u = str(l).strip()

            if u.startswith("http://") or u.startswith("https://"):

                clean_links.append(u)



        if not clean_links:

            return jsonify({"success": False, "message": "Vui lòng nhập ít nhất 1 đường link Shopee gốc hợp lệ!"}), 400



        brands = load_brands()

        b_data = brands.get(brand_key, {})

        folder_name = b_data.get("folder", brand_key)



        channel_sub3 = get_brand_sub_id3(brand_key)



        # Tạo openpyxl Workbook

        wb = openpyxl.Workbook()

        ws = wb.active

        ws.title = "Sheet1"



        # 6 Cột chuẩn

        headers = ["Liên kết gốc", "Sub_id1", "Sub_id2", "Sub_id3", "Sub_id4", "Sub_id5"]

        ws.append(headers)



        video_name = os.path.splitext(os.path.basename(video_path))[0] if video_path else ""



        # Ghi các dòng: gom theo từng nền tảng (7 nền tảng)

        total_rows = 0

        for plat in BATCH_CUSTOM_PLATFORMS:

            for idx, link in enumerate(clean_links, start=1):

                sub2 = make_sub_id2(link, idx=idx, prefix=sub2_prefix, video_name=video_name)

                ws.append([link, plat, sub2, channel_sub3, "video", "organic"])

                total_rows += 1



        # Xác định thư mục lưu file: Lưu thẳng vào folder chứa video

        target_dir = ""

        if video_path:

            raw_vpath = video_path.strip().strip('"').strip("'")

            if os.path.isabs(raw_vpath):

                # Đường dẫn tuyệt đối như C:\Affiliate\Nói Thật Dùng Thật\Video_việt_hóa\Video chưa đăng\đợt 4\9\9.mp4

                if os.path.isdir(raw_vpath):

                    target_dir = raw_vpath

                else:

                    target_dir = os.path.dirname(raw_vpath)

            else:

                # Đường dẫn tương đối

                brand_dir = os.path.join(AFFILIATE_ROOT, folder_name)

                candidate_paths = [

                    os.path.join(brand_dir, raw_vpath),

                    os.path.join(brand_dir, "Video_việt_hóa", "Video chưa đăng", raw_vpath),

                    os.path.join(brand_dir, "video_việt_hóa", "video chua dang", raw_vpath),

                    os.path.join(brand_dir, "Video chưa đăng", raw_vpath),

                ]

                for cand in candidate_paths:

                    if os.path.exists(cand):

                        target_dir = cand if os.path.isdir(cand) else os.path.dirname(cand)

                        break

                if not target_dir:

                    base_cand = os.path.join(brand_dir, raw_vpath)

                    target_dir = base_cand if os.path.isdir(base_cand) else os.path.dirname(base_cand)



        if target_dir:

            os.makedirs(target_dir, exist_ok=True)

        else:

            # Fallback nếu chưa có đường dẫn video: lưu vào thư mục Link gốc

            brand_dir = os.path.join(AFFILIATE_ROOT, folder_name)

            link_goc_base = os.path.join(brand_dir, "Link gốc")

            os.makedirs(link_goc_base, exist_ok=True)



            sub_folder = ""

            if sub2_prefix:

                sub_folder = sub2_prefix

            else:

                first_name = extract_product_name_from_url(clean_links[0])

                if first_name:

                    sub_folder = first_name[:25].strip()



            if not sub_folder:

                sub_folder = datetime.now().strftime("%Y%m%d_%H%M%S")



            sub_folder_clean = re.sub(r'[\\/*?:"<>|]', '_', sub_folder).strip()

            target_dir = os.path.join(link_goc_base, sub_folder_clean)

            os.makedirs(target_dir, exist_ok=True)



        target_filepath = os.path.join(target_dir, "Batch Custom Links.xlsx")

        wb.save(target_filepath)



        # Tự động lưu link gốc vào file danh sách tổng hợp (dạng Chưa có link rút gọn)

        try:

            import sys

            if r"C:\Affiliate" not in sys.path: sys.path.append(r"C:\Affiliate")

            from link_tracker_sync import record_pasted_origin_links

            record_pasted_origin_links(folder_name, clean_links)

        except Exception as _e_sync:

            print(f"⚠️ Lỗi lưu link gốc vào file danh sách: {_e_sync}")



        import urllib.parse

        encoded_path = urllib.parse.quote(target_filepath)

        download_url = f"/api/download_batch_custom_links?path={encoded_path}"



        return jsonify({

            "success": True,

            "message": f"Đã tạo file Batch Custom Links thành công ({len(clean_links)} link × 7 nền tảng = {total_rows} dòng)!",

            "file_path": target_filepath,

            "file_name": "Batch Custom Links.xlsx",

            "rows_count": total_rows,

            "links_count": len(clean_links),

            "download_url": download_url

        })

    except Exception as e:

        print(f"❌ Lỗi tạo file Batch Custom Links: {e}", flush=True)

        return jsonify({"success": False, "message": f"Lỗi tạo file Excel: {str(e)}"}), 500



@app.route("/api/download_batch_custom_links", methods=["GET"])

def download_batch_custom_links():

    """Tải trực tiếp file Batch Custom Links.xlsx về máy tính qua trình duyệt"""

    try:

        path = request.args.get("path", "").strip()

        if not path or not os.path.exists(path):

            return jsonify({"success": False, "message": "Không tìm thấy file"}), 404

        abs_path = os.path.abspath(path)

        return send_file(abs_path, as_attachment=True, download_name="Batch Custom Links.xlsx")

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500





@app.route("/api/load_folder_link_file", methods=["POST"])

def load_folder_link_file():

    """

    Quét và tự động nạp file link CSV/Excel trong chính folder chứa video (ví dụ AffiliateBatchCustomLinks*.csv/xlsx).

    Trích xuất:

    - Danh sách các link custom đã chuyển đổi theo từng nền tảng (cột 'Liên kết chuyển đổi' / cột 7).

    - Tên sản phẩm, Sub_id1, Sub_id2.

    - Đường dẫn file gốc trên đĩa.

    """

    try:

        data = request.get_json(silent=True) or request.json or {}

        brand_key = (data.get("brand_key") or "").strip()

        video_path = (data.get("video_path") or "").strip()



        if not video_path:

            return jsonify({"success": False, "found": False, "message": "Vui lòng chọn hoặc nhập đường dẫn video trước!"}), 400



        brands = load_brands()

        b_data = brands.get(brand_key, {})

        folder_name = b_data.get("folder", brand_key)



        # 1. Xác định folder chứa video

        raw_vpath = video_path.strip().strip('"').strip("'")

        target_dir = ""

        if os.path.isabs(raw_vpath):

            target_dir = raw_vpath if os.path.isdir(raw_vpath) else os.path.dirname(raw_vpath)

        else:

            brand_dir = os.path.join(AFFILIATE_ROOT, folder_name)

            candidate_paths = [

                os.path.join(brand_dir, raw_vpath),

                os.path.join(brand_dir, "Video_việt_hóa", "Video chưa đăng", raw_vpath),

                os.path.join(brand_dir, "video_việt_hóa", "video chua dang", raw_vpath),

                os.path.join(brand_dir, "Video chưa đăng", raw_vpath),

            ]

            for cand in candidate_paths:

                if os.path.exists(cand):

                    target_dir = cand if os.path.isdir(cand) else os.path.dirname(cand)

                    break

            if not target_dir:

                base_cand = os.path.join(brand_dir, raw_vpath)

                target_dir = base_cand if os.path.isdir(base_cand) else os.path.dirname(base_cand)



        if not target_dir or not os.path.exists(target_dir):

            return jsonify({"success": False, "found": False, "message": f"Thư mục video không tồn tại: {target_dir}"}), 404



        # 2. Tìm file CSV/Excel link trong folder video

        candidates = []

        try:

            for fname in os.listdir(target_dir):

                fl = fname.lower()

                if fl.startswith("~$") or fl.startswith("batch custom links") or "batch custom links" in fl:

                    continue

                if fl.endswith(".csv") or fl.endswith(".xlsx") or fl.endswith(".xls"):

                    fp = os.path.join(target_dir, fname)

                    mtime = os.path.getmtime(fp)

                    priority = 2 if "affiliatebatchcustomlinks" in fl else 1

                    candidates.append((priority, mtime, fp, fname))

        except Exception as e:

            return jsonify({"success": False, "found": False, "message": f"Không thể đọc thư mục {target_dir}: {str(e)}"}), 500



        # Nếu không có trong chính folder, thử quét thư mục cha

        if not candidates:

            parent_dir = os.path.dirname(target_dir)

            if parent_dir and os.path.exists(parent_dir) and parent_dir != AFFILIATE_ROOT:

                for fname in os.listdir(parent_dir):

                    fl = fname.lower()

                    if fl.startswith("~$") or "batch custom links" in fl:

                        continue

                    if fl.endswith(".csv") or fl.endswith(".xlsx"):

                        fp = os.path.join(parent_dir, fname)

                        mtime = os.path.getmtime(fp)

                        priority = 2 if "affiliatebatchcustomlinks" in fl else 1

                        candidates.append((priority, mtime, fp, fname))



        if not candidates:

            return jsonify({

                "success": False,

                "found": False,

                "folder": target_dir,

                "message": f"Không tìm thấy file kết quả CSV/Excel trong folder: {target_dir}"

            }), 404



        # Sắp xếp ưu tiên: AffiliateBatchCustomLinks > mtime mới nhất

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

        best_priority, best_mtime, best_path, best_name = candidates[0]



        # 3. Parse nội dung file

        products = parse_link_file(best_path)

        if not products:

            return jsonify({

                "success": False,

                "found": True,

                "file_path": best_path,

                "file_name": best_name,

                "message": f"File {best_name} không chứa link affiliate hợp lệ hoặc rỗng."

            }), 400



        # Định dạng dòng kèm prefix nền tảng

        tag_lines = []

        for p in products:

            plat = p.get("platform") or ""

            link = p.get("link") or ""

            if plat and link:

                tag_lines.append(f"{plat}: {link}")

            elif link:

                tag_lines.append(link)



        return jsonify({

            "success": True,

            "found": True,

            "file_path": best_path,

            "file_name": best_name,

            "folder": target_dir,

            "count": len(products),

            "products": products,

            "tag_lines": tag_lines,

            "message": f"Đã tìm thấy file {best_name} ({len(products)} link chuyển đổi) trong folder video!"

        })

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi nạp file link: {str(e)}"}), 500





@app.route("/api/generate_master_batch_custom_links", methods=["POST"])

def generate_master_batch_custom_links():

    """

    Gom toàn bộ link sản phẩm gốc của TẤT CẢ các kênh có nhập liệu

    và xuất ra 1 FILE MASTER DUY NHẤT: Master_Batch_Custom_Links.xlsx.

    Cấu trúc: 6 cột chuẩn Shopee (Liên kết gốc, Sub_id1, Sub_id2, Sub_id3, Sub_id4, Sub_id5).

    Mỗi link gốc nhân thành 7 dòng cho 7 nền tảng.

    Sub_id3 lưu mã định danh của kênh (ví dụ: noithatdungthat, reviewthatt, ...).

    Sub_id2 lưu định danh thư mục video / sản phẩm.

    """

    try:

        data = request.get_json(silent=True) or request.json or {}

        channels_input = data.get("channels") or []



        if not channels_input:

            return jsonify({"success": False, "message": "Không có kênh nào có link gốc để gom!"}), 400



        brands = load_brands()

        wb = openpyxl.Workbook()

        ws = wb.active

        ws.title = "Sheet1"



        headers = ["Liên kết gốc", "Sub_id1", "Sub_id2", "Sub_id3", "Sub_id4", "Sub_id5"]

        ws.append(headers)



        import datetime

        now_str = datetime.datetime.now().strftime("%Y%m%d%H%M")

        master_map = {

            "timestamp": now_str,

            "created_at": datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y"),

            "channels": {}

        }



        total_rows = 0

        total_links = 0

        channels_processed = []



        for ch in channels_input:

            bkey = (ch.get("brand_key") or "").strip()

            raw_links = ch.get("links") or []

            vpath = (ch.get("video_path") or "").strip()



            clean_links = []

            for l in raw_links:

                if isinstance(l, str):

                    l_str = l.strip()

                    if l_str.startswith("http://") or l_str.startswith("https://"):

                        if l_str not in clean_links:

                            clean_links.append(l_str)



            if not clean_links:

                continue



            b_cfg = brands.get(bkey, {})

            bname = b_cfg.get("name", bkey)

            folder_name = b_cfg.get("folder", bkey)

            sub_id3_val = get_brand_sub_id3(bkey)

            brand_base = resolve_brand_folder_path(b_cfg) or os.path.join(AFFILIATE_ROOT, folder_name)



            # Xác định folder video

            video_dir = ""

            folder_slug = ""

            if vpath:

                raw_vp = vpath.strip().strip('"').strip("'")

                if os.path.isabs(raw_vp):

                    video_dir = raw_vp if os.path.isdir(raw_vp) else os.path.dirname(raw_vp)

                else:

                    video_dir = os.path.join(brand_base, raw_vp)

                    if not os.path.exists(video_dir):

                        video_dir = os.path.dirname(video_dir)



                if video_dir and os.path.exists(video_dir):

                    base_folder = os.path.basename(video_dir)

                    parent_base = os.path.basename(os.path.dirname(video_dir))

                    # Ghép parent_base + base_folder nếu ngắn (ví dụ dot4_9)

                    combined = f"{parent_base}_{base_folder}" if parent_base and parent_base not in [folder_name, "Video chưa đăng"] else base_folder

                    folder_slug = re.sub(r'[^a-zA-Z0-9]', '', remove_accents_str(combined).lower())



            if not folder_slug:

                folder_slug = "sp"



            for idx, link_goc in enumerate(clean_links, 1):

                total_links += 1

                sub2 = make_sub_id2(link_goc, idx, video_name=folder_slug[:12])

                for plat in BATCH_CUSTOM_PLATFORMS:

                    ws.append([link_goc, plat, sub2, sub_id3_val, "video", "organic"])

                    total_rows += 1



            channels_processed.append({

                "brand_key": bkey,

                "brand_name": bname,

                "links_count": len(clean_links),

                "folder_path": video_dir,

                "sub_id3": sub_id3_val

            })



            master_map["channels"][bkey] = {

                "brand_key": bkey,

                "brand_name": bname,

                "sub_id3": sub_id3_val,

                "video_path": vpath,

                "folder_path": video_dir,

                "links": clean_links

            }



        if total_rows == 0:

            return jsonify({"success": False, "message": "Không tìm thấy link gốc hợp lệ nào để tạo file Master!"}), 400



        # 1. Tự động tạo folder đợt tiếp theo trong "C:\Affiliate\Tổng hợp Link Affiliate"

        tong_hop_base = os.path.join(AFFILIATE_ROOT, "Tổng hợp Link Affiliate")

        os.makedirs(tong_hop_base, exist_ok=True)



        existing_dirs = [d for d in os.listdir(tong_hop_base) if os.path.isdir(os.path.join(tong_hop_base, d))]

        max_idx = 0

        for d in existing_dirs:

            m = re.search(r'(?:Batch|Đợt)\s*(\d+)', d, re.IGNORECASE)

            if m:

                try:

                    max_idx = max(max_idx, int(m.group(1)))

                except Exception:

                    pass

        next_idx = (max_idx + 1) if max_idx > 0 else (len(existing_dirs) + 1)

        from datetime import datetime as _dt

        today_str = _dt.now().strftime("%Y-%m-%d")

        now_str = _dt.now().strftime("%Y%m%d_%H%M%S")

        batch_folder_name = f"Batch {next_idx} - {today_str}"

        batch_dir = os.path.join(tong_hop_base, batch_folder_name)

        os.makedirs(batch_dir, exist_ok=True)



        # Lưu file Master_Batch_Custom_Links.xlsx vào folder Batch tiếp theo này

        batch_master_path = os.path.join(batch_dir, "Master_Batch_Custom_Links.xlsx")

        wb.save(batch_master_path)



        # Lưu thêm 1 bản tại gốc C:\Affiliate để tải về nhanh

        master_file_name = "Master_Batch_Custom_Links.xlsx"

        master_filepath = os.path.join(AFFILIATE_ROOT, master_file_name)

        wb.save(master_filepath)



        # Lưu thông tin batch folder vào master_map

        master_map["batch_folder"] = batch_dir

        master_map["batch_folder_name"] = batch_folder_name

        master_map["batch_index"] = next_idx



        # Lưu master map để khi người dùng upload file kết quả thì tự động lưu file CSV vào cùng folder Batch này

        data_dir = os.path.join(BASE_DIR, "data")

        try:

            os.makedirs(data_dir, exist_ok=True)

            map_file = os.path.join(data_dir, "batch_master_map.json")

            with open(map_file, "w", encoding="utf-8") as f:

                json.dump(master_map, f, ensure_ascii=False, indent=2)

        except Exception as _e_map:

            print(f"⚠️ Không thể lưu batch_master_map.json: {_e_map}")



        # Lưu thêm 1 bản backup theo timestamp trong data/

        try:

            backup_name = f"Master_Batch_Custom_Links_{now_str}.xlsx"

            backup_path = os.path.join(data_dir, backup_name)

            wb.save(backup_path)

        except Exception:

            pass



        import urllib.parse

        encoded_path = urllib.parse.quote(master_filepath)

        download_url = f"/api/download_batch_custom_links?path={encoded_path}"



        # Tự động lưu link gốc vào file danh sách tổng hợp từng kênh

        try:

            import sys

            if r"C:\Affiliate" not in sys.path: sys.path.append(r"C:\Affiliate")

            from link_tracker_sync import record_pasted_origin_links

            for ch in channels_processed:

                bkey = ch.get("brand_key")

                ch_links = master_map.get("channels", {}).get(bkey, {}).get("links", [])

                if ch_links:

                    record_pasted_origin_links(bkey, ch_links)

        except Exception as _e_sync:

            print(f"⚠️ Lỗi lưu link gốc master vào file danh sách: {_e_sync}")



        return jsonify({

            "success": True,

            "message": f"Đã gom và tạo thành công file Master cho {len(channels_processed)} kênh ({total_links} link gốc × 7 nền tảng = {total_rows} dòng)! Đã tạo folder: {batch_folder_name}",

            "file_path": master_filepath,

            "file_name": master_file_name,

            "batch_folder": batch_dir,

            "batch_folder_name": batch_folder_name,

            "download_url": download_url,

            "channels_count": len(channels_processed),

            "links_count": total_links,

            "rows_count": total_rows,

            "channels": channels_processed

        })

    except Exception as e:

        print(f"❌ Lỗi tạo file Master Batch Custom Links: {e}", flush=True)

        return jsonify({"success": False, "message": f"Lỗi tạo file Master: {str(e)}"}), 500





@app.route("/api/distribute_master_custom_links", methods=["POST"])

def distribute_master_custom_links():

    """

    Nhận 1 file CSV/Excel kết quả tổng từ Shopee Affiliate (AffiliateBatchCustomLinks*.csv),

    tự động phân loại các dòng theo kênh (Sub_id3) và thư mục video (Sub_id2),

    sau đó tự động tách và lưu file AffiliateBatchCustomLinks.csv con vào đúng từng folder video của kênh,

    đồng thời trả về danh sách link custom để giao diện tự cập nhật thẻ tags và preview.

    """

    try:

        import csv as _csv

        brands = load_brands()

        raw_rows = []

        filename = ""



        # 1. Nhận file upload hoặc đường dẫn

        if "file" in request.files:

            uploaded_file = request.files["file"]

            filename = uploaded_file.filename

            data_dir = os.path.join(BASE_DIR, "data")

            os.makedirs(data_dir, exist_ok=True)

            temp_path = os.path.join(data_dir, f"temp_master_{int(time.time())}_{filename}")

            uploaded_file.save(temp_path)

            raw_filepath = temp_path

        else:

            data = request.get_json(silent=True) or request.form or {}

            raw_filepath = (data.get("file_path") or "").strip()

            filename = os.path.basename(raw_filepath) if raw_filepath else ""



        if not raw_filepath or not os.path.exists(raw_filepath):

            return jsonify({"success": False, "message": "Vui lòng chọn hoặc tải lên file CSV/Excel kết quả từ Shopee!"}), 400



        # Lấy state kênh từ frontend (nếu có) để biết chính xác video_path hiện tại của kênh

        channels_state = {}

        if request.is_json:

            channels_state = (request.json or {}).get("channels_state") or {}

        elif "channels_state" in request.form:

            try:

                channels_state = json.loads(request.form["channels_state"])

            except Exception:

                pass



        # Đọc map đã lưu từ lần tạo master gần nhất

        master_map = {}

        try:

            map_file = os.path.join(BASE_DIR, "data", "batch_master_map.json")

            if os.path.exists(map_file):

                with open(map_file, "r", encoding="utf-8") as f:

                    master_map = json.load(f)

        except Exception:

            pass



        # 2. Đọc nội dung file CSV/Excel

        fl_lower = raw_filepath.lower()

        if fl_lower.endswith(".xlsx") or fl_lower.endswith(".xls"):

            wb = openpyxl.load_workbook(raw_filepath, data_only=True)

            sheet = wb.active

            for r in sheet.iter_rows(values_only=True):

                if any(r):

                    raw_rows.append([str(c or "").strip() for c in r])

        else:

            encodings = ["utf-8-sig", "utf-8", "cp1258", "latin1"]

            for enc in encodings:

                try:

                    with open(raw_filepath, "r", encoding=enc, errors="replace") as f:

                        reader = _csv.reader(f)

                        for r in reader:

                            if any(r):

                                raw_rows.append([str(c or "").strip() for c in r])

                    if raw_rows:

                        break

                except Exception:

                    continue



        if not raw_rows:

            return jsonify({"success": False, "message": "File tải lên không có dữ liệu!"}), 400



        # 3. Phân tích Header

        header = [c.lower() for c in raw_rows[0]]

        goc_col, sub1_col, sub2_col, sub3_col = 0, 1, 2, 3

        sub4_col, sub5_col = 4, 5

        custom_col = None



        for idx, h in enumerate(header):

            if any(k in h for k in ["liên kết gốc", "lien ket goc", "link gốc"]):

                goc_col = idx

            elif any(k in h for k in ["sub_id1", "sub1", "nền tảng"]):

                sub1_col = idx

            elif any(k in h for k in ["sub_id2", "sub2"]):

                sub2_col = idx

            elif any(k in h for k in ["sub_id3", "sub3"]):

                sub3_col = idx

            elif any(k in h for k in ["chuyển đổi", "chuyen doi", "short", "rút gọn"]):

                custom_col = idx



        # Nếu không có header 'chuyển đổi', tìm cột chứa s.shopee.vn

        if custom_col is None:

            for r in raw_rows[1:10]:

                for idx, c in enumerate(r):

                    if "s.shopee.vn" in c or "shp.ee" in c:

                        custom_col = idx

                        break

                if custom_col is not None:

                    break



        if custom_col is None:

            custom_col = len(header) - 2 if len(header) >= 8 else 6



        # 4. Gom nhóm các dòng theo kênh (Sub_id3)

        grouped_by_channel = {}  # { brand_key: [row, ...] }

        for r in raw_rows[1:]:

            if not any(r):

                continue

            sub3_val = r[sub3_col] if len(r) > sub3_col else ""

            bkey = get_brand_key_from_sub_id3(sub3_val)

            if not bkey:

                # Thử tìm trực tiếp

                for bk in brands:

                    if bk in sub3_val.lower() or sub3_val.lower() in bk:

                        bkey = bk

                        break

            if not bkey:

                # Nếu không tìm thấy, thử tra trong master_map

                for bk, ch_info in master_map.get("channels", {}).items():

                    if ch_info.get("sub_id3", "").lower() == sub3_val.lower():

                        bkey = bk

                        break



            if not bkey:

                continue



            if bkey not in grouped_by_channel:

                grouped_by_channel[bkey] = []

            grouped_by_channel[bkey].append(r)



        if not grouped_by_channel:

            return jsonify({

                "success": False,

                "message": "Không tìm thấy mã kênh (Sub_id3) nào khớp với 10 kênh trong hệ thống! Vui lòng đảm bảo file được tạo từ nút Tạo File Master."

            }), 400



        # 5. Phân bổ và lưu file CSV con vào từng thư mục video tương ứng

        from datetime import datetime as _dt

        timestamp_str = _dt.now().strftime("%Y%m%d%H%M")

        distributed_channels = []

        total_custom_links = 0



        for bkey, rows in grouped_by_channel.items():

            b_cfg = brands.get(bkey, {})

            bname = b_cfg.get("name", bkey)

            folder_name = b_cfg.get("folder", bkey)

            brand_base = resolve_brand_folder_path(b_cfg) or os.path.join(AFFILIATE_ROOT, folder_name)



            # Xác định folder đích

            target_folder = ""

            # Ưu tiên 1: Video path đang được chọn trên giao diện

            active_vp = channels_state.get(bkey, {}).get("video_path", "").strip()

            if active_vp:

                raw_avp = active_vp.strip('"').strip("'")

                if os.path.isabs(raw_avp):

                    target_folder = raw_avp if os.path.isdir(raw_avp) else os.path.dirname(raw_avp)

                else:

                    cand = os.path.join(brand_base, raw_avp)

                    target_folder = cand if os.path.isdir(cand) else os.path.dirname(cand)



            # Ưu tiên 2: Tra từ master_map

            if (not target_folder or not os.path.exists(target_folder)) and bkey in master_map.get("channels", {}):

                mapped_folder = master_map["channels"][bkey].get("folder_path")

                if mapped_folder and os.path.exists(mapped_folder):

                    target_folder = mapped_folder



            # Ưu tiên 3: Quét thư mục video chưa đăng mới nhất của kênh

            if not target_folder or not os.path.exists(target_folder):

                cand_vdirs = [

                    os.path.join(brand_base, "Video_việt_hóa", "Video chưa đăng"),

                    os.path.join(brand_base, "Video chưa đăng"),

                    brand_base

                ]

                for cv in cand_vdirs:

                    if os.path.exists(cv):

                        subdirs = [os.path.join(cv, d) for d in os.listdir(cv) if os.path.isdir(os.path.join(cv, d))]

                        if subdirs:

                            subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)

                            target_folder = subdirs[0]

                            break

                        else:

                            target_folder = cv

                            break



            if not target_folder or not os.path.exists(target_folder):

                target_folder = os.path.join(brand_base, "Link gốc")

                os.makedirs(target_folder, exist_ok=True)



            # Lưu file AffiliateBatchCustomLinks.csv duy nhất vào folder đích (gọn gàng, không tạo file timestamp thừa)

            target_csv_path = os.path.join(target_folder, "AffiliateBatchCustomLinks.csv")

            csv_header = ["Liên kết gốc", "Sub_id1", "Sub_id2", "Sub_id3", "Sub_id4", "Sub_id5", "Liên kết chuyển đổi", "Lí do thất bại"]



            try:

                with open(target_csv_path, "w", newline="", encoding="utf-8-sig") as f:

                    writer = _csv.writer(f)

                    writer.writerow(csv_header)

                    for r in rows:

                        row_goc = r[goc_col] if len(r) > goc_col else ""

                        row_sub1 = r[sub1_col] if len(r) > sub1_col else ""

                        row_sub2 = r[sub2_col] if len(r) > sub2_col else ""

                        row_sub3 = r[sub3_col] if len(r) > sub3_col else ""

                        row_sub4 = r[sub4_col] if len(r) > sub4_col else "video"

                        row_sub5 = r[sub5_col] if len(r) > sub5_col else "organic"

                        row_custom = r[custom_col] if len(r) > custom_col else ""

                        writer.writerow([row_goc, row_sub1, row_sub2, row_sub3, row_sub4, row_sub5, row_custom, ""])

            except Exception as e_write:

                print(f"⚠️ Không thể ghi file {target_csv_path}: {e_write}")



            # Đọc lại bằng parse_link_file để trích xuất products và tag_lines đồng nhất

            products = parse_link_file(target_csv_path)

            tag_lines = []

            for p in products:

                plat = p.get("platform") or ""

                link = p.get("link") or ""

                if plat and link:

                    tag_lines.append(f"{plat}: {link}")

                elif link:

                    tag_lines.append(link)



            total_custom_links += len(products)

            distributed_channels.append({

                "brand_key": bkey,

                "brand_name": bname,

                "folder_path": target_folder,

                "csv_path": target_csv_path,

                "count": len(products),

                "products": products,

                "tag_lines": tag_lines

            })



        # Tự động lưu 1 bản file CSV/XLSX kết quả vào đúng folder Batch trong "Tổng hợp Link Affiliate"

        batch_folder_saved = ""

        try:

            tong_hop_base = os.path.join(AFFILIATE_ROOT, "Tổng hợp Link Affiliate")

            batch_dest_folder = master_map.get("batch_folder")

            if not batch_dest_folder or not os.path.exists(batch_dest_folder):

                if os.path.exists(tong_hop_base):

                    all_subdirs = [os.path.join(tong_hop_base, d) for d in os.listdir(tong_hop_base) if os.path.isdir(os.path.join(tong_hop_base, d))]

                    if all_subdirs:

                        all_subdirs.sort(key=lambda p: os.path.getmtime(p), reverse=True)

                        batch_dest_folder = all_subdirs[0]



            if batch_dest_folder and os.path.exists(batch_dest_folder):

                dest_csv_name = filename or f"AffiliateBatchCustomLinks_{timestamp_str}.csv"

                dest_csv_full = os.path.join(batch_dest_folder, dest_csv_name)

                import shutil

                shutil.copy2(raw_filepath, dest_csv_full)

                batch_folder_saved = batch_dest_folder

                print(f"✅ Đã lưu file kết quả CSV vào folder batch: {dest_csv_full}", flush=True)

        except Exception as _e_save_batch:

            print(f"⚠️ Không thể copy file CSV vào batch folder: {_e_save_batch}", flush=True)



        # Dọn dẹp file temp upload nếu có

        try:

            if "temp_master_" in raw_filepath and os.path.exists(raw_filepath):

                os.remove(raw_filepath)

        except Exception:

            pass



        return jsonify({

            "success": True,

            "total_channels": len(distributed_channels),

            "total_custom_links": total_custom_links,

            "distributed_channels": distributed_channels,

            "batch_folder_saved": batch_folder_saved,

            "message": f"✅ Đã tự động phân bổ thành công {total_custom_links} link custom về đúng {len(distributed_channels)} thư mục video tương ứng!"

        })

    except Exception as e:

        print(f"❌ Lỗi phân bổ file Master Custom Links: {e}", flush=True)

        return jsonify({"success": False, "message": f"Lỗi phân bổ file: {str(e)}"}), 500





@app.route("/api/video/sync-all-yt-thumbnails-to-fb", methods=["POST"])

def sync_all_yt_thumbnails_to_fb_route():

    """

    Đồng bộ HÀNG LOẠT (Batch) Thumbnail từ YouTube sang tất cả các video Facebook được gửi lên.

    Payload: { "items": [ { "brand_key": "...", "fb_video_id": "...", "yt_video_id": "...", "title": "..." }, ... ] }

    """

    try:

        req_data = request.get_json(silent=True) or {}

        items = req_data.get("items", [])

        if not items:

            return jsonify({"success": False, "message": "Danh sách video cần đồng bộ trống!"}), 400



        brands = load_brands()

        results = []

        success_count = 0

        fail_count = 0



        # Chạy đồng bộ lần lượt (hoặc thread pool tối đa 3 worker để tránh spam Meta rate limit)

        from concurrent.futures import ThreadPoolExecutor



        def _sync_one(it):

            b_key = it.get("brand_key", "").strip()

            fb_vid = it.get("fb_video_id", "").strip()

            yt_vid = it.get("yt_video_id", "").strip()

            title = it.get("title", "")

            if not b_key or not fb_vid or not yt_vid:

                return {"fb_video_id": fb_vid, "title": title, "success": False, "message": "Thiếu thông tin"}



            b_cfg = brands.get(b_key)

            if not b_cfg:

                return {"fb_video_id": fb_vid, "title": title, "success": False, "message": f"Không tìm thấy cấu hình {b_key}"}



            res = sync_youtube_thumbnail_to_facebook(brand_cfg=b_cfg, fb_video_id=fb_vid, yt_video_id=yt_vid)

            return {

                "brand_key": b_key,

                "fb_video_id": fb_vid,

                "yt_video_id": yt_vid,

                "title": title,

                "success": res.get("success", False),

                "message": res.get("message", ""),

                "youtube_thumb_url": res.get("youtube_thumb_url", "")

            }



        with ThreadPoolExecutor(max_workers=3) as executor:

            for out in executor.map(_sync_one, items):

                results.append(out)

                if out.get("success"):

                    success_count += 1

                else:

                    fail_count += 1



        return jsonify({

            "success": True,

            "total": len(items),

            "success_count": success_count,

            "fail_count": fail_count,

            "results": results,

            "message": f"Đã hoàn tất đồng bộ {success_count}/{len(items)} thumbnail từ YouTube sang Facebook!"

        })

    except Exception as e:

        return jsonify({"success": False, "message": f"Lỗi đồng bộ hàng loạt: {str(e)}"}), 500





# ─────────────────────────────────────────────────────────────────────────────

# TAB "ĐĂNG BÀI VIẾT" - API ROUTES ĐĂNG BÀI ẢNH ĐA NỀN TẢNG (FB, IG, THREADS, YT)

# ─────────────────────────────────────────────────────────────────────────────



@app.route("/api/article-post/publish", methods=["POST"])

def api_article_post_publish():

    """

    API đăng bài viết (kèm bộ ảnh sản phẩm thực tế) cho 1 kênh:

    - Nhận: brand_key, platforms (mảng), product_name, product_link, caption, schedule_time.

    - Hỗ trợ Đăng Ngay hoặc Đăng Hẹn Giờ.

    """

    try:

        data = request.json or {}

        brand_key = data.get("brand_key")

        if not brand_key:

            return jsonify({"success": False, "message": "Thiếu brand_key"}), 400



        platforms = data.get("platforms", ["facebook", "threads", "instagram", "youtube"])

        product_name = data.get("product_name")

        product_link = data.get("product_link")

        caption = data.get("caption")

        schedule_time = data.get("schedule_time")



        from POST.daily_photo_poster import publish_daily_photo_post

        res = publish_daily_photo_post(

            brand_key=brand_key,

            platforms=platforms,

            product_name_custom=product_name,

            product_link_custom=product_link,

            caption_custom=caption,

            schedule_time=schedule_time

        )

        return jsonify(res)

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": f"Lỗi đăng bài viết: {str(e)}"}), 500





@app.route("/api/article-post/publish-all", methods=["POST"])

def api_article_post_publish_all():

    """

    API Master Bar: Đăng hết lên 10 kênh cho các nền tảng được chọn (Đăng Ngay hoặc Hẹn Giờ).

    """

    try:

        data = request.json or {}

        platforms = data.get("platforms", ["facebook", "threads", "instagram", "youtube"])

        schedule_time = data.get("schedule_time")



        from POST.daily_photo_poster import run_daily_photo_job

        results = run_daily_photo_job(platforms=platforms, schedule_time=schedule_time)

        return jsonify({

            "success": True,

            "message": f"Đã thực hiện đăng bài viết cho {len(results)} kênh!",

            "results": results

        })

    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"success": False, "message": f"Lỗi đăng tất cả bài viết: {str(e)}"}), 500





@app.route("/api/article-post/history", methods=["GET"])

def api_article_post_history():

    """

    Lấy danh sách lịch sử đăng bài viết gần nhất.

    """

    try:

        from POST.daily_photo_poster import load_photo_history

        history = load_photo_history()

        return jsonify({"success": True, "history": history[-30:][::-1]})

    except Exception as e:

        return jsonify({"success": False, "message": str(e), "history": []})





def start_background_analytics_scheduler():

    """

    [ĐÃ TẮT ĐỊNH KỲ ĐỂ BẢO VỆ 100% QUOTA YOUTUBE]

    Dữ liệu thống kê được lưu bền vững trong analytics_cache.json và tự động cập nhật

    mỗi khi bạn đăng video mới (qua inject_task_into_analytics_cache) hoặc khi bạn

    chủ động bấm 'Làm mới số liệu' (Force Refresh) trên giao diện.

    """

    pass



def start_background_queue_scheduler():

    """Luồng worker chạy ngầm tự động quét hàng đợi hẹn giờ (Instagram, Threads,...) từ schedule_queue.json."""

    def _scheduler_loop():

        # Chờ 3 giây để hệ thống ổn định sau khi khởi động

        time.sleep(3)

        print("⏰ [Scheduler Worker] Luồng tự động quét hàng đợi hẹn giờ đã khởi động!")

        try:

            from POST.scheduler import run_scheduled_worker

            run_scheduled_worker()

        except Exception as e_sc:

            print(f"⚠️ Lỗi trong scheduler worker: {e_sc}")



    t_sc = threading.Thread(target=_scheduler_loop, daemon=True)

    t_sc.start()



# TẮT QUÉT THỐNG KÊ NGẦM ĐỊNH KỲ ĐỂ BẢO VỆ 100% QUOTA YOUTUBE (Chỉ quét khi người dùng bấm 'Làm mới số liệu')

# start_background_analytics_scheduler()

start_background_queue_scheduler()





# ─────────────────────────────────────────────────────────────────────────────

# ĐỒNG BỘ LINK GỐC & LINK RÚT GỌN VÀO FILE DANH SÁCH TỔNG HỢP (AFFILIATE)

# ─────────────────────────────────────────────────────────────────────────────



@app.route("/api/record_origin_links", methods=["POST"])

def api_record_origin_links():

    try:

        data = request.json or {}

        brand_key = data.get("brand_key")

        links = data.get("links") or []

        if not brand_key or not links:

            return jsonify({"success": False, "message": "Thiếu dữ liệu"}), 400

        import sys

        if r"C:\Affiliate" not in sys.path: sys.path.append(r"C:\Affiliate")

        from link_tracker_sync import record_pasted_origin_links

        res = record_pasted_origin_links(brand_key, links)

        return jsonify(res)

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/api/sync_published_links", methods=["POST"])

def api_sync_published_links():

    try:

        data = request.json or {}

        brand_key = data.get("brand_key")

        video_path = data.get("video_path")

        excel_path = data.get("excel_path")

        tags = data.get("tags") or []

        products = data.get("products") or []

        if not brand_key:

            return jsonify({"success": False, "message": "Thiếu brand_key"}), 400

        import sys

        if r"C:\Affiliate" not in sys.path: sys.path.append(r"C:\Affiliate")

        from link_tracker_sync import record_published_short_links

        res = record_published_short_links(brand_key, short_links=tags, excel_input=excel_path, video_path=video_path, products_list=products)

        return jsonify(res)

    except Exception as e:

        return jsonify({"success": False, "message": str(e)}), 500





if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--port", type=int, default=5000, help="Port to run server on")

    args = parser.parse_args()



    port = args.port

    templates_dir = os.path.join(BASE_DIR, "templates")

    os.makedirs(templates_dir, exist_ok=True)

    print(f"🚀 Đang khởi động Affiliate Dashboard trên http://localhost:{port} ...")

    print(f"📢 Dashboard hỗ trợ đăng ĐỒNG THỜI cho 10 kênh x 4 nền tảng trên 1 PORT duy nhất!")

    app.run(host="0.0.0.0", port=port, debug=False)





