import sys
import json
import os

sys.stdout.reconfigure(encoding='utf-8')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

tok_path = 'c:/Affiliate/post1/POST/credentials/youtube_tokens/noi_that_dung_that.json'
creds = Credentials.from_authorized_user_file(tok_path)
youtube = build('youtube', 'v3', credentials=creds)

ch = youtube.channels().list(mine=True, part='contentDetails').execute()
uploads_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

all_vids = []
next_token = None
while True:
    pl = youtube.playlistItems().list(playlistId=uploads_id, part='contentDetails,snippet', maxResults=50, pageToken=next_token).execute()
    for item in pl.get('items', []):
        all_vids.append({
            'id': item['contentDetails']['videoId'],
            'title': item['snippet']['title'],
            'published': item['snippet']['publishedAt']
        })
    next_token = pl.get('nextPageToken')
    if not next_token:
        break

print(f'Total videos retrieved: {len(all_vids)}')

vid_ids = [v['id'] for v in all_vids]
stats_map = {}
for i in range(0, len(vid_ids), 50):
    chunk = vid_ids[i:i+50]
    vr = youtube.videos().list(id=','.join(chunk), part='statistics,contentDetails').execute()
    for item in vr.get('items', []):
        stats_map[item['id']] = {
            'views': int(item.get('statistics', {}).get('viewCount', 0)),
            'likes': int(item.get('statistics', {}).get('likeCount', 0)),
            'comments': int(item.get('statistics', {}).get('commentCount', 0)),
            'duration': item.get('contentDetails', {}).get('duration', '')
        }

for i, v in enumerate(all_vids, 1):
    st = stats_map.get(v['id'], {})
    title = v['title'][:50]
    print(f"{i:2d}. [{v['id']}] {v['published'][:16]} | Views: {st.get('views',0):5d} | Likes: {st.get('likes',0):3d} | Comms: {st.get('comments',0):2d} | Dur: {st.get('duration',''):6s} | {title}")
