import requests
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

token = "EAAmD979AfWEBSvIUvuEFX2ZC39rsATmBPBsSRZC6zZAIjPYQKZAEURWEnQgTDgVWkZAZBPJ6tZAs87kpLwheOPtYk6VEHYjNtgX983Ou0XG8cU3S8Hw47bYdwo8otBOr82QXQFfWWsJ9tDZCfMOE4n6xKxiwZC9w87Chj49uTEdqTwv5qTJFAkwnwFxCzctRnRIGrgT8l4OwwXVuYXEYT8i2crgl6R8lxA7OoQ04l7Imz2MJ4rV7ZBoPijnZBJHQicXLfLN2a9ZBCZAIPGSOUP9tKfFaZA"

r = requests.get(
    "https://graph.facebook.com/v19.0/me/accounts",
    params={"access_token": token, "fields": "name,id,access_token,instagram_business_account,tasks", "limit": 100}
)
data = r.json()

if "data" in data:
    print(f"Tổng số Pages quản trị: {len(data['data'])}")
    for p in data["data"]:
        ig = p.get("instagram_business_account", {}).get("id") if p.get("instagram_business_account") else "None"
        tasks = p.get("tasks", [])
        print(f"- {p.get('name')} | ID: {p.get('id')} | IG ID: {ig} | Tasks: {tasks}")
else:
    print("Error:", json.dumps(data, indent=2))
