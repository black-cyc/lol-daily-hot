from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BEIJING_TZ, Settings
from services.clustering import cluster_items
from services.collector import collect_sources
from services.douyin_matcher import match_videos
from services.storage import save_history, write_dashboard
from sources.douyin import search_videos


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    now = datetime.now(BEIJING_TZ)
    results = collect_sources(settings)
    items = [item for result in results.values() for item in result.items]
    topics, cluster_mode = cluster_items(items, settings)
    if settings.douyin_search_api_url and settings.douyin_api_token:
        try:
            match_videos(topics, lambda keyword: search_videos(settings, keyword), now)
        except Exception as exc:
            logging.exception("Douyin video matching failed")
            existing = results.get("douyin")
            if existing and existing.status == "ok":
                existing.status = "failed"
                existing.error = f"视频匹配失败: {exc}"
    else:
        logging.info("Douyin video matching skipped because API search configuration is absent")
    payload = write_dashboard(results, topics, cluster_mode, now)
    save_history(payload["date"], payload["generated_at"], results, topics, cluster_mode)
    logging.info("Wrote dashboard for %s with %s topics", payload["date"], len(topics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
