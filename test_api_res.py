import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

req = urllib.request.Request('http://localhost:5000/api/analytics?brand=noi_that_dung_that&platform=youtube&limit=15')
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))

yt = data.get('data', {}).get('noi_that_dung_that', {}).get('platforms', {}).get('youtube', {})
videos = yt.get('videos', [])
print('Cache info:', data.get('cache_info'))
print('Total videos:', len(videos))
for i, v in enumerate(videos, 1):
    title = v.get('title', '')[:40]
    print(f"{i:2d}. id={v.get('id')} | views={v.get('views')} | likes={v.get('likes')} | comms={v.get('comments')} | is_short={v.get('is_short')} | dur={v.get('duration_fmt')} | status={v.get('status')} | {title}")
