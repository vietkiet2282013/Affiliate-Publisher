import os
import json
import uuid
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

token_dir = r'c:\Affiliate\post1\POST\credentials\youtube_tokens'
brands_config_path = r'c:\Affiliate\post1\POST\config\brands.json'

with open(brands_config_path, 'r', encoding='utf-8') as f:
    brands_config = json.load(f)

brand_map = {
    'cham_cong_nghe': 'Trạm Công Nghệ',
    'cham_da_tiet_kiem': 'Chăm Da Tiết Kiệm',
    'dung_roi_moi_noi': 'Dùng Rồi Mới Nói',
    'goc_tap_luyen': 'Góc Tập Luyện',
    'noi_that_dung_that': 'Nội Thất Tiết Kiệm',
    'quan_ao_gia_hoi': 'Quần Áo Giá Hời',
    'review_that_viec_that': 'Review Thật Việc Thật',
    'setup_phong_xinh': 'Setup Phòng Xinh',
    'tu_do_mua_moi': 'Tủ Đồ Mùa Mới',
    'yeu_da_hon_bo': 'Yêu Da Hơn Bồ'
}

channels_data = []

for f in sorted(os.listdir(token_dir)):
    if f.endswith('.json'):
        b_key = f.replace('.json', '')
        p = os.path.join(token_dir, f)
        with open(p, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        creds = Credentials.from_authorized_user_info(data)
        if not creds.valid:
            creds.refresh(Request())
            data['token'] = creds.token
            with open(p, 'w', encoding='utf-8') as fh:
                json.dump(data, fh)
        
        channels_data.append({
            'key': b_key,
            'name': brand_map.get(b_key, b_key),
            'access_token': creds.token,
            'refresh_token': data.get('refresh_token'),
            'client_id': data.get('client_id'),
            'client_secret': data.get('client_secret')
        })

collection = {
    'info': {
        '_postman_id': str(uuid.uuid4()),
        'name': 'YouTube Upload API - 10 Kênh (Full Settings & cURL)',
        'description': 'Collection Postman đầy đủ cho 10 kênh YouTube:\n1. Tự động lấy / refresh Access Token.\n2. Đăng video ngay (Public).\n3. Hẹn giờ đăng video (Schedule / PublishAt).\n4. Đăng không công khai / Riêng tư (Unlisted / Private).\n5. Tải file binary vào Resumable Upload URL.',
        'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
    },
    'variable': [
        {'key': 'video_title', 'value': 'Setup Bàn Làm Việc Thông Minh Đẹp Mê Ly #shorts', 'type': 'string'},
        {'key': 'video_description', 'value': 'Khám phá ngay các món decor hot nhất trong video!\n👉 Link sản phẩm gắn dưới phần bình luận.\n#shorts #decor #review', 'type': 'string'},
        {'key': 'schedule_time_iso', 'value': '2026-10-01T19:00:00.000Z', 'type': 'string'}
    ],
    'item': []
}

for ch in channels_data:
    folder = {
        'name': f"{ch['name']} [{ch['key']}]",
        'item': [
            {
                'name': '1. Refresh Access Token (Tự lấy token mới khi hết hạn)',
                'request': {
                    'method': 'POST',
                    'header': [
                        {'key': 'Content-Type', 'value': 'application/x-www-form-urlencoded'}
                    ],
                    'body': {
                        'mode': 'urlencoded',
                        'urlencoded': [
                            {'key': 'client_id', 'value': ch['client_id'], 'type': 'text'},
                            {'key': 'client_secret', 'value': ch['client_secret'], 'type': 'text'},
                            {'key': 'refresh_token', 'value': ch['refresh_token'], 'type': 'text'},
                            {'key': 'grant_type', 'value': 'refresh_token', 'type': 'text'}
                        ]
                    },
                    'url': {
                        'raw': 'https://oauth2.googleapis.com/token',
                        'protocol': 'https',
                        'host': ['oauth2', 'googleapis', 'com'],
                        'path': ['token']
                    },
                    'description': 'API OAuth2 của Google: Gửi request này để lấy `access_token` mới nhất (có hiệu lực 1 giờ) bất cứ lúc nào.'
                }
            },
            {
                'name': '2. Đăng Ngay (Public) - Bước 1: Khởi Tạo Metadata',
                'request': {
                    'method': 'POST',
                    'header': [
                        {'key': 'Authorization', 'value': f"Bearer {ch['access_token']}"},
                        {'key': 'Content-Type', 'value': 'application/json; charset=UTF-8'},
                        {'key': 'X-Upload-Content-Type', 'value': 'video/*'}
                    ],
                    'body': {
                        'mode': 'raw',
                        'raw': json.dumps({
                            "snippet": {
                                "title": "{{video_title}}",
                                "description": "{{video_description}}",
                                "tags": ["shorts", "review", "affiliate", "trending"],
                                "categoryId": "22",
                                "defaultLanguage": "vi",
                                "defaultAudioLanguage": "vi"
                            },
                            "status": {
                                "privacyStatus": "public",
                                "selfDeclaredMadeForKids": False,
                                "embeddable": True
                            }
                        }, indent=2)
                    },
                    'url': {
                        'raw': 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
                        'protocol': 'https',
                        'host': ['www', 'googleapis', 'com'],
                        'path': ['upload', 'youtube', 'v3', 'videos'],
                        'query': [
                            {'key': 'uploadType', 'value': 'resumable'},
                            {'key': 'part', 'value': 'snippet,status'}
                        ]
                    },
                    'description': 'Bước 1: Thiết lập tiêu đề, mô tả, thẻ tags, ngôn ngữ và chế độ công khai ngay (public). Khi gửi xong, copy URL từ Response Header `Location`.'
                }
            },
            {
                'name': '3. Hẹn Giờ Đăng (Schedule) - Bước 1: Khởi Tạo Metadata',
                'request': {
                    'method': 'POST',
                    'header': [
                        {'key': 'Authorization', 'value': f"Bearer {ch['access_token']}"},
                        {'key': 'Content-Type', 'value': 'application/json; charset=UTF-8'},
                        {'key': 'X-Upload-Content-Type', 'value': 'video/*'}
                    ],
                    'body': {
                        'mode': 'raw',
                        'raw': json.dumps({
                            "snippet": {
                                "title": "{{video_title}}",
                                "description": "{{video_description}}",
                                "tags": ["shorts", "review", "affiliate", "trending"],
                                "categoryId": "22",
                                "defaultLanguage": "vi",
                                "defaultAudioLanguage": "vi"
                            },
                            "status": {
                                "privacyStatus": "private",
                                "publishAt": "{{schedule_time_iso}}",
                                "selfDeclaredMadeForKids": False,
                                "embeddable": True
                            }
                        }, indent=2)
                    },
                    'url': {
                        'raw': 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
                        'protocol': 'https',
                        'host': ['www', 'googleapis', 'com'],
                        'path': ['upload', 'youtube', 'v3', 'videos'],
                        'query': [
                            {'key': 'uploadType', 'value': 'resumable'},
                            {'key': 'part', 'value': 'snippet,status'}
                        ]
                    },
                    'description': 'Bước 1 hẹn giờ: Bắt buộc `privacyStatus`: `private` và thêm trường `publishAt` (chuẩn ISO-8601 UTC ví dụ: 2026-10-01T19:00:00.000Z).'
                }
            },
            {
                'name': '4. Không Công Khai (Unlisted) - Bước 1: Khởi Tạo Metadata',
                'request': {
                    'method': 'POST',
                    'header': [
                        {'key': 'Authorization', 'value': f"Bearer {ch['access_token']}"},
                        {'key': 'Content-Type', 'value': 'application/json; charset=UTF-8'},
                        {'key': 'X-Upload-Content-Type', 'value': 'video/*'}
                    ],
                    'body': {
                        'mode': 'raw',
                        'raw': json.dumps({
                            "snippet": {
                                "title": "{{video_title}}",
                                "description": "{{video_description}}",
                                "tags": ["shorts", "review"],
                                "categoryId": "22",
                                "defaultLanguage": "vi"
                            },
                            "status": {
                                "privacyStatus": "unlisted",
                                "selfDeclaredMadeForKids": False
                            }
                        }, indent=2)
                    },
                    'url': {
                        'raw': 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
                        'protocol': 'https',
                        'host': ['www', 'googleapis', 'com'],
                        'path': ['upload', 'youtube', 'v3', 'videos'],
                        'query': [
                            {'key': 'uploadType', 'value': 'resumable'},
                            {'key': 'part', 'value': 'snippet,status'}
                        ]
                    },
                    'description': 'Chế độ Không công khai (Unlisted): Chỉ những ai có link mới xem được video.'
                }
            },
            {
                'name': '5. Bước 2: Tải Video Vào Resumable Session (PUT Binary File)',
                'request': {
                    'method': 'PUT',
                    'header': [
                        {'key': 'Content-Type', 'value': 'video/mp4'}
                    ],
                    'body': {
                        'mode': 'file',
                        'file': {'src': ''}
                    },
                    'url': {
                        'raw': 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&upload_id=DÁN_UPLOAD_ID_HOẶC_LINK_LOCATION_TẠI_ĐÂY',
                        'protocol': 'https',
                        'host': ['www', 'googleapis', 'com'],
                        'path': ['upload', 'youtube', 'v3', 'videos']
                    },
                    'description': 'Thay thế URL trên bằng chính xác link nhận được từ Header `Location` ở Bước 1. Vào Body -> Binary/File -> Chọn file MP4 từ máy tính -> Nhấn Send để tải video lên.'
                }
            }
        ]
    }
    collection['item'].append(folder)

out_file = r'c:\Affiliate\post1\YouTube_10_Channels_Postman_Collection.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(collection, f, ensure_ascii=False, indent=2)

print('Successfully exported:', out_file)
