"""照片 → 公開用 WebP（AGENTS.md 6.4）：360p、清掉所有中繼資料、對應到景點。

用法：
  uv run scripts/photos.py              # 處理 raw/photos/ 底下所有照片（原檔保留）
  uv run scripts/photos.py --delete-raw # 處理成功後刪掉 raw 原檔（省空間）
  uv run scripts/photos.py --regions    # 行政區大圓圖片：raw/regions/<region>.* → assets/regions/<region>.webp

對應景點的順序：
  1. 檔名含景點中文名（例：淨土之濱.jpg → jodogahama；差一兩個字的錯字也算）
  2. EXIF 有 GPS → 半徑內最近的景點（5.3 的半徑）
  3. 拍攝時間 ＋ 當天 GPX 位置 → 最近的景點
  都對不到就列為「未對應」，原檔保留，請 Percy 決定。

輸出：
  assets/photos/<place>/YYYYMMDD-NN.webp        短邊 360 px（不放大），WebP 品質 80
  assets/photos/<place>/YYYYMMDD-NN-thumb.webp  短邊 160 px
並印出每張照片原本帶了哪些中繼資料（EXIF、GPS、相機型號、ICC…），全部不寫進新檔。
"""
from __future__ import annotations

import sys
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml
from PIL import ExifTags, Image, ImageOps

from common import ASSETS, RAW, WIKI, haversine, radius_for

EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
SHORT, THUMB = 360, 160


def load_places():
    out = []
    for p in (WIKI / "places").rglob("*.md"):
        fm = yaml.safe_load(p.read_text(encoding="utf-8").split("---")[1])
        fm["_names"] = [n for n in str(fm["title"]).split(" ") if n]
        out.append(fm)
    return out


def gps(exif):
    g = exif.get_ifd(0x8825)
    if not g or 2 not in g or 4 not in g:
        return None

    def deg(v, ref):
        d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
        return -d if ref in ("S", "W") else d
    return deg(g[2], g.get(1, "N")), deg(g[4], g.get(3, "E"))


def taken(exif):
    s = exif.get_ifd(0x8769).get(36867) or exif.get(306)
    try:
        return datetime.strptime(str(s), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def metadata_summary(img, exif) -> list[str]:
    """列出原檔帶了哪些資訊（新檔都不會帶）。"""
    out = []
    names = {ExifTags.TAGS.get(k, str(k)) for k in exif}
    if exif.get_ifd(0x8825):
        out.append("GPS 座標")
    if {"Make", "Model"} & names:
        out.append(f"相機型號（{exif.get(271, '')} {exif.get(272, '')}".strip() + "）")
    if exif.get_ifd(0x8769) or "DateTime" in names:
        out.append("拍攝時間與相機參數（光圈、快門、ISO…）")
    if "Software" in names:
        out.append(f"軟體（{exif.get(305)}）")
    if exif.get_ifd(0x8769).get(37500):
        out.append("廠商私有資料（MakerNote）")
    for k, label in (("icc_profile", "色彩描述檔"), ("xmp", "XMP"), ("comment", "註解")):
        if k in img.info:
            out.append(label)
    return out or ["（沒有中繼資料）"]


def nearest(places, lat, lng):
    c = [(haversine(lat, lng, p["lat"], p["lng"]), p) for p in places if p.get("lat") is not None]
    c = [x for x in c if x[0] <= radius_for(x[1].get("category", ""))]
    return min(c, key=lambda x: x[0])[1] if c else None


def gpx_position(when: datetime):
    """用拍攝時間（當地時間）在 GPX 找最接近的點。只找日本旅程以外的也通用：掃 raw/gpx 全部。"""
    try:
        from tracks import load_points
    except ImportError:
        return None
    best = None
    for trip_dir in (RAW / "gpx").iterdir():
        if not trip_dir.is_dir():
            continue
        from common import trip_meta
        try:
            meta = trip_meta(trip_dir.name)
        except SystemExit:
            continue
        tz = ZoneInfo(meta["timezone"])
        t = when.replace(tzinfo=tz)
        for p in load_points(trip_dir.name, tz, meta["countries"]):
            d = abs((p[0] - t).total_seconds())
            if d < 600 and (best is None or d < best[0]):
                best = (d, p[1], p[2])
    return (best[1], best[2]) if best else None


def save_clean(img, path, short):
    im = ImageOps.exif_transpose(img).convert("RGB")
    w, h = im.size
    k = min(1.0, short / min(w, h))
    im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
    clean = Image.new("RGB", im.size)      # 全新的影像，不帶任何中繼資料
    clean.paste(im)
    clean.save(path, "WEBP", quality=80, method=6)
    return clean.size


def main(delete_raw: bool):
    places = load_places()
    counter, done, unmatched = defaultdict(int), [], []
    files = sorted(f for f in (RAW / "photos").rglob("*") if f.suffix.lower() in EXT)
    for f in files:
        img = Image.open(f)
        exif = img.getexif()
        when = taken(exif)
        best, how = None, ""
        # 1. 檔名：完全包含景點名，或差一兩個字（打錯字，相似度 ≥ 0.75）
        score = max(((max((1.0 if n in f.stem else SequenceMatcher(None, n, f.stem).ratio())
                           for n in p["_names"]), i) for i, p in enumerate(places)), default=(0, -1))
        if score[0] >= 0.75:
            best, how = places[score[1]], "檔名" if score[0] == 1.0 else f"檔名（相似度 {score[0]:.2f}）"
        if not best and (loc := gps(exif)):
            best, how = nearest(places, *loc), "GPS"
        if not best and when and (pos := gpx_position(when)):
            best, how = nearest(places, *pos), "時間＋GPX"
        if not best or not when:
            unmatched.append(f"{f.name}（{'沒有拍攝時間' if not when else '對不到景點'}）")
            continue
        slug, day = best["slug"], when.strftime("%Y%m%d")
        counter[(slug, day)] += 1
        name = f"{day}-{counter[(slug, day)]:02d}"
        out = ASSETS / "photos" / slug
        out.mkdir(parents=True, exist_ok=True)
        size = save_clean(img, out / f"{name}.webp", SHORT)
        save_clean(img, out / f"{name}-thumb.webp", THUMB)
        kb = (out / f"{name}.webp").stat().st_size // 1024
        print(f"{f.name} → assets/photos/{slug}/{name}.webp  {img.size[0]}×{img.size[1]} → {size[0]}×{size[1]}，{kb} KB（對應方式：{how}）")
        print(f"   拿掉：{'、'.join(metadata_summary(img, exif))}")
        print(f"   景點頁貼上：![{best['_names'][0]}](../../../assets/photos/{slug}/{name}.webp)")
        done.append(f)
    if delete_raw:
        for f in done:
            f.unlink()
        print(f"\n已刪除 {len(done)} 個 raw 原檔")
    if unmatched:
        print("\n未對應（原檔保留，問 Percy）：", "、".join(unmatched))


def regions(delete_raw: bool):
    """行政區圖片：置中裁成正方形 160 px、清中繼資料。"""
    out = ASSETS / "regions"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted((RAW / "regions").glob("*")):
        if f.suffix.lower() not in EXT:
            continue
        img = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        side = min(img.size)
        x, y = (img.width - side) // 2, (img.height - side) // 2
        im = img.crop((x, y, x + side, y + side)).resize((160, 160), Image.LANCZOS)
        clean = Image.new("RGB", im.size)
        clean.paste(im)
        clean.save(out / f"{f.stem}.webp", "WEBP", quality=85, method=6)
        print(f"{f.name} → assets/regions/{f.stem}.webp（到 wiki/regions/{f.stem}.md 把 icon 填上）")
        if delete_raw:
            f.unlink()


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--regions" in args:
        regions("--delete-raw" in args)
    else:
        main("--delete-raw" in args)
