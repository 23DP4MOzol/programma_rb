import requests
s=requests.Session()
print(s.get('https://support.hp.com/us-en/check-warranty', headers={'User-Agent': 'Mozilla/5.0'}))
print(s.cookies.get_dict())
