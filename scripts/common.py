"""scripts/ 共用工具：路徑、距離、國家範圍、frontmatter 讀取。"""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
ASSETS = ROOT / "assets"
REPORTS = ROOT / "reports"
CACHE = ROOT / ".cache"

# 國家大致範圍 (lat_min, lng_min, lat_max, lng_max)，lint 檢查座標與 tracks.py 刪國外段落用。
# 新增國家時在這裡加一行。
COUNTRY_BBOX = {
    "JP": (24.0, 122.9, 45.6, 154.0),
    "IS": (63.2, -24.6, 66.6, -13.4),
    "SE": (55.3, 10.9, 69.1, 24.2),
    "TW": (21.8, 119.3, 25.4, 122.1),
}

# 5.2：status 兩大類，detail 小類
STATUSES = ["planned", "visited"]
DETAILS = {
    "planned": ["upcoming", "skipped", "unconfirmed", "dropped"],
    "visited": ["as-planned", "moved", "added", "unconfirmed"],
}
PAGE_TYPES = ["place", "day", "trip", "city", "region", "country", "note"]
CATEGORIES = ["landmark", "religious", "museum", "nature", "viewpoint", "food", "shopping",
              "activity", "station", "transport", "lodging-area"]
# 地圖標記顏色（9.4）：依類別上色；路線用旅程顏色，兩者不重複
CATEGORY_COLORS = {
    "landmark": "#2f6fdb", "religious": "#8e44ad", "museum": "#795548", "nature": "#2e7d32",
    "viewpoint": "#00838f", "food": "#ad1457", "shopping": "#3949ab", "activity": "#c79100",
    "station": "#455a64", "transport": "#607d8b", "lodging-area": "#5d4037",
}
REGION_KINDS = ["prefecture", "county", "city", "state", "region"]
# 5.3：GPX 停留判定半徑（公尺）
WIDE_CATEGORIES = {"nature", "viewpoint", "lodging-area"}


def radius_for(category: str) -> int:
    return 1000 if category in WIDE_CATEGORIES else 200


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """兩點距離（公尺）。"""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(a))


def in_country(lat: float, lng: float, countries) -> bool:
    for cc in countries:
        b = COUNTRY_BBOX.get(cc.upper())
        if b and b[0] <= lat <= b[2] and b[1] <= lng <= b[3]:
            return True
    return False


FM_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.S)


def simple_frontmatter(path: Path) -> dict:
    """只用標準庫讀 frontmatter 的「單層 key: value」與「key: [a, b]」，給不需要 PyYAML 的 script 用。"""
    m = FM_RE.match(path.read_text(encoding="utf-8"))
    out: dict = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*(#.*)?$", line)
        if not mm:
            continue
        k, v = mm.group(1), mm.group(2)
        if v.startswith("[") and v.endswith("]"):
            out[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            out[k] = v.strip("'\"")
    return out


def trip_meta(trip: str) -> dict:
    p = WIKI / "trips" / f"{trip}.md"
    if not p.exists():
        raise SystemExit(f"找不到旅程頁 {p}，請先 ingest plan 或建立 trip 頁")
    return simple_frontmatter(p)
