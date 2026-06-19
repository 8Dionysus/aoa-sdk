from __future__ import annotations

import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError("could not resolve aoa-sdk repo root")


sys.path.insert(0, str(_repo_root() / "scripts"))

from workspace_control_plane_common import (  # noqa: E402
    ARTIFACT_IDENTITY,
    ROUTE_SPECS,
    SURFACE_PAYLOAD,
    WORKSPACE_CONTROL_PLANE_PATH,
    build_payload,
)


def test_build_payload_stays_runtime_surface_only() -> None:
    payload = build_payload()

    assert payload["schema_version"] == "aoa_sdk_workspace_control_plane_v2"
    assert payload["schema_ref"] == "schemas/workspace-control-plane.schema.json"
    assert payload["owner_repo"] == "aoa-sdk"
    assert payload["surface_kind"] == "runtime_surface"
    assert [route["route_id"] for route in payload["routes"]] == [
        "workspace-root-resolution",
        "compatibility-posture",
        "owner-layer-signal-handoff",
        "checkpoint-growth",
    ]
    assert payload["artifact_identity"] == ARTIFACT_IDENTITY


def test_generated_surface_matches_canonical_build() -> None:
    current = json.loads(WORKSPACE_CONTROL_PLANE_PATH.read_text(encoding="utf-8"))

    assert current == build_payload()


def test_surface_keeps_expected_refs() -> None:
    payload = build_payload()
    identity = payload["artifact_identity"]

    assert payload["authority_ref"] == SURFACE_PAYLOAD["authority_ref"]
    assert payload["workspace_manifest_ref"] == SURFACE_PAYLOAD["workspace_manifest_ref"]
    assert payload["validation_refs"] == SURFACE_PAYLOAD["validation_refs"]
    assert identity["authority_ref"] == "mechanics/runtime-seam/parts/control-plane-capsule/CONTRACT.md"
    assert identity["contract_version"] == (
        "schemas/workspace-control-plane.schema.json@aoa_sdk_workspace_control_plane_v2#artifact_identity"
    )
    assert [route["surface_ref"] for route in payload["routes"]] == [
        spec["surface_ref"] for spec in ROUTE_SPECS
    ]
    assert all(
        not ref.startswith(("src/", "scripts/"))
        for route in payload["routes"]
        for ref in [route["surface_ref"], *route["verification_refs"]]
    )


def test_artifact_identity_names_consumer_check_and_public_boundary() -> None:
    identity = build_payload()["artifact_identity"]

    assert identity["artifact_class"] == "control_plane_capsule"
    assert identity["surface_state"] == "public_generated_control_plane_surface"
    assert identity["abi_epoch"] == "aoa_sdk_workspace_control_plane_v2"
    assert identity["trust_layer"] == ["abi_contract_signature"]
    assert "build_workspace_control_plane --check" in identity["consumer_expectation"]
    assert "validate_workspace_control_plane" in identity["consumer_expectation"]
    assert "no secrets" in identity["privacy_boundary"]
    assert "private host evidence" in identity["privacy_boundary"]
    assert "sibling-owned source payloads" in identity["privacy_boundary"]
