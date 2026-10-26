import re
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch_yt.html', 'r', encoding='utf-8') as f:
    html = f.read()

# viewCount
m_views = re.findall(r'"viewCount":\s*"(\d+)"', html)
print("All viewCount in html:", m_views)

# title
m_titles = re.findall(r'<title>(.*?)</title>', html)
print("Title:", m_titles)

# author / channel
m_author = re.findall(r'"author":\s*"(.*?)"', html)
print("Author:", m_author[:3])

m_channel_id = re.findall(r'"channelId":\s*"(.*?)"', html)
print("Channel IDs:", m_channel_id[:3])

# likes
m_likes = re.findall(r'like this video along with ([\d,]+) other people', html)
print("Likes phrase:", m_likes)

for m in re.finditer(r'"accessibilityData":\s*\{\s*"label":\s*"([^"]+)"', html):
    lbl = m.group(1)
    if any(k in lbl.lower() for k in ['thích', 'like', 'view', 'lượt xem']):
        print("Accessibility label:", lbl)

# clean up html file
if os.path.exists('scratch_yt.html'):
    os.remove('scratch_yt.html')
