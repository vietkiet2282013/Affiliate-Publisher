import json
import csv
import time
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

BRANDS_FILE = r"C:\Affiliate\post1\POST\config\brands.json"
CSV_PATH = r"C:\Affiliate\Setup Phòng Xinh\Link customed\Instagram\Tập 2.csv"
VIDEO_URL = "https://files.catbox.moe/n2fy5o.mp4"

with open(BRANDS_FILE, 'r', encoding='utf-8') as f:
    brands = json.load(f)

brand = brands["setup_phong_xinh"]
ig_user_id = brand["instagram"]["ig_user_id"]
access_token = brand["instagram"]["access_token"]

caption = """✨ SETUP PHÒNG XINH - TẬP 2 ✨
Gợi ý đồ trang trí & nội thất decor phòng ngủ cực đỉnh!
👉 Link mua sắm các sản phẩm bên dưới phần bình luận nhé cả nhà! 👇
#setupphongxinh #decorphongngu #noithat #shopeeaffiliate"""

print("==================================================")
print("📸 1. ĐĂNG INSTAGRAM REELS - SETUP PHÒNG XINH (TẬP 2)")
print("==================================================")

# Step 1: Create Container
container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
payload = {
    'media_type': 'REELS',
    'video_url': VIDEO_URL,
    'caption': caption,
    'access_token': access_token
}
res = requests.post(container_url, data=payload).json()
print("Container ID:", res)
if 'id' not in res:
    print("❌ Lỗi tạo container IG:", res)
    sys.exit(1)

container_id = res['id']

# Step 2: Poll Container Status
status_url = f"https://graph.facebook.com/v19.0/{container_id}"
for i in range(40):
    time.sleep(10)
    status_res = requests.get(status_url, params={'fields': 'status_code,status', 'access_token': access_token}).json()
    status = status_res.get('status_code')
    print(f"  Trạng thái IG ({i+1}/40): {status}")
    if status == 'FINISHED':
        break
    elif status == 'ERROR':
        print("❌ Lỗi xử lý video IG:", status_res)
        sys.exit(1)

# Step 3: Publish Container
publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
pub_res = requests.post(publish_url, data={'creation_id': container_id, 'access_token': access_token}).json()
print("Publish Result:", pub_res)
if 'id' not in pub_res:
    print("❌ Lỗi đăng Reels IG:", pub_res)
    sys.exit(1)

ig_media_id = pub_res['id']
print(f"🎉 ĐÃ ĐĂNG INSTAGRAM REEL THÀNH CÔNG! ID: {ig_media_id}")

# Step 4: Add Comments from CSV
print("\n📝 Thêm bình luận link Shopee Affiliate...")
comments = []
with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) >= 3 and row[1].strip() and row[2].strip():
            name = row[1].strip()
            link = row[2].strip()
            comments.append(f"{name}: {link}")

comment_url = f"https://graph.facebook.com/v19.0/{ig_media_id}/comments"
for idx, c_text in enumerate(comments, 1):
    c_res = requests.post(comment_url, data={'message': c_text, 'access_token': access_token}).json()
    c_id = c_res.get('id')
    print(f"  ✅ Comment IG {idx}: {c_id}")
    time.sleep(2)

print("\n🎉 HOÀN THÀNH TẤT CẢ TÁC VỤ CHO INSTAGRAM REELS SETUP PHÒNG XINH (TẬP 2)!")
