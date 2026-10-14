from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Settings
from models import ContentItem
from services.clustering import cluster_items


class ClusteringTests(unittest.TestCase):
    def test_missing_llm_config_falls_back_to_local_topics(self) -> None:
        items = [
            ContentItem(f"id-{number}", "bilibili", f"LPL 季后赛焦点内容 {number}", "https://example.test")
            for number in range(15)
        ]
        settings = Settings(2, None, "https://example.test/v1", None, None, None, None)
        topics, mode = cluster_items(items, settings)
        self.assertEqual(mode, "local")
        self.assertGreater(len(topics), 0)
        self.assertLessEqual(len(topics), 10)
        self.assertTrue(all(len(topic.summary.split("。")) >= 2 for topic in topics))
