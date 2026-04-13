from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def load_json(relative_path: str) -> object:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_roadmap_keeps_current_control_plane_surface_explicit() -> None:
    roadmap = read_text("ROADMAP.md")
    payload = load_json("generated/workspace_control_plane.min.json")

    assert payload["schema_version"] == "aoa_sdk_workspace_control_plane_v2"
    assert [route["route_id"] for route in payload["routes"]] == [
        "workspace-topology",
        "compatibility-posture",
        "surface-detection",
        "checkpoint-growth",
    ]
    assert "generated/workspace_control_plane.min.json" in roadmap
    assert ".aoa/workspace.toml" in roadmap
    assert "compatibility checks" in roadmap
    assert "`aoa skills enter` / `aoa skills guard`" in roadmap
    assert "`aoa surfaces detect`" in roadmap
    assert "checkpoint capture, review-note, and explicit closeout-bridge" in roadmap
    assert "release audit and publish" in roadmap
