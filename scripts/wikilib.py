"""build.py 與 lint.py 共用：讀 wiki 頁、解析 [[連結]]、算網址。需要 PyYAML。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from common import WIKI

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]")
SPECIAL = {"overview": "", "index": "wiki/", "log": "log/"}


@dataclass
class Page:
    path: Path
    fm: dict
    body: str
    slug: str
    type: str
    links: list = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.fm.get("title") or self.slug


def parse(path: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    fm, body = {}, text
    if text.startswith("---\n"):
        _, raw, body = text.split("---\n", 2)
        fm = yaml.safe_load(raw) or {}
    if path.parent == WIKI and path.stem in SPECIAL:
        slug, typ = path.stem, "special"
        fm.setdefault("title", {"overview": "全部旅程總覽", "index": "索引", "log": "工作紀錄"}[path.stem])
    else:
        slug, typ = str(fm.get("slug", path.stem)), fm.get("type", "?")
    return Page(path, fm, body, slug, typ, [m.group(1).strip() for m in LINK_RE.finditer(body)])


def load_all() -> dict[str, Page]:
    pages: dict[str, Page] = {}
    for p in sorted(WIKI.rglob("*.md")):
        pg = parse(p)
        pages.setdefault(pg.slug, pg)
    return pages


def load_all_list() -> list[Page]:
    return [parse(p) for p in sorted(WIKI.rglob("*.md"))]


def url_of(pg: Page) -> str:
    """相對於網站根目錄的網址（結尾是 /）。"""
    t, s = pg.type, pg.slug
    if t == "special":
        return SPECIAL[s]
    if t == "day":
        trip, day = s.split("/")
        return f"trips/{trip}/{day}/"
    folder = {"place": "places", "trip": "trips", "city": "cities", "region": "regions",
              "country": "countries", "note": "notes"}[t]
    return f"{folder}/{s}/"


def expected_path(pg: Page) -> Path | None:
    """依 AGENTS.md 3.1 這頁應該放的位置。"""
    t, fm = pg.type, pg.fm
    if t == "place":
        return WIKI / "places" / str(fm.get("city")) / f"{pg.slug}.md"
    if t == "day":
        trip, day = pg.slug.split("/") if "/" in pg.slug else ("?", pg.slug)
        return WIKI / "days" / trip / f"{day}.md"
    folder = {"trip": "trips", "city": "cities", "region": "regions", "country": "countries", "note": "notes"}.get(t)
    return WIKI / folder / f"{pg.slug}.md" if folder else None
