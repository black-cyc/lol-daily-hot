from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

import requests

from config import Settings
from models import ContentItem, Topic


def _tokens(text: str) -> list[str]:
    clean = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text.lower())
    tokens = re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", clean)
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", clean))
    tokens.extend(chinese[i : i + 2] for i in range(max(0, len(chinese) - 1)))
    return [token for token in tokens if token not in {"英雄", "联盟", "英雄联盟"}]


def _topic_from_group(number: int, items: list[ContentItem], keywords: list[str]) -> Topic:
    lead = items[0].title
    title = lead if len(lead) <= 28 else f"{lead[:28]}..."
    source_names = "、".join(sorted({item.source for item in items}))
    summary = f"该话题汇集了 {len(items)} 条来自 {source_names} 的相关内容。"
    summary += "内容按标题关键词和热度信号归并，适合继续追踪创作角度。"
    return Topic(id=f"topic-{number}", title=title, summary=summary, keywords=keywords[:6] or ["英雄联盟"], items=items)


def local_cluster(items: list[ContentItem], limit: int = 10) -> list[Topic]:
    groups: dict[str, list[ContentItem]] = defaultdict(list)
    group_tokens: dict[str, list[str]] = {}
    for item in items:
        tokens = _tokens(f"{item.title} {item.description}")
        key = tokens[0] if tokens else item.source
        groups[key].append(item)
        group_tokens.setdefault(key, tokens)
    ranked = sorted(groups.items(), key=lambda pair: (-len(pair[1]), pair[0]))[:limit]
    return [_topic_from_group(index + 1, group, group_tokens[key]) for index, (key, group) in enumerate(ranked)]


def _parse_llm_content(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I)
    parsed = json.loads(content)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("topics"), list):
        raise ValueError("LLM 响应缺少 topics 数组")
    return parsed


def _llm_cluster(items: list[ContentItem], settings: Settings) -> list[Topic]:
    if not settings.kimi_api_key or not settings.kimi_model:
        raise RuntimeError("未配置 KIMI_API_KEY 或 KIMI_MODEL")
    catalog = [{"index": index, "source": item.source, "title": item.title, "description": item.description} for index, item in enumerate(items[:80])]
    prompt = (
        "将以下英雄联盟内容归并为不超过10个热点。仅返回 JSON："
        '{"topics":[{"name":"一句话名称","summary":"2-3句热度说明","keywords":["检索词"],"item_indexes":[0]}]}。'
        "每个条目最多归属一个话题。\n" + json.dumps(catalog, ensure_ascii=False)
    )
    response = requests.post(
        f"{settings.kimi_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.kimi_api_key}", "Content-Type": "application/json"},
        json={"model": settings.kimi_model, "temperature": 0.2, "messages": [{"role": "user", "content": prompt}]},
        timeout=settings.request_timeout * 3,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = _parse_llm_content(content)
    used: set[int] = set()
    topics: list[Topic] = []
    for raw in parsed["topics"][:10]:
        indexes = [index for index in raw.get("item_indexes", []) if isinstance(index, int) and 0 <= index < len(items) and index not in used]
        if not indexes:
            continue
        used.update(indexes)
        name = str(raw.get("name") or "英雄联盟热点").strip()
        summary = str(raw.get("summary") or "今日相关内容正在持续升温。请结合原始内容判断创作方向。").strip()
        keywords = [str(word).strip() for word in raw.get("keywords", []) if str(word).strip()][:6] or ["英雄联盟"]
        topics.append(Topic(id=f"topic-{len(topics) + 1}", title=name[:60], summary=summary, keywords=keywords, items=[items[index] for index in indexes]))
    if not topics:
        raise ValueError("LLM 没有返回有效话题")
    return topics


def cluster_items(items: list[ContentItem], settings: Settings) -> tuple[list[Topic], str]:
    if not items:
        return [], "local"
    try:
        return _llm_cluster(items, settings), "llm"
    except Exception:
        return local_cluster(items), "local"
