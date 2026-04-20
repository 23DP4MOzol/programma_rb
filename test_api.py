import urllib.request
req = urllib.request.Request(
    'http://127.0.0.1:8787/warranty/lookup',
    data=b'{"make": "hp", "serial": "5CG3387KZJ"}',
    headers={'X-API-Key': '7d9f2c1e4b8a6f3d0c5a1e9b7f2d4c6a8e1f3b5d7a9c2e4f6b8d0a1c3e5f7b9', 'Content-Type': 'application/json'}
)
print(urllib.request.urlopen(req).read().decode())
