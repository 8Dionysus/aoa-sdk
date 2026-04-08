from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from workspace_control_plane_common import (  # noqa: E402
    ROUTE_SPECS,
    SURFACE_PAYLOAD,
    WORKSPACE_CONTROL_PLANE_PATH,
    build_payload,
)


def test_build_payload_stays_runtime_surface_only() -> None:
    payload = build_payload()

    assert payload["schema_version"] == "aoa_sdk_workspace_control_plane_v1"
    assert payload["owner_repo"] == "aoa-sdk"
    assert payload["surface_kind"] == "runtime_surface"
    assert [route["route_id"] for route in payload["routes"]] == [
        "workspace-topology",
        "compatibility-posture",
        "surface-detection",
        "checkpoint-growth",
    ]


def test_generated_surface_matches_canonical_build() -> None:
    current = json.loads(WORKSPACE_CONTROL_PLANE_PATH.read_text(encoding="utf-8"))

    assert current == build_payload()


def test_surface_keeps_expected_refs() -> None:
    payload = build_payload()

    assert payload["authority_ref"] == SURFACE_PAYLOAD["authority_ref"]
    assert payload["workspace_manifest_ref"] == SURFACE_PAYLOAD["workspace_manifest_ref"]
    assert [route["surface_ref"] for route in payload["routes"]] == [
        spec["surface_ref"] for spec in ROUTE_SPECS
    ]
