from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.detector import detect_change_signal
from aoa_sdk.recurrence.registry import pattern_matches
from aoa_sdk.workspace.discovery import Workspace


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _make_workspace(tmp_path: Path) -> tuple[Workspace, Path, Path]:
    federation_root = tmp_path / "federation"
    repo_a = federation_root / "repo-a"
    repo_b = federation_root / "repo-b"
    for repo_root in (repo_a, repo_b):
        (repo_root / "manifests" / "recurrence").mkdir(parents=True, exist_ok=True)

    workspace = Workspace(
        root=federation_root,
        federation_root=federation_root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={
            "repo-a": repo_a,
            "repo-b": repo_b,
        },
        repo_origins={
            "repo-a": "test",
            "repo-b": "test",
        },
    )
    return workspace, repo_a, repo_b


def test_pattern_matches_preserve_directory_globs() -> None:
    assert pattern_matches(".codex/agents/", ".codex/agents/coder.toml")


def test_detect_change_signal_matches_proof_paths_from_command_specs(tmp_path: Path) -> None:
    workspace, repo_a, _repo_b = _make_workspace(tmp_path)
    _write_json(
        repo_a / "manifests" / "recurrence" / "component.repo_a.json",
        {
            "schema_version": "aoa_recurrence_component_v2",
            "component_ref": "component:repo-a:test",
            "owner_repo": "repo-a",
            "proof_surfaces": ["python scripts/validate_repo.py"],
            "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}],
        },
    )

    signal = detect_change_signal(workspace, repo_root=str(repo_a), paths=["scripts/validate_repo.py"])

    assert [item.component_ref for item in signal.direct_components] == ["component:repo-a:test"]
    assert signal.direct_components[0].match_class == "proof"
    assert signal.direct_components[0].inferred_signals == ["proof_changed"]


def test_detect_change_signal_limits_matches_to_repo_owner(tmp_path: Path) -> None:
    workspace, repo_a, repo_b = _make_workspace(tmp_path)
    manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "source_inputs": ["docs/*.md"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}],
    }
    _write_json(
        repo_a / "manifests" / "recurrence" / "component.repo_a.json",
        {
            **manifest,
            "component_ref": "component:repo-a:test",
            "owner_repo": "repo-a",
        },
    )
    _write_json(
        repo_b / "manifests" / "recurrence" / "component.repo_b.json",
        {
            **manifest,
            "component_ref": "component:repo-b:test",
            "owner_repo": "repo-b",
        },
    )

    signal = detect_change_signal(workspace, repo_root=str(repo_a), paths=["docs/change.md"])

    assert [item.component_ref for item in signal.direct_components] == ["component:repo-a:test"]
    assert signal.changed_paths[0].matched_component_refs == ["component:repo-a:test"]
