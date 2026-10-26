import os
import sys
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POST_DIR = r"c:\Affiliate\post1\POST"
with open(os.path.join(POST_DIR, "config", "brands.json"), encoding="utf-8") as f:
    brands = json.load(f)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

for b_key, b_val in brands.items():
    yt_conf = b_val.get("youtube", {})
    tok_file = yt_conf.get("token_file")
    if not tok_file:
        continue
    tok_path = os.path.join(POST_DIR, tok_file) if not os.path.isabs(tok_file) else tok_file
    if not os.path.exists(tok_path):
        print(f"[{b_key}] ❌ File not found: {tok_path}")
        continue
    try:
        creds = Credentials.from_authorized_user_file(tok_path, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(tok_path, "w", encoding="utf-8") as tf:
                tf.write(creds.to_json())
        youtube = build("youtube", "v3", credentials=creds)
        # Lấy channel ID & uploads playlist
        ch_res = youtube.channels().list(mine=True, part="id,snippet,contentDetails,statistics").execute()
        items = ch_res.get("items", [])
        if items:
            ch = items[0]
            print(f"[{b_key}] ✅ Channel: {ch['snippet']['title']} | Subs: {ch['statistics'].get('subscriberCount')} | Views: {ch['statistics'].get('viewCount')}")
            # Lấy 3 video gần nhất
            uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
            pl_res = youtube.playlistItems().list(playlistId=uploads_id, part="snippet,contentDetails", maxResults=3).execute()
            vids = [i["contentDetails"]["videoId"] for i in pl_res.get("items", [])]
            if vids:
                v_res = youtube.videos().list(id=",".join(vids), part="snippet,statistics,contentDetails").execute()
                for v in v_res.get("items", []):
                    title = v["snippet"]["title"]
                    pub = v["snippet"]["publishedAt"]
                    views = v["statistics"].get("viewCount", "0")
                    likes = v["statistics"].get("likeCount", "0")
                    comments = v["statistics"].get("commentCount", "0")
                    dur = v["contentDetails"].get("duration", "")
                    print(f"    🎥 Video: {title[:40]}... | Date: {pub} | Views: {views} | Likes: {likes} | Comments: {comments} | Duration: {dur}")
            break # Thử 1 kênh trước
    except Exception as e:
        print(f"[{b_key}] ⚠️ Error: {e}")
