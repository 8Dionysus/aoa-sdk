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
    assert report["aoa-playbooks.playbook_federation_surfaces.min"].compatible is True
    assert report["aoa-playbooks.playbook_review_status.min"].compatible is True
    assert report["aoa-memo.checkpoint_to_memory_contract.example"].compatible is True
    assert report["aoa-skills.project_core_skill_kernel.min"].compatible is True
    assert report["aoa-skills.project_core_outer_ring.min"].compatible is True
    assert report["aoa-skills.project_core_outer_ring_readiness.min"].compatible is True
    assert report["aoa-stats.object_summary.min"].compatible is True
    assert report["aoa-stats.core_skill_application_summary.min"].compatible is True
    assert report["aoa-stats.automation_pipeline_summary.min"].compatible is True
    assert report["aoa-kag.kag_registry.min"].compatible is True
    assert report["aoa-kag.tos_zarathustra_route_retrieval_pack.min"].compatible is True

    review_status = sdk.playbooks.review_status("AOA-P-0017")
    writeback = sdk.memo.writeback_map("checkpoint_export")
    outer_ring = sdk.skills.project_core_outer_ring()
    outer_ring_readiness = sdk.skills.project_core_outer_ring_readiness()
    core_kernel = sdk.stats.core_skill_applications()
    automation = sdk.stats.automation_pipelines()

    assert review_status.gate_verdict == "composition-landed"
    assert writeback.mapping.target_kind == "state_capsule"
    assert outer_ring.ring_id == "project-core-engineering-ring-v1"
    assert len(outer_ring.skills) == 10
    assert len(outer_ring_readiness) == 10
    assert all(item.readiness_passed for item in outer_ring_readiness)
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
