from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import BEIJING_TZ, DOCS_DATA_DIR, HISTORY_DB
from models import SourceResult, Topic


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (date TEXT PRIMARY KEY, generated_at TEXT NOT NULL, cluster_mode TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS source_status (date TEXT, source TEXT, status TEXT, count INTEGER, error TEXT, PRIMARY KEY(date, source));
        CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, date TEXT, source TEXT, title TEXT, url TEXT, payload TEXT);
        CREATE TABLE IF NOT EXISTS topics (id TEXT, date TEXT, title TEXT, summary TEXT, keywords TEXT, PRIMARY KEY(id, date));
        CREATE TABLE IF NOT EXISTS topic_items (date TEXT, topic_id TEXT, item_id TEXT, PRIMARY KEY(date, topic_id, item_id));
        """
    )
    return connection


def save_history(date: str, generated_at: str, results: dict[str, SourceResult], topics: list[Topic], cluster_mode: str, path: Path = HISTORY_DB) -> None:
    with _connect(path) as connection:
        connection.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?)", (date, generated_at, cluster_mode))
        connection.execute("DELETE FROM source_status WHERE date = ?", (date,))
        connection.execute("DELETE FROM topics WHERE date = ?", (date,))
        connection.execute("DELETE FROM topic_items WHERE date = ?", (date,))
        for result in results.values():
            connection.execute("INSERT INTO source_status VALUES (?, ?, ?, ?, ?)", (date, result.source, result.status, len(result.items), result.error))
            for item in result.items:
                connection.execute("INSERT OR REPLACE INTO items VALUES (?, ?, ?, ?, ?, ?)", (item.id, date, item.source, item.title, item.url, json.dumps(item.to_dict(), ensure_ascii=False)))
        for topic in topics:
            connection.execute("INSERT INTO topics VALUES (?, ?, ?, ?, ?)", (topic.id, date, topic.title, topic.summary, json.dumps(topic.keywords, ensure_ascii=False)))
            connection.executemany("INSERT INTO topic_items VALUES (?, ?, ?)", [(date, topic.id, item.id) for item in topic.items])


def write_dashboard(results: dict[str, SourceResult], topics: list[Topic], cluster_mode: str, now: datetime | None = None, data_dir: Path = DOCS_DATA_DIR) -> dict[str, Any]:
    now = now or datetime.now(BEIJING_TZ)
    date = now.date().isoformat()
    payload = {
        "date": date,
        "generated_at": now.isoformat(),
        "sources": {name: result.status_dict() for name, result in results.items()},
        "topics": [topic.to_dict() for topic in topics],
        "meta": {"cluster_mode": cluster_mode, "item_count": sum(len(result.items) for result in results.values())},
    }
    daily_path = data_dir / f"{date}.json"
    _atomic_json(daily_path, payload)
    _atomic_json(data_dir / "latest.json", payload)
    existing_dates: list[str] = []
    index_path = data_dir / "index.json"
    if index_path.exists():
        try:
            existing_dates = json.loads(index_path.read_text(encoding="utf-8")).get("dates", [])
        except (OSError, json.JSONDecodeError):
            existing_dates = []
    _atomic_json(index_path, {"dates": sorted(set(existing_dates + [date]), reverse=True)})
    return payload
