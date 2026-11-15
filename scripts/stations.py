"""GPX × 車站資料 → 車站候選清單（AGENTS.md 6.3.1）。只用標準庫。

用法：uv run scripts/stations.py <trip>

需要 .cache/stations-jp.csv（第一次執行會自動下載 open-data-jp-railway-stations 並轉成 CSV）。
輸出 reports/<trip>-stations-candidates.tsv，AI 再依路線填「判斷」寫成 reports/<trip>-stations.md。
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.request
from collections import defaultdict
from zoneinfo import ZoneInfo

from common import CACHE, REPORTS, haversine, trip_meta
from tracks import load_points

SRC = "https://raw.githubusercontent.com/piuccio/open-data-jp-railway-stations/master/stations.json"
R_M, MIN_MIN, MERGE_MIN = 300, 4, 10


def ensure_csv():
    path = CACHE / "stations-jp.csv"
    if path.exists():
        return path
    CACHE.mkdir(exist_ok=True)
    print("下載車站資料…")
    with urllib.request.urlopen(SRC, timeout=60) as r:
        data = json.load(r)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "name", "romaji", "lines", "lat", "lon"])
        for g in data:
            s = g["stations"][0]
            lines = sorted({x["line_code"] for x in g["stations"] if x["line_code"]})
            w.writerow([g["group_code"], g["name_kanji"], g.get("name_romaji", ""), "|".join(lines), s["lat"], s["lon"]])
    return path


def main(trip: str):
    meta = trip_meta(trip)
    if "JP" not in [c.upper() for c in meta.get("countries", [])]:
        raise SystemExit("目前只有日本的車站資料")
    st = list(csv.DictReader(ensure_csv().open(encoding="utf-8")))
    grid = defaultdict(list)
    for s in st:
        s["lat"], s["lon"] = float(s["lat"]), float(s["lon"])
        grid[(round(s["lat"], 2), round(s["lon"], 2))].append(s)

    def near(la, lo):
        out = set()
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for s in grid[(round(round(la, 2) + i * 0.01, 2), round(round(lo, 2) + j * 0.01, 2))]:
                    if haversine(la, lo, s["lat"], s["lon"]) < R_M:
                        out.add(s["name"])
        return out

    pts = load_points(trip, ZoneInfo(meta["timezone"]), meta["countries"])
    active, eps = {}, []
    for t, la, lo, _ in pts:
        ns = near(la, lo)
        for n in list(active):
            if n not in ns:
                eps.append((n, *active.pop(n)))
        for n in ns:
            active[n] = [active[n][0], t] if n in active else [t, t]
    eps += [(n, *v) for n, v in active.items()]
    eps.sort(key=lambda e: (e[0], e[1]))
    merged = []
    for e in eps:
        if merged and merged[-1][0] == e[0] and (e[1] - merged[-1][2]).total_seconds() < MERGE_MIN * 60:
            merged[-1] = (e[0], merged[-1][1], max(merged[-1][2], e[2]))
        else:
            merged.append(e)
    merged = sorted((e for e in merged if (e[2] - e[1]).total_seconds() >= MIN_MIN * 60), key=lambda e: e[1])
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"{trip}-stations-candidates.tsv"
    with out.open("w", encoding="utf-8") as f:
        f.write("date\tstart\tend\tminutes\tstation\n")
        for n, a, b in merged:
            f.write(f"{a:%Y-%m-%d}\t{a:%H:%M}\t{b:%H:%M}\t{int((b - a).total_seconds() // 60)}\t{n}\n")
    print(f"{len(merged)} 個候選 → {out.relative_to(out.parent.parent)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法：uv run scripts/stations.py <trip>")
    main(sys.argv[1])
