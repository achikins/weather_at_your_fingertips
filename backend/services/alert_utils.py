from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any

def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()

def format_city_name(name: str | None) -> str | None:
    if not name:
        return None
    trimmed = name.strip()
    if trimmed.isupper() or trimmed.islower():
        return trimmed.title()
    return trimmed

def normalize_string_list(items: Any, max_items: int) -> list[str]:
    if not isinstance(items, list):
        return []
    normalized: list[str] = []
    for raw in items:
        clean = clean_text(str(raw) if raw is not None else "")
        if clean:
            normalized.append(clean)
        if len(normalized) >= max_items:
            break
    return normalized

def as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
