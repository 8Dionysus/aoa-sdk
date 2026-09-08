from __future__ import annotations

import copy
import json
from shutil import copytree, rmtree

import pytest
from pydantic import TypeAdapter, ValidationError

from aoa_sdk import AoASDK
from aoa_sdk.errors import InvalidSurface
from aoa_sdk.models import AnySkillHomePortManifest, SkillHomePortManifest


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
    assert (
        next(
            entry.status
            for entry in _root(drift, "user").entries
            if entry.name == "aoa-decision"
        )
        == "drift"
    )
    assert not (user_skill / "agents" / "openai.yaml").exists()

    rmtree(user_skill)
    missing = sdk.skills.inspect(
        repo_root=skill_environment_fixture.repo_root,
        user_skill_root=skill_environment_fixture.user_root,
    )
    assert (
        next(
            entry.status
            for entry in _root(missing, "user").entries
            if entry.name == "aoa-decision"
        )
        == "missing"
    )
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
    assert [
        (entry.name, entry.status, entry.admitted) for entry in unowned.entries
    ] == [("orphan", "legacy-unowned", False)]
    assert not (unadmitted_repo / "skills" / "port.manifest.json").exists()


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_owner_home_is_source_and_eligibility_not_an_install(
    skill_environment_fixture,
    owner_home_payload,
    version,
) -> None:
    fixture = skill_environment_fixture
    payload = owner_home_payload
    if version == "v2":
        payload["schema_version"] = "aoa_skill_home_port_v2"
        payload["exposure"] = payload.pop("exposures")[0]
        payload["exposure"]["mode"] = "profile-selected"
    port = fixture.repo_root / "skills/port.manifest.json"
    port.write_text(json.dumps(payload))
    rmtree(fixture.repo_root / ".agents/skills")
    copytree(fixture.repo_root / "skills/repo-home", fixture.user_root / "repo-home")

    report = AoASDK.from_workspace(fixture.workspace_root).skills.inspect(
        repo_root=fixture.repo_root,
        user_skill_root=fixture.user_root,
    )

    source = _root(report, "owner-source")
    assert source.scope == "source"
    assert source.authority == "owner-source"
    assert source.source_schema_version == f"aoa_skill_home_port_{version}"
    assert [(item.name, item.status) for item in source.entries] == [
        ("repo-home", "owner-source")
    ]
    assert source.exposures[0].skills == ["repo-home"]
    assert not source.issues
    assert not any(root.root_kind == "repo-projection" for root in report.roots)
    assert not any(
        "repo-home" in warning and "multiple scopes" in warning
        for warning in report.warnings
    )
    assert (
        next(
            item for item in _root(report, "user").entries if item.name == "repo-home"
        ).admitted
        is False
    )
    assert not (fixture.repo_root / ".agents/skills").exists()


@pytest.mark.parametrize(
    "exposures",
    [
        [],
        [
            {
                "runtime": "other-agent",
                "scope": "project",
                "profile": "read-only",
                "mode": "profile-eligible",
                "skills": ["repo-home"],
            }
        ],
    ],
)
def test_foreign_or_no_exposure_keeps_all_owner_bundles_without_codex_duplicate_rule(
    skill_environment_fixture,
    owner_home_payload,
    exposures,
) -> None:
    fixture = skill_environment_fixture
    payload = owner_home_payload
    payload["exposures"] = exposures
    second = copy.deepcopy(payload["bundles"][0])
    second.update(name="other-home", path="skills/other-home")
    payload["bundles"].append(second)
    copytree(
        fixture.repo_root / "skills/repo-home", fixture.repo_root / "skills/other-home"
    )
    port = fixture.repo_root / "skills/port.manifest.json"
    port.write_text(json.dumps(payload))

    report = AoASDK.from_workspace(fixture.workspace_root).skills.inspect(
        repo_root=fixture.repo_root,
        user_skill_root=fixture.user_root,
    )

    source = _root(report, "owner-source")
    assert source.admitted_names == ["repo-home", "other-home"]
    assert len(source.entries) == 2
    assert not any("competing" in issue for issue in source.issues)
    assert _root(report, "repo-unowned").entries[0].admitted is False


def test_codex_user_exposure_flags_competing_copy_and_missing_source_without_repair(
    skill_environment_fixture,
    owner_home_payload,
    tmp_path,
) -> None:
    fixture = skill_environment_fixture
    source = fixture.repo_root / "skills/repo-home/SKILL.md"
    source.unlink()
    outside = tmp_path / "outside.txt"
    outside.write_text("Not an admitted owner source.")
    source.symlink_to(outside)

    report = AoASDK.from_workspace(fixture.workspace_root).skills.inspect(
        repo_root=fixture.repo_root,
        user_skill_root=fixture.user_root,
    )

    owner = _root(report, "owner-source")
    assert owner.entries[0].status == "missing"
    assert any("competing" in issue for issue in owner.issues)
    assert any("symlink" in issue for issue in owner.issues)
    assert source.is_symlink()
    assert outside.read_text() == "Not an admitted owner source."


@pytest.mark.parametrize(
    "fault",
    [
        "missing-exposures",
        "unknown-bundle",
        "duplicate-skill",
        "duplicate-target",
        "unsafe-runtime",
        "wrong-mode",
        "owner-escape",
        "bundle-escape",
        "v2-foreign-runtime",
        "v2-incomplete-exposure",
        "v3-legacy-field",
    ],
)
def test_owner_home_union_rejects_malformed_versioned_contracts(
    owner_home_payload, fault
) -> None:
    payload = copy.deepcopy(owner_home_payload)
    if fault == "missing-exposures":
        payload.pop("exposures")
    elif fault == "unknown-bundle":
        payload["exposures"][0]["skills"] = ["unknown"]
    elif fault == "duplicate-skill":
        payload["exposures"][0]["skills"] *= 2
    elif fault == "duplicate-target":
        payload["exposures"] *= 2
    elif fault == "unsafe-runtime":
        payload["exposures"][0]["runtime"] = "../codex"
    elif fault == "wrong-mode":
        payload["exposures"][0]["mode"] = "profile-selected"
    elif fault == "owner-escape":
        payload["owner_ref"] = "../README.md"
    elif fault == "bundle-escape":
        payload["bundles"][0]["path"] = "../repo-home"
    elif fault.startswith("v2-"):
        payload["schema_version"] = "aoa_skill_home_port_v2"
        payload["exposure"] = payload.pop("exposures")[0]
        payload["exposure"]["mode"] = "profile-selected"
        payload["exposure"][
            "runtime" if fault == "v2-foreign-runtime" else "skills"
        ] = "other-agent" if fault == "v2-foreign-runtime" else ["unknown"]
    else:
        payload["projection"] = {}
    with pytest.raises(ValidationError):
        TypeAdapter(AnySkillHomePortManifest).validate_python(payload)


def test_versioned_union_roundtrips_and_keeps_legacy_v1_constructor(
    skill_environment_fixture,
    owner_home_payload,
) -> None:
    adapter = TypeAdapter(AnySkillHomePortManifest)
    current = adapter.validate_python(owner_home_payload)
    assert adapter.validate_python(current.model_dump()) == current
    legacy = SkillHomePortManifest(
        schema_version="aoa_skill_home_port_v1",
        contract_ref="legacy-ref",
        owner_repo="repo-home",
        owner_ref="legacy-owner",
        bundles=[],
        projection={
            "runtime": "codex",
            "scope": "repo",
            "root": ".agents/skills",
            "mode": "generated-copy",
            "skills": [],
        },
    )
    assert adapter.validate_python(legacy.model_dump()) == legacy
