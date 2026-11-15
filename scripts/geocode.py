"""查座標（OpenStreetMap Nominatim）。只用標準庫。

用法：uv run scripts/geocode.py "Hallgrímskirkja, Reykjavík, Iceland" ["其他地名" ...]

Nominatim 規定：每秒最多 1 次、要帶 User-Agent。結果請人工確認後寫進 frontmatter（coord_source: nominatim）。
"""
import json
import sys
import time
import urllib.parse
import urllib.request

UA = "world-tour-llm-wiki/1.0 (https://github.com/youping13/world-tour-llm-wiki)"


def geocode(q: str):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 3})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-TW,en"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for i, q in enumerate(sys.argv[1:]):
        if i:
            time.sleep(1.1)
        res = geocode(q)
        if not res:
            print(f"{q}\t查不到（請 Percy 提供 Google 地圖座標，coord_source: manual）")
        for r in res:
            print(f"{q}\tlat: {float(r['lat']):.5f}\tlng: {float(r['lon']):.5f}\t{r['display_name'][:80]}")
