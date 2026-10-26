import json
import sys
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user_token = "EAAmD979AfWEBSlPUkm4tM3GaaqQHKl6fbMopFBDPdNHvQrZAf6wvGwjsKa9ZBj4ZA5ZA1NNcLBroXb6kFpLCvxYtMQiDb4zNMyL2H9yv1bZBzZA5rWhVRRZAwOmO9KIzgafBKZCLm83nz6v3Odw3iGUWMp8PIwmByuvZBZANgl2ZBlRdHq8wDOiJ1ziZBPnaUrZAPJTDVpwUuLZBZAH1Ey42SUI5ullTTOSLF1R7KNWLqXudeCY73YPbWvZC8CLoAzsHkVmZB1uO6ZBFplz3HNUsRnUvvB1rtS"

url = "https://graph.facebook.com/v19.0/me/accounts?" + urllib.parse.urlencode({
    "limit": "100",
    "access_token": user_token
})

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        pages = res.get("data", [])
        print(f"Total pages returned: {len(pages)}")
        for p in pages:
            print(f"Name: {p.get('name')}")
            print(f"  ID: {p.get('id')}")
            print(f"  Category: {p.get('category')}")
            print(f"  Tasks: {p.get('tasks')}")
            print(f"  Token prefix: {p.get('access_token', '')[:25]}...")
except Exception as e:
    if hasattr(e, 'read'):
        print("API Error:", e.read().decode('utf-8', errors='replace'))
    else:
        print("Error:", e)
