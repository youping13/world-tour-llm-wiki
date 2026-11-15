"""GPX → 公開用每日軌跡 ＋ 停留點清單（AGENTS.md 6.3）。只用標準庫。

用法：uv run scripts/tracks.py <trip>

輸出：
- assets/tracks/<trip>/YYYY-MM-DD.geojson：刪掉國外段、去頭尾 500 m、簡化 20 m（公開）
- reports/<trip>-stops.tsv：200 m 內停留 ≥ 10 分鐘的停留點（不進 git）
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from common import ASSETS, RAW, REPORTS, haversine, in_country, trip_meta

NS = "{http://www.topografix.com/GPX/1/1}"
TRIM_M = 500        # 每天頭尾去掉的距離（住宿位置）
SIMPLIFY_M = 20     # Douglas–Peucker 容差
MAX_KMH = 400       # 超過視為飛機
MAX_ELE = 3000      # 超過視為飛機
STOP_R, STOP_MIN = 200, 10


def load_points(trip: str, tz: ZoneInfo, countries: list[str]):
    pts = []
    for f in sorted((RAW / "gpx" / trip).glob("*.gpx")):
        for p in ET.parse(f).getroot().iter(NS + "trkpt"):
            t = p.find(NS + "time")
            if t is None:
                continue
            lat, lng = float(p.get("lat")), float(p.get("lon"))
            if not in_country(lat, lng, countries):
                continue
            e = p.find(NS + "ele")
            ele = float(e.text) if e is not None else 0.0
            dt = datetime.fromisoformat(t.text.replace("Z", "+00:00")).astimezone(tz)
            pts.append((dt, lat, lng, ele))
    pts.sort()
    # 刪除飛行中的點
    kept = []
    for p in pts:
        if p[3] > MAX_ELE:
            continue
        if kept:
            dt = (p[0] - kept[-1][0]).total_seconds()
            if dt > 0 and haversine(kept[-1][1], kept[-1][2], p[1], p[2]) / dt * 3.6 > MAX_KMH:
                continue
        kept.append(p)
    return kept


def trim(points, dist):
    """去掉頭尾各 dist 公尺。"""
    def cut(seq):
        acc = 0.0
        for i in range(1, len(seq)):
            acc += haversine(seq[i - 1][1], seq[i - 1][2], seq[i][1], seq[i][2])
            if acc >= dist:
                return seq[i:]
        return []
    head = cut(points)
    return cut(head[::-1])[::-1]


def simplify(coords, tol):
    """Douglas–Peucker（用平面近似，夠用）。coords: [(lat, lng)]"""
    if len(coords) < 3:
        return coords

    def perp(p, a, b):
        if a == b:
            return haversine(p[0], p[1], a[0], a[1])
        # 投影到 a-b 線段
        ax, ay, bx, by, px, py = a[1], a[0], b[1], b[0], p[1], p[0]
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return haversine(py, px, ay + t * dy, ax + t * dx)

    keep = [False] * len(coords)
    keep[0] = keep[-1] = True
    stack = [(0, len(coords) - 1)]
    while stack:
        s, e = stack.pop()
        dmax, idx = 0.0, 0
        for i in range(s + 1, e):
            d = perp(coords[i], coords[s], coords[e])
            if d > dmax:
                dmax, idx = d, i
        if dmax > tol:
            keep[idx] = True
            stack += [(s, idx), (idx, e)]
    return [c for c, k in zip(coords, keep) if k]


def stops(points):
    out, i = [], 0
    while i < len(points):
        j = i
        while j + 1 < len(points) and haversine(points[i][1], points[i][2], points[j + 1][1], points[j + 1][2]) < STOP_R:
            j += 1
        if (points[j][0] - points[i][0]).total_seconds() >= STOP_MIN * 60:
            la = sum(p[1] for p in points[i:j + 1]) / (j - i + 1)
            ln = sum(p[2] for p in points[i:j + 1]) / (j - i + 1)
            out.append((points[i][0], points[j][0], la, ln))
            i = j + 1
        else:
            i += 1
    return out


def main(trip: str):
    meta = trip_meta(trip)
    tz = ZoneInfo(meta.get("timezone", "UTC"))
    countries = meta.get("countries", [])
    pts = load_points(trip, tz, countries)
    by_day = defaultdict(list)
    for p in pts:
        by_day[p[0].date().isoformat()].append(p)

    outdir = ASSETS / "tracks" / trip
    outdir.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    stop_lines = ["date\tstart\tend\tminutes\tlat\tlng"]
    for day, dpts in sorted(by_day.items()):
        for a, b, la, ln in stops(dpts):
            stop_lines.append(f"{day}\t{a:%H:%M}\t{b:%H:%M}\t{int((b - a).total_seconds() // 60)}\t{la:.5f}\t{ln:.5f}")
        dpts = trim(dpts, TRIM_M)
        if len(dpts) < 2:
            continue
        # 中斷超過 30 分鐘且距離超過 5 km 就分段（避免畫出不存在的直線）
        segs, cur = [], [dpts[0]]
        for p in dpts[1:]:
            q = cur[-1]
            if (p[0] - q[0]).total_seconds() > 1800 and haversine(q[1], q[2], p[1], p[2]) > 5000:
                segs.append(cur)
                cur = []
            cur.append(p)
        segs.append(cur)
        lines = []
        for s in segs:
            c = simplify([(p[1], p[2]) for p in s], SIMPLIFY_M)
            if len(c) >= 2:
                lines.append([[round(ln, 5), round(la, 5)] for la, ln in c])
        gj = {"type": "Feature", "properties": {"trip": trip, "date": day},
              "geometry": {"type": "MultiLineString", "coordinates": lines}}
        (outdir / f"{day}.geojson").write_text(json.dumps(gj, separators=(",", ":")), encoding="utf-8")
        print(f"{day}: {len(dpts)} 點 → {sum(len(l) for l in lines)} 點")
    (REPORTS / f"{trip}-stops.tsv").write_text("\n".join(stop_lines) + "\n", encoding="utf-8")
    print(f"停留點 {len(stop_lines) - 1} 個 → reports/{trip}-stops.tsv")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法：uv run scripts/tracks.py <trip>")
    main(sys.argv[1])
