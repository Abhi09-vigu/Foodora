import urllib.request
import sys

req = urllib.request.Request(
    'https://annapooraninj.com/',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
)
try:
    with urllib.request.urlopen(req) as response:
        with open('target_site.html', 'wb') as f:
            f.write(response.read())
    print("Success")
except Exception as e:
    print(f"Error: {e}")
