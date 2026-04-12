from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from aoa_sdk import AoASDK
from aoa_sdk.errors import RecordNotFound


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_codex_plane_deploy_status_example_validates_against_schema() -> None:
    schema = load_json("schemas/codex_plane_deploy_status_snapshot_v1.json")
    example = load_json("examples/codex_plane_deploy_status_snapshot.example.json")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.absolute_path))

    assert errors == []


def test_codex_plane_deploy_status_reads_live_rollout_artifacts(workspace_root: Path) -> None:
    rollout_root = workspace_root / ".codex" / "generated" / "rollout"
    write_json(
        rollout_root / "codex_plane_trust_state.current.json",
        {
            "schema_version": "8dionysus_codex_plane_trust_state_v1",
            "trust_state_id": "cptrust-live",
            "workspace_root": str(workspace_root),
            "detected_project_root": str(workspace_root),
            "project_root_markers_expected": ["AOA_WORKSPACE_ROOT", ".git"],
            "project_root_marker_match": ["AOA_WORKSPACE_ROOT"],
            "project_config_active": True,
            "active_config_layers": [str(workspace_root / ".codex" / "config.toml")],
            "hooks_enabled": True,
            "hook_layers_detected": [str(workspace_root / ".codex" / "hooks.json")],
            "mcp_server_names_expected": ["aoa_workspace", "aoa_stats", "dionysus"],
            "mcp_server_names_detected": ["aoa_workspace", "aoa_stats", "dionysus"],
            "stable_names_ok": True,
            "trust_posture": "trusted_ready",
            "warnings": [],
            "captured_at": "2026-04-11T21:04:00Z"
        },
    )
    write_json(
        rollout_root / "codex_plane_regeneration_report.latest.json",
        {
            "schema_version": "8dionysus_codex_plane_regeneration_report_v1",
            "regeneration_report_id": "cpregen-live",
            "source_profile_ref": "8Dionysus:config/codex_plane/profiles/linux-python3.json",
            "target_workspace_root": str(workspace_root),
            "render_posture": "execute",
            "rendered_files": [
                {
                    "relative_path": ".codex/config.toml",
                    "source_path": "8Dionysus:config/codex_plane/runtime_manifest.v1.json",
                    "mode": "rewrite",
                    "changed": True,
                    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                }
            ],
            "stable_names": {
                "aoa_workspace": True,
                "aoa_stats": True,
                "dionysus": True
            },
            "warnings": [],
            "generated_at": "2026-04-11T21:05:00Z"
        },
    )
    write_json(
        rollout_root / "codex_plane_rollout_receipt.latest.json",
        {
            "schema_version": "8dionysus_codex_plane_rollout_receipt_v1",
            "rollout_receipt_id": "cprollout-live",
            "trust_state_id": "cptrust-live",
            "regeneration_report_id": "cpregen-live",
            "apply_mode": "execute",
            "deployment_state": "verified",
            "doctor_result": "pass",
            "rollback_plan_ref": "docs/CODEX_PLANE_ROLLOUT.md#rollback-posture",
            "stats_refresh_required": True,
            "verified_at": "2026-04-11T21:07:00Z"
        },
    )

    snapshot = AoASDK.from_workspace(workspace_root / "aoa-sdk").codex.deploy_status()

    assert snapshot.workspace_root == str(workspace_root)
    assert snapshot.trust_posture == "trusted_ready"
    assert snapshot.latest_trust_state_ref == "cptrust-live"
    assert snapshot.latest_rollout_receipt_ref == "cprollout-live"
    assert snapshot.project_config_active is True
    assert snapshot.hooks_active is True
    assert snapshot.active_mcp_servers == ["aoa_stats", "aoa_workspace", "dionysus"]
    assert snapshot.rollout_state == "verified"
    assert snapshot.drift_detected is False
    assert snapshot.next_action == "none"
    assert snapshot.observed_at.isoformat() == "2026-04-11T21:07:00+00:00"


def test_codex_plane_deploy_status_requires_live_rollout_artifacts(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    with pytest.raises(RecordNotFound, match="Missing Codex rollout artifact"):
        sdk.codex.deploy_status()
