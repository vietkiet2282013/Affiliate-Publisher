import sys
import json
import requests
import os

sys.stdout.reconfigure(encoding='utf-8')
brands = json.load(open(r'c:\Affiliate\post1\POST\config\brands.json', encoding='utf-8'))

for k, v in brands.items():
    name = v.get('name')
    print(f"\n=== {name} ({k}) ===")
    
    # 1. FB Token check
    fb = v.get('facebook', {})
    fb_pid = fb.get('page_id')
    fb_tok = fb.get('access_token')
    if fb_pid and fb_tok:
        try:
            url = f"https://graph.facebook.com/v19.0/{fb_pid}?fields=id,name&access_token={fb_tok}"
            r = requests.get(url, timeout=10).json()
            if 'name' in r:
                print(f"  [FB] OK: {r['name']}")
            else:
                print(f"  [FB] LOI: {r.get('error', {}).get('message')}")
        except Exception as e:
            print(f"  [FB] Exception: {e}")
            
    # 2. IG Token check
    ig = v.get('instagram', {})
    ig_uid = ig.get('ig_user_id')
    ig_tok = ig.get('access_token')
    if ig_uid and ig_tok:
        try:
            url = f"https://graph.facebook.com/v19.0/{ig_uid}?fields=id,username&access_token={ig_tok}"
            r = requests.get(url, timeout=10).json()
            if 'username' in r:
                print(f"  [IG] OK: @{r['username']}")
            else:
                print(f"  [IG] LOI: {r.get('error', {}).get('message')}")
        except Exception as e:
            print(f"  [IG] Exception: {e}")

    # 3. Threads Token check
    th = v.get('threads', {})
    th_uid = th.get('user_id')
    th_tok = th.get('access_token')
    if th_uid and th_tok:
        try:
            url = f"https://graph.threads.net/v1.0/me?fields=id,username&access_token={th_tok}"
            r = requests.get(url, timeout=10).json()
            if 'username' in r:
                print(f"  [TH] OK: @{r['username']}")
            else:
                print(f"  [TH] LOI: {r.get('error', {}).get('message')}")
        except Exception as e:
            print(f"  [TH] Exception: {e}")

    # 4. YouTube Token check
    yt = v.get('youtube', {})
    yt_file = yt.get('token_file')
    if yt_file:
        full_yt = os.path.join(r'c:\Affiliate\post1\POST', yt_file)
        if os.path.exists(full_yt):
            print(f"  [YT] Token file ton tai: {yt_file}")
        else:
            print(f"  [YT] KHONG TIM THAY TOKEN FILE: {full_yt}")
