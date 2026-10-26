import os
import json
import uuid
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

token_dir = r'c:\Affiliate\post1\POST\credentials\youtube_tokens'
brands_config_path = r'c:\Affiliate\post1\POST\config\brands.json'

with open(brands_config_path, 'r', encoding='utf-8') as f:
    brands_config = json.load(f)

# Refresh YouTube tokens and collect them
yt_tokens = {}
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
        yt_tokens[b_key] = {
            'access_token': creds.token,
            'refresh_token': data.get('refresh_token'),
            'client_id': data.get('client_id'),
            'client_secret': data.get('client_secret')
        }

user_token_sample = "EAAmD979AfWEBShSvyQTvXLgYT139wgqoQyxzgtgaShnL8KVovJxWPOioH2CyRZAu9qcvrZASTVHxhAiK9ZBYfeJLRZCHZCd4HSOgx8NZC4aqOeYacE3TfQVT4eNjJ06pofznj9JXqTTQv7NjIwZCyJ8EYYR8fyPxsqB6nHXF6HwAiAmPeEosgI6zxSWiZBY0WSKqPXNMtB78MidpyNVWKjOsIkbWFWi6Ff67wRXJgMbYKJCO9z2ccsR9Mcw7jBVbjtPF5Lc6BAod5uYkW9YKMOgY"

collection = {
    'info': {
        '_postman_id': str(uuid.uuid4()),
        'name': 'Affiliate Multi-Platform (YouTube, Facebook, Instagram, Threads) - 10 Brands',
        'description': (
            'Bộ sưu tập Postman đầy đủ cho 10 Brand trên 4 nền tảng (YouTube, Facebook Reels, Instagram Reels, Threads):\n\n'
            '🔑 QUẢN LÝ TOKEN:\n'
            '- Meta (Facebook & Instagram): Dùng Page Access Token riêng biệt được gán sẵn cho từng kênh (đã lấy từ User Token mới nhất).\n'
            '- Có sẵn thư mục "⚡ META TOKEN UTILITIES" để bạn chỉ cần dán User Token mới từ Graph Explorer vào biến `user_access_token` và bấm Send là tự động xem được toàn bộ token của 10 trang!\n'
            '- YouTube: Có sẵn API "Refresh Access Token" cho từng kênh để tự động gia hạn token vĩnh viễn mà không bao giờ cần đăng nhập lại.\n'
        ),
        'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
    },
    'variable': [
        {'key': 'user_access_token', 'value': user_token_sample, 'type': 'string'},
        {'key': 'video_title', 'value': 'Setup Bàn Làm Việc Thông Minh Đẹp Mê Ly #shorts', 'type': 'string'},
        {'key': 'video_caption', 'value': 'Khám phá ngay các món đồ decor hot nhất trong video!\n👉 Link sản phẩm gắn dưới phần bình luận.\n#shorts #decor #review', 'type': 'string'},
        {'key': 'affiliate_comment_1', 'value': 'Mọi người xem và mua sản phẩm 1 tại đây nhé: https://s.shopee.vn/sample1', 'type': 'string'},
        {'key': 'affiliate_comment_2', 'value': 'Sản phẩm 2 chính hãng bảo hành 12 tháng tại: https://s.shopee.vn/sample2', 'type': 'string'},
        {'key': 'fb_schedule_unix_timestamp', 'value': '1790856000', 'type': 'string'},
        {'key': 'yt_schedule_iso_utc', 'value': '2026-10-01T19:00:00.000Z', 'type': 'string'},
        {'key': 'direct_video_cdn_url', 'value': 'https://files.catbox.moe/example.mp4', 'type': 'string'}
    ],
    'item': []
}

# 1. Thư mục công cụ lấy Page Token tự động từ User Token
util_folder = {
    'name': '⚡ META TOKEN UTILITIES (Lấy & Gia Hạn Token Facebook/IG)',
    'item': [
        {
            'name': '1. Lấy Toàn Bộ Page Tokens Từ User Access Token (me/accounts)',
            'request': {
                'method': 'GET',
                'header': [],
                'url': {
                    'raw': 'https://graph.facebook.com/v19.0/me/accounts?fields=id,name,access_token,instagram_business_account&limit=50&access_token={{user_access_token}}',
                    'protocol': 'https',
                    'host': ['graph', 'facebook', 'com'],
                    'path': ['v19.0', 'me', 'accounts'],
                    'query': [
                        {'key': 'fields', 'value': 'id,name,access_token,instagram_business_account'},
                        {'key': 'limit', 'value': '50'},
                        {'key': 'access_token', 'value': '{{user_access_token}}'}
                    ]
                },
                'description': 'Khi bạn gen User Token mới từ Graph Explorer, chỉ cần dán vào biến `user_access_token` và gửi request này. Postman sẽ trả về toàn bộ 10 Page Token tương ứng cho 10 trang của bạn.'
            }
        },
        {
            'name': '2. Đổi User Token Ngắn Hạn Sang Token Dài Hạn (60 Ngày)',
            'request': {
                'method': 'GET',
                'header': [],
                'url': {
                    'raw': 'https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id={{fb_app_id}}&client_secret={{fb_app_secret}}&fb_exchange_token={{user_access_token}}',
                    'protocol': 'https',
                    'host': ['graph', 'facebook', 'com'],
                    'path': ['v19.0', 'oauth', 'access_token'],
                    'query': [
                        {'key': 'grant_type', 'value': 'fb_exchange_token'},
                        {'key': 'client_id', 'value': '{{fb_app_id}}'},
                        {'key': 'client_secret', 'value': '{{fb_app_secret}}'},
                        {'key': 'fb_exchange_token', 'value': '{{user_access_token}}'}
                    ]
                },
                'description': 'Đổi token ngắn hạn (1-2 tiếng từ Explorer) thành token dài hạn 60 ngày. Nhờ đó các Page Token lấy ra từ nó sẽ là VĨNH VIỄN (Never Expire)!'
            }
        }
    ]
}
collection['item'].append(util_folder)

# 2. Các kênh
for b_key, b_info in brands_config.items():
    brand_name = b_info.get('name', b_key)
    fb_data = b_info.get('facebook', {})
    ig_data = b_info.get('instagram', {})
    th_data = b_info.get('threads', {})
    yt_data = yt_tokens.get(b_key, {})

    brand_folder = {
        'name': f"{brand_name} [{b_key}]",
        'item': []
    }

    # ==================== FACEBOOK ====================
    if fb_data:
        fb_page_id = fb_data.get('page_id', '')
        fb_page_token = fb_data.get('access_token', '')

        fb_folder = {
            'name': 'Facebook Reels',
            'item': [
                {
                    'name': '0. [Gia Hạn] Lấy Page Token Riêng Của Trang Này',
                    'request': {
                        'method': 'GET',
                        'header': [],
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{fb_page_id}?fields=id,name,access_token&access_token={{{{user_access_token}}}}",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', str(fb_page_id)],
                            'query': [
                                {'key': 'fields', 'value': 'id,name,access_token'},
                                {'key': 'access_token', 'value': '{{user_access_token}}'}
                            ]
                        },
                        'description': f"Gọi API này để lấy Page Token mới nhất của trang {brand_name} bằng User Token."
                    }
                },
                {
                    'name': '1. Đăng Ngay (Public) - Khởi tạo phiên Reels',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'upload_phase', 'value': 'start', 'type': 'text'},
                                {'key': 'access_token', 'value': fb_page_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{fb_page_id}/video_reels",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', str(fb_page_id), 'video_reels']
                        },
                        'description': 'Bước 1: Khởi tạo upload Reel. Kết quả trả về `video_id` và `upload_url`.'
                    }
                },
                {
                    'name': '2. Đăng Ngay (Public) - Hoàn tất & Xuất bản Reel',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'upload_phase', 'value': 'finish', 'type': 'text'},
                                {'key': 'access_token', 'value': fb_page_token, 'type': 'text'},
                                {'key': 'video_id', 'value': '{{fb_video_id_from_step_1}}', 'type': 'text'},
                                {'key': 'video_state', 'value': 'PUBLISHED', 'type': 'text'},
                                {'key': 'title', 'value': '{{video_title}}', 'type': 'text'},
                                {'key': 'description', 'value': '{{video_caption}}', 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{fb_page_id}/video_reels",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', str(fb_page_id), 'video_reels']
                        },
                        'description': 'Bước 3 (sau khi PUT file vào upload_url): Xuất bản bài viết ngay lập tức.'
                    }
                },
                {
                    'name': '3. Hẹn Giờ Đăng (Schedule) - Hoàn tất & Đặt lịch hẹn',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'upload_phase', 'value': 'finish', 'type': 'text'},
                                {'key': 'access_token', 'value': fb_page_token, 'type': 'text'},
                                {'key': 'video_id', 'value': '{{fb_video_id_from_step_1}}', 'type': 'text'},
                                {'key': 'video_state', 'value': 'SCHEDULED', 'type': 'text'},
                                {'key': 'scheduled_publish_time', 'value': '{{fb_schedule_unix_timestamp}}', 'type': 'text'},
                                {'key': 'title', 'value': '{{video_title}}', 'type': 'text'},
                                {'key': 'description', 'value': '{{video_caption}}', 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{fb_page_id}/video_reels",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', str(fb_page_id), 'video_reels']
                        },
                        'description': 'Bước 3 (Hẹn giờ): Đặt `video_state` = `SCHEDULED` và `scheduled_publish_time` = timestamp (giây). Thời gian hẹn từ 10 phút đến 75 ngày trong tương lai.'
                    }
                },
                {
                    'name': '4. Tải file Binary vào Upload URL (PUT Binary)',
                    'request': {
                        'method': 'POST',
                        'header': [
                            {'key': 'Authorization', 'value': f"OAuth {fb_page_token}"},
                            {'key': 'offset', 'value': '0'},
                            {'key': 'file_size', 'value': '10485760'},
                            {'key': 'Content-Type', 'value': 'application/octet-stream'}
                        ],
                        'body': {
                            'mode': 'file',
                            'file': {'src': ''}
                        },
                        'url': {
                            'raw': '{{fb_upload_url_from_step_1}}',
                            'host': ['{{fb_upload_url_from_step_1}}']
                        },
                        'description': 'Bước 2: Gửi dữ liệu video nhị phân (binary) lên `upload_url` do Facebook cấp.'
                    }
                },
                {
                    'name': '5. Bình Luận Link Affiliate Vào Video Reel',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'message', 'value': '{{affiliate_comment_1}}', 'type': 'text'},
                                {'key': 'access_token', 'value': fb_page_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': 'https://graph.facebook.com/v19.0/{{fb_video_id}}/comments',
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', '{{fb_video_id}}', 'comments']
                        },
                        'description': 'Thêm bình luận chứa link Affiliate vào Reel. Thay `{{fb_video_id}}` bằng ID video.'
                    }
                }
            ]
        }
        brand_folder['item'].append(fb_folder)

    # ==================== INSTAGRAM ====================
    if ig_data:
        ig_user_id = ig_data.get('ig_user_id', '')
        ig_token = ig_data.get('access_token', '')

        ig_folder = {
            'name': 'Instagram Reels',
            'item': [
                {
                    'name': '1. Khởi Tạo Container Reels (Resumable)',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'media_type', 'value': 'REELS', 'type': 'text'},
                                {'key': 'upload_type', 'value': 'resumable', 'type': 'text'},
                                {'key': 'caption', 'value': '{{video_caption}}', 'type': 'text'},
                                {'key': 'access_token', 'value': ig_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', str(ig_user_id), 'media']
                        },
                        'description': 'Khởi tạo container tải lên cho Instagram Reel. Nhận về container `id` và `uri` upload.'
                    }
                },
                {
                    'name': '2. Tải File Video Binary Vào URI',
                    'request': {
                        'method': 'POST',
                        'header': [
                            {'key': 'Authorization', 'value': f"OAuth {ig_token}"},
                            {'key': 'offset', 'value': '0'},
                            {'key': 'file_size', 'value': '10485760'},
                            {'key': 'Content-Type', 'value': 'application/octet-stream'}
                        ],
                        'body': {
                            'mode': 'file',
                            'file': {'src': ''}
                        },
                        'url': {
                            'raw': '{{ig_upload_uri_from_step_1}}',
                            'host': ['{{ig_upload_uri_from_step_1}}']
                        },
                        'description': 'Tải dữ liệu video nhị phân (binary) lên `uri` nhận được ở Bước 1.'
                    }
                },
                {
                    'name': '3. Kiểm Tra Trạng Thái Container (Status FINISHED)',
                    'request': {
                        'method': 'GET',
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{{{{ig_container_id}}}}?fields=status_code,status&access_token={ig_token}",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', '{{ig_container_id}}'],
                            'query': [
                                {'key': 'fields', 'value': 'status_code,status'},
                                {'key': 'access_token', 'value': ig_token}
                            ]
                        },
                        'description': 'Kiểm tra container xử lý video xong chưa. Khi nào status_code = "FINISHED" mới chuyển sang Bước 4.'
                    }
                },
                {
                    'name': '4. Xuất Bản Instagram Reel',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'creation_id', 'value': '{{ig_container_id}}', 'type': 'text'},
                                {'key': 'access_token', 'value': ig_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', str(ig_user_id), 'media_publish']
                        },
                        'description': 'Xuất bản video lên Instagram. Kết quả trả về `id` (Media ID).'
                    }
                },
                {
                    'name': '5. Bình Luận Link Affiliate Vào Instagram Reel',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'message', 'value': '{{affiliate_comment_1}}', 'type': 'text'},
                                {'key': 'access_token', 'value': ig_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.facebook.com/v19.0/{{ig_media_id}}/comments",
                            'protocol': 'https',
                            'host': ['graph', 'facebook', 'com'],
                            'path': ['v19.0', '{{ig_media_id}}', 'comments']
                        },
                        'description': 'Thêm comment chứa link sản phẩm vào bài Reel trên Instagram. Thay `{{ig_media_id}}` bằng ID video xuất bản thành công.'
                    }
                }
            ]
        }
        brand_folder['item'].append(ig_folder)

    # ==================== THREADS ====================
    if th_data:
        th_token = th_data.get('access_token', '')
        th_user_id = th_data.get('user_id', '')

        th_folder = {
            'name': 'Threads Video',
            'item': [
                {
                    'name': '1. Tạo Media Container Video',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'media_type', 'value': 'VIDEO', 'type': 'text'},
                                {'key': 'video_url', 'value': '{{direct_video_cdn_url}}', 'type': 'text'},
                                {'key': 'text', 'value': '{{video_caption}}', 'type': 'text'},
                                {'key': 'access_token', 'value': th_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.threads.net/v1.0/{th_user_id}/threads",
                            'protocol': 'https',
                            'host': ['graph', 'threads', 'net'],
                            'path': ['v1.0', str(th_user_id), 'threads']
                        },
                        'description': 'Khởi tạo container bài đăng Threads kèm video URL (link trực tiếp từ Catbox/CDN). Kết quả trả về `id` container.'
                    }
                },
                {
                    'name': '2. Kiểm Tra Trạng Thái Container Video',
                    'request': {
                        'method': 'GET',
                        'url': {
                            'raw': f"https://graph.threads.net/v1.0/{{{{th_container_id}}}}?fields=status,error_message&access_token={th_token}",
                            'protocol': 'https',
                            'host': ['graph', 'threads', 'net'],
                            'path': ['v1.0', '{{th_container_id}}'],
                            'query': [
                                {'key': 'fields', 'value': 'status,error_message'},
                                {'key': 'access_token', 'value': th_token}
                            ]
                        },
                        'description': 'Đợi cho đến khi status = "FINISHED" rồi mới tiến hành xuất bản.'
                    }
                },
                {
                    'name': '3. Xuất Bản Bài Đăng Video Lên Threads',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'creation_id', 'value': '{{th_container_id}}', 'type': 'text'},
                                {'key': 'access_token', 'value': th_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.threads.net/v1.0/{th_user_id}/threads_publish",
                            'protocol': 'https',
                            'host': ['graph', 'threads', 'net'],
                            'path': ['v1.0', str(th_user_id), 'threads_publish']
                        },
                        'description': 'Xuất bản bài video lên Threads. Trả về `id` của bài post.'
                    }
                },
                {
                    'name': '4. Bình Luận (Reply) Link Affiliate Vào Bài Viết Threads',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'media_type', 'value': 'TEXT', 'type': 'text'},
                                {'key': 'text', 'value': '{{affiliate_comment_1}}', 'type': 'text'},
                                {'key': 'reply_to_id', 'value': '{{th_post_id}}', 'type': 'text'},
                                {'key': 'access_token', 'value': th_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.threads.net/v1.0/{th_user_id}/threads",
                            'protocol': 'https',
                            'host': ['graph', 'threads', 'net'],
                            'path': ['v1.0', str(th_user_id), 'threads']
                        },
                        'description': 'Bước 4a: Tạo container trả lời (reply) vào bài post Threads gốc.'
                    }
                },
                {
                    'name': '5. Xuất Bản Bình Luận (Reply) Threads',
                    'request': {
                        'method': 'POST',
                        'header': [],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'creation_id', 'value': '{{th_reply_container_id}}', 'type': 'text'},
                                {'key': 'access_token', 'value': th_token, 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': f"https://graph.threads.net/v1.0/{th_user_id}/threads_publish",
                            'protocol': 'https',
                            'host': ['graph', 'threads', 'net'],
                            'path': ['v1.0', str(th_user_id), 'threads_publish']
                        },
                        'description': 'Bước 4b: Đẩy bình luận reply lên bài viết Threads.'
                    }
                }
            ]
        }
        brand_folder['item'].append(th_folder)

    # ==================== YOUTUBE ====================
    if yt_data:
        yt_folder = {
            'name': 'YouTube Shorts',
            'item': [
                {
                    'name': '0. [Tự Động Gia Hạn] Refresh Access Token',
                    'request': {
                        'method': 'POST',
                        'header': [
                            {'key': 'Content-Type', 'value': 'application/x-www-form-urlencoded'}
                        ],
                        'body': {
                            'mode': 'urlencoded',
                            'urlencoded': [
                                {'key': 'client_id', 'value': yt_data.get('client_id', ''), 'type': 'text'},
                                {'key': 'client_secret', 'value': yt_data.get('client_secret', ''), 'type': 'text'},
                                {'key': 'refresh_token', 'value': yt_data.get('refresh_token', ''), 'type': 'text'},
                                {'key': 'grant_type', 'value': 'refresh_token', 'type': 'text'}
                            ]
                        },
                        'url': {
                            'raw': 'https://oauth2.googleapis.com/token',
                            'protocol': 'https',
                            'host': ['oauth2', 'googleapis', 'com'],
                            'path': ['token']
                        },
                        'description': 'Lấy Access Token mới nhất khi token cũ hết hạn (1 tiếng).'
                    }
                },
                {
                    'name': '1. Đăng Ngay (Public) - Khởi Tạo Metadata',
                    'request': {
                        'method': 'POST',
                        'header': [
                            {'key': 'Authorization', 'value': f"Bearer {yt_data.get('access_token', '')}"},
                            {'key': 'Content-Type', 'value': 'application/json; charset=UTF-8'},
                            {'key': 'X-Upload-Content-Type', 'value': 'video/*'}
                        ],
                        'body': {
                            'mode': 'raw',
                            'raw': json.dumps({
                                "snippet": {
                                    "title": "{{video_title}}",
                                    "description": "{{video_caption}}",
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
                        'description': 'Bước 1: Khởi tạo tải lên video công khai ngay lập tức.'
                    }
                },
                {
                    'name': '2. Hẹn Giờ Đăng (Schedule) - Khởi Tạo Metadata',
                    'request': {
                        'method': 'POST',
                        'header': [
                            {'key': 'Authorization', 'value': f"Bearer {yt_data.get('access_token', '')}"},
                            {'key': 'Content-Type', 'value': 'application/json; charset=UTF-8'},
                            {'key': 'X-Upload-Content-Type', 'value': 'video/*'}
                        ],
                        'body': {
                            'mode': 'raw',
                            'raw': json.dumps({
                                "snippet": {
                                    "title": "{{video_title}}",
                                    "description": "{{video_caption}}",
                                    "tags": ["shorts", "review", "affiliate", "trending"],
                                    "categoryId": "22",
                                    "defaultLanguage": "vi",
                                    "defaultAudioLanguage": "vi"
                                },
                                "status": {
                                    "privacyStatus": "private",
                                    "publishAt": "{{yt_schedule_iso_utc}}",
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
                        'description': 'Bước 1 hẹn giờ: `privacyStatus` = `private` và truyền `publishAt` (chuẩn ISO-8601 UTC).'
                    }
                },
                {
                    'name': '3. Tải File Video Vào Resumable Upload URL (PUT Binary)',
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
                            'raw': '{{yt_upload_url_from_location_header}}',
                            'host': ['{{yt_upload_url_from_location_header}}']
                        },
                        'description': 'Bước 2: Dán link từ header `Location` của Bước 1 vào đây để đẩy file video mp4 lên YouTube.'
                    }
                },
                {
                    'name': '4. Bình Luận Link Affiliate Vào Video YouTube',
                    'request': {
                        'method': 'POST',
                        'header': [
                            {'key': 'Authorization', 'value': f"Bearer {yt_data.get('access_token', '')}"},
                            {'key': 'Content-Type', 'value': 'application/json; charset=UTF-8'}
                        ],
                        'body': {
                            'mode': 'raw',
                            'raw': json.dumps({
                                "snippet": {
                                    "videoId": "{{yt_video_id}}",
                                    "topLevelComment": {
                                        "snippet": {
                                            "textOriginal": "{{affiliate_comment_1}}"
                                        }
                                    }
                                }
                            }, indent=2)
                        },
                        'url': {
                            'raw': 'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet',
                            'protocol': 'https',
                            'host': ['www', 'googleapis', 'com'],
                            'path': ['youtube', 'v3', 'commentThreads'],
                            'query': [
                                {'key': 'part', 'value': 'snippet'}
                            ]
                        },
                        'description': 'Đăng bình luận chứa link Affiliate vào video YouTube.'
                    }
                }
            ]
        }
        brand_folder['item'].append(yt_folder)

    collection['item'].append(brand_folder)

out_file = r'c:\Affiliate\post1\Affiliate_Full_Platforms_10_Brands_Postman_Collection.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(collection, f, ensure_ascii=False, indent=2)

print('Postman full collection with Token Utilities updated successfully:', out_file)
