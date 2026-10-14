from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import Settings
from models import ContentItem
from sources.common import clean_text, item_id


NAME = "hupu"
FORUM_URL = "https://bbs.hupu.com/lol"


def collect(settings: Settings) -> list[ContentItem]:
    response = requests.get(
        FORUM_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LOLDailyMonitor/1.0)"},
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    seen: set[str] = set()
    items: list[ContentItem] = []
    for anchor in soup.select("a[href]"):
        title = clean_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href") or ""
        url = urljoin(FORUM_URL, href)
        if len(title) < 6 or url in seen or "bbs.hupu.com" not in url:
            continue
        if not any(marker in href for marker in ("/", "thread")):
            continue
        seen.add(url)
        items.append(
            ContentItem(
                id=item_id(NAME, url),
                source=NAME,
                title=title,
                url=url,
                keywords=["英雄联盟"],
            )
        )
        if len(items) == 30:
            break
    if not items:
        raise RuntimeError("虎扑页面未解析到可用帖子，页面结构可能已变更")
    return items
