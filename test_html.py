import urllib.request
import re

htmlStr = urllib.request.urlopen('http://127.0.0.1:8000/').read().decode('utf-8')
htmlStr += urllib.request.urlopen('http://127.0.0.1:8000/menu/').read().decode('utf-8')

matches = re.finditer(r'<div[^>]*data-name="Chicken Dum Biryani"[^>]*>', htmlStr)
with open('test_html_output.txt', 'w') as f:
    for m in matches:
        f.write(m.group(0))
        f.write('\n' + "-" * 20 + '\n')
