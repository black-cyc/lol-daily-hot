from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from config import BEIJING_TZ
from models import Topic


def _published_at(value: Any) -> datetime | None:
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        try:
            return datetime.fromtimestamp(int(value), tz=BEIJING_TZ)
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(BEIJING_TZ) if parsed.tzinfo else parsed.replace(tzinfo=BEIJING_TZ)
        except ValueError:
            return None
    return None


def _score(topic: Topic, video: dict[str, Any]) -> int:
    text = f"{video.get('title', '')} {video.get('description', '')}".lower()
    return sum(1 for keyword in topic.keywords if keyword.lower() in text)


def match_videos(topics: list[Topic], search: Any, now: datetime | None = None) -> None:
    now = now or datetime.now(BEIJING_TZ)
    threshold = now - timedelta(hours=72)
    candidates: dict[str, dict[str, Any]] = {}
    for topic in topics:
        for keyword in topic.keywords[:6]:
            for video in search(keyword):
                published = _published_at(video.get("published_at"))
                if not published or published < threshold or published > now + timedelta(minutes=5):
                    continue
                video_id = str(video.get("id") or video.get("url"))
                if video_id:
                    candidates[video_id] = video
    assigned: dict[str, list[dict[str, Any]]] = {topic.id: [] for topic in topics}
    for video in candidates.values():
        scores = [(index, _score(topic, video)) for index, topic in enumerate(topics)]
        best_index, best_score = max(scores, key=lambda pair: (pair[1], -pair[0]))
        if best_score > 0:
            assigned[topics[best_index].id].append(video)
    for topic in topics:
        topic.douyin_videos = sorted(assigned[topic.id], key=lambda video: int(video.get("like_count") or 0), reverse=True)[:5]
