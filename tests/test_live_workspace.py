from __future__ import annotations

from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import IncompatibleSurfaceVersion, SurfaceNotFound


LIVE_WORKSPACE_ROOT = Path("/srv/aoa-sdk")
LIVE_ABYSS_STACK_SOURCE = Path("~/src/abyss-stack").expanduser().resolve()


@pytest.mark.skipif(
    not LIVE_WORKSPACE_ROOT.exists() or not LIVE_ABYSS_STACK_SOURCE.exists(),
    reason="live /srv workspace or ~/src/abyss-stack source checkout is unavailable",
)
def test_live_workspace_prefers_home_src_abyss_stack_and_keeps_core_compat_green() -> None:
    sdk = AoASDK.from_workspace(LIVE_WORKSPACE_ROOT)
    report = {entry.surface_id: entry for entry in sdk.compatibility.check_all()}

    assert sdk.workspace.repo_path("abyss-stack") == LIVE_ABYSS_STACK_SOURCE
    assert sdk.workspace.repo_origins["abyss-stack"] == "manifest:repos.abyss-stack.preferred"
    assert report["aoa-techniques.technique_capsules"].compatible is True
    assert report["aoa-techniques.technique_sections.full"].compatible is True
    assert report["aoa-routing.federation_entrypoints.min"].compatible is True
    assert report["aoa-routing.return_navigation_hints.min"].compatible is True
    assert report["aoa-playbooks.playbook_federation_surfaces.min"].compatible is True
    assert report["aoa-playbooks.playbook_review_status.min"].compatible is True
    assert report["aoa-playbooks.playbook_landing_governance.min"].compatible is True
    assert report["aoa-memo.checkpoint_to_memory_contract.example"].compatible is True
    assert report["aoa-memo.runtime_writeback_governance.min"].compatible is True
    assert report["aoa-techniques.technique_promotion_readiness.min"].compatible is True
    assert report["aoa-skills.project_core_skill_kernel.min"].compatible is True
    assert report["aoa-skills.project_foundation_profile.min"].compatible is True
    assert report["aoa-skills.project_core_outer_ring.min"].compatible is True
    assert report["aoa-skills.project_core_outer_ring_readiness.min"].compatible is True
    assert report["aoa-skills.project_risk_guard_ring.min"].compatible is True
    assert report["aoa-skills.project_risk_guard_ring_governance.min"].compatible is True
    assert report["aoa-skills.tiny_router_candidate_bands"].compatible is True
    assert report["aoa-skills.tiny_router_capsules.min"].compatible is True
    assert report["aoa-skills.skill_trigger_collision_matrix"].compatible is True
    assert report["aoa-stats.object_summary.min"].compatible is True
    assert report["aoa-stats.core_skill_application_summary.min"].compatible is True
    assert report["aoa-stats.automation_pipeline_summary.min"].compatible is True
    assert report["8Dionysus.public_route_map.min"].compatible is True
    assert report["Dionysus.seed_route_map.min"].compatible is True
    assert report["abyss-stack.diagnostic_surface_catalog.min"].compatible is True
    assert report["aoa-kag.kag_registry.min"].compatible is True
    assert report["aoa-kag.tos_zarathustra_route_retrieval_pack.min"].compatible is True

    review_status = sdk.playbooks.review_status("AOA-P-0017")
    landing_governance = sdk.playbooks.landing_governance("AOA-P-0017")
    writeback = sdk.memo.writeback_map("checkpoint_export")
    writeback_governance = sdk.memo.writeback_governance("checkpoint_export")
    technique_readiness = sdk.techniques.promotion_readiness("AOA-T-0001")
    technique_readiness_entries = sdk.techniques.promotion_readiness()
    foundation = sdk.skills.project_foundation()
    outer_ring = sdk.skills.project_core_outer_ring()
    outer_ring_readiness = sdk.skills.project_core_outer_ring_readiness()
    risk_ring = sdk.skills.project_risk_guard_ring()
    risk_ring_governance = sdk.skills.project_risk_guard_ring_governance()
    core_kernel = sdk.stats.core_skill_applications()
    automation = sdk.stats.automation_pipelines()

    assert review_status.gate_verdict == "composition-landed"
    assert landing_governance.landing_passed is True
    assert writeback.mapping.target_kind == "state_capsule"
    assert writeback_governance.governance_passed is True
    assert technique_readiness.readiness_passed is True
    assert len(technique_readiness_entries) >= 90
    assert foundation.foundation_id == "project-foundation-v1"
    assert len(foundation.skills) == 22
    assert outer_ring.ring_id == "project-core-engineering-ring-v1"
    assert len(outer_ring.skills) == 10
    assert len(outer_ring_readiness) == 10
    assert all(item.readiness_passed for item in outer_ring_readiness)
    assert risk_ring.ring_id == "project-risk-guard-ring-v1"
    assert len(risk_ring.skills) == 5
    assert len(risk_ring_governance) == 5
    assert all(item.governance_passed for item in risk_ring_governance)
    assert isinstance(core_kernel, list)
    assert automation
    assert any(item.seed_ready_count >= 1 for item in automation)


@pytest.mark.skipif(
    not LIVE_WORKSPACE_ROOT.exists() or not LIVE_ABYSS_STACK_SOURCE.exists(),
    reason="live /srv workspace or ~/src/abyss-stack source checkout is unavailable",
)
def test_live_workspace_rpg_slice_reports_missing_future_transport_surfaces_honestly() -> None:
    sdk = AoASDK.from_workspace(LIVE_WORKSPACE_ROOT)
    report = {entry.surface_id: entry for entry in sdk.rpg.compatibility.check_all()}

    expected_surface_ids = {
        "Agents-of-Abyss.dual_vocabulary_overlay",
        "abyss-stack.rpg_build_snapshots",
        "abyss-stack.rpg_reputation_ledgers",
        "abyss-stack.rpg_quest_run_results",
        "abyss-stack.rpg_frontend_projection_bundles",
    }

    assert expected_surface_ids <= set(report)
    assert sdk.workspace.repo_path("abyss-stack") == LIVE_ABYSS_STACK_SOURCE
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
