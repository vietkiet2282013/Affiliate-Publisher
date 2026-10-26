import requests
import json

user_token = 'EAAmD979AfWEBSmFmKELRPw79yaXT1ULIVEXeJiIFfAC84gw0zWZA7dRWcdakUHxzTMMgGz7vy7v7QbvtuRA2EUQ85Oa6gYhurxBpvWM0BZBZC30UhDqZA1g0ZCZAtextNzMfEy78koxG7lYAMnHNYE2hIMSJwhCgGYMfErdSeTlu5DGqrREAfuqKFZAZAZAlvSJDEOsbpEKdZB5oL9O2XvwwdRgdAzZBSjRTejvyNT1QDYkIGyQZAULZBwtgbfyDxSZC3nqVyU8WHPl0rZA7ik62R9jDa3p'

r = requests.get(f'https://graph.facebook.com/v19.0/me/accounts?fields=id,name,access_token,instagram_business_account&access_token={user_token}')
print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    pages = data.get('data', [])
    print(f'Total pages returned: {len(pages)}')
    for p in pages:
        ig = p.get('instagram_business_account', {})
        print(f"Page: {p.get('name')} | Page ID: {p.get('id')} | IG ID: {ig.get('id')}")
else:
    print('Error:', r.text)
