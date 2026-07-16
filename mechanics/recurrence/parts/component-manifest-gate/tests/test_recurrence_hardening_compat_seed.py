from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.recurrence.doctor import build_connectivity_gap_report
from aoa_sdk.recurrence.registry import load_registry, pattern_matches
from aoa_sdk.workspace.discovery import Workspace


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _make_workspace(tmp_path: Path) -> Workspace:
    root = tmp_path / "federation"
    sdk = root / "aoa-sdk"
    techniques = root / "aoa-techniques"
    for repo in (sdk, techniques):
        repo.mkdir(parents=True, exist_ok=True)
    _write_json(
        techniques
        / "mechanics/recurrence/parts/live-observation-producers/manifests/recurrence/component.techniques.canon-and-intake-beacons.json",
        {
            "manifest_kind": "recurrence_component",
            "schema_version": "aoa_recurrence_component_v2",
            "component_ref": "component:techniques:canon-and-intake-beacons",
            "owner_repo": "aoa-techniques",
            "source_inputs": [
                "techniques/**/*.md",
                "mechanics/distillation/parts/cross-layer-candidate-ledger/README.md",
            ],
            "proof_surfaces": ["python scripts/validate_repo.py"],
            "refresh_routes": [
                {"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}
            ],
        },
    )
    _write_json(
        techniques
        / "mechanics/recurrence/parts/live-observation-producers/manifests/recurrence/hooks/component.techniques.canon-and-intake-beacons.hooks.json",
        {
            "manifest_kind": "hook_binding_set",
            "schema_version": "aoa_hook_binding_set_v1",
            "component_ref": "component:techniques:canon-and-intake-beacons",
            "owner_repo": "aoa-techniques",
            "bindings": [],
        },
    )
    _write_json(
        sdk / "manifests/recurrence/agon.observation-only.json",
        {
            "component_id": "agon:trial:preparation-posture",
            "authority": "observation_only",
            "observation_only": True,
            "surface_refs": ["docs/AGON_PREPARATION_POSTURE.md"],
            "forbidden_actions": ["create_arena_session", "write_scar"],
        },
    )
    _write_json(
        sdk / "manifests/recurrence/agon.legacy-component-like.json",
        {
            "component_ref": "component:agon:legacy-prebinding",
            "owner_repo": "aoa-sdk",
            "schema_version": "recurrence_component_manifest_v1",
            "live_protocol": False,
            "observed_surfaces": ["docs/AGON_LEGACY.md"],
            "runtime_effect": "none",
        },
    )
    _write_json(
        sdk / "manifests/recurrence/unknown.json",
        {"planet": "pluto", "rings": False},
    )
    _write_json(
        sdk / "manifests/recurrence/bad-component.json",
        {
            "manifest_kind": "recurrence_component",
            "schema_version": "aoa_recurrence_component_v2",
            "owner_repo": "aoa-sdk",
            "source_inputs": ["docs/NO_COMPONENT_REF.md"],
        },
    )
    (sdk / "manifests/recurrence/broken.json").write_text("{not json", encoding="utf-8")
    return Workspace(
        root=root,
        federation_root=root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={"aoa-sdk": sdk, "aoa-techniques": techniques},
        repo_origins={"aoa-sdk": "test", "aoa-techniques": "test"},
    )


def test_tolerant_registry_loads_components_and_quarantines_mixed_manifests(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    registry = load_registry(workspace)

    assert [item.component.component_ref for item in registry.iter_components()] == [
        "component:techniques:canon-and-intake-beacons"
    ]
    diagnostics = list(registry.iter_manifest_diagnostics())
    kinds = {item.diagnostic_kind for item in diagnostics}
    assert "loaded_manifest" in kinds
    assert "known_foreign_manifest" in kinds
    assert "adapter_required" in kinds
    assert "unknown_manifest_kind" in kinds
    assert "invalid_manifest_shape" in kinds
    assert "manifest_json_error" in kinds

    report = registry.manifest_scan_report()
    assert report.by_kind["recurrence_component"] == 1
    assert report.by_kind["hook_binding_set"] == 1
    assert report.by_kind["agon_recurrence_adapter"] == 2
    assert report.by_severity["high"] >= 2


def test_doctor_converts_manifest_diagnostics_to_gaps(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    registry = load_registry(workspace)
    report = build_connectivity_gap_report(workspace, registry=registry)
    gap_kinds = {item.gap_kind for item in report.gaps}

    assert "manifest_json_error" in gap_kinds
    assert "invalid_manifest_shape" in gap_kinds
    assert "unknown_manifest_kind" in gap_kinds
    assert "foreign_manifest_requires_adapter" in gap_kinds
    assert report.manifest_diagnostics


def test_api_manifest_scan_and_pattern_tokens(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    scan = RecurrenceAPI(workspace).manifest_scan()
    assert scan.loaded_components == ["component:techniques:canon-and-intake-beacons"]
    assert pattern_matches("techniques/**/*.md", "techniques/canonical/README.md")
    assert pattern_matches(
        "mechanics/distillation/parts/cross-layer-candidate-ledger/",
        "mechanics/distillation/parts/cross-layer-candidate-ledger/README.md",
    )
