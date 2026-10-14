from __future__ import annotations

from urllib.parse import quote

import requests

from config import Settings
from models import ContentItem
from sources.common import clean_text, item_id, unix_to_iso


NAME = "bilibili"
SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"


def collect(settings: Settings) -> list[ContentItem]:
    response = requests.get(
        SEARCH_URL,
        params={"search_type": "video", "keyword": "英雄联盟", "order": "click", "page": 1},
        headers={"User-Agent": "Mozilla/5.0 (compatible; LOLDailyMonitor/1.0)"},
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") not in (0, None):
        raise RuntimeError(f"B站接口返回 code={payload.get('code')}: {payload.get('message', '')}")

    results = (payload.get("data") or {}).get("result") or []
    items: list[ContentItem] = []
    for row in results[:30]:
        bvid = row.get("bvid") or row.get("aid") or row.get("arcurl")
        if not bvid:
            continue
        url = row.get("arcurl") or f"https://www.bilibili.com/video/{bvid}"
        title = clean_text(row.get("title"))
        if not title:
            continue
        items.append(
            ContentItem(
                id=item_id(NAME, str(bvid)),
                source=NAME,
                title=title,
                url=url,
                description=clean_text(row.get("description")),
                author=clean_text(row.get("author")),
                published_at=unix_to_iso(row.get("pubdate")),
                metrics={"views": row.get("play", 0), "comments": row.get("video_review", 0)},
                keywords=["英雄联盟"],
            )
        )
    return items
