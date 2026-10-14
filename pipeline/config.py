from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"
DOCS_DATA_DIR = ROOT_DIR / "docs" / "data"
HISTORY_DB = PIPELINE_DIR / "data" / "history.sqlite3"
# China Standard Time has no daylight-saving transitions. A fixed offset also
# works on Windows Python installations that do not ship an IANA tz database.
BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


@dataclass(frozen=True)
class Settings:
    request_timeout: int
    kimi_api_key: str | None
    kimi_base_url: str
    kimi_model: str | None
    douyin_hot_api_url: str | None
    douyin_search_api_url: str | None
    douyin_api_token: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "20")),
            kimi_api_key=os.getenv("KIMI_API_KEY") or None,
            kimi_base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/"),
            kimi_model=os.getenv("KIMI_MODEL") or None,
            douyin_hot_api_url=os.getenv("DOUYIN_HOT_API_URL") or None,
            douyin_search_api_url=os.getenv("DOUYIN_SEARCH_API_URL") or None,
            douyin_api_token=os.getenv("DOUYIN_API_TOKEN") or None,
        )
