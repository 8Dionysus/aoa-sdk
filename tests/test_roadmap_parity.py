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
    readme = read_text("README.md")
    changelog = read_text("CHANGELOG.md")
    payload = load_json("generated/workspace_control_plane.min.json")

    assert "> Current release: `v0.2.2`" in readme
    assert "## [0.2.2] - 2026-04-19" in changelog
    assert "`v0.2.2`" in roadmap
    assert "Current release contour" in roadmap
    assert "Roadmap drift is an SDK-layer risk" in roadmap
    assert "must not turn\n`aoa-sdk` into a source-owning runtime layer" in roadmap
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

    current_release_surfaces = [
        ".aoa/workspace.toml",
        "docs/workspace-layout.md",
        "generated/workspace_control_plane.min.json",
        "docs/CODEX_PLANE_DEPLOY_STATUS.md",
        "docs/CODEX_DEPLOY_OPERATION_BOUNDARY_NOTE.md",
        "docs/codex_rollout_campaign_refs.md",
        "schemas/codex_plane_deploy_status_snapshot_v1.json",
        "examples/codex_plane_deploy_status_snapshot.example.json",
        "src/aoa_sdk/codex/registry.py",
        "docs/closeout-followthrough-map.md",
        "docs/COMPONENT_DRIFT_HINTS.md",
        "docs/SELF_AGENCY_CONTINUITY_CARRY.md",
        "docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md",
        "schemas/closeout_owner_followthrough_map.schema.json",
        "schemas/closeout_continuity_window.schema.json",
        "schemas/closeout_followthrough_decision.schema.json",
        "docs/session-growth-checkpoints.md",
        "docs/checkpoint-note-promotion.md",
        "docs/session-closeout.md",
        "docs/aoa-surface-detection-closeout-handoff.md",
        "docs/RELEASING.md",
        "docs/RELEASE_CI_POSTURE.md",
    ]
    for surface in current_release_surfaces:
        assert (REPO_ROOT / surface).exists(), surface
        assert surface in roadmap
