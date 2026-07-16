from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError("could not resolve aoa-sdk repo root")


REPO_ROOT = _repo_root()


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def load_json(relative_path: str) -> object:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_roadmap_keeps_current_control_plane_surface_explicit() -> None:
    roadmap = read_text("ROADMAP.md")
    readme = read_text("README.md")
    changelog = read_text("CHANGELOG.md")
    payload = load_json("generated/workspace_control_plane.min.json")

    assert "> Current release: `v0.5.1`" in readme
    assert "## [0.5.1] - 2026-07-13" in changelog
    assert "`v0.5.1`" in roadmap
    assert "Current unreleased contour" in roadmap
    assert "Roadmap drift is an SDK-layer risk" in roadmap
    assert "## Authority" in roadmap
    assert "## Update Rule" in roadmap
    assert "## Operating Card" in roadmap
    assert "## Horizons" in roadmap
    assert "## When The Time Comes" in roadmap
    assert "must not turn\n`aoa-sdk` into a source-owning runtime layer" in roadmap
    assert payload["schema_version"] == "aoa_sdk_workspace_control_plane_v2"
    assert [route["route_id"] for route in payload["routes"]] == [
        "workspace-root-resolution",
        "compatibility-posture",
        "owner-layer-signal-handoff",
        "checkpoint-growth",
    ]
    assert "generated/workspace_control_plane.min.json" in roadmap
    assert ".aoa/workspace.toml" in roadmap
    assert "compatibility checks" in roadmap
    assert "passive skill-environment inspection" in roadmap
    assert "`aoa surfaces detect`" in roadmap
    assert "checkpoint capture, review-note, and reviewed evidence materialization" in roadmap
    assert "release audit and publish" in roadmap
    assert "Detailed shipped-surface maps live in" in readme
    assert "ROADMAP](ROADMAP.md) keeps direction" in readme

    owner_surfaces = [
        ".aoa/workspace.toml",
        "docs/workspace-layout.md",
        "generated/workspace_control_plane.min.json",
        "mechanics/README.md",
        "docs/decisions/indexes/",
        "docs/RELEASING.md",
        "docs/RELEASE_CI_POSTURE.md",
    ]
    for surface in owner_surfaces:
        assert (REPO_ROOT / surface).exists(), surface
        assert surface in roadmap
    assert "release-support parts" in roadmap

    part_local_surfaces = [
        "mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md",
        "mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md",
        "mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md",
        "mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json",
        "mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json",
        "src/aoa_sdk/codex/registry.py",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/README.md",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/owner-followthrough-map.md",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/component-refresh-followthrough.md",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/self-agency-continuity-carry.md",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/next-kernel-followthrough-decision.md",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_owner_followthrough_map.schema.json",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_continuity_window.schema.json",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_followthrough_decision.schema.json",
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md",
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/reviewed-checkpoint-note-promotion.md",
        "mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md",
        "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-closeout-handoff.md",
        "mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md",
        "mechanics/release-support/parts/public-support-ci-posture/docs/public-support-ci-posture.md",
    ]
    for surface in part_local_surfaces:
        assert (REPO_ROOT / surface).exists(), surface
        assert surface not in roadmap
