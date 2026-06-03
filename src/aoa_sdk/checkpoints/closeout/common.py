"""Shared small helpers for checkpoint closeout pipeline branches."""

from __future__ import annotations


def _dict_records(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_field(mapping: dict[str, object] | None, key: str) -> str | None:
    value = mapping.get(key) if mapping is not None else None
    return value if isinstance(value, str) and value else None


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
