from __future__ import annotations

import logging
from collections.abc import Callable

from config import Settings
from models import ContentItem, SourceResult
from sources import bilibili, douyin, hupu, weibo


SourceCollector = Callable[[Settings], list[ContentItem]]
DEFAULT_SOURCES: dict[str, SourceCollector] = {
    bilibili.NAME: bilibili.collect,
    weibo.NAME: weibo.collect,
    hupu.NAME: hupu.collect,
    douyin.NAME: douyin.collect,
}


def collect_sources(settings: Settings, sources: dict[str, SourceCollector] | None = None) -> dict[str, SourceResult]:
    results: dict[str, SourceResult] = {}
    for name, collector in (sources or DEFAULT_SOURCES).items():
        try:
            items = collector(settings)
            results[name] = SourceResult(source=name, status="ok", items=items)
            logging.info("%s collected %s items", name, len(items))
        except Exception as exc:  # A source must never prevent the daily report.
            logging.exception("%s collection failed", name)
            results[name] = SourceResult(source=name, status="failed", error=str(exc))
    return results
