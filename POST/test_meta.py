import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

tokens_file = r"C:\Affiliate\post1\POST\config\permanent_meta_tokens.json"
with open(tokens_file, "r", encoding="utf-8") as f:
    data = json.load(f)

page_id = "1211541072052658"
token_page = data.get("Góc Tập Luyện", {}).get("page_access_token")
ig_id = "17841438553537040"

r2 = requests.get(f"https://graph.facebook.com/v19.0/{ig_id}", params={"fields": "username,id", "access_token": token_page})
print("Result r2 (IG with token_page):", r2.json())
