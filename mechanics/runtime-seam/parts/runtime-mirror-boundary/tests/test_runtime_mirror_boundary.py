from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import IncompatibleSurfaceVersion, SurfaceNotFound
from aoa_sdk.workspace.config import load_workspace_config, resolve_pattern


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError("could not resolve aoa-sdk repo root")


LIVE_WORKSPACE_ROOT = _repo_root()
CORE_COMPAT_SURFACE_IDS = (
    "aoa-techniques.technique_capsules",
    "aoa-techniques.technique_sections.full",
    "aoa-routing.federation_entrypoints.min",
    "aoa-routing.return_navigation_hints.min",
    "aoa-playbooks.playbook_federation_surfaces.min",
    "aoa-playbooks.playbook_review_status.min",
    "aoa-playbooks.playbook_landing_governance.min",
    "aoa-memo.checkpoint_to_memory_contract.example",
    "aoa-memo.runtime_writeback_governance.min",
    "aoa-techniques.technique_promotion_readiness.min",
    "aoa-skills.agent_skill_catalog",
    "aoa-skills.skill_pack_profiles.resolved",
    "aoa-skills.capability_graph",
    "aoa-skills.portable_export_map",
    "aoa-skills.mcp_dependency_manifest",
    "aoa-stats.object_summary.min",
    "aoa-stats.core_skill_application_summary.min",
    "aoa-stats.automation_pipeline_summary.min",
    "8Dionysus.public_route_map.min",
    "Dionysus.seed_route_map.min",
    "abyss-stack.diagnostic_surface_catalog.min",
    "aoa-kag.kag_registry.min",
    "aoa-kag.tos_zarathustra_route_retrieval_pack.min",
)


def test_live_workspace_prefers_home_src_abyss_stack_and_keeps_core_compat_green() -> None:
    sdk, expected_abyss_stack_source = _live_sdk_or_skip()
    _require_live_repos(
        sdk,
        [
            "8Dionysus",
            "Dionysus",
            "aoa-kag",
            "aoa-memo",
            "aoa-playbooks",
            "aoa-routing",
            "aoa-skills",
            "aoa-stats",
            "aoa-techniques",
        ],
    )
    report = {entry.surface_id: entry for entry in sdk.compatibility.check_all()}
    _require_compatible_surfaces(report, CORE_COMPAT_SURFACE_IDS)

    assert sdk.workspace.repo_path("abyss-stack") == expected_abyss_stack_source
    assert sdk.workspace.repo_origins["abyss-stack"] == "manifest:repos.abyss-stack.preferred"
    for surface_id in CORE_COMPAT_SURFACE_IDS:
        assert report[surface_id].compatible is True

    review_status = sdk.playbooks.review_status("AOA-P-0017")
    landing_governance = sdk.playbooks.landing_governance("AOA-P-0017")
    writeback = sdk.memo.writeback_map("checkpoint_export")
    writeback_governance = sdk.memo.writeback_governance("checkpoint_export")
    technique_readiness = sdk.techniques.promotion_readiness("AOA-T-0001")
    technique_readiness_entries = sdk.techniques.promotion_readiness()
    skill_catalog = sdk.skills.catalog()
    user_profile = sdk.skills.profile("user-default")
    capability_graph = sdk.skills.capability_graph()
    decision_capability = sdk.skills.capability("skill.aoa-decision")
    portable_exports = sdk.skills.portable_exports()
    mcp_dependencies = sdk.skills.mcp_dependencies()
    core_kernel = sdk.stats.core_skill_applications()
    automation = sdk.stats.automation_pipelines()

    assert review_status.gate_verdict == "composition-landed"
    assert landing_governance.landing_passed is True
    assert writeback.mapping.target_kind == "state_capsule"
    assert writeback_governance.governance_passed is True
    assert technique_readiness.readiness_passed is True
    assert len(technique_readiness_entries) >= 90
    assert skill_catalog.catalog_version == 2
    assert [entry.name for entry in skill_catalog.skills if not entry.candidate_only] == [
        "aoa-decision"
    ]
    assert user_profile.scope == "user"
    assert [entry.name for entry in user_profile.skills] == ["aoa-decision"]
    assert capability_graph.authority is False
    assert decision_capability.node.kind == "skill"
    assert decision_capability.node.owner.repo == "aoa-skills"
    assert portable_exports.export_version == 2
    assert any(entry.name == "aoa-decision" for entry in portable_exports.exports)
    assert mcp_dependencies.schema_version == 2
    assert isinstance(core_kernel, list)
    assert automation
    assert any(item.seed_ready_count >= 1 for item in automation)


def test_live_workspace_rpg_slice_reports_missing_future_transport_surfaces_honestly() -> None:
    sdk, expected_abyss_stack_source = _live_sdk_or_skip()
    _require_live_repos(sdk, ["Agents-of-Abyss"])
    report = {entry.surface_id: entry for entry in sdk.rpg.compatibility.check_all()}

    expected_surface_ids = {
        "Agents-of-Abyss.dual_vocabulary_overlay",
        "abyss-stack.rpg_build_snapshots",
        "abyss-stack.rpg_reputation_ledgers",
        "abyss-stack.rpg_quest_run_results",
        "abyss-stack.rpg_frontend_projection_bundles",
    }

    assert expected_surface_ids <= set(report)
    assert sdk.workspace.repo_path("abyss-stack") == expected_abyss_stack_source
    loaders = {
        "Agents-of-Abyss.dual_vocabulary_overlay": sdk.rpg.vocabulary,
        "abyss-stack.rpg_build_snapshots": sdk.rpg.builds,
        "abyss-stack.rpg_reputation_ledgers": sdk.rpg.ledgers,
        "abyss-stack.rpg_quest_run_results": sdk.rpg.runs,
        "abyss-stack.rpg_frontend_projection_bundles": sdk.rpg.bundles,
    }

    for surface_id in expected_surface_ids:
        if report[surface_id].compatible:
            assert loaders[surface_id]() is not None
        else:
            with pytest.raises((SurfaceNotFound, IncompatibleSurfaceVersion)):
                loaders[surface_id]()


def _live_sdk_or_skip() -> tuple[AoASDK, Path]:
    if not LIVE_WORKSPACE_ROOT.exists():
        pytest.skip("live aoa-sdk workspace checkout is unavailable")

    config = load_workspace_config(LIVE_WORKSPACE_ROOT)
    repo_config = config.repo_configs.get("abyss-stack")
    if repo_config is None or not repo_config.preferred:
        pytest.skip("abyss-stack preferred source checkout is not declared in the workspace manifest")

    expected_abyss_stack_source = resolve_pattern(repo_config.preferred[0], config)
    if not expected_abyss_stack_source.exists():
        pytest.skip("preferred abyss-stack source checkout is unavailable")

    return AoASDK.from_workspace(LIVE_WORKSPACE_ROOT), expected_abyss_stack_source


def _require_live_repos(sdk: AoASDK, repo_names: list[str]) -> None:
    for repo_name in repo_names:
        try:
            sdk.workspace.repo_path(repo_name)
        except Exception:
            pytest.skip(f"live workspace dependency is unavailable: {repo_name}")


def _require_compatible_surfaces(report: dict[str, object], surface_ids: tuple[str, ...]) -> None:
    missing = [
        surface_id
        for surface_id in surface_ids
        if surface_id not in report or getattr(report[surface_id], "exists", True) is False
    ]
    if missing:
        pytest.skip(
            "live workspace surface dependency is unavailable: "
            + ", ".join(missing)
        )
    incompatible = [
        surface_id
        for surface_id in surface_ids
        if not getattr(report[surface_id], "compatible", False)
    ]
    if incompatible:
        details = [
            f"{surface_id}: {getattr(report[surface_id], 'reason', 'incompatible')}"
            for surface_id in incompatible
        ]
        raise AssertionError(
            "live workspace surface dependency is incompatible: "
            + "; ".join(details)
        )


def test_require_compatible_surfaces_skips_only_missing_surfaces() -> None:
    with pytest.raises(pytest.skip.Exception):
        _require_compatible_surfaces({}, ("missing.surface",))


def test_require_compatible_surfaces_skips_existing_report_for_missing_surface() -> None:
    report = {
        "missing.surface": SimpleNamespace(
            exists=False,
            compatible=False,
            reason="Surface file is missing.",
        )
    }

    with pytest.raises(pytest.skip.Exception):
        _require_compatible_surfaces(report, ("missing.surface",))


def test_require_compatible_surfaces_fails_incompatible_surfaces() -> None:
    report = {
        "present.surface": SimpleNamespace(
            exists=True,
            compatible=False,
            reason="Detected unsupported version.",
        )
    }

    with pytest.raises(AssertionError, match="present\\.surface"):
        _require_compatible_surfaces(report, ("present.surface",))
