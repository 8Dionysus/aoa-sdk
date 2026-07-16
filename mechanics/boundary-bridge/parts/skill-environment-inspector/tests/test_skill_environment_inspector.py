from __future__ import annotations

from shutil import rmtree

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import InvalidSurface


def _root(report, root_kind: str):
    return next(root for root in report.roots if root.root_kind == root_kind)


def test_owner_surfaces_and_capability_lookup_are_passive_and_exact(
    skill_environment_fixture,
) -> None:
    sdk = AoASDK.from_workspace(skill_environment_fixture.workspace_root)

    assert sdk.skills.catalog().catalog_version == 2
    assert sdk.skills.profile("user-default").scope == "user"
    assert sdk.skills.portable_exports().export_version == 2
    assert sdk.skills.mcp_dependencies().schema_version == 2

    neighborhood = sdk.skills.capability("workflow.operations.checkpoint-closeout")
    assert neighborhood.node.kind == "workflow"
    assert neighborhood.node.owner.repo == "aoa-playbooks"
    assert [(edge.kind, edge.target) for edge in neighborhood.outgoing] == [
        ("primary-parent", "operations.continuity")
    ]
    assert neighborhood.incoming == []

    for retired_name in (
        "detect",
        "dispatch",
        "activate",
        "deactivate",
        "enter",
        "guard",
        "session",
    ):
        assert not hasattr(sdk.skills, retired_name)

    with pytest.raises(InvalidSurface, match="not present in the owner graph"):
        sdk.skills.capability("missing.capability")


def test_inspection_keeps_owner_and_install_scopes_distinct(
    skill_environment_fixture,
) -> None:
    sdk = AoASDK.from_workspace(skill_environment_fixture.workspace_root)
    report = sdk.skills.inspect(
        repo_root=skill_environment_fixture.repo_root,
        user_skill_root=skill_environment_fixture.user_root,
    )

    assert [root.root_kind for root in report.roots] == [
        "source-export",
        "user",
        "repo-projection",
        "workspace-legacy",
    ]
    assert _root(report, "source-export").authority == "portable-export"

    user_entries = {entry.name: entry for entry in _root(report, "user").entries}
    assert user_entries["aoa-decision"].status == "current"
    assert user_entries["aoa-decision"].admitted is True
    assert user_entries["foreign-owner-skill"].status == "unmanaged"
    assert user_entries["foreign-owner-skill"].admitted is False

    repo_root = _root(report, "repo-projection")
    assert repo_root.owner_repo == "repo-home"
    assert [(entry.name, entry.status) for entry in repo_root.entries] == [
        ("repo-home", "current")
    ]

    legacy_root = _root(report, "workspace-legacy")
    assert legacy_root.authority == "legacy-unowned"
    assert legacy_root.entries[0].status == "legacy-unowned"
    assert "aoa-decision" in report.duplicate_names
    assert len(report.duplicate_names["aoa-decision"]) == 3
    assert any("multiple scopes" in warning for warning in report.warnings)


def test_inspection_reports_drift_missing_and_unadmitted_repo_without_repair(
    skill_environment_fixture,
) -> None:
    sdk = AoASDK.from_workspace(skill_environment_fixture.workspace_root)
    user_skill = skill_environment_fixture.user_root / "aoa-decision"
    (user_skill / "agents" / "openai.yaml").unlink()

    drift = sdk.skills.inspect(
        repo_root=skill_environment_fixture.repo_root,
        user_skill_root=skill_environment_fixture.user_root,
    )
    assert next(
        entry.status for entry in _root(drift, "user").entries if entry.name == "aoa-decision"
    ) == "drift"
    assert not (user_skill / "agents" / "openai.yaml").exists()

    rmtree(user_skill)
    missing = sdk.skills.inspect(
        repo_root=skill_environment_fixture.repo_root,
        user_skill_root=skill_environment_fixture.user_root,
    )
    assert next(
        entry.status for entry in _root(missing, "user").entries if entry.name == "aoa-decision"
    ) == "missing"
    assert not user_skill.exists()

    unadmitted_repo = skill_environment_fixture.workspace_root / "unadmitted"
    (unadmitted_repo / ".agents" / "skills" / "orphan").mkdir(parents=True)
    (unadmitted_repo / ".agents" / "skills" / "orphan" / "SKILL.md").write_text(
        "# orphan\n",
        encoding="utf-8",
    )
    report = sdk.skills.inspect(
        repo_root=unadmitted_repo,
        user_skill_root=skill_environment_fixture.user_root,
    )
    unowned = _root(report, "repo-unowned")
    assert [(entry.name, entry.status, entry.admitted) for entry in unowned.entries] == [
        ("orphan", "legacy-unowned", False)
    ]
    assert not (unadmitted_repo / "skills" / "port.manifest.json").exists()
