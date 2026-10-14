from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import BEIJING_TZ
from models import Topic
from services.douyin_matcher import match_videos


class DouyinMatcherTests(unittest.TestCase):
    def test_filters_sorts_and_assigns_a_video_once(self) -> None:
        now = datetime(2026, 10, 14, 9, tzinfo=BEIJING_TZ)
        fresh = (now - timedelta(hours=1)).isoformat()
        old = (now - timedelta(hours=73)).isoformat()
        topics = [
            Topic("one", "赛事", "说明。说明。", ["lpl", "英雄联盟"], []),
            Topic("two", "版本", "说明。说明。", ["版本", "英雄联盟"], []),
        ]
        videos = [
            {"id": "shared", "title": "LPL 英雄联盟版本讨论", "description": "lpl", "published_at": fresh, "like_count": 10},
            {"id": "high", "title": "LPL 赛场回顾", "description": "lpl", "published_at": fresh, "like_count": 99},
            {"id": "old", "title": "LPL 旧视频", "description": "lpl", "published_at": old, "like_count": 999},
        ]

        match_videos(topics, lambda _: videos, now)
        assigned_ids = [video["id"] for topic in topics for video in topic.douyin_videos]
        self.assertNotIn("old", assigned_ids)
        self.assertEqual(len(assigned_ids), len(set(assigned_ids)))
        self.assertEqual(topics[0].douyin_videos[0]["id"], "high")
        self.assertLessEqual(len(topics[0].douyin_videos), 5)
