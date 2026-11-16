"""wiki/ + assets/ → site/（AGENTS.md 第 9 節）。

用法：uv run scripts/build.py

- 每頁是一張全螢幕 Leaflet 地圖＋側邊面板（templates/page.html）
- [[slug]] 轉成相對連結；找不到的頁顯示成紅字
- 今天以後的日期一律只顯示到月（9.5）
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

import markdown
from jinja2 import Environment, FileSystemLoader

from common import ASSETS, CATEGORY_COLORS, ROOT
from wikilib import LINK_RE, Page, load_all, url_of

SITE = ROOT / "site"
TPL = ROOT / "templates"
TODAY = datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()

STATUS_ZH = {"planned/upcoming": "計畫・還沒去", "planned/skipped": "計畫・沒去", "planned/unconfirmed": "計畫・待確認",
             "planned/dropped": "計畫・改版拿掉", "visited/as-planned": "去過・照計畫", "visited/moved": "去過・改期",
             "visited/added": "去過・臨時加", "visited/unconfirmed": "去過・待確認"}
CAT_ZH = {"landmark": "地標", "religious": "寺社與教堂", "museum": "博物館", "nature": "自然",
          "viewpoint": "展望點", "food": "美食", "shopping": "購物", "activity": "體驗",
          "station": "車站", "transport": "交通", "lodging-area": "住宿區域"}
TYPE_ZH = {"place": "景點", "day": "日程", "trip": "旅程", "city": "城市", "region": "行政區", "country": "國家",
           "note": "筆記", "special": ""}
REGION_KIND_ZH = {"prefecture": "都道府縣", "county": "縣", "city": "市", "state": "州", "region": "地區"}


def is_done(v) -> bool:
    return v.get("status") == "visited" and v.get("detail") != "unconfirmed"


def skey(v) -> str:
    return f"{v.get('status')}/{v.get('detail')}"

DATE_RE = re.compile(r"\b(\d{4}-\d{2})-(\d{2})\b")


def mask(text: str) -> str:
    """未來的日期只留年月（隱私規則 9.5）。"""
    return DATE_RE.sub(lambda m: m.group(1) if m.group(0) > TODAY else m.group(0), text)


def rel(depth_url: str) -> str:
    return "../" * depth_url.count("/")


def render_body(pg: Page, pages: dict, root: str) -> str:
    def link(m):
        slug, label = m.group(1).strip(), m.group(2)
        tgt = pages.get(slug)
        if not tgt:
            return f'<span class="broken" title="還沒有這頁">{label or slug}</span>'
        text = label or short_title(tgt)
        return f"[{text}]({root}{url_of(tgt)})"
    body = LINK_RE.sub(link, pg.body)
    return markdown.markdown(body, extensions=["tables", "sane_lists"])


def short_title(pg: Page) -> str:
    return pg.title


def visits_of(pg: Page):
    return [v for v in (pg.fm.get("visits") or []) if v]


def place_record(pg: Page, root_url: str) -> dict:
    fm = pg.fm
    thumb = None
    pdir = ASSETS / "photos" / pg.slug
    if pdir.exists():
        th = sorted(pdir.glob("*-thumb.webp"))
        thumb = f"assets/photos/{pg.slug}/{th[0].name}" if th else None
    return {
        "slug": pg.slug, "title": pg.title, "lat": fm.get("lat"), "lng": fm.get("lng"),
        "category": fm.get("category"), "city": fm.get("city"), "country": fm.get("country"),
        "lines": fm.get("lines") or [], "url": url_of(pg), "thumb": thumb,
        "visits": [{"trip": v.get("trip"), "day": v.get("day"),
                    "planned": str(v.get("planned")) if v.get("planned") else None,
                    "actual": str(v.get("actual")) if v.get("actual") else None,
                    "status": v.get("status"), "detail": v.get("detail")} for v in visits_of(pg)],
    }


REGION_PALETTE = ["#5d4037", "#c2185b", "#1565c0", "#00897b", "#6a1b9a", "#ef6c00", "#2e7d32", "#37474f", "#ad1457", "#283593"]


def region_records(pages: dict) -> list:
    """都道府縣／縣市／州的大圓標記（9.4）。座標沒填就用旗下景點的中心。"""
    city_region = {p.slug: p.fm.get("region") for p in pages.values() if p.type == "city"}
    by_region: dict = {}
    for p in pages.values():
        if p.type == "place" and p.fm.get("lat") is not None:
            by_region.setdefault(city_region.get(p.fm.get("city")), []).append(p)
    out = []
    for pg in pages.values():
        if pg.type != "region":
            continue
        ps = by_region.get(pg.slug, [])
        cities = [c for c in pages.values() if c.type == "city" and c.fm.get("region") == pg.slug]
        lat, lng = pg.fm.get("lat"), pg.fm.get("lng")
        if lat is None and ps:
            lat = sum(p.fm["lat"] for p in ps) / len(ps)
            lng = sum(p.fm["lng"] for p in ps) / len(ps)
        visited = any(is_done(v) for p in ps for v in visits_of(p))
        trips = sorted({v.get("trip") for p in ps for v in visits_of(p)})
        out.append({"slug": pg.slug, "title": pg.title, "label": pg.fm.get("label") or pg.title[:2],
                    "icon": pg.fm.get("icon"), "lat": lat, "lng": lng, "url": url_of(pg),
                    "country": pg.fm.get("country"), "visited": visited, "trips": trips,
                    "color": pg.fm.get("color") or REGION_PALETTE[len(out) % len(REGION_PALETTE)],
                    "places": len(ps), "name": pg.title.split(" ")[0],
                    "cities": [{"name": c.title.split(" ")[0], "url": url_of(c)} for c in cities]})
    return out


def _in_ring(x, y, ring):
    inside = False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i], ring[i + 1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _in_feature(lat, lng, feat):
    return any(_in_ring(lng, lat, poly[0]) and not any(_in_ring(lng, lat, h) for h in poly[1:])
               for poly in feat["geometry"]["coordinates"])


def boundary_records(pages: dict, regions: list) -> dict:
    """迷霧地圖（9.4）：assets/boundaries/<cc>.geojson 的每個行政區，依座標對到 region，並標記去過沒有。
    對應方式：region 的 `boundary`（ISO 3166-2 清單）優先；沒有就看 region 大圓與旗下景點落在哪個邊界裡。"""
    city_region = {p.slug: p.fm.get("region") for p in pages.values() if p.type == "city"}
    pts: dict = {}
    for p in pages.values():
        if p.type == "place" and p.fm.get("lat") is not None:
            pts.setdefault(city_region.get(p.fm.get("city")), []).append((p.fm["lat"], p.fm["lng"]))
    by_slug = {r["slug"]: r for r in regions}
    feats = []
    for f in sorted((ASSETS / "boundaries").glob("*.geojson")) if (ASSETS / "boundaries").exists() else []:
        feats += json.loads(f.read_text(encoding="utf-8"))["features"]
    owner: dict = {}
    for r in regions:
        explicit = pages[r["slug"]].fm.get("boundary") or []
        for f in feats:
            iso = f["properties"]["iso"]
            if iso in explicit:
                owner[iso] = r["slug"]
            elif not explicit and iso not in owner:
                cand = ([(r["lat"], r["lng"])] if r["lat"] is not None else []) + pts.get(r["slug"], [])
                if any(_in_feature(la, ln, f) for la, ln in cand):
                    owner[iso] = r["slug"]
    unmatched = [r["slug"] for r in regions if r["slug"] not in owner.values()]
    if feats and unmatched:
        print("沒有對到邊界的行政區（在 region 頁加 boundary: [ISO 3166-2]）：", "、".join(unmatched))
    out = []
    for f in feats:
        r = by_slug.get(owner.get(f["properties"]["iso"]))
        out.append({"type": "Feature", "geometry": f["geometry"],
                    "properties": {"iso": f["properties"]["iso"], "region": r["slug"] if r else None,
                                   "name": r["name"] if r else f["properties"]["name"],
                                   "url": r["url"] if r else None, "color": r["color"] if r else None,
                                   "visited": bool(r and r["visited"])}})
    return {"type": "FeatureCollection", "features": out}


def country_records(pages: dict, regions: list) -> list:
    """世界縮放（zoom ≤ 4）的國家標記：國旗＋國名。"""
    out = []
    for c in pages.values():
        if c.type != "country":
            continue
        cc = c.fm.get("country")
        out.append({"cc": cc, "name": c.title.split(" ")[0], "lat": c.fm.get("lat"), "lng": c.fm.get("lng"),
                    "url": url_of(c), "visited": any(r["visited"] for r in regions if r["country"] == cc),
                    "flag": f"static/flags/{cc.lower()}.svg" if (TPL / "static" / "flags" / f"{cc.lower()}.svg").exists() else None})
    return out


def short_date(d) -> str:
    """卡片用的短日期：已發生寫 · 7/30，未來的不寫（9.5）。"""
    d = str(d or "")
    if not d or mask(d) != d:
        return ""
    return f" · {int(d[5:7])}/{int(d[8:10])}"


DAYS_RE = re.compile(r"(<h2>每日</h2>\s*)<ul>.*?</ul>", re.S)


def day_cards(html: str, trip: Page, pages: dict, root: str) -> str:
    """旅程頁的「每日」：長方形圓角卡片，小字第幾天與日期、大字當天主題、小字城市（可點）。"""
    days = sorted((p for p in pages.values() if p.type == "day" and p.fm.get("trip") == trip.slug),
                  key=lambda p: p.fm.get("day", 0))
    if not days:
        return html
    color = trip.fm.get("color", "#888")
    cards = []
    for d in days:
        fm = d.fm
        topic = re.sub(r"^第 \d+ 天\s*", "", d.title)
        cities = "・".join(f'<a href="{root}{url_of(pages[c])}">{pages[c].title.split(" ")[0]}</a>'
                          for c in fm.get("cities") or [] if c in pages)
        n_act, n_plan = len(fm.get("actual") or []), len(fm.get("planned") or [])
        stat = f"去過 {n_act}" if n_act else (f"計畫 {n_plan}" if n_plan else "")
        cards.append(
            f'<div class="rcard dcard{" done" if n_act else ""}" style="--c:{color}">'
            f'<span class="dc-head"><span>第 {fm.get("day")} 天{short_date(fm.get("date"))}</span>{f"<b>{stat}</b>" if stat else ""}</span>'
            f'<a class="rc-name" href="{root}{url_of(d)}">{topic}</a>'
            f'<span class="rc-cities">{cities}</span></div>')
    return DAYS_RE.sub(lambda m: m.group(1) + f'<div class="rcards dcards">{"".join(cards)}</div>', html, count=1)


TRIP_STATUS_ZH = {"completed": "已完成", "ongoing": "旅行中", "planned": "規劃中"}
COUNTRIES_RE = re.compile(r"<h2>國家</h2>\s*<ul>.*?</ul>", re.S)
TRIPS_RE = re.compile(r"<h2>旅程</h2>\s*<ul>.*?</ul>", re.S)
HOWTO_RE = re.compile(r"<h2>怎麼看</h2>\s*(<ul>.*?</ul>)", re.S)


def flag(cc: str, root: str) -> str:
    """國旗 SVG（flag-icons，MIT）；沒有檔案就顯示國家代碼。"""
    cc = (cc or "").lower()
    if (TPL / "static" / "flags" / f"{cc}.svg").exists():
        return f'<img class="flag" src="{root}static/flags/{cc}.svg" alt="{cc.upper()}">'
    return f'<span class="flag flag-txt">{cc.upper()}</span>'


def dates(start: str, end: str) -> str:
    """卡片用的期間：2026-07-30 ～ 08-15；未來的旅程只到月。"""
    if mask(start) != start or mask(end) != end:   # 未來的旅程只顯示到月（9.5），不能留下「06-21」這種片段
        ms, me = mask(start)[:7], mask(end)[:7]
        return ms if ms == me else f"{ms} ～ {me}"
    return f"{start} ～ {end[5:]}" if end[:4] == start[:4] and len(end) == 10 else f"{start} ～ {end}"


def trip_cards(trips: dict, root: str, country: str | None = None) -> str:
    """旅程卡片：國旗、旅程名稱（大字）、日期、狀態、去過幾個點；左邊色條＝旅程顏色。"""
    rows = sorted((t for t in trips.values() if country is None or country in t["countries"]),
                  key=lambda t: t["start"], reverse=True)
    cards = "".join(
        f'<div class="rcard tcard{" done" if t["status"] != "planned" else ""}" style="--c:{t["color"]}">'
        f'<span class="tc-head">{"".join(flag(c, root) for c in t["countries"])}'
        f'<span>{dates(t["start"], t["end"])}</span></span>'
        f'<a class="rc-name" href="{root}{t["url"]}">{t["title"]}</a>'
        f'<span class="rc-cities">{TRIP_STATUS_ZH.get(t["status"], t["status"])} · {t["days"]} 天'
        + (f' · 去過 {t["visited"]} 個點' if t["visited"] else f' · 計畫 {t["planned"]} 個點') + "</span></div>"
        for t in rows)
    return f'<div class="rcards tcards">{cards}</div>'


def country_cards(pages: dict, trips: dict, regions: list, root: str) -> str:
    """國家卡片：國旗＋國名（大字），小字是旅程數、行政區數、去過幾個點。"""
    cs = sorted((p for p in pages.values() if p.type == "country"),
                key=lambda p: (-sum(t["visited_by_cc"].get(p.fm.get("country"), 0) for t in trips.values()), p.slug))
    out = []
    for c in cs:
        cc = c.fm.get("country")
        n_trip = sum(1 for t in trips.values() if cc in t["countries"])
        n_reg = sum(1 for r in regions if r["country"] == cc)
        n_vis = sum(t["visited_by_cc"].get(cc, 0) for t in trips.values())
        main = max((t for t in trips.values() if cc in t["countries"]), default=None,
                   key=lambda t: (t["visited_by_cc"].get(cc, 0), t["planned"]))
        color = main["color"] if main else "#888"
        out.append(
            f'<div class="rcard ccard{" done" if n_vis else ""}" style="--c:{color}">'
            f'<span class="cc-name">{flag(cc, root)}<a class="rc-name" href="{root}{url_of(c)}">{c.title}</a></span>'
            f'<span class="rc-cities">{n_trip} 趟旅程 · {n_reg} 個行政區'
            + (f" · 去過 {n_vis} 個點" if n_vis else " · 只有計畫") + "</span></div>")
    return f'<div class="rcards ccards">{"".join(out)}</div>'


def fold(title: str, inner: str) -> str:
    return f'<details class="fold"><summary>{title}</summary>{inner}</details>'


SECTION_RE = re.compile(r"(<h2>都道府縣／縣市／州</h2>\s*)<ul>.*?</ul>", re.S)


def region_cards(html: str, regions: list, root: str, country: str | None) -> str:
    """國家頁與索引頁的「都道府縣／縣市／州」：長方形圓角卡片，大字行政區、小字城市（都可以點）。"""
    rs = sorted((r for r in regions if country is None or r["country"] == country),
                key=lambda r: (r["country"], -(r["lat"] or 0)))   # 同一國由北到南
    if not rs:
        return html
    cards = "".join(
        f'<div class="rcard{" done" if r["visited"] else ""}" style="--c:{r["color"]}">'
        f'<a class="rc-name" href="{root}{r["url"]}">{r["name"]}</a><span class="rc-cities">'
        + "・".join(f'<a href="{root}{c["url"]}">{c["name"]}</a>' for c in r["cities"]) + "</span></div>"
        for r in rs)
    return SECTION_RE.sub(lambda m: m.group(1) + f'<div class="rcards">{cards}</div>', html, count=1)


def routes(pages: dict) -> dict:
    """每趟旅程每天的計畫線（planned 順序）與實際線（GPX，沒有就用 actual 順序）。"""
    out: dict = {}
    coords = {s: (p.fm.get("lat"), p.fm.get("lng")) for s, p in pages.items() if p.type == "place"}
    for pg in pages.values():
        if pg.type != "day":
            continue
        fm = pg.fm
        trip = fm["trip"]

        def line(seq):
            pts = [coords[s] for s in (seq or []) if s in coords and coords[s][0] is not None]
            return [[round(a, 5), round(b, 5)] for a, b in pts]
        actual = []
        if fm.get("track") and (ROOT / fm["track"]).exists():
            gj = json.loads((ROOT / fm["track"]).read_text(encoding="utf-8"))
            actual = [[[c[1], c[0]] for c in seg] for seg in gj["geometry"]["coordinates"]]
            kind = gj.get("properties", {}).get("source", "gpx")   # gpx | sketch（Percy 手繪重建）
        else:
            seg = line(fm.get("actual"))
            actual = [seg] if len(seg) > 1 else []
            kind = "order"
        out.setdefault(trip, []).append({"day": fm.get("day"), "date": str(fm.get("date")),
                                         "url": url_of(pg), "plan": line(fm.get("planned")),
                                         "actual": actual, "actual_kind": kind})
    for v in out.values():
        v.sort(key=lambda d: d["day"])
    return out


def bounds(points):
    pts = [(a, b) for a, b in points if a is not None and b is not None]
    if not pts:
        return None
    return [[min(p[0] for p in pts), min(p[1] for p in pts)], [max(p[0] for p in pts), max(p[1] for p in pts)]]


def page_config(pg: Page, pages: dict) -> dict:
    fm, t = pg.fm, pg.type
    places = [p for p in pages.values() if p.type == "place"]
    cfg = {"type": t, "slug": pg.slug}
    sel = places
    if t == "place":
        cfg.update(center=[fm.get("lat"), fm.get("lng")], zoom=15)
        trips = [v.get("trip") for v in visits_of(pg)]
        cfg["trip"] = trips[0] if trips else None
        return cfg
    if t == "country":
        sel = [p for p in places if p.fm.get("country") == fm.get("country")]
    elif t == "city":
        sel = [p for p in places if p.fm.get("city") == pg.slug]
    elif t == "region":
        cities = {c.slug for c in pages.values() if c.type == "city" and c.fm.get("region") == pg.slug}
        sel = [p for p in places if p.fm.get("city") in cities]
    elif t == "trip":
        cfg["trip"] = pg.slug
        sel = [p for p in places if any(v.get("trip") == pg.slug and v.get("detail") != "dropped" for v in visits_of(p))]
    elif t == "day":
        cfg["trip"], cfg["day"] = fm.get("trip"), fm.get("day")
        names = set(fm.get("planned") or []) | set(fm.get("actual") or [])
        sel = [p for p in places if p.slug in names]
        cfg["only"] = sorted(names)
    elif t == "note":
        sel = [p for p in places if p.slug in (fm.get("about") or [])]
    b = bounds([(p.fm.get("lat"), p.fm.get("lng")) for p in sel])
    if b:
        cfg["fit"] = b
    elif fm.get("lat") is not None:
        cfg.update(center=[fm["lat"], fm["lng"]], zoom=fm.get("zoom", 10))
    return cfg


def infobox(pg: Page, pages: dict, root: str) -> list:
    """標題下方的資訊框（像維基百科的 infobox）。"""
    fm, rows = pg.fm, []

    def a(slug, text=None):
        p = pages.get(slug)
        return f'<a href="{root}{url_of(p)}">{text or p.title}</a>' if p else (text or slug)
    if pg.type == "place":
        rows.append(("類別", CAT_ZH.get(fm.get("category"), fm.get("category"))))
        if fm.get("lines"):
            rows.append(("路線", "、".join(fm["lines"])))
        rows.append(("城市", a(fm.get("city"))))
        for v in visits_of(pg):
            date = v.get("actual") or v.get("planned") or ""
            ev = "＋".join(v.get("evidence") or []) or "—"
            rows.append((a(v.get("trip"), pages[v["trip"]].title if v.get("trip") in pages else v.get("trip")),
                         f'<span class="badge s-{v.get("status")} d-{v.get("detail")}">{STATUS_ZH.get(skey(v), skey(v))}</span> {date}'
                         f'<br><small>證據：{ev}</small>'))
    elif pg.type == "trip":
        rows += [("期間", f"{fm.get('start')} ～ {fm.get('end')}"), ("狀態", {"planned": "規劃中", "ongoing": "旅行中", "completed": "已完成"}.get(fm.get("status"), fm.get("status"))),
                 ("國家", "、".join(a(c.lower()) for c in fm.get("countries", [])))]
    elif pg.type == "day":
        rows += [("日期", str(fm.get("date"))), ("旅程", a(fm.get("trip")))]
    elif pg.type == "city":
        rows += [("種類", "城市" if fm.get("kind") == "city" else "地區"), ("上層", a(fm.get("region"))),
                 ("國家", a(str(fm.get("country", "")).lower()))]
    elif pg.type == "region":
        rows += [("種類", REGION_KIND_ZH.get(fm.get("kind"), fm.get("kind"))), ("國家", a(str(fm.get("country", "")).lower()))]
    return rows


def main():
    pages = load_all()
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "data").mkdir(parents=True)
    shutil.copytree(TPL / "static", SITE / "static")
    if ASSETS.exists():
        shutil.copytree(ASSETS, SITE / "assets")

    places = [place_record(p, "") for p in pages.values() if p.type == "place"]
    trips = {p.slug: {"title": p.title, "color": p.fm.get("color", "#888"), "start": str(p.fm.get("start")),
                      "end": str(p.fm.get("end")), "status": p.fm.get("status"), "url": url_of(p)}
             for p in pages.values() if p.type == "trip"}
    cards_info = {}   # 卡片用的統計，不放進 wiki.json
    for p in pages.values():
        if p.type != "trip":
            continue
        vis = [(pl.fm.get("country"), v) for pl in pages.values() if pl.type == "place"
               for v in visits_of(pl) if v.get("trip") == p.slug]
        by_cc = {}
        for cc, v in vis:
            if v.get("status") == "visited":
                by_cc[cc] = by_cc.get(cc, 0) + 1
        cards_info[p.slug] = {**trips[p.slug], "countries": p.fm.get("countries") or [],
                              "days": sum(1 for d in pages.values() if d.type == "day" and d.fm.get("trip") == p.slug),
                              "visited": sum(by_cc.values()), "visited_by_cc": by_cc,
                              "planned": sum(1 for _, v in vis if v.get("status") == "planned")}
    regions = region_records(pages)
    (SITE / "data" / "boundaries.json").write_text(
        json.dumps(boundary_records(pages, regions), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    data = {"places": places, "trips": trips, "regions": regions, "countries": country_records(pages, regions),
            "routes": routes(pages),
            "status_zh": STATUS_ZH, "cat_zh": CAT_ZH, "cat_color": CATEGORY_COLORS, "today": TODAY}
    (SITE / "data" / "wiki.json").write_text(mask(json.dumps(data, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")

    env = Environment(loader=FileSystemLoader(TPL), autoescape=False)
    tpl = env.get_template("page.html")
    trips_sorted = sorted(trips.items(), key=lambda kv: kv[1]["start"], reverse=True)
    n = 0
    for pg in list(pages.values()) + [None]:
        if pg is None:   # 旅程列表頁
            url, title, body, cfg, rows, kind = "trips/", "全部旅程", "", {"type": "trips"}, [], "trips"
        else:
            url, title, kind = url_of(pg), pg.title, pg.type
            root = rel(url)
            body = render_body(pg, pages, root)
            cfg = page_config(pg, pages)
            rows = infobox(pg, pages, root)
            if pg.type == "trip":
                body = day_cards(body, pg, pages, root)
            if pg.type == "country":
                body = TRIPS_RE.sub(lambda m: "<h2>旅程</h2>" + trip_cards(cards_info, root, pg.fm.get("country")), body, count=1)
            if pg.slug in ("overview", "index"):
                extra = "<h2>旅程</h2>" + trip_cards(cards_info, root) if pg.slug == "overview" else ""   # 首頁：國家下面接旅程
                body = COUNTRIES_RE.sub(lambda m: "<h2>國家</h2>" + country_cards(pages, cards_info, regions, root) + extra, body, count=1)
            howto = HOWTO_RE.search(body)
            if howto:   # 「怎麼看」收合，移到最下面（和圖例放一起）
                body = body.replace(howto.group(0), "") + fold("怎麼看", howto.group(1))
            if pg.type == "country" or pg.slug == "index":
                body = region_cards(body, regions, root, pg.fm.get("country") if pg.type == "country" else None)
            if rows:
                box = '<table class="infobox">' + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows) + "</table>"
                body = body.replace("</p>", "</p>" + box, 1) if "</p>" in body else body + box
        root = rel(url)
        html = tpl.render(title=title, body=body, root=root, cfg=json.dumps(cfg, ensure_ascii=False),
                          kind=kind, cats=[(k, CAT_ZH[k], CATEGORY_COLORS[k]) for k in CATEGORY_COLORS], type_zh=TYPE_ZH.get(kind, ""), trips=trips_sorted, today=TODAY,
                          is_home=(url == ""), trip_cards=trip_cards(cards_info, root), updated=(pg.fm.get("updated") if pg else None))
        out = SITE / url / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(mask(html), encoding="utf-8")
        n += 1
    (SITE / ".nojekyll").write_text("")
    print(f"build 完成：{n} 頁，{len(places)} 個景點，{len(regions)} 個行政區，{len(trips)} 趟旅程 → site/（今天 {TODAY}）")


if __name__ == "__main__":
    main()
