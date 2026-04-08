#!/usr/bin/env python3
"""Shared builder helpers for the aoa-sdk workspace control-plane capsule."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_CONTROL_PLANE_PATH = REPO_ROOT / "generated" / "workspace_control_plane.min.json"

SURFACE_PAYLOAD = {
    "schema_version": "aoa_sdk_workspace_control_plane_v1",
    "owner_repo": "aoa-sdk",
    "surface_kind": "runtime_surface",
    "authority_ref": "docs/boundaries.md",
    "workspace_manifest_ref": ".aoa/workspace.toml",
}

ROUTE_SPECS = (
    {
        "route_id": "workspace-topology",
        "need": "resolve workspace topology, source checkouts, and override rules without guessing",
        "surface_ref": "docs/workspace-layout.md",
        "verification_refs": [
            ".aoa/workspace.toml",
            "src/aoa_sdk/workspace/discovery.py",
        ],
    },
    {
        "route_id": "compatibility-posture",
        "need": "check consumed-surface compatibility posture before trusting a sibling read path",
        "surface_ref": "docs/versioning.md",
        "verification_refs": [
            "docs/RELEASE_CI_POSTURE.md",
            "scripts/sibling_canary_matrix.json",
        ],
    },
    {
        "route_id": "surface-detection",
        "need": "inspect additive owner-layer surface detection and reviewed handoff posture",
        "surface_ref": "docs/aoa-surface-detection-second-wave.md",
        "verification_refs": [
            "docs/aoa-surface-detection-first-wave.md",
            "docs/aoa-surface-detection-closeout-handoff.md",
        ],
    },
    {
        "route_id": "checkpoint-growth",
        "need": "capture reviewable mid-session checkpoint notes without mistaking them for harvest verdicts",
        "surface_ref": "docs/session-growth-checkpoints.md",
        "verification_refs": [
            "docs/checkpoint-note-promotion.md",
            "src/aoa_sdk/checkpoints/registry.py",
        ],
    },
)


def resolve_ref(value: str) -> Path:
    target = REPO_ROOT / value
    if not target.exists():
        raise ValueError(f"missing ref target '{value}'")
    return target


def build_payload() -> dict[str, object]:
    resolve_ref(SURFACE_PAYLOAD["authority_ref"])
    resolve_ref(SURFACE_PAYLOAD["workspace_manifest_ref"])

    routes: list[dict[str, object]] = []
    for spec in ROUTE_SPECS:
        resolve_ref(spec["surface_ref"])
        for ref in spec["verification_refs"]:
            resolve_ref(ref)
        routes.append(
            {
                "route_id": spec["route_id"],
                "need": spec["need"],
                "surface_ref": spec["surface_ref"],
                "verification_refs": list(spec["verification_refs"]),
            }
        )

    return {
        **SURFACE_PAYLOAD,
        "routes": routes,
    }


def render_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
