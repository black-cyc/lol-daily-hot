from __future__ import annotations

from urllib.parse import quote

import requests

from config import Settings
from models import ContentItem
from sources.common import clean_text, item_id


NAME = "weibo"
HOT_URL = "https://weibo.com/ajax/side/hotSearch"
LOL_TERMS = ("英雄联盟", "lol", "lpl", "lck", "msi", "s赛", "世界赛", "rng", "tes", "edg", "blg", "ig")


def _relevant(title: str) -> bool:
    lowered = title.lower()
    return any(term in lowered for term in LOL_TERMS)


def collect(settings: Settings) -> list[ContentItem]:
    response = requests.get(
        HOT_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LOLDailyMonitor/1.0)",
            "Referer": "https://weibo.com/hot/search",
        },
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    rows = ((response.json().get("data") or {}).get("realtime")) or []
    items: list[ContentItem] = []
    for row in rows:
        title = clean_text(row.get("note") or row.get("word"))
        if not title or not _relevant(title):
            continue
        query = row.get("word_scheme") or title
        items.append(
            ContentItem(
                id=item_id(NAME, title),
                source=NAME,
                title=title,
                url=f"https://s.weibo.com/weibo?q={quote(str(query))}",
                description=clean_text(row.get("label_name")),
                metrics={"hot_value": row.get("num", 0), "rank": row.get("rank", 0)},
                keywords=["英雄联盟"],
            )
        )
    return items
