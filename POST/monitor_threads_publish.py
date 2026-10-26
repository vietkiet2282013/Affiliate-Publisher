# -*- coding: utf-8 -*-
import sys
import time
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

token = 'THAAXS7Ru2STVBYmFOTU1CaWxfQ0lOLUVoT2RlaFl2WDNMR1lvN0ZATTlhzRldsSHRZAR1dNN3FoeUh5UFI0NE5JMXN6ejBxNE9hTTFsS0c3YV9YODZAHMWdLd2F5ZAE5aZA1F5bXppXzJVdnA4ZAVFQa3dYSEhtU3hiTF90OVJlZAmZAaNE45aUNsWEEyLW9fbzNTMEUZD'
user_id = '28151207317907080'
container_id = '18103005368143548'

print(f"Đang theo dõi container {container_id}...")
for i in range(40):
    time.sleep(5)
    r = requests.get(f'https://graph.threads.net/v1.0/{container_id}', params={'fields': 'status,error_message', 'access_token': token}).json()
    st = r.get('status')
    print(f"[{i+1}/40] Trạng thái: {st}")
    if st == 'FINISHED':
        print("✅ Container FINISHED! Đang xuất bản video lên Threads...")
        p_res = requests.post(f'https://graph.threads.net/v1.0/{user_id}/threads_publish', data={'creation_id': container_id, 'access_token': token}).json()
        print('Kết quả xuất bản:', p_res)
        if 'id' in p_res:
            post_id = p_res['id']
            post_url = f"https://www.threads.net/@setupphongxinh/post/{post_id}"
            print(f"🎉 LINK THREADS: {post_url}")
            
            # Đọc danh sách link để comment
            links_file = r'C:\Affiliate\Setup Phòng Xinh\Link customed\Threads\Tập 1_copy_nhanh.txt'
            with open(links_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [l.strip() for l in f if l.strip().startswith('http')]
            
            print(f"💬 Bắt đầu đăng {len(lines)} bình luận link riêng biệt...")
            for idx, link in enumerate(lines):
                c_payload = {
                    'media_type': 'TEXT',
                    'text': f'Món {idx+1}: {link}',
                    'reply_to_id': post_id,
                    'access_token': token
                }
                c_res = requests.post(f'https://graph.threads.net/v1.0/{user_id}/threads', data=c_payload).json()
                if 'id' in c_res:
                    requests.post(f'https://graph.threads.net/v1.0/{user_id}/threads_publish', data={'creation_id': c_res['id'], 'access_token': token})
                    print(f"   -> Đã reply món {idx+1}/{len(lines)}")
                time.sleep(1.5)
            print("DONE!")
        break
    elif st == 'ERROR':
        print('❌ Lỗi:', r)
        break
