# -*- coding: utf-8 -*-
"""
Script quét toàn bộ video YouTube của các kênh, kiểm tra description:
Nếu video chưa có link sản phẩm trong description, script sẽ lấy link từ comment
và update vào description của video.
"""
import os
import sys
import json
import re
import time
import argparse
from typing import Dict, List, Any, Optional

# Override print to always flush immediately for real-time progress logging
_orig_print = print
def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    return _orig_print(*args, **kwargs)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRANDS_FILE = os.path.join(BASE_DIR, "config", "brands.json")
PROGRESS_FILE = os.path.join(BASE_DIR, "config", "yt_desc_update_status.json")

def load_brands() -> Dict[str, Any]:
    with open(BRANDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_youtube_service(token_file: str):
    token_path = os.path.join(BASE_DIR, token_file) if not os.path.isabs(token_file) else token_file
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"Không tìm thấy file token: {token_path}")
    
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print(f"🔄 Đang làm mới access token cho {os.path.basename(token_path)}...")
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as tf:
                tf.write(creds.to_json())
        else:
            raise ValueError(f"Token không hợp lệ hoặc đã hết hạn: {token_path}")
    
    return build("youtube", "v3", credentials=creds)

def fetch_all_channel_videos(youtube, uploads_playlist_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách tất cả video từ playlist uploads của kênh"""
    videos = []
    next_page = None
    while True:
        res = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page
        ).execute()

        for item in res.get("items", []):
            snippet = item.get("snippet", {})
            vid = snippet.get("resourceId", {}).get("videoId")
            if vid:
                videos.append({
                    "id": vid,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "publishedAt": snippet.get("publishedAt", "")
                })

        next_page = res.get("nextPageToken")
        if not next_page:
            break

    return videos

def extract_product_links_from_comments(youtube, video_id: str) -> List[str]:
    """
    Quét comment của video để lấy link sản phẩm.
    Ưu tiên lấy cả câu comment chứa link (ví dụ: Link sản phẩm ở đây: https://...)
    Loại bỏ link/câu trùng lặp.
    """
    try:
        res = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=50
        ).execute()
    except Exception as e:
        # Nếu video tắt bình luận hoặc lỗi query
        return []

    comment_blocks = []
    seen_urls = set()

    for item in res.get("items", []):
        top_snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        text = (top_snippet.get("textOriginal") or top_snippet.get("textDisplay") or "").strip()
        if not text:
            continue

        # Tìm các URLs trong comment
        urls = re.findall(r'https?://[^\s<>"]+', text)
        if not urls:
            continue

        # Kiểm tra xem có URL sản phẩm nào chưa được thêm
        has_new_url = False
        for u in urls:
            u_clean = u.rstrip("/?#&").lower()
            if u_clean not in seen_urls:
                seen_urls.add(u_clean)
                has_new_url = True

        if has_new_url:
            # Lưu lại nguyên văn dòng comment chứa link
            comment_blocks.append(text)

    return comment_blocks

def reformat_description_links(desc: str) -> Optional[str]:
    """
    Kiểm tra và chuẩn hóa lại phần link sản phẩm trong description để các dòng cách nhau thoáng đãng.
    Trả về description mới nếu cần sửa đổi, hoặc None nếu đã chuẩn.
    """
    if not desc or "🛒 MUA SẢN PHẨM TẠI ĐÂY:" not in desc:
        return None

    parts = desc.split("🛒 MUA SẢN PHẨM TẠI ĐÂY:")
    main_desc = parts[0].strip()
    links_section = parts[1].strip()

    urls = re.findall(r'https?://[^\s<>"]+', links_section)
    if not urls:
        return None

    raw_lines = [l.strip() for l in links_section.split("\n") if l.strip()]

    items = []
    seen_urls = set()
    current_prefix = []

    for line in raw_lines:
        line_urls = re.findall(r'https?://[^\s<>"]+', line)
        if line_urls:
            u = line_urls[0]
            u_clean = u.rstrip("/?#&").lower()
            if u_clean not in seen_urls:
                seen_urls.add(u_clean)
                prefix_in_line = line.replace(u, "").strip()
                if prefix_in_line:
                    current_prefix.append(prefix_in_line)
                p_text = " ".join(current_prefix).strip()
                if p_text:
                    items.append(f"{p_text}\n{u}")
                else:
                    items.append(u)
            current_prefix = []
        else:
            current_prefix.append(line)

    if not items:
        return None

    formatted_block = "\n\n".join(items)
    new_desc = f"{main_desc}\n\n🛒 MUA SẢN PHẨM TẠI ĐÂY:\n\n{formatted_block}".strip()

    # Kiểm tra xem có khác gì so với mô tả hiện tại không
    if new_desc == desc.strip():
        return None
    return new_desc

def format_product_links_clean(comment_links: List[str]) -> str:
    """Định dạng danh sách link comment thành các khối cách dòng thoáng mắt"""
    formatted_items = []
    seen_urls = set()
    for text in comment_links:
        urls = re.findall(r'https?://[^\s<>"]+', text)
        if not urls:
            continue
        u = urls[0]
        u_clean = u.rstrip("/?#&").lower()
        if u_clean in seen_urls:
            continue
        seen_urls.add(u_clean)
        prefix = text.replace(u, "").strip()
        if prefix:
            formatted_items.append(f"{prefix}\n{u}")
        else:
            formatted_items.append(u)
    return "\n\n".join(formatted_items)

def has_product_link_in_desc(desc: str) -> bool:
    """Kiểm tra xem mô tả đã có link sản phẩm chưa"""
    if not desc:
        return False
    desc_lower = desc.lower()
    return "shopee.vn" in desc_lower or "s.shopee.vn" in desc_lower

def update_video_description(youtube, video_id: str, new_description: str, snippet_details: Dict[str, Any]) -> bool:
    """Gọi YouTube API để cập nhật description cho video"""
    body = {
        "id": video_id,
        "snippet": {
            "title": snippet_details.get("title", ""),
            "description": new_description,
            "categoryId": snippet_details.get("categoryId", "22"),
            "tags": snippet_details.get("tags", [])
        }
    }
    youtube.videos().update(part="snippet", body=body).execute()
    return True

def process_channel(
    bkey: str,
    bdata: Dict[str, Any],
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    ch_name = bdata.get("name", bkey)
    yt_cfg = bdata.get("youtube", {})
    token_file = yt_cfg.get("token_file", "")
    
    print(f"\n{'='*70}")
    print(f"🎬 KÊNH: {ch_name} (brand_key: {bkey})")
    print(f"{'='*70}")

    stats = {
        "channel_key": bkey,
        "channel_name": ch_name,
        "total_videos": 0,
        "already_has_link": 0,
        "updated": 0,
        "no_comment_link": 0,
        "errors": 0,
        "skipped": 0
    }

    try:
        youtube = get_youtube_service(token_file)
    except Exception as e:
        print(f"❌ Không thể kết nối YouTube API cho {ch_name}: {e}")
        stats["errors"] += 1
        return stats

    # Lấy uploads playlist ID
    try:
        ch_resp = youtube.channels().list(part="snippet,contentDetails", mine=True).execute()
        if not ch_resp.get("items"):
            print(f"❌ Không tìm thấy thông tin kênh cho token {token_file}")
            return stats
        uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        actual_title = ch_resp["items"][0]["snippet"]["title"]
        print(f"✅ Xác thực thành công: {actual_title} (Uploads ID: {uploads_id})")
    except Exception as e:
        print(f"❌ Lỗi khi lấy thông tin kênh: {e}")
        stats["errors"] += 1
        return stats

    # Quét tất cả video
    print(f"🔍 Đang quét toàn bộ video từ kênh...")
    try:
        all_videos = fetch_all_channel_videos(youtube, uploads_id)
        stats["total_videos"] = len(all_videos)
        print(f"📊 Tổng số video tìm thấy: {len(all_videos)}")
    except Exception as e:
        print(f"❌ Lỗi khi tải danh sách video: {e}")
        stats["errors"] += 1
        return stats

    count_processed = 0

    for idx, v in enumerate(all_videos, 1):
        if limit and count_processed >= limit:
            print(f"⏹️ Đã đạt giới hạn xử lý {limit} video cho kênh này.")
            break

        vid = v["id"]
        vtitle = v["title"]
        vdesc = v["description"]

        need_update = False
        new_desc = ""

        # Kiểm tra xem description đã có link sản phẩm chưa
        if has_product_link_in_desc(vdesc):
            # Kiểm tra xem link có bị dính sát vào nhau không
            spaced_desc = reformat_description_links(vdesc)
            if spaced_desc and spaced_desc != vdesc:
                print(f"\n  [{idx}/{len(all_videos)}] 🔄 CẦN CÁCH DÒNG LẠI CHO THOÁNG: {vtitle} (ID: {vid})")
                new_desc = spaced_desc
                need_update = True
            else:
                stats["already_has_link"] += 1
                print(f"  [{idx}/{len(all_videos)}] ⏩ ĐÃ CÓ LINK & CÁCH DÒNG CHUẨN: {vtitle[:40]}... (ID: {vid})")
                continue
        else:
            print(f"\n  [{idx}/{len(all_videos)}] 🔍 CẦN BỔ SUNG LINK: {vtitle} (ID: {vid})")
            print(f"     Mô tả hiện tại: {vdesc.replace(chr(10), ' ')[:70]}...")

            # Tìm link trong comment
            time.sleep(0.3)
            comment_links = extract_product_links_from_comments(youtube, vid)

            if not comment_links:
                stats["no_comment_link"] += 1
                print(f"     ⚠️ Không tìm thấy link trong bình luận!")
                continue

            links_block = format_product_links_clean(comment_links)
            if not links_block:
                stats["no_comment_link"] += 1
                print(f"     ⚠️ Không tách được URL hợp lệ trong bình luận!")
                continue

            print(f"     💬 Tìm thấy {len(comment_links)} link trong bình luận (đã format cách dòng)")
            new_desc = f"{vdesc}\n\n🛒 MUA SẢN PHẨM TẠI ĐÂY:\n\n{links_block}".strip()
            need_update = True

        if dry_run:
            print(f"     [DRY-RUN] Sẽ cập nhật mô tả thành:\n{new_desc}")
            stats["updated"] += 1
            count_processed += 1
            continue

        # Cần lấy categoryId và tags đầy đủ của video để update không bị mất
        try:
            v_detail = youtube.videos().list(part="snippet", id=vid).execute()
            if not v_detail.get("items"):
                print(f"     ❌ Không lấy được chi tiết video {vid}")
                stats["errors"] += 1
                continue

            full_snippet = v_detail["items"][0]["snippet"]
            
            # Thực hiện update
            time.sleep(0.5)
            update_video_description(youtube, vid, new_desc, full_snippet)
            stats["updated"] += 1
            count_processed += 1
            print(f"     ✅ ĐÃ CẬP NHẬT DESCRIPTION THÀNH CÔNG!")
        except HttpError as he:
            if "quotaExceeded" in str(he):
                print(f"\n🚨 HẾT QUOTA YOUTUBE API TRONG NGÀY (403 quotaExceeded)!")
                print(f"Tài khoản Google Cloud đã dùng hết hạn mức 10,000 quota/ngày.")
                stats["errors"] += 1
                raise he
            else:
                print(f"     ❌ Lỗi HttpError khi update video {vid}: {he}")
                stats["errors"] += 1
        except Exception as e:
            print(f"     ❌ Lỗi khi update video {vid}: {e}")
            stats["errors"] += 1

    return stats

def main():
    parser = argparse.ArgumentParser(description="Quét video YouTube và cập nhật link sản phẩm từ comment vào description")
    parser.add_argument("--channel", default="all", help="Brand key (ví dụ: dung_roi_moi_noi, setup_phong_xinh) hoặc 'all'")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm không ghi dữ liệu thật lên YouTube")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số video cập nhật mỗi kênh")
    args = parser.parse_args()

    brands = load_brands()

    if args.channel != "all":
        if args.channel not in brands:
            print(f"❌ Không tìm thấy brand key '{args.channel}'. Các brand hợp lệ: {list(brands.keys())}")
            sys.exit(1)
        target_brands = {args.channel: brands[args.channel]}
    else:
        # Bỏ qua kênh bị suspend (noi_that_dung_that)
        target_brands = {k: v for k, v in brands.items() if k != "noi_that_dung_that"}

    print("="*70)
    print("🚀 BẮT ĐẦU QUÉT VÀ CẬP NHẬT LINK VÀO DESCRIPTION CHO YOUTUBE")
    print(f"- Số kênh xử lý: {len(target_brands)}")
    print(f"- Chế độ: {'DRY-RUN (Thử nghiệm)' if args.dry_run else 'GHI THẬT (Live Update)'}")
    if args.limit:
        print(f"- Giới hạn mỗi kênh: {args.limit} video")
    print("="*70)

    overall_stats = []

    try:
        for bkey, bdata in target_brands.items():
            stats = process_channel(bkey, bdata, dry_run=args.dry_run, limit=args.limit)
            overall_stats.append(stats)
            # Tự động lưu tiến độ sau mỗi kênh
            try:
                with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "details": overall_stats
                    }, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
    except HttpError as he:
        if "quotaExceeded" in str(he):
            print("\n🚨 TẠM DỪNG: Đã đạt hạn mức Quota API của Google Cloud trong ngày.")
            print("Toàn bộ tiến độ đã được lưu an toàn. Bạn có thể chạy lại script vào ngày mai để tiếp tục.")
    except KeyboardInterrupt:
        print("\n⏹️ Người dùng đã tạm dừng tiến trình.")

    # In báo cáo tổng kết
    print("\n" + "="*70)
    print("📊 BÁO CÁO TỔNG KẾT QUÉT VÀ CẬP NHẬT DESCRIPTION YOUTUBE")
    print("="*70)
    total_vids = sum(s["total_videos"] for s in overall_stats)
    total_had_link = sum(s["already_has_link"] for s in overall_stats)
    total_updated = sum(s["updated"] for s in overall_stats)
    total_no_comment = sum(s["no_comment_link"] for s in overall_stats)
    total_errors = sum(s["errors"] for s in overall_stats)

    for s in overall_stats:
        print(f"• {s['channel_name']}: Tổng {s['total_videos']} video | Đã có: {s['already_has_link']} | Cập nhật mới: {s['updated']} | Thiếu comment: {s['no_comment_link']} | Lỗi: {s['errors']}")

    print("-" * 70)
    print(f"👉 TỔNG CỘNG: {total_vids} video | Đã có sẵn link: {total_had_link} | Đã thêm link mới: {total_updated} | Không có comment: {total_no_comment} | Lỗi: {total_errors}")
    print("="*70)

    # Lưu kết quả
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "overall": {
                    "total_videos": total_vids,
                    "already_had_link": total_had_link,
                    "updated": total_updated,
                    "no_comment": total_no_comment,
                    "errors": total_errors
                },
                "details": overall_stats
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu báo cáo chi tiết vào: {PROGRESS_FILE}")
    except Exception as e:
        print(f"⚠️ Không thể lưu file báo cáo: {e}")

if __name__ == "__main__":
    main()
