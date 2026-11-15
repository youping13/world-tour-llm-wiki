"""機械式健檢（AGENTS.md 12.2）。錯誤 > 0 時 exit code 1。

用法：uv run scripts/lint.py
"""
from __future__ import annotations

import sys
from datetime import date

from common import COUNTRY_BBOX, DETAILS, PAGE_TYPES, REGION_KINDS, ROOT, STATUSES, WIKI, CATEGORIES, in_country
from wikilib import LINK_RE, load_all_list, expected_path

REQUIRED = ["type", "title", "slug", "sources", "updated"]
TODAY = date.today().isoformat()
HOTEL_WORDS = ["hotel", "hostel", "inn", "旅館", "飯店", "酒店", "capsule", "膠囊"]


def main() -> int:
    pages = load_all_list()
    errors, warns, asks = [], [], []
    slugs: dict[str, str] = {}
    for pg in pages:
        rel = pg.path.relative_to(ROOT).as_posix()
        if pg.slug in slugs:
            errors.append(f"{rel}: slug `{pg.slug}` 和 {slugs[pg.slug]} 重複")
        slugs[pg.slug] = rel
        if pg.type == "special":
            continue
        fm = pg.fm
        for k in REQUIRED:
            if k not in fm:
                errors.append(f"{rel}: 缺必填欄位 `{k}`")
        if pg.type not in PAGE_TYPES:
            errors.append(f"{rel}: type `{pg.type}` 不在七種之內")
            continue
        exp = expected_path(pg)
        if exp and exp != pg.path:
            errors.append(f"{rel}: 位置應該是 {exp.relative_to(ROOT).as_posix()}")
        for s in fm.get("sources") or []:
            if str(s).startswith("raw/") and not (ROOT / s).exists():
                errors.append(f"{rel}: sources 指向不存在的 {s}")
        if pg.type == "city" and not fm.get("region"):
            errors.append(f"{rel}: 城市缺 `region`（上層的都道府縣／縣市／州）")
        if pg.type == "region":
            if fm.get("kind") not in REGION_KINDS:
                errors.append(f"{rel}: kind `{fm.get('kind')}` 不合法")
            if fm.get("icon") and not (ROOT / fm["icon"]).exists():
                errors.append(f"{rel}: icon 指向不存在的 {fm['icon']}")
            if not fm.get("icon") and not fm.get("label"):
                errors.append(f"{rel}: 沒有 icon 也沒有 label，地圖上無法顯示")
        if pg.type == "place":
            if fm.get("lat") is None or fm.get("lng") is None:
                errors.append(f"{rel}: 沒有座標")
            elif fm.get("country") in COUNTRY_BBOX and not in_country(fm["lat"], fm["lng"], [fm["country"]]):
                errors.append(f"{rel}: 座標不在 {fm['country']} 範圍內")
            if fm.get("category") not in CATEGORIES:
                errors.append(f"{rel}: category `{fm.get('category')}` 不合法")
            if fm.get("category") == "lodging-area" and any(w in pg.title.lower() for w in HOTEL_WORDS):
                errors.append(f"{rel}: lodging-area 標題像飯店名（隱私）")
            for v in fm.get("visits") or []:
                st, dt, ev = v.get("status"), v.get("detail"), set(v.get("evidence") or [])
                if st not in STATUSES:
                    errors.append(f"{rel}: status `{st}` 不合法（只能是 planned / visited）")
                    continue
                if dt not in DETAILS[st]:
                    errors.append(f"{rel}: {st} 的 detail `{dt}` 不合法（{' / '.join(DETAILS[st])}）")
                if st == "visited" and dt != "unconfirmed" and not ({"journal", "gpx"} <= ev or "percy" in ev):
                    errors.append(f"{rel}: visited/{dt} 但證據只有 {sorted(ev) or '無'}（要 journal＋gpx 或 percy）")
                if dt == "unconfirmed":
                    asks.append(f"{pg.slug}（{v.get('trip')} 第 {v.get('day')} 天，{st}/unconfirmed）證據：{sorted(ev) or '無'}")
                when = str(v.get("planned") or "")
                if st == "planned" and dt == "upcoming" and when and when < TODAY:
                    asks.append(f"{pg.slug}：{when} 已過但仍是 planned/upcoming")
    # 城市的 region 要存在
    for pg in pages:
        if pg.type == "city" and pg.fm.get("region") and pg.fm["region"] not in slugs:
            errors.append(f"{pg.path.relative_to(ROOT).as_posix()}: region `{pg.fm['region']}` 沒有對應的頁")
    # 連結、索引、孤兒頁
    inbound = {s: 0 for s in slugs}
    index_links = set()
    for pg in pages:
        for l in pg.links:
            if l not in slugs:
                errors.append(f"{pg.path.relative_to(ROOT).as_posix()}: [[{l}]] 指向不存在的頁")
            elif pg.slug == "index":
                index_links.add(l)
            elif l != pg.slug:
                inbound[l] += 1
    for s, rel in slugs.items():
        if s in ("index", "log", "overview"):
            continue
        if s not in index_links:
            errors.append(f"{rel}: index.md 沒有列出 [[{s}]]")
        if inbound[s] == 0:
            warns.append(f"{rel}: 孤兒頁（除了 index 沒有頁連到它）")
    # 照片 EXIF
    photos = ROOT / "assets" / "photos"
    if photos.exists():
        try:
            from PIL import Image
            for f in photos.rglob("*.webp"):
                if Image.open(f).getexif():
                    errors.append(f"{f.relative_to(ROOT).as_posix()}: 還帶 EXIF")
        except ImportError:
            warns.append("沒有 Pillow，略過 EXIF 檢查")

    print(f"頁數 {len(pages)} · 錯誤 {len(errors)} · 警告 {len(warns)} · 待問 {len(asks)}")
    for title, items in (("錯誤", errors), ("警告", warns), ("待問（給 Percy）", asks)):
        if items:
            print(f"\n## {title}")
            for i in items:
                print(f"- {i}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
