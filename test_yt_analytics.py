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
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

b_key = "noi_that_dung_that"
tok_file = os.path.join(POST_DIR, brands[b_key]["youtube"]["token_file"])
creds = Credentials.from_authorized_user_file(tok_file, SCOPES)
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

try:
    yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)
    res = yt_analytics.reports().query(
        ids="channel==MINE",
        startDate="2026-09-01",
        endDate="2026-09-29",
        metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
        dimensions="video",
        maxResults=5
    ).execute()
    print("YT Analytics OK:", res)
except Exception as e:
    print("YT Analytics Error:", e)
