from __future__ import annotations

import hashlib
import re
from datetime import datetime
from html import unescape

from bs4 import BeautifulSoup


def item_id(source: str, value: str) -> str:
    digest = hashlib.sha1(f"{source}:{value}".encode("utf-8")).hexdigest()[:16]
    return f"{source}-{digest}"


def clean_text(value: object) -> str:
    text = BeautifulSoup(unescape(str(value or "")), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def unix_to_iso(value: object) -> str | None:
    try:
        return datetime.fromtimestamp(int(value)).astimezone().isoformat()
    except (TypeError, ValueError, OSError):
        return None
