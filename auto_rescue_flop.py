# -*- coding: utf-8 -*-
"""
HỆ THỐNG TỰ ĐỘNG TỐI ƯU CỨU FLOP VIDEO (YOUTUBE & FACEBOOK)
==========================================================
Chạy độc lập (Standalone / Scheduled Task), tự động quét và tối ưu siêu dữ liệu
(Tiêu đề, Mô tả, Hashtag) cho video YouTube và Facebook sau 24h đăng nếu bị Flop.

Quy tắc:
- Chỉ áp dụng cho YouTube & Facebook.
- Video đã đăng >= 24h và lượt xem < ngưỡng flop (mặc định 200 views).
- Tối đa 3 lần tối ưu cho mỗi video (Lần 1 -> Lần 2 -> Lần 3).
- Mỗi lần tối ưu cách nhau >= 24h.
- Quá 3 lần mà vẫn flop (> 3 ngày) -> Dừng hẳn, không tối ưu nữa.
- Tự động bảo lưu toàn bộ link Affiliate mua hàng trong phần mô tả.
- Chạy xong tự động đóng tiến trình, giải phóng 100% RAM!
"""

import os
import sys
import json
import re
import time
from datetime import datetime, timedelta

# Thiết lập encoding UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thiết lập đường dẫn thư mục
BASE_DIR = r"C:\Affiliate"
POST_DIR = os.path.join(BASE_DIR, "post1", "POST")
sys.path.insert(0, os.path.join(BASE_DIR, "post1"))
sys.path.insert(0, POST_DIR)

CONFIG_DIR = os.path.join(POST_DIR, "config")
BRANDS_FILE = os.path.join(CONFIG_DIR, "brands.json")
OPTIMIZED_VIDEOS_FILE = os.path.join(CONFIG_DIR, "optimized_flop_videos.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "flop_settings.json")
LOG_DIR = os.path.join(BASE_DIR, "post1", "logs")
LOG_FILE = os.path.join(LOG_DIR, "auto_flop_rescue.log")

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def log_message(msg):
    """Ghi log có dấu thời gian ra màn hình và file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"⚠️ Lỗi ghi file log: {e}")


def load_settings():
    """Tải cài đặt cứu flop hoặc tạo mặc định."""
    defaults = {
        "enabled": True,
        "view_threshold": 200,      # View < 200 sau 24h = FLOP
        "min_age_hours": 24,        # Đã đăng ít nhất 24 giờ
        "cooldown_hours": 24,       # Cách lần tối ưu trước ít nhất 24 giờ
        "max_optimizations": 3,     # Tối đa 3 lần
        "platforms": ["youtube", "facebook"],
        "ai_models": ["gemini-flash-lite-latest", "gemini-3-flash-preview", "gemini-flash-latest"]
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception as e:
            log_message(f"⚠️ Lỗi đọc settings, dùng mặc định: {e}")
    else:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(defaults, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return defaults


def get_gemini_api_key():
    """Đọc Gemini API key từ file .env hoặc biến môi trường."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key
    env_paths = [
        os.path.join(BASE_DIR, "post1", ".env"),
        os.path.join(BASE_DIR, ".env")
    ]
    for ep in env_paths:
        if os.path.exists(ep):
            try:
                with open(ep, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return None


def parse_datetime(dt_str):
    """Phân tích chuỗi ngày giờ linh hoạt theo nhiều định dạng."""
    if not dt_str:
        return None
    dt_str = str(dt_str).strip()
    
    # 1. Thử ISO formats (2026-10-23T13:10:55Z, 2026-10-23T12:16:11.069576)
    clean_iso = dt_str.replace("Z", "")
    if "+" in clean_iso:
        clean_iso = clean_iso.split("+")[0]
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M"
    ]:
        try:
            return datetime.strptime(clean_iso, fmt)
        except Exception:
            pass
            
    # 2. Thử định dạng VN (HH:MM DD/MM/YYYY)
    try:
        parts = dt_str.split(" ")
        if len(parts) >= 2:
            time_part = parts[0]
            date_part = parts[1]
            d, m, y = date_part.split("/")
            h, mi = time_part.split(":")[:2]
            return datetime(int(y), int(m), int(d), int(h), int(mi))
    except Exception:
        pass

    return None


def extract_affiliate_links(description):
    """Trích xuất tất cả các liên kết (đặc biệt là link Shopee, Lazada, Affiliate)."""
    if not description:
        return []
    url_pattern = r'https?://[^\s<>"\')]+'
    return re.findall(url_pattern, description)


def generate_flop_metadata_with_ai(api_key, video_info, optimize_round=1, models_to_try=None):
    """
    Sử dụng Gemini AI để tái cấu trúc siêu dữ liệu cứu Flop cho video:
    - Tiêu đề mới (CTR cao, hook mạnh, chuẩn 55-80 ký tự)
    - Mô tả mới (Hook lôi cuốn, bảo lưu link affiliate)
    - 7-8 Hashtag ngách mới
    """
    from google import genai

    if models_to_try is None:
        models_to_try = ["gemini-flash-lite-latest", "gemini-3-flash-preview", "gemini-flash-latest"]

    cur_title = video_info.get("title", "")
    cur_desc = video_info.get("description", "")
    brand_name = video_info.get("brand_name", "")
    platform = video_info.get("platform", "YouTube Shorts")
    views = video_info.get("views", 0)
    likes = video_info.get("likes", 0)
    comments = video_info.get("comments", 0)
    age_hours = int(video_info.get("age_hours", 24))

    # Tìm link affiliate sẵn có
    existing_links = extract_affiliate_links(cur_desc)
    links_text = "\n".join([f"• {link}" for link in existing_links]) if existing_links else "(Không có link cụ thể)"

    # Tùy biến chiến lược theo vòng cứu flop (1, 2, hoặc 3)
    if optimize_round == 1:
        strategy_angle = """• CHIẾN LƯỢC VÒNG 1 (Cứu flop 24h đầu):
  - Khai thác Hook Nghịch lý / Gây tò mò cực độ: 'Tưởng Phí Tiền Hóa Ra Lại Quá Đỉnh...', 'Đừng Mua Nếu Chưa Biết 1 Điều Này...'
  - Đặt lại câu hỏi nhắm thẳng vào sự hoài nghi của người xem."""
    elif optimize_round == 2:
        strategy_angle = """• CHIẾN LƯỢC VÒNG 2 (Cứu flop sau 48h - Vẫn đứng view):
  - Khai thác Hook Cảnh báo / Tránh bẫy / Bóc phốt: 'Ai Đang Dùng Cái Này Thì Bỏ Ngay Đi! ⚠️', 'Sự Thật Đằng Sau...'
  - Sử dụng từ ngữ dứt khoát, tạo cảm giác người xem ĐANG BỎ LỠ điều quan trọng."""
    else:
        strategy_angle = """• CHIẾN LƯỢC VÒNG 3 (Vòng giải cứu cuối cùng sau 72h):
  - Khai thác Hook Giải quyết nỗi đau / Tiết kiệm khẩn cấp: 'Bí Quyết Tránh Mất Tiền Oan Khi Mua...', '3 Lý Do Nên Mua Ngay Trước Khi Hết...'
  - Đưa trực diện lợi ích lớn nhất của sản phẩm lên ngay 3 từ đầu tiên của tiêu đề."""

    prompt = f"""Bạn là Bậc Thầy Tối Ưu Thuật Toán Video Ngắn (YouTube Shorts & Facebook Reels) chuyên giải cứu các video bị FLOP / BỊ BÓP TƯƠNG TÁC / ĐỨNG VIEW sau 24h đăng.

━━━ THÔNG TIN VIDEO CẦN CỨU FLOP (LẦN {optimize_round}/3) ━━━
• Tiêu đề hiện tại : {cur_title if cur_title else '(chưa có)'}
• Mô tả hiện tại   : {cur_desc[:400] if cur_desc else '(chưa có)'}
• Kênh sở hữu      : {brand_name if brand_name else '(kênh affiliate)'}
• Nền tảng         : {platform}
• Thời gian đã đăng: {age_hours} giờ
• Chỉ số hiện tại  : {views} views, {likes} likes, {comments} bình luận (Flop nặng)
• Danh sách link affiliate từ mô tả cũ cần giữ lại:
{links_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{strategy_angle}

YÊU CẦU BẮT BUỘC:
1. TIÊU ĐỀ (Title):
   - Tuyệt đối KHÔNG giữ cách đặt tên cũ khô khan.
   - Chiều dài: 55 - 80 ký tự (chuẩn mobile, không bị che khuất).
   - Thêm 1 hashtag ngắn gọn về sản phẩm + #Shorts (nếu YouTube) hoặc #Reels (nếu Facebook).

2. MÔ TẢ (Description):
   - 1-2 câu đầu: Hook tạo tranh cãi hoặc đồng cảm sâu sắc.
   - 2-3 câu tiếp theo: Nêu giải pháp và công năng nổi bật nhất.
   - Lời kêu gọi hành động (CTA) rõ ràng: 'Link chi tiết và ưu đãi mình để sẵn dưới bình luận/bio nhé! 👇'
   - NẾU CÓ LINK AFFILIATE TRONG MÔ TẢ CŨ: BẮT BUỘC BẢO LƯU ĐẦY ĐỦ CÁC ĐƯỜNG LINK ĐÓ TRONG MÔ TẢ MỚI.
   - 3-5 hashtag đuôi.

3. HASHTAGS:
   - 7-8 tags ngách có tính chuyển đổi cao, tránh các tag quá bão hòa (như #viral, #trending).

4. GIẢI THÍCH CHIẾN LƯỢC (strategy_reason):
   - 1 câu ngắn giải thích vì sao tiêu đề và cách tiếp cận này sẽ giúp kích hoạt lại thuật toán phân phối.

Trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm markdown ```json, không thêm chữ thừa):
{{
  "title": "...",
  "description": "...",
  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "strategy_reason": "..."
}}"""

    client = genai.Client(api_key=api_key)
    result_text = None
    last_err = None

    for m in models_to_try:
        try:
            resp = client.models.generate_content(model=m, contents=prompt)
            if resp and (resp.text or "").strip():
                result_text = resp.text.strip()
                break
        except Exception as e:
            last_err = e
            continue

    if not result_text:
        raise RuntimeError(f"Gemini AI không phản hồi (các model đã thử {models_to_try}): {last_err}")

    # Làm sạch chuỗi JSON nếu có markdown
    if result_text.startswith("```"):
        result_text = re.sub(r"^```\w*\n?", "", result_text)
        result_text = re.sub(r"\n?```$", "", result_text.strip())

    try:
        parsed = json.loads(result_text.strip())
    except Exception as je:
        # Thử regex trích xuất JSON
        m_json = re.search(r"\{[\s\S]*\}", result_text)
        if m_json:
            parsed = json.loads(m_json.group(0))
        else:
            raise RuntimeError(f"Không thể phân tích kết quả JSON từ Gemini: {je}")

    # Bảo hiểm an toàn 100%: Nếu mô tả cũ có link affiliate mà Gemini vô tình quên, nối thêm vào cuối
    new_desc = parsed.get("description", "")
    for lk in existing_links:
        if lk not in new_desc:
            new_desc += f"\n\n🛒 Link mua hàng chính hãng:\n👉 {lk}"
    parsed["description"] = new_desc.strip()

    return parsed


def run_auto_flop_rescue():
    """
    Hàm chính thực thi toàn bộ quy trình:
    1. Đọc cấu hình & danh sách kênh
    2. Quét video của YouTube & Facebook
    3. Lọc video thỏa mãn: đã đăng >= 24h, flop (< 200 views), tối ưu < 3 lần, cách lần trước >= 24h
    4. Gọi Gemini AI viết lại tiêu đề, mô tả, hashtag
    5. Cập nhật trực tiếp lên kênh qua API
    6. Lưu log & cập nhật bộ nhớ đệm
    """
    start_time = datetime.now()
    log_message("=" * 65)
    log_message("🚀 BẮT ĐẦU TIẾN TRÌNH TỰ ĐỘNG CỨU FLOP (YOUTUBE & FACEBOOK)")
    log_message(f"⏰ Thời gian bắt đầu: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    settings = load_settings()
    if not settings.get("enabled", True):
        log_message("⏸️ Cứu Flop tự động đang bị TẮT trong file cài đặt (enabled = false). Dừng tiến trình.")
        return

    api_key = get_gemini_api_key()
    if not api_key:
        log_message("❌ KHÔNG TÌM THẤY GEMINI_API_KEY trong file .env! Dừng tiến trình.")
        return

    # Tải brands cấu hình
    if not os.path.exists(BRANDS_FILE):
        log_message(f"❌ Không tìm thấy file brands.json tại: {BRANDS_FILE}")
        return

    try:
        with open(BRANDS_FILE, "r", encoding="utf-8") as f:
            brands = json.load(f)
    except Exception as e:
        log_message(f"❌ Lỗi đọc brands.json: {e}")
        return

    from fetch_analytics import (
        _load_optimized_videos,
        record_video_optimization,
        update_youtube_video,
        update_facebook_video,
        load_cached_analytics,
        fetch_all_channels_data
    )

    opt_cache = _load_optimized_videos()
    view_threshold = int(settings.get("view_threshold", 200))
    min_age_hours = float(settings.get("min_age_hours", 24))
    max_age_hours = float(settings.get("max_age_hours", 96))      # Sau 3-4 ngày flop thì dừng
    cooldown_hours = float(settings.get("cooldown_hours", 24))
    max_opts = int(settings.get("max_optimizations", 3))
    batch_size = int(settings.get("batch_size_per_run", 20))

    log_message(f"📋 Tiêu chí lọc:")
    log_message(f"   • Nền tảng: YouTube & Facebook")
    log_message(f"   • Thời gian đã đăng: >= {min_age_hours} giờ và <= {max_age_hours} giờ (cửa sổ 3 ngày)")
    log_message(f"   • Lượt xem flop: < {view_threshold} views")
    log_message(f"   • Số lần tối ưu tối đa: {max_opts} lần (giãn cách >= {cooldown_hours}h giữa các lần)")
    log_message(f"   • Giới hạn xử lý mỗi lượt chạy: Tối đa {batch_size} video")

    # Lấy dữ liệu analytics: Ưu tiên cache gần nhất nếu có, hoặc fetch mới
    log_message("🔍 Đang đọc dữ liệu video từ hệ thống...")
    cached_data = load_cached_analytics()
    raw_data = cached_data.get("data", {}) if isinstance(cached_data, dict) else {}

    # Nếu cache rỗng, tiến hành quét nhanh YouTube và Facebook
    if not raw_data:
        log_message("⚡ Cache rỗng, đang quét trực tiếp YouTube và Facebook từ API...")
        try:
            raw_data = fetch_all_channels_data(brands, limit=30)
        except Exception as e:
            log_message(f"⚠️ Lỗi fetch_all_channels_data: {e}")
            raw_data = {}

    if not raw_data:
        log_message("⚠️ Không có dữ liệu video nào để kiểm tra. Kết thúc.")
        return

    now = datetime.now()
    all_videos_checked = 0
    flop_videos_found = 0
    exhausted_videos = 0
    cooldown_videos = 0
    eligible_videos = []

    # Duyệt qua tất cả các kênh và video
    for b_key, b_val in raw_data.items():
        if not isinstance(b_val, dict):
            continue
        brand_cfg = brands.get(b_key, {})
        brand_name = brand_cfg.get("name", b_val.get("name", b_key))
        platforms = b_val.get("platforms", {})

        for p_key in ["youtube", "facebook"]:
            p_val = platforms.get(p_key)
            if not isinstance(p_val, dict):
                continue
            videos = p_val.get("videos", [])

            for vid in videos:
                if not isinstance(vid, dict):
                    continue
                v_id = str(vid.get("id", "")).strip()
                if not v_id:
                    continue

                all_videos_checked += 1
                views = int(vid.get("views", 0) or 0)
                pub_raw = vid.get("published_at_raw") or vid.get("published_at")
                pub_dt = parse_datetime(pub_raw)

                if not pub_dt:
                    continue

                age_hours = (now - pub_dt).total_seconds() / 3600.0

                # Điều kiện 1: Đã đăng đủ 24 giờ
                if age_hours < min_age_hours:
                    continue

                # Điều kiện 1b: Quá 3-4 ngày mà vẫn flop -> Dừng hẳn (không tối ưu nữa)
                if age_hours > max_age_hours:
                    exhausted_videos += 1
                    continue

                # Điều kiện 2: Bị Flop (< view_threshold)
                if views >= view_threshold:
                    continue

                flop_videos_found += 1

                # Kiểm tra lịch sử tối ưu của video này
                opt_rec = opt_cache.get(v_id, {})
                cur_count = int(opt_rec.get("optimize_count", 0))

                # Điều kiện 3: Kiểm tra đã đạt tối đa 3 lần chưa
                if cur_count >= max_opts:
                    exhausted_videos += 1
                    continue

                # Điều kiện 4: Kiểm tra cooldown 24h giữa các lần tối ưu
                if cur_count > 0:
                    last_opt_str = opt_rec.get("last_optimized_at")
                    last_opt_dt = parse_datetime(last_opt_str)
                    if last_opt_dt:
                        hours_since_last = (now - last_opt_dt).total_seconds() / 3600.0
                        if hours_since_last < cooldown_hours:
                            cooldown_videos += 1
                            continue

                # Video thỏa mãn toàn bộ điều kiện -> Đưa vào danh sách giải cứu
                next_round = cur_count + 1
                eligible_videos.append({
                    "brand_key": b_key,
                    "brand_cfg": brand_cfg,
                    "brand_name": brand_name,
                    "platform": p_key,
                    "video_id": v_id,
                    "title": vid.get("title", ""),
                    "description": vid.get("description", ""),
                    "views": views,
                    "likes": vid.get("likes", 0),
                    "comments": vid.get("comments", 0),
                    "age_hours": age_hours,
                    "optimize_round": next_round,
                    "cur_count": cur_count
                })

    # Sắp xếp ưu tiên các video mới nhất (gần mốc 24h/48h/72h nhất)
    eligible_videos.sort(key=lambda x: x["age_hours"])
    total_eligible = len(eligible_videos)
    if total_eligible > batch_size:
        eligible_videos = eligible_videos[:batch_size]

    log_message("-" * 65)
    log_message(f"📊 BÁO CÁO TỔNG QUAN:")
    log_message(f"   • Tổng số video quét: {all_videos_checked}")
    log_message(f"   • Số video bị Flop (sau 24h, view < {view_threshold}): {flop_videos_found}")
    log_message(f"   • Video quá 3 ngày flop hoặc đã tối ưu 3 lần (Dừng hẳn): {exhausted_videos}")
    log_message(f"   • Video đang trong thời gian chờ (chưa đủ 24h kể từ lần sửa trước): {cooldown_videos}")
    log_message(f"   • Video ĐỦ ĐIỀU KIỆN TỐI ƯU: {total_eligible} (Xử lý đợt này: {len(eligible_videos)})")
    log_message("-" * 65)

    if not eligible_videos:
        log_message("✅ Không có video nào cần cứu flop tại thời điểm này. Hệ thống sẽ quét lại ở lần chạy sau.")
        log_message("=" * 65)
        return

    # Tiến hành tối ưu lần lượt từng video
    success_count = 0
    fail_count = 0

    for idx, item in enumerate(eligible_videos, 1):
        v_id = item["video_id"]
        plat = item["platform"]
        b_name = item["brand_name"]
        b_key = item["brand_key"]
        round_num = item["optimize_round"]
        old_title = item["title"]

        log_message(f"\n[{idx}/{len(eligible_videos)}] 🎯 Đang cứu flop cho video: {v_id} ({plat.upper()} - Kênh: {b_name})")
        log_message(f"   • Lần tối ưu: Lần {round_num}/{max_opts}")
        log_message(f"   • Đã đăng: {item['age_hours']:.1f} giờ | Views hiện tại: {item['views']}")
        log_message(f"   • Tiêu đề cũ: {old_title[:65]}...")

        # 1. Gọi Gemini AI sinh siêu dữ liệu mới
        try:
            log_message(f"   🧠 Đang gọi Gemini AI phân tích và viết lại Tiêu đề, Mô tả, Hashtag...")
            ai_meta = generate_flop_metadata_with_ai(
                api_key=api_key,
                video_info=item,
                optimize_round=round_num,
                models_to_try=settings.get("ai_models")
            )
            new_title = (ai_meta.get("title") or "").strip()
            new_desc = (ai_meta.get("description") or "").strip()
            strategy = (ai_meta.get("strategy_reason") or "").strip()

            log_message(f"   ✨ Tiêu đề AI mới: {new_title}")
            log_message(f"   💡 Chiến lược AI : {strategy}")

            if not new_title:
                log_message(f"   ⚠️ Gemini không trả về tiêu đề mới hợp lệ. Bỏ qua video này.")
                fail_count += 1
                continue

        except Exception as e_ai:
            log_message(f"   ❌ Lỗi khi gọi Gemini AI: {e_ai}")
            fail_count += 1
            continue

        # 2. Cập nhật trực tiếp lên kênh qua API tương ứng
        update_res = None
        try:
            if plat == "youtube":
                log_message(f"   📤 Đang gửi cập nhật lên YouTube qua YouTube Data API v3...")
                update_res = update_youtube_video(
                    brand_cfg=item["brand_cfg"],
                    video_id=v_id,
                    title=new_title,
                    description=new_desc
                )
            elif plat == "facebook":
                log_message(f"   📤 Đang gửi cập nhật lên Facebook qua Facebook Graph API...")
                update_res = update_facebook_video(
                    brand_cfg=item["brand_cfg"],
                    video_id=v_id,
                    title=new_title,
                    description=new_desc
                )
        except Exception as e_up:
            log_message(f"   ❌ Ngoại lệ khi gọi API cập nhật {plat}: {e_up}")
            fail_count += 1
            continue

        # 3. Kiểm tra kết quả cập nhật
        if isinstance(update_res, dict) and update_res.get("success"):
            log_message(f"   🎉 CẬP NHẬT THÀNH CÔNG lên {plat.upper()}!")

            # 4. Ghi nhận số lần tối ưu vào cơ sở dữ liệu
            try:
                new_opt_count = record_video_optimization(
                    platform=plat,
                    brand_key=b_key,
                    video_id=v_id,
                    new_title=new_title,
                    new_desc=new_desc,
                    strategy_reason=strategy
                )
                log_message(f"   📝 Đã ghi nhận: Video hiện đã tối ưu {new_opt_count}/{max_opts} lần.")
                if new_opt_count >= max_opts:
                    log_message(f"   🛑 Video này đã đạt tối đa {max_opts} lần tối ưu. Từ lần sau sẽ dừng hẳn.")
            except Exception as e_rec:
                log_message(f"   ⚠️ Lỗi ghi record_video_optimization: {e_rec}")

            success_count += 1
        else:
            err_msg = update_res.get("message", "Lỗi không xác định") if isinstance(update_res, dict) else str(update_res)
            log_message(f"   ❌ Cập nhật thất bại lên {plat.upper()}: {err_msg}")
            fail_count += 1

        # Nghỉ an toàn 5 giây giữa các video để không bị rate limit
        if idx < len(eligible_videos):
            time.sleep(5)

    duration = (datetime.now() - start_time).total_seconds()
    log_message("-" * 65)
    log_message(f"🏁 KẾT THÚC TIẾN TRÌNH CỨU FLOP!")
    log_message(f"   • Thành công: {success_count} video")
    log_message(f"   • Thất bại  : {fail_count} video")
    log_message(f"   • Thời gian thực thi: {duration:.1f} giây")
    log_message("=" * 65 + "\n")


if __name__ == "__main__":
    try:
        run_auto_flop_rescue()
    except Exception as e_main:
        log_message(f"💥 LỖI CHÍNH TOÀN CỤC: {e_main}")
        import traceback
        log_message(traceback.format_exc())
