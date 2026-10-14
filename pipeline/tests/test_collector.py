from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Settings
from models import ContentItem
from services.collector import collect_sources


def settings() -> Settings:
    return Settings(2, None, "https://example.test/v1", None, None, None, None)


class CollectorTests(unittest.TestCase):
    def test_one_source_failure_does_not_stop_other_sources(self) -> None:
        def healthy(_: Settings) -> list[ContentItem]:
            return [ContentItem("a", "healthy", "标题", "https://example.test")]

        def broken(_: Settings) -> list[ContentItem]:
            raise RuntimeError("expected failure")

        results = collect_sources(settings(), {"healthy": healthy, "broken": broken})
        self.assertEqual(results["healthy"].status, "ok")
        self.assertEqual(results["healthy"].status_dict()["count"], 1)
        self.assertEqual(results["broken"].status, "failed")
        self.assertIn("expected failure", results["broken"].error or "")
