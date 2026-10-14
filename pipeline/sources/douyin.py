from __future__ import annotations

from typing import Any

import requests

from config import Settings
from models import ContentItem
from sources.common import clean_text, item_id


NAME = "douyin"


def _headers(settings: Settings) -> dict[str, str]:
    if not settings.douyin_api_token:
        raise RuntimeError("未配置 DOUYIN_API_TOKEN")
    return {"Authorization": f"Bearer {settings.douyin_api_token}", "Accept": "application/json"}


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise RuntimeError("抖音 API 响应不是对象或数组")
    data = payload.get("data", payload)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        rows = data.get("items") or data.get("list") or data.get("data")
        if isinstance(rows, list):
            return rows
    rows = payload.get("items") or payload.get("list")
    if isinstance(rows, list):
        return rows
    raise RuntimeError("抖音 API 响应缺少 items/list 数组")


def collect(settings: Settings) -> list[ContentItem]:
    if not settings.douyin_hot_api_url:
        raise RuntimeError("未配置 DOUYIN_HOT_API_URL")
    response = requests.get(
        settings.douyin_hot_api_url,
        headers=_headers(settings),
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    items: list[ContentItem] = []
    for row in _items(response.json()):
        keyword = clean_text(row.get("keyword") or row.get("title") or row.get("word"))
        if not keyword or "英雄联盟" not in keyword.lower() and "lol" not in keyword.lower() and "lpl" not in keyword.lower():
            continue
        items.append(
            ContentItem(
                id=item_id(NAME, keyword),
                source=NAME,
                title=keyword,
                url=str(row.get("url") or "https://www.douyin.com/hot"),
                description="抖音热榜相关词条",
                metrics={"hot_value": row.get("hot_value", 0), "rank": row.get("rank", 0)},
                keywords=[keyword, "英雄联盟"],
            )
        )
    return items


def search_videos(settings: Settings, keyword: str) -> list[dict[str, Any]]:
    if not settings.douyin_search_api_url:
        raise RuntimeError("未配置 DOUYIN_SEARCH_API_URL")
    response = requests.get(
        settings.douyin_search_api_url,
        params={"keyword": keyword},
        headers=_headers(settings),
        timeout=settings.request_timeout,
    )
    response.raise_for_status()
    videos: list[dict[str, Any]] = []
    for row in _items(response.json()):
        video_id = str(row.get("id") or row.get("aweme_id") or row.get("url") or "")
        title = clean_text(row.get("title") or row.get("description") or row.get("desc"))
        if not video_id or not title:
            continue
        videos.append(
            {
                "id": video_id,
                "title": title,
                "url": str(row.get("url") or row.get("share_url") or ""),
                "author": clean_text(row.get("author") or row.get("author_name")),
                "like_count": row.get("like_count") or row.get("digg_count") or 0,
                "published_at": row.get("published_at") or row.get("create_time"),
                "description": clean_text(row.get("description") or row.get("desc")),
            }
        )
    return videos
