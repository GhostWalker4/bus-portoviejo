import urllib.request
import http.cookiejar
import re
import json

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

url = 'https://umap.openstreetmap.fr/es/map/anonymous-edit/1486568:8sHZJ2HsnraeqvTQLWdXDUnzh0RKE-s_lJ6O087f7tE'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = opener.open(req)
html = resp.read().decode('utf-8')
print('Status:', resp.status)

for line in html.splitlines():
    if 'datalayer' in line or 'download' in line or 'umap' in line.lower():
        if len(line.strip()) < 300:
            print('Line:', line.strip())
