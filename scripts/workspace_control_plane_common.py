#!/usr/bin/env python3
"""Shared builder helpers for the aoa-sdk workspace control-plane capsule."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_CONTROL_PLANE_PATH = REPO_ROOT / "generated" / "workspace_control_plane.min.json"
SCHEMA_REF = "schemas/workspace-control-plane.schema.json"
VALIDATION_REFS = (
    "scripts/build_workspace_control_plane.py",
    "scripts/validate_workspace_control_plane.py",
    "tests/test_workspace_control_plane.py",
    "tests/test_compatibility.py",
)
FORBIDDEN_LOW_CONTEXT_PREFIXES = ("src/", "scripts/")

SURFACE_PAYLOAD = {
    "schema_version": "aoa_sdk_workspace_control_plane_v2",
    "schema_ref": SCHEMA_REF,
    "owner_repo": "aoa-sdk",
    "surface_kind": "runtime_surface",
    "authority_ref": "docs/boundaries.md",
    "workspace_manifest_ref": ".aoa/workspace.toml",
    "validation_refs": list(VALIDATION_REFS),
}

ROUTE_SPECS = (
    {
        "route_id": "workspace-topology",
        "need": "resolve workspace topology, source checkouts, and override rules without guessing",
        "surface_ref": "docs/workspace-layout.md",
        "verification_refs": [
            ".aoa/workspace.toml",
            "docs/versioning.md",
        ],
    },
    {
        "route_id": "compatibility-posture",
        "need": "check consumed-surface compatibility posture before trusting a sibling read path",
        "surface_ref": "docs/versioning.md",
        "verification_refs": [
            "docs/RELEASE_CI_POSTURE.md",
            "schemas/workspace-control-plane.schema.json",
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
            "docs/versioning.md",
        ],
    },
)


def resolve_ref(value: str) -> Path:
    target = REPO_ROOT / value
    if not target.exists():
        raise ValueError(f"missing ref target '{value}'")
    return target


def validate_low_context_ref(value: str, location: str) -> Path:
    for prefix in FORBIDDEN_LOW_CONTEXT_PREFIXES:
        if value.startswith(prefix):
            raise ValueError(f"{location} must not point to implementation path '{value}'")
    return resolve_ref(value)


def load_schema() -> dict[str, object]:
    schema_path = resolve_ref(SCHEMA_REF)
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_payload_schema(payload: dict[str, object]) -> None:
    validator = Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if not errors:
        return
    error = errors[0]
    path = "".join(f"[{item}]" if isinstance(item, int) else f".{item}" for item in error.absolute_path)
    if path.startswith("."):
        path = path[1:]
    if path:
        raise ValueError(f"schema violation at '{path}': {error.message}")
    raise ValueError(f"schema violation: {error.message}")


def build_payload() -> dict[str, object]:
    resolve_ref(SURFACE_PAYLOAD["authority_ref"])
    resolve_ref(SURFACE_PAYLOAD["workspace_manifest_ref"])
    resolve_ref(SURFACE_PAYLOAD["schema_ref"])
    for ref in SURFACE_PAYLOAD["validation_refs"]:
        resolve_ref(ref)

    routes: list[dict[str, object]] = []
    for spec in ROUTE_SPECS:
        validate_low_context_ref(spec["surface_ref"], f"route:{spec['route_id']}.surface_ref")
        for ref in spec["verification_refs"]:
            validate_low_context_ref(ref, f"route:{spec['route_id']}.verification_refs")
        routes.append(
            {
                "route_id": spec["route_id"],
                "need": spec["need"],
                "surface_ref": spec["surface_ref"],
                "verification_refs": list(spec["verification_refs"]),
            }
        )

    payload = {
        **SURFACE_PAYLOAD,
        "routes": routes,
    }
    validate_payload_schema(payload)
    return payload


def render_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
