from __future__ import annotations

from typing import Any, TypeGuard

from ..errors import InvalidSurface, RecordNotFound


def _is_record_list(value: Any) -> TypeGuard[list[dict[str, Any]]]:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def extract_records(data: Any, *, preferred_keys: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    if _is_record_list(data):
        return data

    if isinstance(data, dict):
        for key in preferred_keys:
            value = data.get(key)
            if _is_record_list(value):
                return value

        candidates = [value for value in data.values() if _is_record_list(value)]
        if len(candidates) == 1:
            return candidates[0]

    raise InvalidSurface("Could not find a list of records in the loaded JSON surface")


def find_record(
    records: list[dict[str, Any]],
    *,
    field: str,
    value: str,
) -> dict[str, Any]:
    for record in records:
        if str(record.get(field, "")).casefold() == value.casefold():
            return record

    raise RecordNotFound(f"Could not find record where {field!r} == {value!r}")
