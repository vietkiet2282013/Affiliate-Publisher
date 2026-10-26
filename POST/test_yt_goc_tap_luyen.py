import sys
import os

sys.path.insert(0, r"C:\Affiliate\post1\POST")
from uploaders import YouTubeShortsUploader

token_file = r"C:\Affiliate\post1\POST\credentials\youtube_tokens\goc_tap_luyen.json"
uploader = YouTubeShortsUploader(token_file=token_file)
ok = uploader.authenticate()
print("YouTube Auth:", ok)
