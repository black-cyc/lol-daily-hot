from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class ContentItem:
    id: str
    source: str
    title: str
    url: str
    description: str = ""
    author: str = ""
    published_at: str | None = None
    metrics: dict[str, int | float | str] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceResult:
    source: str
    status: str
    items: list[ContentItem] = field(default_factory=list)
    error: str | None = None
    collected_at: str = field(default_factory=lambda: datetime.now(timezone(timedelta(hours=8))).isoformat())

    def status_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "count": len(self.items),
            "error": self.error,
            "collected_at": self.collected_at,
        }


@dataclass
class Topic:
    id: str
    title: str
    summary: str
    keywords: list[str]
    items: list[ContentItem]
    douyin_videos: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "keywords": self.keywords,
            "items": [item.to_dict() for item in self.items],
            "douyin_videos": self.douyin_videos,
        }
