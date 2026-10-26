# -*- coding: utf-8 -*-
import os
import sys
import time
import openpyxl

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import YouTubeShortsUploader

def load_template_sentences():
    comment_file = r"C:\Affiliate\post1\comment.txt"
    with open(comment_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines

def get_links_from_excel(excel_path):
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    links = []
    # Row 1 is header
    for row in list(sheet.iter_rows(values_only=True))[1:]:
        if row and len(row) >= 3 and row[2]:
            link = str(row[2]).strip()
            if link.startswith("http"):
                links.append(link)
    return links

def build_comments(links, templates):
    comments = []
    for idx, link in enumerate(links):
        prefix = templates[idx % len(templates)]
        if not prefix.endswith(" "):
            prefix += " "
        comments.append(f"{prefix}{link}")
    return comments

def fix_youtube_comments(channel_name, token_file, video_id, excel_path):
    print(f"\n======================================================================")
    print(f"🔧 ĐANG SỬA COMMENT YOUTUBE CHO KÊNH: {channel_name}")
    print(f"📹 Video ID: {video_id} (https://youtube.com/shorts/{video_id})")
    print(f"📁 Nguồn Link Excel: {excel_path}")
    print(f"======================================================================")

    templates = load_template_sentences()
    correct_links = get_links_from_excel(excel_path)
    print(f"✅ Đã đọc {len(correct_links)} link chuẩn từ Excel:")
    for i, l in enumerate(correct_links, 1):
        print(f"  {i}. {l}")

    target_comments = build_comments(correct_links, templates)

    yt = YouTubeShortsUploader(token_file=token_file)
    if not yt.authenticate():
        print(f"❌ Không thể xác thực YouTube cho kênh {channel_name}")
        return

    # 1. Lấy toàn bộ comment cũ và xóa
    print("\n⏳ Đang quét và xóa các comment cũ bị sai...")
    res = yt.youtube.commentThreads().list(part="id,snippet", videoId=video_id).execute()
    old_items = res.get("items", [])
    print(f"👉 Tìm thấy {len(old_items)} comment cũ cần xóa.")

    for item in old_items:
        cid = item["id"]
        try:
            yt.youtube.comments().delete(id=cid).execute()
            print(f"  🗑️ Đã xóa comment cũ ID: {cid}")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ Lỗi khi xóa comment {cid}: {e}")

    # 2. Đăng lại dàn comment đúng 100%
    print(f"\n🚀 Đang đăng lại {len(target_comments)} comment chuẩn xác từ Excel...")
    for idx, c_text in enumerate(target_comments, 1):
        try:
            body = {
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": c_text
                        }
                    }
                }
            }
            res_c = yt.youtube.commentThreads().insert(part="snippet", body=body).execute()
            print(f"  ✅ Đã đăng comment mới {idx}: {c_text}")
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Lỗi khi đăng comment {idx}: {e}")

    print(f"🎉 HOÀN TẤT SỬA BÌNH LUẬN YOUTUBE CHO KÊNH {channel_name}!\n")

def main():
    # 1. Tủ Đồ Mùa Mới
    fix_youtube_comments(
        channel_name="Tủ Đồ Mùa Mới",
        token_file=r"C:\Affiliate\post1\POST\credentials\youtube_tokens\tu_do_mua_moi.json",
        video_id="s3TPE5XKdss",
        excel_path=r"C:\Affiliate\Tủ Đồ Mùa Mới\Link customed\YouTube\Tập 3.xlsx"
    )

    # 2. Góc Tập Luyện
    fix_youtube_comments(
        channel_name="Góc Tập Luyện",
        token_file=r"C:\Affiliate\post1\POST\credentials\youtube_tokens\goc_tap_luyen.json",
        video_id="IPf_o74lJXc",
        excel_path=r"C:\Affiliate\Góc Tập Luyện\Link customed\YouTube\Tập 3.xlsx"
    )

if __name__ == "__main__":
    main()
