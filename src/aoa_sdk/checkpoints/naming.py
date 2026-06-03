"""Shared checkpoint slug naming helpers."""

from __future__ import annotations

import re


def safe_checkpoint_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "session"
