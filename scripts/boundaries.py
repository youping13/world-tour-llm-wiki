"""行政區邊界（迷霧地圖用，AGENTS.md 9.4）：Natural Earth 1:10m admin-1 → assets/boundaries/<cc>.geojson

用法：
  uv run scripts/boundaries.py          # 處理所有有國家頁的國家
  uv run scripts/boundaries.py JP IS    # 只處理指定國家

資料：Natural Earth（公有領域）ne_10m_admin_1_states_provinces，第一次執行會下載到 .cache/（約 40 MB，不進 git）。
輸出：每個一級行政區一個 Feature，properties 只有 iso（例 JP-26）、name；
      哪個邊界屬於哪個 region、有沒有去過，由 build.py 依景點座標判斷（落在邊界裡就算）。
簡化：Douglas–Peucker 容差約 500 m，小於約 0.1 km² 的小島丟掉，座標取 4 位小數。只用標準庫。
"""
from __future__ import annotations

import json
import sys
import urllib.request

import yaml

from common import ASSETS, CACHE, WIKI

URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/"
       "geojson/ne_10m_admin_1_states_provinces.geojson")
SRC = CACHE / "ne-admin1.geojson"
TOL = 0.005        # 度，約 500 m
MIN_AREA = 1e-5    # 平方度，約 0.1 km²


def simplify(pts, tol):
    """Douglas–Peucker（非遞迴）。"""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = (dx * dx + dy * dy) ** 0.5
        best, idx = 0.0, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n if n else ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
            if d > best:
                best, idx = d, i
        if best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def area(r):
    return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2


def clean_polygon(poly):
    out = []
    for i, ring in enumerate(poly):
        r = [[round(x, 4), round(y, 4)] for x, y in simplify(ring, TOL)]
        if len(r) < 4 or area(r) < MIN_AREA:
            if i == 0:
                return None          # 外圈太小：整個小島丟掉
            continue
        out.append(r)
    return out


def main(only: list[str]):
    if not SRC.exists():
        CACHE.mkdir(exist_ok=True)
        print(f"下載 Natural Earth admin-1 → {SRC}")
        urllib.request.urlretrieve(URL, SRC)
    countries = only or [yaml.safe_load(p.read_text(encoding="utf-8").split("---")[1])["country"]
                         for p in (WIKI / "countries").glob("*.md")]
    data = json.loads(SRC.read_text(encoding="utf-8"))
    out_dir = ASSETS / "boundaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    for cc in countries:
        feats = []
        for f in data["features"]:
            p = f["properties"]
            if p.get("iso_a2") != cc:
                continue
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            polys = [q for q in (clean_polygon(pl) for pl in polys) if q]
            if not polys:
                continue
            feats.append({"type": "Feature", "properties": {"iso": p.get("iso_3166_2"), "name": p.get("name")},
                          "geometry": {"type": "MultiPolygon", "coordinates": polys}})
        feats.sort(key=lambda f: f["properties"]["iso"] or "")
        path = out_dir / f"{cc.lower()}.geojson"
        path.write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{cc}：{len(feats)} 個行政區 → {path.relative_to(ASSETS.parent)}（{path.stat().st_size // 1024} KB）")


if __name__ == "__main__":
    main([a.upper() for a in sys.argv[1:]])
