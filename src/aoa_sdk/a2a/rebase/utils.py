from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, TypeVar, cast
import re


T = TypeVar("T")


def utc_now_z() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return cleaned or "item"


def unique_preserve_order(items: Iterable[T]) -> list[T]:
    seen: set[Any] = set()
    result: list[T] = []
    for item in items:
        marker = repr(item)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {
            key: to_jsonable(item) for key, item in asdict(cast(Any, value)).items()
        }
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return value
