import json, sys, requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"c:\Affiliate\post1\POST\config\brands.json", "r", encoding="utf-8") as f:
    brands = json.load(f)

b = brands["yeu_da_hon_bo"]
ig_id = b["instagram"]["ig_user_id"]
tok = b["instagram"]["access_token"]

params = {
    "fields": "id,permalink,timestamp,caption",
    "limit": "5",
    "access_token": tok
}
r = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}/media", params=params).json()
print("Yêu Da Hơn Bồ Instagram media:", r)
