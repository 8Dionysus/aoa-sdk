#!/usr/bin/env python3
"""Validate the aoa-sdk control-plane capsule surface."""

from __future__ import annotations

import json

from workspace_control_plane_common import (
    ROUTE_SPECS,
    SURFACE_PAYLOAD,
    WORKSPACE_CONTROL_PLANE_PATH,
    build_payload,
    resolve_ref,
    validate_low_context_ref,
    validate_payload_schema,
)


def main() -> int:
    expected_payload = build_payload()
    current_payload = json.loads(WORKSPACE_CONTROL_PLANE_PATH.read_text(encoding="utf-8"))
    validate_payload_schema(current_payload)
    if current_payload != expected_payload:
        raise SystemExit("generated/workspace_control_plane.min.json does not match the canonical rebuild")

    for key, expected in SURFACE_PAYLOAD.items():
        if current_payload.get(key) != expected:
            raise SystemExit(f"generated/workspace_control_plane.min.json must keep {key}={expected!r}")
        if key in {"authority_ref", "workspace_manifest_ref", "schema_ref"}:
            resolve_ref(expected)
        if key == "validation_refs":
            for ref in expected:
                resolve_ref(ref)

    routes = current_payload.get("routes")
    if not isinstance(routes, list) or len(routes) != len(ROUTE_SPECS):
        raise SystemExit("generated/workspace_control_plane.min.json must publish exactly four control-plane routes")

    for route, spec in zip(routes, ROUTE_SPECS, strict=True):
        if not isinstance(route, dict):
            raise SystemExit("generated/workspace_control_plane.min.json routes must be objects")
        for key in ("route_id", "need", "surface_ref", "verification_refs"):
            if route.get(key) != spec[key]:
                raise SystemExit(f"generated/workspace_control_plane.min.json route '{spec['route_id']}' must keep {key}")
        validate_low_context_ref(route["surface_ref"], f"route:{spec['route_id']}.surface_ref")
        verification_refs = route["verification_refs"]
        if not isinstance(verification_refs, list) or not verification_refs:
            raise SystemExit("generated/workspace_control_plane.min.json verification_refs must be a non-empty list")
        for ref in verification_refs:
            if not isinstance(ref, str) or not ref.strip():
                raise SystemExit("generated/workspace_control_plane.min.json verification_refs must contain strings")
            validate_low_context_ref(ref, f"route:{spec['route_id']}.verification_refs")

    print("[ok] validated generated/workspace_control_plane.min.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
