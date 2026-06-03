"""Checkpoint kind inference helpers."""

from __future__ import annotations

import re
from typing import Literal


CheckpointKind = Literal[
    "manual",
    "commit",
    "verify_green",
    "pr_opened",
    "pr_merged",
    "pause",
    "owner_followthrough",
]


def infer_auto_checkpoint_kind(*, intent_text: str) -> CheckpointKind:
    normalized = re.sub(r"[\s_-]+", " ", intent_text.strip().lower())
    if any(token in normalized for token in ("owner follow through", "owner handoff", "follow through")):
        return "owner_followthrough"
    if any(token in normalized for token in ("pull request merged", "pr merged", "merged pr", "merge complete")):
        return "pr_merged"
    if any(token in normalized for token in ("pull request", "open pr", "pr open", "review thread")):
        return "pr_opened"
    if any(
        token in normalized
        for token in (
            "verify green",
            "green verify",
            "all green",
            "tests green",
            "verified",
            "verification",
            "verify",
        )
    ):
        return "verify_green"
    if any(token in normalized for token in ("resume later", "continue later", "pick up later", "pause")):
        return "pause"
    if "checkpoint" in normalized or "commit" in normalized:
        return "commit"
    return "commit"
