# -*- coding: utf-8 -*-
"""
token_refresher.py — Module kiểm tra & tự động gia hạn token Meta (IG / Facebook)
                     trước khi chạy bất kỳ task upload nào.

Dùng độc lập từ task scripts, không phụ thuộc vào app.py Flask context.

Cách dùng:
    from token_refresher import refresh_meta_tokens_if_needed
    refresh_meta_tokens_if_needed("dung_roi_moi_noi", ["instagram", "threads"])
"""

import os
import sys
import time
import json
import requests
import datetime

POST_DIR    = os.path.dirname(os.path.abspath(__file__))
BRANDS_PATH = os.path.join(POST_DIR, "config", "brands.json")

# ── Đọc từ .env nếu có, fallback hard-code ────────────────────────────────────
def _load_env_var(key: str, fallback: str = "") -> str:
    env_path = os.path.join(POST_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, fallback)

FB_APP_ID     = _load_env_var("FB_APP_ID",     "2105066176522945")
FB_APP_SECRET = _load_env_var("FB_APP_SECRET", "975ca71ab78e1676c5dd4fc356ce337f")


def _load_brands() -> dict:
    with open(BRANDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_brands(brands: dict):
    with open(BRANDS_PATH, "w", encoding="utf-8") as f:
        json.dump(brands, f, indent=4, ensure_ascii=False)


def _log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _check_token_valid(token: str) -> dict:
    """
    Gọi /debug_token để kiểm tra tình trạng token.
    Trả về dict: {"valid": bool, "expires_at": int (0 = không hết hạn)}
    """
    try:
        r = requests.get(
            "https://graph.facebook.com/v19.0/debug_token",
            params={"input_token": token, "access_token": token},
            timeout=15
        )
        if r.status_code != 200:
            return {"valid": False, "expires_at": 0}
        data = r.json().get("data", {})
        return {
            "valid":      data.get("is_valid", False),
            "expires_at": data.get("expires_at", 0)
        }
    except Exception as e:
        _log(f"  ⚠️ Không thể debug_token: {e}")
        return {"valid": True, "expires_at": 0}   # Giả định còn hợp lệ nếu không check được


def _exchange_long_lived_token(short_token: str, page_id: str = "") -> str:
    """
    Đổi token sang long-lived (60 ngày) rồi lấy Page Access Token vĩnh viễn nếu có page_id.
    Trả về token mới hoặc chuỗi rỗng nếu thất bại.
    """
    try:
        resp = requests.get(
            "https://graph.facebook.com/v21.0/oauth/access_token",
            params={
                "grant_type":       "fb_exchange_token",
                "client_id":        FB_APP_ID,
                "client_secret":    FB_APP_SECRET,
                "fb_exchange_token": short_token,
            },
            timeout=20
        )
        new_tok = resp.json().get("access_token", "")
        if not new_tok:
            _log(f"  ⚠️ fb_exchange_token trả về rỗng: {resp.json()}")
            return ""

        # Nếu có page_id, lấy Page Access Token vĩnh viễn qua /me/accounts
        if page_id:
            try:
                r_acc = requests.get(
                    "https://graph.facebook.com/v21.0/me/accounts",
                    params={"access_token": new_tok, "fields": "id,access_token", "limit": 100},
                    timeout=20
                )
                for acc in r_acc.json().get("data", []):
                    if str(acc.get("id")) == str(page_id):
                        return acc.get("access_token", new_tok)
            except Exception:
                pass
        return new_tok
    except Exception as e:
        _log(f"  ❌ Lỗi exchange token: {e}")
        return ""


def refresh_meta_tokens_if_needed(brand_key: str, platforms: list = None) -> bool:
    """
    Kiểm tra và gia hạn token Meta cho brand_key trên các platforms.
    platforms: list trong ["instagram", "facebook", "threads"]
               (threads dùng chung token với instagram/facebook tuỳ config)
    Trả về True nếu token còn hợp lệ hoặc đã gia hạn thành công, False nếu thất bại.
    """
    if platforms is None:
        platforms = ["instagram", "facebook"]

    try:
        brands    = _load_brands()
        brand_cfg = brands.get(brand_key, {})
        if not brand_cfg:
            _log(f"❌ Không tìm thấy brand '{brand_key}' trong brands.json")
            return False

        changed   = False
        now_ts    = int(time.time())
        threshold = 7 * 24 * 3600   # Gia hạn nếu còn dưới 7 ngày

        # Gom các (platform, token_key, id_key) cần kiểm tra
        checks = []
        if "instagram" in platforms or "threads" in platforms:
            ig_cfg = brand_cfg.get("instagram", {})
            if ig_cfg.get("access_token"):
                checks.append(("instagram", ig_cfg["access_token"], ig_cfg.get("ig_user_id", "")))
        if "facebook" in platforms:
            fb_cfg = brand_cfg.get("facebook", {})
            if fb_cfg.get("access_token"):
                checks.append(("facebook", fb_cfg["access_token"], fb_cfg.get("page_id", "")))

        for plat, token, entity_id in checks:
            _log(f"🔍 Kiểm tra token {plat} cho kênh {brand_key}...")
            info = _check_token_valid(token)

            need_refresh = False
            if not info["valid"]:
                _log(f"  ❌ Token {plat} KHÔNG HỢP LỆ — cần gia hạn ngay!")
                need_refresh = True
            elif info["expires_at"] > 0 and (info["expires_at"] - now_ts) < threshold:
                days_left = (info["expires_at"] - now_ts) // 86400
                _log(f"  ⚠️ Token {plat} còn {days_left} ngày — gia hạn trước khi hết!")
                need_refresh = True
            else:
                expires_str = (
                    datetime.datetime.fromtimestamp(info["expires_at"]).strftime("%d/%m/%Y")
                    if info["expires_at"] > 0 else "Không hết hạn"
                )
                _log(f"  ✅ Token {plat} còn hợp lệ (hết hạn: {expires_str})")

            if need_refresh:
                page_id   = brand_cfg.get("facebook", {}).get("page_id", "")
                new_token = _exchange_long_lived_token(token, page_id=page_id)
                if new_token:
                    _log(f"  ✅ Đã gia hạn token {plat} cho kênh {brand_key} thành công!")
                    # Cập nhật token cho instagram, facebook, và threads (dùng chung)
                    for p in ["instagram", "facebook", "threads"]:
                        if p in brand_cfg and "access_token" in brand_cfg[p]:
                            brands[brand_key][p]["access_token"] = new_token
                    changed = True
                else:
                    _log(f"  ❌ Không thể gia hạn token {plat}. Tiếp tục với token hiện tại.")
                    # Vẫn trả True để không block upload — sẽ thấy lỗi chi tiết ở uploader
                    return True

        if changed:
            _save_brands(brands)
            _log(f"💾 Đã cập nhật brands.json với token mới cho kênh {brand_key}")

        return True

    except Exception as e:
        _log(f"❌ Lỗi token_refresher: {e}")
        return True   # Không block upload dù lỗi refresh — uploader sẽ log chi tiết
