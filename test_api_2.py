import requests
url = 'http://localhost:8787/warranty/lookup'
headers = {'Authorization': 'Bearer 7d9f2c1e4b8a6f3d0c5a1e9b7f2d4c6a8e1f3b5d7a9c2e4f6b8d0a1c3e5f7b9'}
payload = {
    'make': 'hp',
    'serial': '5CG3032ML9',
    'checker_url': 'https://support.hp.com/lv-en/check-warranty',
    'timeout_sec': 30.0
}
try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print('Status:', response.status_code)
    print('Body:', response.json())
except Exception as e:
    print('Error:', e)
