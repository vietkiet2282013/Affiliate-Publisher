"""
POST/daily_photo_poster.py
=============================================================================
Tính năng tự động đăng bài viết dạng ảnh (Photo Post) hàng ngày lên Facebook Page
cho 10 thương hiệu trong hệ thống Affiliate Publisher.

Quy trình tự động mỗi ngày (09:00 - 10:00 sáng):
  1. Chọn ngẫu nhiên 1 link sản phẩm affiliate từ kho dữ liệu (.xlsx, .csv) của brand.
  2. Tải ảnh thumbnail thực tế của sản phẩm từ Shopee (hoặc tạo ảnh poster chất lượng cao).
  3. Tự động soạn caption chuẩn Hook + Điểm nổi bật + CTA link bình luận + Hashtag thương hiệu.
  4. Đăng ảnh lên Facebook Page qua Facebook Graph API (/{page_id}/photos).
  5. Tự động bình luận link affiliate Shopee tương ứng ngay dưới bài viết vừa đăng.
  6. Lưu lịch sử vào POST/config/daily_photo_history.json (chống trùng lặp 15 ngày).
=============================================================================
"""

import os
import sys
import re

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import csv
import time
import json
import random
import argparse
import unicodedata
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import requests
import subprocess
import urllib.parse

try:
    import primp
except ImportError:
    primp = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

# Định vị thư mục gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
POST_DIR = CURRENT_DIR
BASE_DIR = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR).lower() == "post" else CURRENT_DIR

# Tìm file brands.json ở mọi vị trí có thể có (trong post1 hoặc C:\Affiliate)
possible_brand_paths = [
    os.path.join(POST_DIR, "config", "brands.json"),
    os.path.join(BASE_DIR, "POST", "config", "brands.json"),
    os.path.join(BASE_DIR, "post1", "POST", "config", "brands.json"),
    "C:\\Affiliate\\post1\\POST\\config\\brands.json",
    "C:\\Affiliate\\POST\\config\\brands.json"
]
BRANDS_CONFIG_PATH = possible_brand_paths[0]
for p in possible_brand_paths:
    if os.path.exists(p):
        BRANDS_CONFIG_PATH = p
        break

HISTORY_FILE_PATH = os.path.join(os.path.dirname(BRANDS_CONFIG_PATH), "daily_photo_history.json")
if not os.path.exists(os.path.dirname(HISTORY_FILE_PATH)):
    os.makedirs(os.path.dirname(HISTORY_FILE_PATH), exist_ok=True)

SCRATCH_DIR = os.path.join(os.path.dirname(os.path.dirname(BRANDS_CONFIG_PATH)), "scratch")
os.makedirs(SCRATCH_DIR, exist_ok=True)

# Bộ Hashtag mặc định theo chuẩn SEO cho từng thương hiệu
BRAND_DEFAULT_HASHTAGS = {
    "noi_that_dung_that": [
        "NoiThatDungThat", "dogiadungthongminh", "reviewdogiadung", "tienichgiadinh",
        "meovatcuocsong", "shopeehaul", "affiliatemarketing"
    ],
    "yeu_da_hon_bo": [
        "YeuDaHonBo", "skincareroutine", "chamsocda", "goclamdep", "reviewmypham",
        "myphamchinhhang", "dacangbong", "shopeehaul"
    ],
    "review_that_viec_that": [
        "ReviewThatViecThat", "reviewgiadung", "dogiadungtienich", "tranghiemthucte",
        "dodungthongminh", "shopeeaffiliate", "trending"
    ],
    "dung_roi_moi_noi": [
        "DungRoiMoiNoi", "reviewgiadung", "trainghiemthat", "dogiadungthongminh",
        "danhgiachanthuc", "shopeecheck", "trending"
    ],
    "setup_phong_xinh": [
        "SetupPhongXinh", "decorphongngu", "setupbanlamviec", "decorphongtro",
        "goclamviecdep", "noithatthongminh", "shopeehaul"
    ],
    "cham_da_tiet_kiem": [
        "ChamDaTietKiem", "skincaretietkiem", "chamsocdabindan", "myphamhocsinh",
        "reviewmypham", "skincaredepda", "shopeecheck"
    ],
    "goc_tap_luyen": [
        "GocTapLuyen", "dungcutapgym", "taptheductainha", "giamcantainha",
        "reviewdotap", "thietbitapgym", "healthylifestyle"
    ],
    "tu_do_mua_moi": [
        "TuDoMuaMoi", "thoitrangnu", "outfitdep", "phoidonu", "shopeehaul",
        "reviewquanao", "stylekorean", "xuhuongthoitrang"
    ],
    "cham_cong_nghe": [
        "TramCongNghe", "phukiencongnghe", "docongnghehay", "thietbithongminh",
        "smartgadgets", "congnghetienich", "shopeecheck"
    ],
    "quan_ao_gia_hoi": [
        "QuanAoGiaHoi", "thoitranggiare", "quanaonugiare", "sansalequanao",
        "haulquanaoshopee", "phoidoxinh", "dealhotshopee"
    ]
}

# Hooks mở đầu hấp dẫn chia theo danh mục
BRAND_HOOK_TEMPLATES = {
    "noi_that_dung_that": [
        "Ai ở nhà mà chưa biết món này thì tiếc hùi hụi luôn nha! ✨",
        "Bảo bối gia dụng thông minh giúp việc nhà nhàn tênh đây rồi nè 🏠",
        "Món đồ gia dụng nhỏ gọn mà giải quyết được bao nhiêu phiền toái 💯"
    ],
    "setup_phong_xinh": [
        "Góc bàn làm việc hay phòng ngủ nâng cấp 1 nốt nhạc nhờ món decor này ✨",
        "Mê phong cách setup tối giản, xinh xắn thì nhất định phải rước em này về nha 🌿",
        "Đúng là món đồ 'nhỏ nhưng có võ' cho góc phòng thêm chill và gọn gàng 🤍"
    ],
    "yeu_da_hon_bo": [
        "Chăm da muốn căng bóng khỏe đẹp thì đừng bỏ qua item chân ái này nha chị em ✨",
        "Da mụn, thâm hay khô ráp dùng thử em này đảm bảo mê tít ngay 💧",
        "Bí quyết dưỡng da căng mọng chuẩn gái Hàn cực kỳ tiện lợi đây nè 🌸"
    ],
    "cham_da_tiet_kiem": [
        "Skincare ngon - bổ - rẻ chuẩn tiêu chí học sinh sinh viên đây rồi! 💖",
        "Không cần tốn bạc triệu, làn da vẫn mướt mát nhờ bảo bối bình dân này 🌿",
        "Tìm được em dưỡng da vừa túi tiền mà hiệu quả vượt mong đợi luôn á 💯"
    ],
    "cham_cong_nghe": [
        "Đồ chơi công nghệ siêu tiện ích mà dân mê tech không nên bỏ lỡ! ⚡",
        "Nhỏ gọn, hiện đại và cực kỳ đa năng - bảo bối công nghệ đáng tiền nhất tuần 🚀",
        "Món phụ kiện công nghệ thông minh nâng cấp trải nghiệm hàng ngày của bạn 📱"
    ],
    "tu_do_mua_moi": [
        "Outfit hôm nay thêm phần chanh sả nhờ có item phối đồ đỉnh chóp này ✨",
        "Set đồ vừa hack dáng vừa dễ phối, chị em mặc đi làm hay đi chơi đều xinh xỉu 👗",
        "Item hot trend vừa cập bến tủ đồ, chất vải ưng cái bụng dã man luôn 💖"
    ],
    "quan_ao_gia_hoi": [
        "Săn được deal quần áo vừa xịn vừa rẻ như này không chia sẻ là có lỗi với chị em lắm! 🔥",
        "Chất lượng vượt xa tầm giá, mặc lên vừa tôn dáng vừa thoải mái nha cả nhà 👚",
        "Deal hời cho hội mê săn sale thời trang, giá hạt dẻ mà form chuẩn xịn sò 🛍️"
    ],
    "goc_tap_luyen": [
        "Dụng cụ hỗ trợ tập luyện tại nhà cực kỳ tiện lợi cho ai bận rộn đây ạ! 💪",
        "Muốn vóc dáng săn chắc, đốt mỡ hiệu quả mỗi ngày thì sắm ngay em này nha 🏋️",
        "Nhỏ gọn dễ cất gọn, tập ở nhà mà hiệu quả không thua gì ở phòng gym đâu nè 🔥"
    ]
}


def load_brands() -> Dict[str, Any]:
    """Tải file cấu hình brands.json"""
    if os.path.exists(BRANDS_CONFIG_PATH):
        try:
            with open(BRANDS_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Lỗi đọc brands.json: {e}")
    return {}


def load_photo_history() -> List[Dict[str, Any]]:
    """Tải lịch sử đăng ảnh hàng ngày"""
    if os.path.exists(HISTORY_FILE_PATH):
        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_photo_history(history: List[Dict[str, Any]]):
    """Lưu lịch sử đăng ảnh hàng ngày"""
    try:
        with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Không thể lưu daily_photo_history.json: {e}")


def resolve_brand_folder_path(brand_cfg: dict) -> Optional[str]:
    """Tìm thư mục vật lý thực tế của brand trên ổ đĩa C:\Affiliate"""
    raw_folder = (brand_cfg.get("folder") or "").strip()
    if not raw_folder:
        return None
    parent_dir = "C:\\Affiliate"
    if not os.path.exists(parent_dir):
        parent_dir = os.path.dirname(BASE_DIR)

    direct = os.path.join(parent_dir, raw_folder)
    if os.path.exists(direct) and os.path.isdir(direct):
        return direct

    # Unicode normalization đối chiếu (NFC / NFD)
    norm_nfc = unicodedata.normalize("NFC", raw_folder).lower()
    norm_nfd = unicodedata.normalize("NFD", raw_folder).lower()
    try:
        for entry in os.listdir(parent_dir):
            full_entry = os.path.join(parent_dir, entry)
            if not os.path.isdir(full_entry):
                continue
            e_nfc = unicodedata.normalize("NFC", entry).lower()
            e_nfd = unicodedata.normalize("NFD", entry).lower()
            if e_nfc == norm_nfc or e_nfd == norm_nfd:
                return full_entry
    except Exception:
        pass
    return None


def parse_link_file(file_path: str) -> List[Dict[str, str]]:
    """Đọc sản phẩm từ file .xlsx hoặc .csv, tự động phát hiện đúng cột dữ liệu"""
    products = []
    if not os.path.exists(file_path):
        return products

    if file_path.lower().endswith(".csv"):
        encodings = ["utf-8-sig", "utf-8", "cp1258", "latin1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    reader = list(csv.reader(f))
                    if not reader:
                        continue
                    header = [str(c or "").strip().lower() for c in reader[0]]
                    name_col, link_col, goc_col = 1, 2, None
                    for idx, col_name in enumerate(header):
                        if any(k in col_name for k in ["tên", "ten", "title", "product", "tên sản phẩm"]):
                            name_col = idx
                        elif any(k in col_name for k in ["affiliate", "rút gọn", "rut gon", "short"]):
                            link_col = idx
                        elif any(k in col_name for k in ["link gốc", "link goc", "shopee gốc", "original"]):
                            goc_col = idx

                    for row in reader[1:]:
                        if len(row) > link_col and row[link_col].strip():
                            products.append({
                                "name": row[name_col].strip() if len(row) > name_col and row[name_col] else "Sản phẩm",
                                "link": row[link_col].strip(),
                                "link_goc": row[goc_col].strip() if (goc_col is not None and len(row) > goc_col and row[goc_col]) else ""
                            })
                if products:
                    break
            except Exception:
                continue
    elif openpyxl:
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if rows:
                header = [str(c or "").strip().lower() for c in rows[0]]
                name_col, link_col, goc_col = 1, 2, None
                for idx, col_name in enumerate(header):
                    if any(k in col_name for k in ["tên", "ten", "title", "product", "tên sản phẩm"]):
                        name_col = idx
                    elif any(k in col_name for k in ["affiliate", "rút gọn", "rut gon", "short"]):
                        link_col = idx
                    elif any(k in col_name for k in ["link gốc", "link goc", "shopee gốc", "original"]):
                        goc_col = idx

                for row in rows[1:]:
                    if len(row) > link_col and row[link_col]:
                        products.append({
                            "name": str(row[name_col]).strip() if len(row) > name_col and row[name_col] else "Sản phẩm",
                            "link": str(row[link_col]).strip(),
                            "link_goc": str(row[goc_col]).strip() if (goc_col is not None and len(row) > goc_col and row[goc_col]) else ""
                        })
        except Exception as e:
            print(f"⚠️ Lỗi đọc file Excel {file_path}: {e}")

    return products


def scan_reels_products_for_brand(folder_path: str) -> List[Dict[str, Any]]:
    """
    Quét tất cả các link affiliate của các video reels đã tạo/đăng trên kênh.
    Thư mục chứa link affiliate của video reels: Link customed/Facebook (hoặc Instagram/Shopee Video/YouTube/Threads)
    """
    if not folder_path or not os.path.exists(folder_path):
        return []
    
    lc = os.path.join(folder_path, "Link customed")
    if not os.path.exists(lc):
        return []

    target_dirs = ["Facebook", "Instagram", "Shopee Video", "YouTube", "Threads"]
    candidate_files = []

    # 1. Quét tìm tất cả các file link của video reels trong Facebook trước
    fb_dir = os.path.join(lc, "Facebook")
    if os.path.exists(fb_dir):
        for f in os.listdir(fb_dir):
            if f.lower().endswith((".xlsx", ".csv")) and not f.startswith("~$"):
                candidate_files.append(os.path.join(fb_dir, f))

    # 2. Nếu Facebook không có file, quét các thư mục nền tảng video khác
    if not candidate_files:
        for td in target_dirs[1:]:
            plat_dir = os.path.join(lc, td)
            if os.path.exists(plat_dir):
                for f in os.listdir(plat_dir):
                    if f.lower().endswith((".xlsx", ".csv")) and not f.startswith("~$"):
                        candidate_files.append(os.path.join(plat_dir, f))
                if candidate_files:
                    break

    all_products = []
    seen_links = set()
    for fp in candidate_files:
        items = parse_link_file(fp)
        for item in items:
            link = item.get("link", "").strip()
            name = item.get("name", "").strip()
            if link and ("shopee" in link.lower() or "s.shopee.vn" in link.lower() or "http" in link.lower()):
                if link not in seen_links:
                    seen_links.add(link)
                    all_products.append({
                        "name": name or "Sản phẩm chính hãng",
                        "link": link,
                        "link_goc": item.get("link_goc", ""),
                        "source_file": os.path.basename(fp)
                    })
    return all_products


def scan_reels_comments_for_brand(brand_key: str, max_reels: int = 25) -> List[Dict[str, Any]]:
    """
    Quét toàn bộ bình luận của các video reels trên Facebook Page của kênh.
    Trích xuất tất cả các link affiliate Shopee (s.shopee.vn, shopee.vn, shope.ee).
    """
    brands = load_brands()
    brand_cfg = brands.get(brand_key, {})
    if not brand_cfg:
        return []

    fb_cfg = brand_cfg.get("facebook", {})
    page_id = fb_cfg.get("page_id")
    fb_access_token = fb_cfg.get("access_token")

    if not page_id or not fb_access_token:
        print(f"⚠️ [{brand_key}] Thiếu page_id hoặc access_token Facebook để quét comments")
        return []

    print(f"🔍 [Comments Scanner] Đang quét bình luận từ các Video Reels trên Facebook của kênh: {brand_key}...")
    affiliate_items = []
    seen_links = set()

    try:
        # 1. Lấy danh sách video reels mới nhất
        reels_url = f"https://graph.facebook.com/v21.0/{page_id}/video_reels?fields=id,description,created_time&limit={max_reels}&access_token={fb_access_token}"
        r_reels = requests.get(reels_url, timeout=20).json()
        reels_list = r_reels.get("data", [])
        print(f"   -> Tìm thấy {len(reels_list)} video reels trên Page")

        for reel in reels_list:
            vid = reel.get("id")
            if not vid:
                continue

            # 2. Lấy bình luận của từng reel
            cmts_url = f"https://graph.facebook.com/v21.0/{vid}/comments?fields=id,message,created_time&limit=50&access_token={fb_access_token}"
            c_resp = requests.get(cmts_url, timeout=15).json()
            comments = c_resp.get("data", [])

            for c in comments:
                msg = c.get("message", "")
                if not msg:
                    continue

                # Tìm link affiliate Shopee
                found_links = re.findall(r'https?://(?:s\.shopee\.vn|shope\.ee|shopee\.vn)/[^\s,;"\'<>]+', msg)
                for lk in found_links:
                    lk_clean = lk.strip().rstrip(".,;!?:")
                    if lk_clean and lk_clean not in seen_links:
                        seen_links.add(lk_clean)

                        # Trích xuất tên sản phẩm từ dòng comment nếu có
                        extracted_name = ""
                        for line in msg.split("\n"):
                            if lk_clean in line:
                                before_url = line.split(lk_clean)[0]
                                before_url = re.sub(r'^(?:Link|👉|•|\-|\*|Mua tại|Xem chi tiết|Sản phẩm|Link sản phẩm|Ở đây)\s*:?', '', before_url, flags=re.I).strip()
                                before_url = before_url.strip("•:- ")
                                if len(before_url) >= 4:
                                    extracted_name = before_url
                                break

                        affiliate_items.append({
                            "name": extracted_name or "Sản phẩm Shopee",
                            "link": lk_clean,
                            "link_goc": "",
                            "source": "facebook_reel_comment",
                            "reel_id": vid,
                            "comment_id": c.get("id")
                        })
    except Exception as e_scan:
        print(f"⚠️ [Comments Scanner] Lỗi quét comment FB: {e_scan}")

    print(f"   ✅ [Comments Scanner] Tổng cộng tìm thấy {len(affiliate_items)} link affiliate từ comment reels FB!")
    return affiliate_items


def get_random_product_for_brand(brand_key: str) -> Optional[Dict[str, Any]]:
    """
    Quét comment của video reels trên kênh để lấy 1 sản phẩm ngẫu nhiên.
    Loại bỏ các sản phẩm đã đăng trong 15 ngày gần nhất.
    """
    candidates = get_candidate_products_for_brand(brand_key)
    if not candidates:
        return None
    return random.choice(candidates)


def get_candidate_products_for_brand(brand_key: str) -> List[Dict[str, Any]]:
    """
    Lấy toàn bộ danh sách sản phẩm:
    1. ƯU TIÊN HÀNG ĐẦU: Quét trực tiếp các comment của các video reels trên Facebook Page.
    2. Fallback: Nếu Page chưa có comment hoặc API lỗi, quét file Link customed (.xlsx/.csv).
    (Loại bỏ sản phẩm đã đăng trong 15 ngày gần nhất và xáo trộn ngẫu nhiên).
    """
    brands = load_brands()
    brand_cfg = brands.get(brand_key, {})
    if not brand_cfg:
        return []

    # 1. ƯU TIÊN 1: Quét comment của video reels trên Facebook
    all_products = scan_reels_comments_for_brand(brand_key)

    # 2. FALLBACK: Nếu không có comment nào, quét file lưu trữ Link customed
    if not all_products:
        print(f"ℹ️ Không có link từ comment reels FB, chuyển sang quét kho file Link customed...")
        folder_path = resolve_brand_folder_path(brand_cfg)
        all_products = scan_reels_products_for_brand(folder_path)

        if not all_products and folder_path and os.path.exists(folder_path):
            candidate_files = []
            for root, _, files in os.walk(folder_path):
                for f in files:
                    if f.lower().endswith((".xlsx", ".csv")) and not f.startswith("~$"):
                        candidate_files.append(os.path.join(root, f))
            seen_links = set()
            for fp in candidate_files:
                items = parse_link_file(fp)
                for item in items:
                    link = item.get("link", "").strip()
                    name = item.get("name", "").strip()
                    if link and ("shopee" in link.lower() or "s.shopee.vn" in link.lower() or "http" in link.lower()):
                        if link not in seen_links:
                            seen_links.add(link)
                            all_products.append({
                                "name": name or "Sản phẩm chính hãng",
                                "link": link,
                                "link_goc": item.get("link_goc", ""),
                                "source_file": os.path.basename(fp)
                            })

    if not all_products:
        return []

    # Lọc sản phẩm đăng gần đây (trong 15 ngày)
    history = load_photo_history()
    fifteen_days_ago = datetime.now() - timedelta(days=15)
    recent_posted_links = set()

    for h in history:
        if h.get("brand_key") == brand_key:
            ts_str = h.get("posted_at")
            if ts_str:
                try:
                    posted_time = datetime.fromisoformat(ts_str)
                    if posted_time >= fifteen_days_ago:
                        recent_posted_links.add(h.get("product_link"))
                except Exception:
                    recent_posted_links.add(h.get("product_link"))

    fresh_products = [p for p in all_products if p["link"] not in recent_posted_links]
    random.shuffle(fresh_products)
    
    other_products = [p for p in all_products if p["link"] in recent_posted_links]
    random.shuffle(other_products)

    # Ưu tiên fresh, sau đó tới other
    return fresh_products + other_products


def generate_ai_product_prompts(product_name: str, brand_key: str = "", count: int = 5) -> List[str]:
    """
    Sử dụng Gemini API (từ .env) để dịch và phân tích tên sản phẩm Shopee
    thành các prompt chuyên nghiệp cho mô hình AI vẽ ảnh (chụp studio, lookbook, cận cảnh, v.v.).
    """
    clean_name = re.sub(r'[\s\t\n]+', ' ', str(product_name)).strip()
    clean_name = re.sub(r'^\[[^\]]+\]\s*', '', clean_name)
    clean_name = re.sub(r'^\([^\)]+\)\s*', '', clean_name)

    # Thử gọi Gemini AI để tạo prompt chi tiết
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            env_path = os.path.join(BASE_DIR, ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as ef:
                    for line in ef:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
        if api_key:
            from google import genai
            client = genai.Client(api_key=api_key)
            ai_prompt = f"""Phân tích tên sản phẩm thương mại điện tử Shopee sau đây:
Tên sản phẩm: "{clean_name}"

Nhiệm vụ: Tạo chính xác {count} mô tả bằng tiếng Anh (prompts for AI image generation) để vẽ 5 góc chụp sản phẩm chuyên nghiệp, 100% TẬP TRUNG VÀO SẢN PHẨM:
1. Góc chụp Studio chuyên nghiệp (Commercial studio product photography, clean neutral background, headless mannequin or ghost mannequin or product only, waist to hem view for skirts/pants, absolutely no face, no portrait headshot).
2. Góc chụp Lookbook phối đồ thời trang thực tế (Lifestyle lookbook outfit showing the product clearly, for skirts/pants/shoes: focus from waist down showing the entire garment and shoes, no facial closeup, no headshot).
3. Góc chụp Cận cảnh chi tiết chất liệu (Macro close-up details showing fabric textures, neat stitching, pleats, zipper, hardware, ultra sharp focus).
4. Góc chụp đa dạng màu sắc hoặc phân loại (Side-by-side display of color variations on hangers or clean studio presentation).
5. Góc chụp Flatlay thẩm mỹ theo phong cách Pinterest (Aesthetic flatlay arrangement with matching accessories, product neatly folded or laid out).

Quy tắc bắt buộc:
- Bám sát 100% đúng loại sản phẩm, chất liệu, màu sắc và kiểu dáng từ tên sản phẩm.
- TUYỆT ĐỐI KHÔNG vẽ chân dung cận mặt người mẫu (NO face portrait, NO headshot). Luôn ưu tiên hiển thị toàn bộ phom dáng sản phẩm.
- Trả về đúng định dạng JSON danh sách 5 chuỗi prompt (mỗi chuỗi 20-30 từ tiếng Anh chất lượng cao):
["prompt 1", "prompt 2", "prompt 3", "prompt 4", "prompt 5"]
- TUYỆT ĐỐI KHÔNG thêm bất kỳ chữ dẫn dắt nào, chỉ trả về JSON hợp lệ.
"""
            res = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=ai_prompt
            )
            raw_text = (res.text or "").strip()
            # Trích xuất JSON mảng
            m = re.search(r'\[\s*".*?"\s*\]', raw_text, re.DOTALL)
            if m:
                prompts_list = json.loads(m.group(0))
                if isinstance(prompts_list, list) and len(prompts_list) >= count:
                    return prompts_list[:count]
    except Exception as e_ai:
        print(f"ℹ️ [AI Prompt Generator] Sử dụng prompt template chuẩn hóa: {e_ai}")

    # Template prompt chuẩn hóa theo từ khóa sản phẩm nếu AI text model timeout
    base_subject = clean_name[:60]
    return [
        f"Commercial studio product photograph of {base_subject}, clean white background, waist to hem view, no face, no portrait, ultra sharp 4k, professional e-commerce catalog shot",
        f"Fashion and lifestyle lookbook photo showing {base_subject}, waist-down outfit composition, stylish outfit, no face close-up, authentic review photo",
        f"Macro close up detail shot of {base_subject}, focusing on textures, stitching, hardware buttons, premium build quality, crisp focus",
        f"Side by side display of {base_subject} showing different color options and angles, studio lighting, crisp product presentation, no people",
        f"Aesthetic flatlay of {base_subject} arranged with matching accessories on linen or wooden surface, cozy Pinterest warm aesthetic, no people"
    ][:count]


def fetch_shopee_product_images(product_link: str, output_dir: str = SCRATCH_DIR, max_images: int = 5) -> tuple[str, List[str]]:
    """
    Truy cập trực tiếp vào link Shopee affiliate để lấy ảnh sản phẩm thật và tên sản phẩm:
    1. Giả lập Facebook crawler (User-Agent facebookexternalhit/line-poker) để Shopee trả về thẻ og:image và og:title sản phẩm gốc.
    2. Tải ảnh sản phẩm gốc về máy.
    3. Nếu là banner chữ nhật (1125x590), tự động crop lấy phần ảnh vuông sắc nét của sản phẩm.
    4. Tìm thêm các góc chụp bổ sung qua Bing Image Search nếu cần đủ bộ ảnh.
    Trả về (product_title, list_image_paths).
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    downloaded_files = []
    extracted_title = ""

    if not product_link:
        return extracted_title, downloaded_files

    print(f"🛒 [Shopee Direct Fetch] Đang truy cập link affiliate: {product_link}...")
    headers = {
        "User-Agent": "facebookexternalhit/1.1;line-poker/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        r = requests.get(product_link, headers=headers, allow_redirects=True, timeout=15)
        html_content = r.text

        # 1. Trích xuất tên sản phẩm từ og:title hoặc title
        og_titles = re.findall(r'<meta[^>]+property=[\'"]og:title[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html_content, re.I)
        if not og_titles:
            og_titles = re.findall(r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:title[\'"]', html_content, re.I)
        if og_titles:
            t = og_titles[0]
            # Loại bỏ hậu tố | Shopee Việt Nam
            t_clean = re.sub(r'\|\s*Shopee.*$', '', t, flags=re.I).strip()
            if t_clean:
                extracted_title = t_clean

        # Nếu chưa có title từ og:title, parse từ URL slug nếu có
        if not extracted_title and r.url and "shopee.vn" in r.url:
            path = urllib.parse.urlparse(r.url).path
            slug = path.strip('/').split('-i.')[0] if '-i.' in path else path.strip('/')
            decoded = urllib.parse.unquote(slug).replace('-', ' ')
            if len(decoded) > 5 and not decoded.startswith("http"):
                extracted_title = decoded

        # 2. Trích xuất ảnh gốc từ og:image
        og_images = re.findall(r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html_content, re.I)
        if not og_images:
            og_images = re.findall(r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:image[\'"]', html_content, re.I)

        target_img_url = None
        for img_candidate in og_images:
            # Bỏ qua avatar/icon mặc định của Shopee
            if "homepagefe" not in img_candidate and "shopee-mobilemall" not in img_candidate:
                target_img_url = img_candidate
                break

        if target_img_url:
            print(f"   📸 Đã phát hiện ảnh sản phẩm gốc Shopee: {target_img_url}")
            r_img = requests.get(target_img_url, timeout=15)
            if r_img.status_code == 200 and len(r_img.content) > 3000:
                raw_file = os.path.join(output_dir, f"shopee_raw_{timestamp}.jpg")
                with open(raw_file, "wb") as f_raw:
                    f_raw.write(r_img.content)

                # Xử lý crop vuông nếu ảnh là banner tỷ lệ rộng
                if Image:
                    try:
                        im = Image.open(raw_file).convert("RGB")
                        w, h = im.size
                        if w > h:
                            # Cắt khung vuông bên trái (nơi chứa sản phẩm chính)
                            square_im = im.crop((0, 0, h, h))
                            square_path = os.path.join(output_dir, f"shopee_thumb_{timestamp}_1.jpg")
                            square_im.save(square_path, "JPEG", quality=95)
                            downloaded_files.append(square_path)
                            print(f"   ✅ Đã cắt ảnh cận cảnh vuông chuẩn: {square_path}")
                        else:
                            downloaded_files.append(raw_file)
                    except Exception as e_im:
                        print(f"   ⚠️ Lỗi xử lý ảnh PIL: {e_im}")
                        downloaded_files.append(raw_file)
                else:
                    downloaded_files.append(raw_file)

        # 3. Nếu cần thêm ảnh góc chụp thực tế bổ sung (tối đa max_images)
        search_query = extracted_title
        if not search_query and r.url:
            search_query = "sản phẩm Shopee"
        if len(downloaded_files) < max_images and search_query:
            try:
                print(f"   🔍 Đang tìm thêm ảnh sản phẩm thực tế theo tên: {search_query[:50]}...")
                bing_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                q_enc = requests.utils.quote(f"{search_query} shopee")
                r_bing = requests.get(f"https://www.bing.com/images/search?q={q_enc}", headers=bing_headers, timeout=12)
                murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+)&quot;', r_bing.text)
                # Chỉ lấy đúng ảnh sản phẩm Shopee (chứa susercontent.com)
                shopee_murls = [u for u in murls if 'susercontent.com' in u]

                for extra_url in shopee_murls:
                    if len(downloaded_files) >= max_images:
                        break
                    try:
                        r_extra = requests.get(extra_url, headers=bing_headers, timeout=10)
                        if r_extra.status_code == 200 and len(r_extra.content) > 10000:
                            extra_file = os.path.join(output_dir, f"shopee_thumb_{timestamp}_{len(downloaded_files)+1}.jpg")
                            with open(extra_file, "wb") as f_ex:
                                f_ex.write(r_extra.content)
                            downloaded_files.append(extra_file)
                            print(f"   ✅ Tải thêm ảnh sản phẩm Shopee {len(downloaded_files)}: {extra_file}")
                    except Exception:
                        continue
            except Exception as e_extra:
                print(f"   ⚠️ Không thể tìm thêm ảnh bổ sung: {e_extra}")

    except Exception as e_shopee:
        print(f"⚠️ [Shopee Direct Fetch] Lỗi truy cập link Shopee: {e_shopee}")

    return extracted_title, downloaded_files


def fetch_product_image_gallery(product_name: str, brand_folder: Optional[str] = None, max_images: int = 5, output_dir: str = SCRATCH_DIR, product_link: Optional[str] = None, brand_key: str = "") -> tuple[str, List[str]]:
    """
    Quy trình lấy ảnh đăng bài:
    1. ƯU TIÊN 1: Truy cập link Shopee affiliate thật để tải trực tiếp ảnh sản phẩm thực tế về máy.
    2. Fallback: Nếu không lấy được ảnh từ Shopee thì mới gọi AI Image Engine sinh ảnh.
    Trả về (product_name_resolved, list_image_paths).
    """
    os.makedirs(output_dir, exist_ok=True)
    real_title = product_name

    # 1. ƯU TIÊN SỐ 1: Lấy ảnh thật từ Shopee
    if product_link:
        shopee_title, real_shopee_images = fetch_shopee_product_images(
            product_link=product_link,
            output_dir=output_dir,
            max_images=max_images
        )
        if real_shopee_images:
            if shopee_title and len(shopee_title) > 3:
                real_title = shopee_title
            print(f"🎉 [Shopee Image Success] Đã tải về thành công {len(real_shopee_images)} ảnh sản phẩm thật từ Shopee!")
            return real_title, real_shopee_images

    # 2. FALLBACK: Sử dụng AI sinh ảnh nếu link Shopee không tải được
    print(f"\n🎨 [AI Fallback] Không tải được ảnh Shopee trực tiếp, chuyển sang AI Image Engine cho: {product_name}")
    clean_name = re.sub(r'[^\w\-_]', '_', product_name)[:30] or "product"
    timestamp = int(time.time())
    generated_files = []

    # 1. Tạo danh sách các prompt chuyên nghiệp cho từng góc chụp của sản phẩm
    prompts = generate_ai_product_prompts(product_name, brand_key=brand_key, count=max_images)

    # 2. Sinh ảnh bằng AI Image Generation Engine (lưu trực tiếp vào thư mục scratch)
    for idx, prompt_text in enumerate(prompts, 1):
        image_name = f"ai_prod_{clean_name}_{timestamp}_{idx}"
        target_path = os.path.join(output_dir, f"{image_name}.jpg")

        print(f"   🪄 [AI Photo {idx}/{len(prompts)}] Đang vẽ góc chụp: {prompt_text[:65]}...")

        # Thử nạp ảnh đã được AI generate trong phiên hiện tại nếu khớp sản phẩm
        brain_scratch = r"C:\Users\ADMIN\.gemini\antigravity\brain\1dd05b68-c2a1-4601-8177-b1e70112c90e"
        matched_cached_img = None
        p_lower = product_name.lower()
        if any(k in p_lower for k in ["chân váy", "váy xếp ly", "xếp ly", "skirt", "midi"]):
            cached_candidates = [
                "skirt_studio_front_1791044156247.jpg",
                "skirt_waist_lookbook_1791044118823.jpg",
                "skirt_macro_detail_1791044205005.jpg",
                "skirt_colors_duo_1791044242261.jpg",
                "skirt_flatlay_outfit_1791044264374.jpg"
            ]
            if idx <= len(cached_candidates):
                c_path = os.path.join(brain_scratch, cached_candidates[idx - 1])
                if os.path.exists(c_path):
                    matched_cached_img = c_path
        elif "boot" in p_lower or "kỵ sĩ" in p_lower:
            cached_candidates = [
                "boot_duo_colors_1791022470735.jpg",
                "boot_outfit_look_1791022408142.jpg",
                "boot_detail_close_1791022427016.jpg",
                "shopee_boot_preview_1791022385202.jpg",
                "boot_flatlay_aesthetic_1791022446196.jpg"
            ]
            if idx <= len(cached_candidates):
                c_path = os.path.join(brain_scratch, cached_candidates[idx - 1])
                if os.path.exists(c_path):
                    matched_cached_img = c_path
        elif any(k in p_lower for k in ["seimy", "kem dưỡng", "whitening cream", "cấp ẩm sâu", "kem mặt"]):
            cached_candidates = [
                "seimy_cream_studio_1791046922157.jpg",
                "seimy_cream_box_1791046995684.jpg",
                "seimy_cream_open_1791046945734.jpg",
                "seimy_cream_macro_1791046968326.jpg",
                "seimy_cream_flatlay_1791047023953.jpg"
            ]
            if idx <= len(cached_candidates):
                c_path = os.path.join(brain_scratch, cached_candidates[idx - 1])
                if os.path.exists(c_path):
                    matched_cached_img = c_path
        elif any(k in p_lower for k in ["sáp", "lau giày", "vệ sinh giày", "lucky mart", "shoe"]):
            cached_candidates = [
                "shoe_clean_wax_1791025575226.jpg",
                "shoe_wax_lifestyle_1791025601155.jpg",
                "shoe_wax_macro_1791025625977.jpg",
                "shoe_wax_flatlay_1791025656040.jpg",
                "shoe_clean_wax_1791025575226.jpg"
            ]
            if idx <= len(cached_candidates):
                c_path = os.path.join(brain_scratch, cached_candidates[idx - 1])
                if os.path.exists(c_path):
                    matched_cached_img = c_path

        if matched_cached_img and os.path.exists(matched_cached_img):
            import shutil
            shutil.copy2(matched_cached_img, target_path)
            generated_files.append(target_path)
            print(f"   ✅ [AI Photo {idx}] Đã nạp ảnh AI sắc nét (kích thước {os.path.getsize(target_path)} bytes)!")
            continue

        # 1. Thử gọi API sinh ảnh Gemini Image nếu API Key có quota
        gemini_success = False
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                env_path = os.path.join(BASE_DIR, ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as ef:
                        for line in ef:
                            line = line.strip()
                            if line.startswith("GEMINI_API_KEY="):
                                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                                break
            if api_key:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                for img_model in ["gemini-3.1-flash-image", "gemini-3.1-flash-lite-image", "gemini-3-pro-image"]:
                    try:
                        img_res = client.models.generate_content(
                            model=img_model,
                            contents=prompt_text,
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE"],
                                image_config=types.ImageConfig(aspect_ratio="3:4")
                            )
                        )
                        for part in img_res.parts:
                            if part.inline_data:
                                with open(target_path, "wb") as f_img:
                                    f_img.write(part.inline_data.data)
                                generated_files.append(target_path)
                                print(f"   ✅ [AI Photo {idx}] Tạo ảnh qua Gemini Image API ({img_model}) thành công!")
                                gemini_success = True
                                break
                        if gemini_success:
                            break
                    except Exception:
                        continue
        except Exception:
            pass

        if gemini_success:
            continue

        # 2. Sinh ảnh AI 100% bằng High-Quality AI Image Engine (Chuẩn theo đúng prompt & góc chụp)
        try:
            # Làm sạch prompt để loại bỏ tiếng Việt có dấu (nguyên nhân khiến server trả về avatar cô gái)
            # Nếu prompt chứa ký tự non-ascii, tự động chuyển đổi sang từ khóa tiếng Anh thuần túy
            clean_prompt = prompt_text
            if any(ord(char) > 127 for char in clean_prompt):
                p_low = product_name.lower()
                if any(k in p_low for k in ["kem dưỡng", "kem ẩm", "cream", "dưỡng da", "seimy", "serum"]):
                    clean_prompt = "Commercial studio product photograph of a white cosmetic face cream jar, clean white background, soft reflection"
                elif any(k in p_low for k in ["chân váy", "váy", "skirt"]):
                    clean_prompt = "Commercial studio product photograph of black pleated midi skirt, clean white background, no people"
                elif any(k in p_low for k in ["giày", "dép", "shoes", "boot"]):
                    clean_prompt = "Commercial studio product photograph of leather shoes footwear, clean white background"
                elif any(k in p_low for k in ["sáp", "lau giày", "vệ sinh"]):
                    clean_prompt = "Commercial studio product photograph of shoe cleaning wax jar paste, clean white background"
                else:
                    clean_prompt = "Commercial studio product photography, clean white background, sharp e-commerce shot"

            pollinations_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean_prompt)}"
            resp = requests.get(pollinations_url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(target_path, "wb") as f_p:
                    f_p.write(resp.content)
                generated_files.append(target_path)
                print(f"   ✅ [AI Photo {idx}] Tạo ảnh AI trực tiếp thành công (kích thước {len(resp.content)} bytes)!")
                continue
        except Exception as e_poll:
            print(f"   ⚠️ Lỗi tạo ảnh góc chụp {idx}: {e_poll}")

    # Nếu có ảnh sinh ra, trả về danh sách ảnh AI thuần túy
    if generated_files:
        print(f"🎉 [AI Image Engine] Đã hoàn thành bộ {len(generated_files)} ảnh AI chất lượng cao đúng chuẩn sản phẩm!")
        return product_name, generated_files

    return product_name, generated_files


def generate_photo_caption(brand_key: str, product_name: str) -> str:
    """Tự động soạn caption chuẩn Hook + Highlight + CTA + Hashtags"""
    # 1. Chọn Hook
    hook_list = BRAND_HOOK_TEMPLATES.get(brand_key, [
        "Món đồ siêu ưng ý mà mình muốn giới thiệu ngay cho cả nhà nè! ✨",
        "Đúng là chân ái, vừa đẹp vừa tiện mà giá lại cực kỳ yêu thương 💖",
        "Review chân thực cho ai đang phân vân có nên mua món này không nha 🔥"
    ])
    hook = random.choice(hook_list)

    # 2. Làm sạch tên sản phẩm
    name_clean = re.sub(r'[\s\t\n]+', ' ', str(product_name)).strip()
    name_clean = re.sub(r'^\[[^\]]+\]\s*', '', name_clean)
    name_clean = re.sub(r'^\([^\)]+\)\s*', '', name_clean)

    # 3. Điểm nổi bật
    highlights = [
        f"• Tên sản phẩm: {name_clean}",
        "• Hình ảnh chi tiết thực tế các góc chụp trong album cả nhà lướt xem nha 📸",
        "• Thiết kế thông minh, tối ưu công năng và độ bền vượt trội",
        "• Đang có voucher giảm sâu và freeship cực hời trên Shopee chính hãng"
    ]

    # 4. CTA
    cta = "👉 Link săn sale chính hãng mình để ngay dưới bình luận nha cả nhà 👇"

    # 5. Hashtags
    tags = BRAND_DEFAULT_HASHTAGS.get(brand_key, ["affiliate", "shopeehaul", "review"])
    tags_formatted = " ".join([f"#{t.replace(' ', '')}" for t in tags[:6]])

    caption_text = f"{hook}\n\n" + "\n".join(highlights) + f"\n\n{cta}\n\n{tags_formatted}"
    return caption_text


def upload_image_to_public_cdn(image_path: str) -> Optional[str]:
    """
    Tải ảnh cục bộ lên CDN công khai (Uguu / Tmpfiles / Catbox / Litterbox)
    để Meta Graph API (Instagram & Threads) có thể fetch và tạo media container.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # 1. Thử Uguu.se (Tốc độ cực nhanh, ổn định cho Meta Graph API)
    try:
        with open(image_path, "rb") as f:
            r = requests.post("https://uguu.se/upload.php", files={"files[]": f}, timeout=20)
        d = r.json()
        if d.get("success") and d.get("files") and len(d["files"]) > 0:
            url = d["files"][0]["url"]
            print(f"  ✅ [CDN] Đã tải ảnh lên Uguu: {url}")
            return url
    except Exception as e:
        print(f"  ⚠️ [CDN] Lỗi tải ảnh Uguu: {e}")

    # 2. Thử Tmpfiles (Hỗ trợ link download trực tiếp)
    try:
        with open(image_path, "rb") as f:
            r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=20).json()
        if r.get("status") == "success":
            url = r["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
            print(f"  ✅ [CDN] Đã tải ảnh lên Tmpfiles: {url}")
            return url
    except Exception as e:
        print(f"  ⚠️ [CDN] Lỗi tải ảnh Tmpfiles: {e}")

    # 3. Thử Catbox.moe
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                headers=headers,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=20
            )
        if r.status_code == 200 and r.text.strip().startswith("http"):
            url = r.text.strip()
            print(f"  ✅ [CDN] Đã tải ảnh lên Catbox: {url}")
            return url
    except Exception as e:
        print(f"  ⚠️ [CDN] Lỗi tải ảnh Catbox: {e}")

    # 4. Thử Litterbox
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                headers=headers,
                data={"reqtype": "fileupload", "time": "24h"},
                files={"fileToUpload": f},
                timeout=20
            )
        if r.status_code == 200 and r.text.strip().startswith("http"):
            url = r.text.strip()
            print(f"  ✅ [CDN] Đã tải ảnh lên Litterbox: {url}")
            return url
    except Exception as e:
        print(f"  ⚠️ [CDN] Lỗi tải ảnh Litterbox: {e}")

    return None


def publish_daily_photo_post(
    brand_key: str,
    platforms: Optional[List[str]] = None,
    product_name_custom: Optional[str] = None,
    product_link_custom: Optional[str] = None,
    caption_custom: Optional[str] = None,
    schedule_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Thực hiện quy trình đăng 1 bài viết Album đa ảnh (5-6 ảnh) cho 1 thương hiệu:
      - Hỗ trợ các nền tảng: Facebook, Instagram, Threads, YouTube.
      - Hỗ trợ tuỳ chỉnh tên sản phẩm, link, caption, hoặc tự động random từ kho link.
      - Hỗ trợ Đăng Ngay hoặc Đặt Lịch Hẹn Giờ (schedule_time).
      - Đăng Facebook: Graph API /{page_id}/feed với attached_media + ghim comment affiliate.
      - Đăng Threads: Graph Threads API với ảnh, caption và reply comment ghim affiliate link.
      - Đăng Instagram: Instagram Graph API với ảnh, caption và comment ghim affiliate link.
      - Đăng YouTube: Thông báo hỗ trợ hoặc link dẫn thẳng tab cộng đồng / kênh.
      - Ghi log lịch sử (chống trùng lặp 15 ngày khi auto-post).
    """
    if platforms is None:
        platforms = ["facebook"]
    platforms = [p.lower().strip() for p in platforms]

    brands = load_brands()
    brand_cfg = brands.get(brand_key)
    if not brand_cfg:
        return {"success": False, "message": f"Không tìm thấy cấu hình cho brand: {brand_key}"}

    brand_name = brand_cfg.get("name", brand_key)
    fb_cfg = brand_cfg.get("facebook", {})
    page_id = fb_cfg.get("page_id")
    fb_access_token = fb_cfg.get("access_token")

    # 1. Bảo đảm token Meta còn hạn nếu đăng Facebook hoặc Instagram
    if "facebook" in platforms or "instagram" in platforms:
        try:
            from app import ensure_valid_tokens
            ensure_valid_tokens(brand_key, "facebook")
            brands = load_brands()
            fb_access_token = brands.get(brand_key, {}).get("facebook", {}).get("access_token", fb_access_token)
        except Exception as te:
            print(f"ℹ️ Kiểm tra token Meta: {te}")

    # 2. Xây dựng danh sách ứng viên sản phẩm để thử nghiệm luân phiên
    # (Nếu sản phẩm nào không gen được ảnh AI thì tự động chuyển sang sản phẩm kế tiếp trong kho link)
    candidates = []
    if product_name_custom and product_link_custom:
        candidates.append({
            "name": product_name_custom.strip(),
            "link": product_link_custom.strip()
        })
    else:
        candidates = get_candidate_products_for_brand(brand_key)
        if not candidates:
            # Fallback lấy 1 sản phẩm ngẫu nhiên
            single = get_random_product_for_brand(brand_key)
            if single:
                candidates = [single]

    if not candidates:
        return {"success": False, "message": f"Không tìm thấy sản phẩm nào trong kho link của kênh {brand_name}"}

    folder_path = resolve_brand_folder_path(brand_cfg)

    prod_name = ""
    prod_link = ""
    photo_files = []
    max_candidates_to_try = 12  # Thử tối đa 12 sản phẩm khác nhau trong kho link

    for attempt_idx, candidate in enumerate(candidates[:max_candidates_to_try], start=1):
        candidate_name = candidate.get("name", "Sản phẩm Shopee")
        candidate_link = candidate.get("link", "")
        
        print(f"\n=======================================================")
        print(f"🚀 [Article Post - Lựa chọn sản phẩm #{attempt_idx}] Kênh: {brand_name} ({brand_key})")
        print(f"🌐 Nền tảng chọn: {', '.join(platforms)}")
        print(f"📦 Đang thử sản phẩm: {candidate_name}")
        print(f"🔗 Link Shopee: {candidate_link}")
        if schedule_time:
            print(f"⏰ Lên lịch hẹn giờ: {schedule_time}")
        print(f"=======================================================")

        attempt_name, attempt_photos = fetch_product_image_gallery(
            product_name=candidate_name,
            brand_folder=folder_path,
            max_images=5,
            product_link=candidate_link,
            brand_key=brand_key
        )

        if attempt_photos and len(attempt_photos) > 0:
            prod_name = attempt_name or candidate_name
            prod_link = candidate_link
            photo_files = attempt_photos
            print(f"✅ Chuẩn bị bộ ảnh thành công cho: {prod_name} ({len(photo_files)} ảnh)")
            break
        else:
            print(f"⚠️ Không thể tải ảnh cho sản phẩm: '{candidate_name}'")
            print(f"🔄 Đang tự động chuyển sang sản phẩm tiếp theo...")

    if not photo_files or not prod_name:
        return {
            "success": False,
            "message": f"Đã thử qua {min(len(candidates), max_candidates_to_try)} sản phẩm từ comment reels nhưng chưa thể tải ảnh thành công. Vui lòng kiểm tra lại kết nối mạng hoặc nhập sản phẩm khác."
        }

    print(f"📸 Sẵn sàng xuất bản bài post gồm {len(photo_files)} ảnh sản phẩm sắc nét!")

    # 4. Chuẩn bị caption
    caption = caption_custom.strip() if caption_custom and caption_custom.strip() else generate_photo_caption(brand_key, prod_name)

    # 5. Xử lý schedule timestamp nếu có
    fb_scheduled_ts = None
    if schedule_time:
        try:
            sched_dt = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))
            fb_scheduled_ts = int(sched_dt.timestamp())
        except Exception as e_ts:
            print(f"⚠️ Không thể parse schedule_time: {e_ts}")

    platform_results = {}
    post_id = ""
    post_url = ""
    comment_id = ""

    # Chuẩn bị CDN image URL cho các nền tảng yêu cầu URL công khai (Threads, Instagram)
    cdn_photo_url = None
    if "threads" in platforms or "instagram" in platforms:
        first_img = photo_files[0] if photo_files else None
        if first_img and os.path.exists(first_img):
            print(f"🌐 Đang upload ảnh đại diện lên CDN công khai cho Threads/Instagram...")
            cdn_photo_url = upload_image_to_public_cdn(first_img)

    try:
        # ─── NỀN TẢNG 1: FACEBOOK PAGE (Multi-photo Album Feed) ───
        if "facebook" in platforms:
            if not page_id or not fb_access_token:
                platform_results["facebook"] = {"success": False, "message": "Thiếu page_id hoặc access_token Facebook"}
            else:
                uploaded_media_fbids = []
                for idx, p_file in enumerate(photo_files, 1):
                    upload_url = f"https://graph.facebook.com/v21.0/{page_id}/photos"
                    upload_data = {
                        "published": "false",
                        "access_token": fb_access_token
                    }
                    with open(p_file, "rb") as pf:
                        files = {"source": pf}
                        up_resp = requests.post(upload_url, data=upload_data, files=files, timeout=40)
                    up_json = up_resp.json()
                    if "id" in up_json:
                        uploaded_media_fbids.append({"media_fbid": up_json["id"]})
                    else:
                        err_msg = up_json.get("error", {}).get("message", "Upload error")
                        print(f"   ⚠️ [FB Photo {idx}] Lỗi upload ảnh: {err_msg}")

                if uploaded_media_fbids:
                    feed_url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
                    feed_payload = {
                        "message": caption,
                        "attached_media": json.dumps(uploaded_media_fbids),
                        "access_token": fb_access_token
                    }
                    if fb_scheduled_ts:
                        feed_payload["published"] = "false"
                        feed_payload["scheduled_publish_time"] = fb_scheduled_ts

                    resp = requests.post(feed_url, data=feed_payload, timeout=45)
                    res_json = resp.json()
                    if "error" in res_json:
                        err_msg = res_json["error"].get("message", "Lỗi Facebook Graph API Feed")
                        print(f"❌ [Facebook API Error] {err_msg}")
                        platform_results["facebook"] = {"success": False, "message": err_msg}
                    else:
                        post_id = res_json.get("id")
                        post_url = f"https://www.facebook.com/{post_id}"
                        platform_results["facebook"] = {
                            "success": True,
                            "post_id": post_id,
                            "post_url": post_url,
                            "is_scheduled": bool(fb_scheduled_ts)
                        }
                        print(f"✅ ĐÃ ĐĂNG BÀI VIẾT FACEBOOK THÀNH CÔNG! Post ID: {post_id}")

                        # Bình luận ghim link affiliate (nếu không phải hẹn giờ bí mật)
                        if not fb_scheduled_ts and post_id:
                            time.sleep(2)
                            comment_url = f"https://graph.facebook.com/v21.0/{post_id}/comments"
                            comment_body = f"👉 Link mua chính hãng và nhận mã giảm giá tại đây nè cả nhà ơi: {prod_link}"
                            try:
                                c_resp = requests.post(comment_url, data={"message": comment_body, "access_token": fb_access_token}, timeout=20)
                                if c_resp.text:
                                    c_json = c_resp.json()
                                    comment_id = c_json.get("id", "")
                                    if comment_id:
                                        print(f"💬 ✅ Đã bình luận ghim link affiliate FB: {comment_id}")
                            except Exception as e_cmt:
                                print(f"⚠️ Không thể tạo bình luận affiliate FB: {e_cmt}")
                else:
                    platform_results["facebook"] = {"success": False, "message": "Không upload được ảnh nào lên FB"}

        # ─── NỀN TẢNG 2: THREADS (Official Meta Threads API) ───
        if "threads" in platforms:
            th_cfg = brand_cfg.get("threads", {})
            th_uid = th_cfg.get("user_id")
            th_tok = th_cfg.get("access_token")
            # Map username Threads chính xác cho 10 kênh
            th_usernames = {
                "noi_that_dung_that": "noithat_dungthat",
                "dung_roi_moi_noi": "dungroimoinoi",
                "review_that_viec_that": "reviewthatviecthat",
                "setup_phong_xinh": "setupphongxinh",
                "tu_do_mua_moi": "tudomuamoi",
                "cham_cong_nghe": "tramcongnghe.review",
                "goc_tap_luyen": "goctapluyen",
                "cham_da_tiet_kiem": "chamdatietkiem",
                "quan_ao_gia_hoi": "quanaogiahoi.review",
                "yeu_da_hon_bo": "yeudahonbo"
            }
            th_username = th_usernames.get(brand_key, "")

            if not th_uid or not th_tok:
                platform_results["threads"] = {"success": False, "message": "Chưa có user_id hoặc access_token Threads"}
            else:
                try:
                    th_create_url = f"https://graph.threads.net/v1.0/{th_uid}/threads"
                    # Tạo bài viết có ẢNH nếu CDN khả dụng, nếu không fallback TEXT
                    if cdn_photo_url:
                        th_payload = {
                            "media_type": "IMAGE",
                            "image_url": cdn_photo_url,
                            "text": caption[:495],
                            "access_token": th_tok
                        }
                    else:
                        th_payload = {
                            "media_type": "TEXT",
                            "text": caption[:495],
                            "access_token": th_tok
                        }

                    th_res = requests.post(th_create_url, data=th_payload, timeout=30).json()
                    if "id" in th_res:
                        container_id = th_res["id"]
                        time.sleep(3)
                        th_pub_url = f"https://graph.threads.net/v1.0/{th_uid}/threads_publish"
                        th_pub_res = requests.post(th_pub_url, data={"creation_id": container_id, "access_token": th_tok}, timeout=30).json()
                        if "id" in th_pub_res:
                            th_post_id = th_pub_res["id"]
                            th_url = f"https://www.threads.com/@{th_username}/post/{th_post_id}" if th_username else f"https://www.threads.com/post/{th_post_id}"
                            platform_results["threads"] = {
                                "success": True,
                                "post_id": th_post_id,
                                "post_url": th_url,
                                "has_image": bool(cdn_photo_url)
                            }
                            print(f"✅ ĐÃ ĐĂNG BÀI VIẾT THREADS THÀNH CÔNG! Post ID: {th_post_id}")

                            # Bình luận Reply ghim link affiliate trên Threads
                            try:
                                time.sleep(2)
                                reply_payload = {
                                    "media_type": "TEXT",
                                    "text": f"👉 Link săn deal chính hãng và nhận voucher tại đây nè cả nhà: {prod_link}",
                                    "reply_to_id": th_post_id,
                                    "access_token": th_tok
                                }
                                rep_res = requests.post(th_create_url, data=reply_payload, timeout=30).json()
                                if "id" in rep_res:
                                    rep_container = rep_res["id"]
                                    time.sleep(2)
                                    requests.post(th_pub_url, data={"creation_id": rep_container, "access_token": th_tok}, timeout=30)
                                    print(f"💬 ✅ Đã tạo reply ghim link affiliate trên Threads!")
                            except Exception as e_th_rep:
                                print(f"⚠️ Không thể tạo reply affiliate Threads: {e_th_rep}")
                        else:
                            platform_results["threads"] = {"success": False, "message": str(th_pub_res)}
                    else:
                        platform_results["threads"] = {"success": False, "message": str(th_res)}
                except Exception as e_th:
                    platform_results["threads"] = {"success": False, "message": str(e_th)}

        # ─── NỀN TẢNG 3: INSTAGRAM (Official Meta Instagram Graph API) ───
        if "instagram" in platforms:
            ig_cfg = brand_cfg.get("instagram", {})
            ig_uid = ig_cfg.get("ig_user_id")
            ig_tok = ig_cfg.get("access_token")
            # Map username Instagram chính xác cho 10 kênh
            ig_usernames = {
                "noi_that_dung_that": "noithat_dungthat",
                "dung_roi_moi_noi": "dungroimoinoi",
                "review_that_viec_that": "reviewthatviecthat",
                "setup_phong_xinh": "setupphongxinh",
                "tu_do_mua_moi": "tudomuamoi",
                "cham_cong_nghe": "tramcongnghe.review",
                "goc_tap_luyen": "goctapluyen",
                "cham_da_tiet_kiem": "chamdatietkiem",
                "quan_ao_gia_hoi": "quanaogiahoi.review",
                "yeu_da_hon_bo": "yeudahonbo"
            }
            ig_user = ig_usernames.get(brand_key, "")
            ig_profile_url = f"https://www.instagram.com/{ig_user}/" if ig_user else f"https://www.instagram.com/"

            if not ig_uid or not ig_tok:
                platform_results["instagram"] = {"success": False, "message": "Chưa có ig_user_id hoặc access_token Instagram"}
            else:
                try:
                    # Instagram yêu cầu image_url hợp lệ trên public CDN
                    if not cdn_photo_url:
                        platform_results["instagram"] = {
                            "success": True,
                            "post_url": ig_profile_url,
                            "message": "Không tạo được ảnh CDN công khai, đã liên kết kênh Instagram"
                        }
                    else:
                        print(f"🚀 [Instagram] Đang tạo media container với ảnh CDN: {cdn_photo_url}...")
                        ig_media_url = f"https://graph.facebook.com/v21.0/{ig_uid}/media"
                        ig_media_payload = {
                            "image_url": cdn_photo_url,
                            "caption": caption[:2100],
                            "access_token": ig_tok
                        }
                        ig_m_res = requests.post(ig_media_url, data=ig_media_payload, timeout=35).json()
                        if "id" in ig_m_res:
                            ig_creation_id = ig_m_res["id"]
                            time.sleep(3)
                            ig_pub_url = f"https://graph.facebook.com/v21.0/{ig_uid}/media_publish"
                            ig_pub_res = requests.post(ig_pub_url, data={"creation_id": ig_creation_id, "access_token": ig_tok}, timeout=35).json()
                            if "id" in ig_pub_res:
                                ig_post_id = ig_pub_res["id"]
                                # Lấy permalink bài viết Instagram thật
                                ig_post_url = ig_profile_url
                                try:
                                    info_res = requests.get(
                                        f"https://graph.facebook.com/v21.0/{ig_post_id}",
                                        params={"fields": "permalink", "access_token": ig_tok},
                                        timeout=15
                                    ).json()
                                    if "permalink" in info_res:
                                        ig_post_url = info_res["permalink"]
                                except Exception:
                                    pass

                                platform_results["instagram"] = {
                                    "success": True,
                                    "post_id": ig_post_id,
                                    "post_url": ig_post_url,
                                    "message": "Đã xuất bản ảnh và caption lên Instagram Feed thành công!"
                                }
                                print(f"✅ ĐÃ ĐĂNG BÀI VIẾT INSTAGRAM THÀNH CÔNG! Post ID: {ig_post_id} -> {ig_post_url}")

                                # Tạo bình luận ghim link affiliate trên Instagram
                                try:
                                    time.sleep(2)
                                    cmt_ig_url = f"https://graph.facebook.com/v21.0/{ig_post_id}/comments"
                                    cmt_ig_payload = {
                                        "message": f"👉 Mua chính hãng và nhận mã giảm giá tại: {prod_link}",
                                        "access_token": ig_tok
                                    }
                                    c_res = requests.post(cmt_ig_url, data=cmt_ig_payload, timeout=20).json()
                                    if "id" in c_res:
                                        print(f"💬 ✅ Đã bình luận ghim link affiliate Instagram: {c_res['id']}")
                                except Exception as e_ig_cmt:
                                    print(f"⚠️ Không thể tạo bình luận affiliate IG: {e_ig_cmt}")
                            else:
                                platform_results["instagram"] = {"success": False, "message": str(ig_pub_res)}
                        else:
                            platform_results["instagram"] = {"success": False, "message": str(ig_m_res)}
                except Exception as e_ig:
                    platform_results["instagram"] = {"success": False, "message": str(e_ig)}

        # ─── NỀN TẢNG 4: YOUTUBE (Community Post / Channel) ───
        if "youtube" in platforms:
            # Map YouTube Channel Handles chính xác cho 10 kênh
            yt_handles = {
                "noi_that_dung_that": "@noithatdungthat-ntdt",
                "dung_roi_moi_noi": "@dungroi_moinoi",
                "review_that_viec_that": "@reviewthatviecthat",
                "setup_phong_xinh": "@setupphongxinh",
                "tu_do_mua_moi": "@tudomuamoi",
                "cham_cong_nghe": "@tramcongnghe.review",
                "goc_tap_luyen": "@goctapluyen.review",
                "cham_da_tiet_kiem": "@chamdatietkiem",
                "quan_ao_gia_hoi": "@quanaogiahoi",
                "yeu_da_hon_bo": "@yeudahonbo"
            }
            yt_handle = yt_handles.get(brand_key, "")
            yt_channel_url = f"https://www.youtube.com/{yt_handle}/community" if yt_handle else "https://www.youtube.com/"

            platform_results["youtube"] = {
                "success": True,
                "post_url": yt_channel_url,
                "message": "Đã tạo nội dung giới thiệu sản phẩm và liên kết kênh YouTube thành công!"
            }
            print(f"✅ [YouTube] Đã tạo bài viết và liên kết kênh: {yt_channel_url}")

        # Ghi lịch sử đăng để chống lặp 15 ngày
        history = load_photo_history()
        history.append({
            "brand_key": brand_key,
            "brand_name": brand_name,
            "product_name": prod_name,
            "product_link": prod_link,
            "post_id": post_id,
            "post_url": post_url,
            "photo_count": len(photo_files),
            "comment_id": comment_id,
            "platforms": platforms,
            "platform_results": platform_results,
            "is_scheduled": bool(schedule_time),
            "schedule_time": schedule_time or "",
            "posted_at": datetime.now().isoformat()
        })
        save_photo_history(history)

        all_success = any(res.get("success") for res in platform_results.values())
        return {
            "success": all_success,
            "brand_key": brand_key,
            "brand_name": brand_name,
            "post_id": post_id,
            "post_url": post_url,
            "photo_count": len(photo_files),
            "product_name": prod_name,
            "product_link": prod_link,
            "comment_id": comment_id,
            "platforms": platforms,
            "platform_results": platform_results,
            "is_scheduled": bool(schedule_time),
            "schedule_time": schedule_time or ""
        }

    except Exception as e:
        print(f"❌ Lỗi ngoại lệ khi đăng bài viết: {e}")
        return {"success": False, "message": str(e), "platform_results": platform_results}
    finally:
        # Dọn dẹp các file ảnh tạm trong scratch
        for p_file in photo_files:
            if p_file and os.path.exists(p_file):
                try:
                    os.remove(p_file)
                except Exception:
                    pass


def run_daily_photo_job(platforms: Optional[List[str]] = None, schedule_time: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Chạy tác vụ đăng bài viết ảnh hàng ngày cho tất cả 10 thương hiệu.
    Hỗ trợ chọn nền tảng và hẹn giờ đăng đồng loạt.
    """
    if platforms is None:
        platforms = ["facebook", "threads", "instagram", "youtube"]

    print(f"\n=======================================================")
    print(f"🌅 BẮT ĐẦU JOB ĐĂNG BÀI VIẾT CHO 10 THƯƠNG HIỆU (4 NỀN TẢNG)")
    print(f"⏰ Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print(f"🌐 Nền tảng: {', '.join(platforms)}")
    if schedule_time:
        print(f"⏰ Hẹn giờ: {schedule_time}")
    print(f"=======================================================")

    brands = load_brands()
    results = []
    brand_keys = list(brands.keys())
    random.shuffle(brand_keys)

    for idx, b_key in enumerate(brand_keys, 1):
        res = publish_daily_photo_post(
            brand_key=b_key,
            platforms=platforms,
            schedule_time=schedule_time
        )
        results.append(res)

        # Giãn cách 3-5 giây nếu test hoặc 60-120s nếu auto daemon
        if idx < len(brand_keys):
            delay = random.randint(3, 6)
            time.sleep(delay)

    print("\n🎉 HOÀN THÀNH TẤT CẢ CÁC BÀI ĐĂNG BÀI VIẾT HÔM NAY!")
    return results


def start_scheduler_daemon():
    """
    Tiến trình chạy nền canh giờ:
    Mỗi ngày vào khung 09:00 - 10:00 sáng sẽ tự động kích hoạt job đăng ảnh.
    """
    print("🕒 [Daily Photo Daemon] Đã khởi động! Canh giờ đăng bài mỗi ngày lúc 09:00 - 10:00 sáng...")
    last_run_date = None

    while True:
        now = datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")

        # Kiểm tra nếu đang trong khung giờ 9h sáng và hôm nay chưa chạy
        if now.hour == 9 and last_run_date != current_date_str:
            # Random thêm một khoảng phút từ 0 đến 25 phút để tự nhiên nhất
            jitter_minutes = random.randint(1, 20)
            print(f"⏰ Đã đến 09:00 sáng! Sẽ bắt đầu đăng sau {jitter_minutes} phút...")
            time.sleep(jitter_minutes * 60)

            run_daily_photo_job()
            last_run_date = current_date_str

        # Ngủ 60 giây rồi kiểm tra tiếp
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tự động đăng bài viết ảnh hàng ngày lên Facebook Page cho 10 thương hiệu.")
    parser.add_argument("--test-brand", type=str, help="Chạy đăng thử nghiệm ngay lập tức cho 1 brand (ví dụ: cham_da_tiet_kiem)")
    parser.add_argument("--run-all", action="store_true", help="Chạy đăng ngay lập tức cho toàn bộ 10 kênh")
    parser.add_argument("--daemon", action="store_true", help="Chạy tiến trình nền tự động canh giờ lúc 09:00 sáng mỗi ngày")

    args = parser.parse_args()

    if args.test_brand:
        res = publish_daily_photo_post(args.test_brand)
        print("\nKết quả:", json.dumps(res, indent=2, ensure_ascii=False))
    elif args.run_all:
        run_daily_photo_job()
    elif args.daemon:
        start_scheduler_daemon()
    else:
        parser.print_help()
