from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import BEIJING_TZ
from models import ContentItem, SourceResult, Topic
from services.storage import save_history, write_dashboard


class StorageTests(unittest.TestCase):
    def test_writes_daily_latest_index_and_sqlite(self) -> None:
        item = ContentItem("item-1", "bilibili", "测试内容", "https://example.test")
        result = SourceResult("bilibili", "ok", [item])
        topic = Topic("topic-1", "测试话题", "第一句。第二句。", ["测试"], [item])
        now = datetime(2026, 10, 14, 9, tzinfo=BEIJING_TZ)
        root = Path(__file__).resolve().parent / ".test-output"
        data_dir = root / "docs-data"
        for path in [data_dir / "2026-10-14.json", data_dir / "latest.json", data_dir / "index.json", root / "history.sqlite3"]:
            path.unlink(missing_ok=True)
        payload = write_dashboard({"bilibili": result}, [topic], "local", now, data_dir)
        self.assertTrue((data_dir / "2026-10-14.json").exists())
        self.assertEqual(json.loads((data_dir / "index.json").read_text(encoding="utf-8"))["dates"], ["2026-10-14"])
        save_history(payload["date"], payload["generated_at"], {"bilibili": result}, [topic], "local", root / "history.sqlite3")
        self.assertTrue((root / "history.sqlite3").exists())
