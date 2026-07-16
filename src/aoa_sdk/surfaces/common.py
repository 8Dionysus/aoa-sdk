from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from ..models import RoutingOwnerLayerShortlistHint, SurfaceOpportunityReference
from ..workspace.discovery import Workspace


SurfacePhase = Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"]
MutationSurface = Literal["none", "code", "repo-config", "infra", "runtime", "public-share"]
CheckpointKind = Literal[
    "manual",
    "commit",
    "verify_green",
    "pr_opened",
    "pr_merged",
    "pause",
    "owner_followthrough",
]
ExplicitGrowthCheckpointKind = Literal[
    "commit",
    "verify_green",
    "pr_opened",
    "pr_merged",
    "owner_followthrough",
]
ProgressionAxis = Literal[
    "boundary_integrity",
    "execution_reliability",
    "change_legibility",
    "review_sharpness",
    "proof_discipline",
    "provenance_hygiene",
    "deep_readiness",
]
ProgressionMovement = Literal["advance", "hold", "reanchor", "downgrade"]
SurfaceSignal = Literal[
    "explicit-request",
    "repeated-pattern",
    "proof-need",
    "recall-need",
    "scenario-recurring",
    "role-posture",
    "closeout-chain",
]

TOKEN_RE = re.compile(r"[a-z0-9_-]+")
SURFACE_PHASES = {"ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"}
MUTATION_SURFACES = {"none", "code", "repo-config", "infra", "runtime", "public-share"}
SIGNAL_ORDER: list[SurfaceSignal] = [
    "explicit-request",
    "repeated-pattern",
    "proof-need",
    "recall-need",
    "scenario-recurring",
    "role-posture",
    "closeout-chain",
]


def context_label(workspace: Workspace, repo_root: str) -> str:
    resolved = Path(repo_root).expanduser()
    if not resolved.is_absolute():
        resolved = (workspace.root / resolved).resolve()
    else:
        resolved = resolved.resolve()
    return "workspace" if resolved == workspace.federation_root else resolved.name


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def session_scope_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._") or "session"


def dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def dedupe_shortlist_hints(
    hints: list[RoutingOwnerLayerShortlistHint],
) -> list[RoutingOwnerLayerShortlistHint]:
    deduped: dict[str, RoutingOwnerLayerShortlistHint] = {}
    for hint in hints:
        deduped[hint.shortlist_id] = hint
    return list(deduped.values())


def dedupe_refs(refs: list[SurfaceOpportunityReference]) -> list[SurfaceOpportunityReference]:
    deduped: dict[tuple[str, str], SurfaceOpportunityReference] = {}
    for ref in refs:
        deduped[(ref.role, ref.ref)] = ref
    return list(deduped.values())
