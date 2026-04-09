from __future__ import annotations

from ..errors import IncompatibleSurfaceVersion, RepoNotFound, SurfaceNotFound
from ..loaders.json_file import load_json
from ..models import SurfaceCompatibilityCheck, SurfaceCompatibilityRule
from ..workspace.discovery import Workspace

SURFACE_COMPATIBILITY_RULES = {
    "aoa-routing.task_to_surface_hints": SurfaceCompatibilityRule(
        surface_id="aoa-routing.task_to_surface_hints",
        repo="aoa-routing",
        relative_path="generated/task_to_surface_hints.json",
        version_field="version",
        supported_versions=[1],
    ),
    "aoa-routing.cross_repo_registry.min": SurfaceCompatibilityRule(
        surface_id="aoa-routing.cross_repo_registry.min",
        repo="aoa-routing",
        relative_path="generated/cross_repo_registry.min.json",
        version_field="registry_version",
        supported_versions=[1],
    ),
    "aoa-routing.owner_layer_shortlist.min": SurfaceCompatibilityRule(
        surface_id="aoa-routing.owner_layer_shortlist.min",
        repo="aoa-routing",
        relative_path="generated/owner_layer_shortlist.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-routing.federation_entrypoints.min": SurfaceCompatibilityRule(
        surface_id="aoa-routing.federation_entrypoints.min",
        repo="aoa-routing",
        relative_path="generated/federation_entrypoints.min.json",
        version_field="version",
        supported_versions=[1],
    ),
    "aoa-routing.return_navigation_hints.min": SurfaceCompatibilityRule(
        surface_id="aoa-routing.return_navigation_hints.min",
        repo="aoa-routing",
        relative_path="generated/return_navigation_hints.min.json",
        version_field="version",
        supported_versions=[1],
    ),
    "aoa-sdk.workspace_control_plane.min": SurfaceCompatibilityRule(
        surface_id="aoa-sdk.workspace_control_plane.min",
        repo="aoa-sdk",
        relative_path="generated/workspace_control_plane.min.json",
        version_field="schema_version",
        supported_versions=["aoa_sdk_workspace_control_plane_v2"],
    ),
    "Dionysus.seed_route_map.min": SurfaceCompatibilityRule(
        surface_id="Dionysus.seed_route_map.min",
        repo="Dionysus",
        relative_path="generated/seed_route_map.min.json",
        version_field="schema_version",
        supported_versions=["dionysus_seed_route_map_v2"],
    ),
    "8Dionysus.public_route_map.min": SurfaceCompatibilityRule(
        surface_id="8Dionysus.public_route_map.min",
        repo="8Dionysus",
        relative_path="generated/public_route_map.min.json",
        version_field="schema_version",
        supported_versions=["8dionysus_public_route_map_v2"],
    ),
    "abyss-stack.diagnostic_surface_catalog.min": SurfaceCompatibilityRule(
        surface_id="abyss-stack.diagnostic_surface_catalog.min",
        repo="abyss-stack",
        relative_path="generated/diagnostic_surface_catalog.min.json",
        version_field="schema_version",
        supported_versions=["abyss_stack_diagnostic_surface_catalog_v1"],
    ),
    "aoa-techniques.technique_capsules": SurfaceCompatibilityRule(
        surface_id="aoa-techniques.technique_capsules",
        repo="aoa-techniques",
        relative_path="generated/technique_capsules.json",
        version_field="capsule_version",
        supported_versions=[1],
    ),
    "aoa-techniques.technique_sections.full": SurfaceCompatibilityRule(
        surface_id="aoa-techniques.technique_sections.full",
        repo="aoa-techniques",
        relative_path="generated/technique_sections.full.json",
        version_field="section_version",
        supported_versions=[1],
    ),
    "aoa-techniques.technique_promotion_readiness.min": SurfaceCompatibilityRule(
        surface_id="aoa-techniques.technique_promotion_readiness.min",
        repo="aoa-techniques",
        relative_path="generated/technique_promotion_readiness.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.runtime_discovery_index": SurfaceCompatibilityRule(
        surface_id="aoa-skills.runtime_discovery_index",
        repo="aoa-skills",
        relative_path="generated/runtime_discovery_index.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.runtime_disclosure_index": SurfaceCompatibilityRule(
        surface_id="aoa-skills.runtime_disclosure_index",
        repo="aoa-skills",
        relative_path="generated/runtime_disclosure_index.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.runtime_activation_aliases": SurfaceCompatibilityRule(
        surface_id="aoa-skills.runtime_activation_aliases",
        repo="aoa-skills",
        relative_path="generated/runtime_activation_aliases.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.runtime_tool_schemas": SurfaceCompatibilityRule(
        surface_id="aoa-skills.runtime_tool_schemas",
        repo="aoa-skills",
        relative_path="generated/runtime_tool_schemas.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.skill_capsules": SurfaceCompatibilityRule(
        surface_id="aoa-skills.skill_capsules",
        repo="aoa-skills",
        relative_path="generated/skill_capsules.json",
        version_field="capsule_version",
        supported_versions=[1],
    ),
    "aoa-skills.skill_sections.full": SurfaceCompatibilityRule(
        surface_id="aoa-skills.skill_sections.full",
        repo="aoa-skills",
        relative_path="generated/skill_sections.full.json",
        version_field="section_version",
        supported_versions=[1],
    ),
    "aoa-skills.runtime_session_contract": SurfaceCompatibilityRule(
        surface_id="aoa-skills.runtime_session_contract",
        repo="aoa-skills",
        relative_path="generated/runtime_session_contract.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.project_foundation_profile.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.project_foundation_profile.min",
        repo="aoa-skills",
        relative_path="generated/project_foundation_profile.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.tiny_router_candidate_bands": SurfaceCompatibilityRule(
        surface_id="aoa-skills.tiny_router_candidate_bands",
        repo="aoa-skills",
        relative_path="generated/tiny_router_candidate_bands.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.tiny_router_capsules.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.tiny_router_capsules.min",
        repo="aoa-skills",
        relative_path="generated/tiny_router_capsules.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.skill_trigger_collision_matrix": SurfaceCompatibilityRule(
        surface_id="aoa-skills.skill_trigger_collision_matrix",
        repo="aoa-skills",
        relative_path="generated/skill_trigger_collision_matrix.json",
        version_field="matrix_version",
        supported_versions=[1],
    ),
    "aoa-agents.runtime_seam_bindings": SurfaceCompatibilityRule(
        surface_id="aoa-agents.runtime_seam_bindings",
        repo="aoa-agents",
        relative_path="generated/runtime_seam_bindings.json",
        version_field="version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_registry.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_registry.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_registry.min.json",
        version_field="version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_activation_surfaces.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_activation_surfaces.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_activation_surfaces.min.json",
        version_field=None,
        supported_versions=[],
        notes="Versionless list surface; treated as strict-shape local-first dependency.",
    ),
    "aoa-playbooks.playbook_federation_surfaces.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_federation_surfaces.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_federation_surfaces.min.json",
        version_field=None,
        supported_versions=[],
        notes="Versionless list surface; treated as strict-shape local-first dependency.",
    ),
    "aoa-playbooks.playbook_handoff_contracts": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_handoff_contracts",
        repo="aoa-playbooks",
        relative_path="generated/playbook_handoff_contracts.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_failure_catalog": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_failure_catalog",
        repo="aoa-playbooks",
        relative_path="generated/playbook_failure_catalog.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_subagent_recipes": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_subagent_recipes",
        repo="aoa-playbooks",
        relative_path="generated/playbook_subagent_recipes.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_automation_seeds": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_automation_seeds",
        repo="aoa-playbooks",
        relative_path="generated/playbook_automation_seeds.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_composition_manifest": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_composition_manifest",
        repo="aoa-playbooks",
        relative_path="generated/playbook_composition_manifest.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_review_status.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_review_status.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_review_status.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_review_packet_contracts.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_review_packet_contracts.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_review_packet_contracts.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_review_intake.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_review_intake.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_review_intake.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-playbooks.playbook_landing_governance.min": SurfaceCompatibilityRule(
        surface_id="aoa-playbooks.playbook_landing_governance.min",
        repo="aoa-playbooks",
        relative_path="generated/playbook_landing_governance.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-memo.memory_catalog.min": SurfaceCompatibilityRule(
        surface_id="aoa-memo.memory_catalog.min",
        repo="aoa-memo",
        relative_path="generated/memory_catalog.min.json",
        version_field="catalog_version",
        supported_versions=[1],
    ),
    "aoa-memo.memory_capsules": SurfaceCompatibilityRule(
        surface_id="aoa-memo.memory_capsules",
        repo="aoa-memo",
        relative_path="generated/memory_capsules.json",
        version_field="capsule_version",
        supported_versions=[1],
    ),
    "aoa-memo.memory_sections.full": SurfaceCompatibilityRule(
        surface_id="aoa-memo.memory_sections.full",
        repo="aoa-memo",
        relative_path="generated/memory_sections.full.json",
        version_field="sections_version",
        supported_versions=[1],
    ),
    "aoa-memo.memory_object_catalog.min": SurfaceCompatibilityRule(
        surface_id="aoa-memo.memory_object_catalog.min",
        repo="aoa-memo",
        relative_path="generated/memory_object_catalog.min.json",
        version_field="catalog_version",
        supported_versions=[1],
    ),
    "aoa-memo.memory_object_capsules": SurfaceCompatibilityRule(
        surface_id="aoa-memo.memory_object_capsules",
        repo="aoa-memo",
        relative_path="generated/memory_object_capsules.json",
        version_field="capsule_version",
        supported_versions=[1],
    ),
    "aoa-memo.memory_object_sections.full": SurfaceCompatibilityRule(
        surface_id="aoa-memo.memory_object_sections.full",
        repo="aoa-memo",
        relative_path="generated/memory_object_sections.full.json",
        version_field="sections_version",
        supported_versions=[1],
    ),
    "aoa-memo.checkpoint_to_memory_contract.example": SurfaceCompatibilityRule(
        surface_id="aoa-memo.checkpoint_to_memory_contract.example",
        repo="aoa-memo",
        relative_path="examples/checkpoint_to_memory_contract.example.json",
        version_field=None,
        supported_versions=[],
        notes="Unversioned example contract; treated as strict-shape local-first dependency.",
    ),
    "aoa-memo.runtime_writeback_targets.min": SurfaceCompatibilityRule(
        surface_id="aoa-memo.runtime_writeback_targets.min",
        repo="aoa-memo",
        relative_path="generated/runtime_writeback_targets.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-memo.runtime_writeback_intake.min": SurfaceCompatibilityRule(
        surface_id="aoa-memo.runtime_writeback_intake.min",
        repo="aoa-memo",
        relative_path="generated/runtime_writeback_intake.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-memo.runtime_writeback_governance.min": SurfaceCompatibilityRule(
        surface_id="aoa-memo.runtime_writeback_governance.min",
        repo="aoa-memo",
        relative_path="generated/runtime_writeback_governance.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-evals.eval_catalog.min": SurfaceCompatibilityRule(
        surface_id="aoa-evals.eval_catalog.min",
        repo="aoa-evals",
        relative_path="generated/eval_catalog.min.json",
        version_field="catalog_version",
        supported_versions=[1],
    ),
    "aoa-evals.eval_capsules": SurfaceCompatibilityRule(
        surface_id="aoa-evals.eval_capsules",
        repo="aoa-evals",
        relative_path="generated/eval_capsules.json",
        version_field="capsule_version",
        supported_versions=[1],
    ),
    "aoa-evals.eval_sections.full": SurfaceCompatibilityRule(
        surface_id="aoa-evals.eval_sections.full",
        repo="aoa-evals",
        relative_path="generated/eval_sections.full.json",
        version_field="section_version",
        supported_versions=[1],
    ),
    "aoa-evals.comparison_spine": SurfaceCompatibilityRule(
        surface_id="aoa-evals.comparison_spine",
        repo="aoa-evals",
        relative_path="generated/comparison_spine.json",
        version_field="comparison_spine_version",
        supported_versions=[1],
    ),
    "aoa-evals.runtime_candidate_template_index.min": SurfaceCompatibilityRule(
        surface_id="aoa-evals.runtime_candidate_template_index.min",
        repo="aoa-evals",
        relative_path="generated/runtime_candidate_template_index.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-evals.runtime_candidate_intake.min": SurfaceCompatibilityRule(
        surface_id="aoa-evals.runtime_candidate_intake.min",
        repo="aoa-evals",
        relative_path="generated/runtime_candidate_intake.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.project_core_skill_kernel.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.project_core_skill_kernel.min",
        repo="aoa-skills",
        relative_path="generated/project_core_skill_kernel.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.project_core_outer_ring.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.project_core_outer_ring.min",
        repo="aoa-skills",
        relative_path="generated/project_core_outer_ring.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.project_core_outer_ring_readiness.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.project_core_outer_ring_readiness.min",
        repo="aoa-skills",
        relative_path="generated/project_core_outer_ring_readiness.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.project_risk_guard_ring.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.project_risk_guard_ring.min",
        repo="aoa-skills",
        relative_path="generated/project_risk_guard_ring.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-skills.project_risk_guard_ring_governance.min": SurfaceCompatibilityRule(
        surface_id="aoa-skills.project_risk_guard_ring_governance.min",
        repo="aoa-skills",
        relative_path="generated/project_risk_guard_ring_governance.min.json",
        version_field="schema_version",
        supported_versions=[1],
    ),
    "aoa-stats.object_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.object_summary.min",
        repo="aoa-stats",
        relative_path="generated/object_summary.min.json",
        preferred_relative_paths=["state/generated/object_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_object_summary_v1"],
    ),
    "aoa-stats.core_skill_application_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.core_skill_application_summary.min",
        repo="aoa-stats",
        relative_path="generated/core_skill_application_summary.min.json",
        preferred_relative_paths=["state/generated/core_skill_application_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_core_skill_application_summary_v1"],
    ),
    "aoa-stats.repeated_window_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.repeated_window_summary.min",
        repo="aoa-stats",
        relative_path="generated/repeated_window_summary.min.json",
        preferred_relative_paths=["state/generated/repeated_window_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_repeated_window_summary_v1"],
    ),
    "aoa-stats.route_progression_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.route_progression_summary.min",
        repo="aoa-stats",
        relative_path="generated/route_progression_summary.min.json",
        preferred_relative_paths=["state/generated/route_progression_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_route_progression_summary_v1"],
    ),
    "aoa-stats.fork_calibration_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.fork_calibration_summary.min",
        repo="aoa-stats",
        relative_path="generated/fork_calibration_summary.min.json",
        preferred_relative_paths=["state/generated/fork_calibration_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_fork_calibration_summary_v1"],
    ),
    "aoa-stats.automation_pipeline_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.automation_pipeline_summary.min",
        repo="aoa-stats",
        relative_path="generated/automation_pipeline_summary.min.json",
        preferred_relative_paths=["state/generated/automation_pipeline_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_automation_pipeline_summary_v1"],
    ),
    "aoa-stats.surface_detection_summary.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.surface_detection_summary.min",
        repo="aoa-stats",
        relative_path="generated/surface_detection_summary.min.json",
        preferred_relative_paths=["state/generated/surface_detection_summary.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_surface_detection_summary_v1"],
    ),
    "aoa-stats.summary_surface_catalog.min": SurfaceCompatibilityRule(
        surface_id="aoa-stats.summary_surface_catalog.min",
        repo="aoa-stats",
        relative_path="generated/summary_surface_catalog.min.json",
        preferred_relative_paths=["state/generated/summary_surface_catalog.min.json"],
        version_field="schema_version",
        supported_versions=["aoa_stats_summary_surface_catalog_v1"],
    ),
    "aoa-kag.kag_registry.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.kag_registry.min",
        repo="aoa-kag",
        relative_path="generated/kag_registry.min.json",
        version_field="version",
        supported_versions=[1],
    ),
    "aoa-kag.federation_spine.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.federation_spine.min",
        repo="aoa-kag",
        relative_path="generated/federation_spine.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
    "aoa-kag.tiny_consumer_bundle.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.tiny_consumer_bundle.min",
        repo="aoa-kag",
        relative_path="generated/tiny_consumer_bundle.min.json",
        version_field="bundle_version",
        supported_versions=[1],
    ),
    "aoa-kag.reasoning_handoff_pack.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.reasoning_handoff_pack.min",
        repo="aoa-kag",
        relative_path="generated/reasoning_handoff_pack.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
    "aoa-kag.return_regrounding_pack.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.return_regrounding_pack.min",
        repo="aoa-kag",
        relative_path="generated/return_regrounding_pack.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
    "aoa-kag.tos_text_chunk_map.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.tos_text_chunk_map.min",
        repo="aoa-kag",
        relative_path="generated/tos_text_chunk_map.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
    "aoa-kag.tos_retrieval_axis_pack.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.tos_retrieval_axis_pack.min",
        repo="aoa-kag",
        relative_path="generated/tos_retrieval_axis_pack.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
    "aoa-kag.cross_source_node_projection.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.cross_source_node_projection.min",
        repo="aoa-kag",
        relative_path="generated/cross_source_node_projection.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
    "aoa-kag.counterpart_federation_exposure_review.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.counterpart_federation_exposure_review.min",
        repo="aoa-kag",
        relative_path="generated/counterpart_federation_exposure_review.min.json",
        version_field="review_version",
        supported_versions=[1],
    ),
    "aoa-kag.tos_zarathustra_route_retrieval_pack.min": SurfaceCompatibilityRule(
        surface_id="aoa-kag.tos_zarathustra_route_retrieval_pack.min",
        repo="aoa-kag",
        relative_path="generated/tos_zarathustra_route_retrieval_pack.min.json",
        version_field="pack_version",
        supported_versions=[1],
    ),
}


def get_rule(surface_id: str) -> SurfaceCompatibilityRule:
    return SURFACE_COMPATIBILITY_RULES[surface_id]


def _candidate_relative_paths(rule: SurfaceCompatibilityRule) -> list[str]:
    candidates: list[str] = []
    for relative_path in [*rule.preferred_relative_paths, rule.relative_path]:
        if relative_path not in candidates:
            candidates.append(relative_path)
    return candidates


def _evaluate_data(
    rule: SurfaceCompatibilityRule,
    data,
    *,
    resolved_relative_path: str,
) -> SurfaceCompatibilityCheck:
    if rule.version_field is None:
        return SurfaceCompatibilityCheck(
            surface_id=rule.surface_id,
            repo=rule.repo,
            relative_path=rule.relative_path,
            resolved_relative_path=resolved_relative_path,
            compatibility_mode="unversioned",
            version_field=None,
            supported_versions=[],
            compatible=True,
            reason=rule.notes or "Unversioned surface accepted under strict-shape local-first policy.",
        )

    if not isinstance(data, dict):
        return SurfaceCompatibilityCheck(
            surface_id=rule.surface_id,
            repo=rule.repo,
            relative_path=rule.relative_path,
            resolved_relative_path=resolved_relative_path,
            compatibility_mode="versioned",
            version_field=rule.version_field,
            supported_versions=rule.supported_versions,
            compatible=False,
            reason="Versioned surface must load as a JSON object.",
        )

    if rule.version_field not in data:
        return SurfaceCompatibilityCheck(
            surface_id=rule.surface_id,
            repo=rule.repo,
            relative_path=rule.relative_path,
            resolved_relative_path=resolved_relative_path,
            compatibility_mode="versioned",
            version_field=rule.version_field,
            supported_versions=rule.supported_versions,
            compatible=False,
            reason=f"Missing version field {rule.version_field!r}.",
        )

    detected_version = data[rule.version_field]
    compatible = detected_version in rule.supported_versions
    reason = (
        f"Detected supported version {detected_version!r}."
        if compatible
        else f"Detected unsupported version {detected_version!r}; supported versions: {rule.supported_versions!r}."
    )
    return SurfaceCompatibilityCheck(
        surface_id=rule.surface_id,
        repo=rule.repo,
        relative_path=rule.relative_path,
        resolved_relative_path=resolved_relative_path,
        compatibility_mode="versioned",
        version_field=rule.version_field,
        supported_versions=rule.supported_versions,
        detected_version=detected_version,
        compatible=compatible,
        reason=reason,
    )


def load_surface(workspace: Workspace, surface_id: str):
    rule = get_rule(surface_id)
    last_missing_error: Exception | None = None
    for relative_path in _candidate_relative_paths(rule):
        try:
            data = load_json(workspace.surface_path(rule.repo, relative_path))
        except (RepoNotFound, SurfaceNotFound) as exc:
            last_missing_error = exc
            continue
        result = _evaluate_data(rule, data, resolved_relative_path=relative_path)
        if not result.compatible:
            raise IncompatibleSurfaceVersion(
                f"Incompatible surface {surface_id}: {result.reason}"
            )
        return data
    if last_missing_error is not None:
        raise last_missing_error
    raise SurfaceNotFound(f"Surface file is missing: {rule.repo}/{rule.relative_path}")


class CompatibilityAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def rules(self) -> list[SurfaceCompatibilityRule]:
        return list(SURFACE_COMPATIBILITY_RULES.values())

    def check(self, surface_id: str) -> SurfaceCompatibilityCheck:
        rule = get_rule(surface_id)
        for relative_path in _candidate_relative_paths(rule):
            try:
                data = load_json(self.workspace.surface_path(rule.repo, relative_path))
            except (RepoNotFound, SurfaceNotFound):
                continue
            return _evaluate_data(rule, data, resolved_relative_path=relative_path)

        return SurfaceCompatibilityCheck(
            surface_id=rule.surface_id,
            repo=rule.repo,
            relative_path=rule.relative_path,
            exists=False,
            compatibility_mode="versioned" if rule.version_field else "unversioned",
            version_field=rule.version_field,
            supported_versions=rule.supported_versions,
            compatible=False,
            reason="Surface file is missing.",
        )

    def check_repo(self, repo: str) -> list[SurfaceCompatibilityCheck]:
        return [self.check(rule.surface_id) for rule in self.rules() if rule.repo == repo]

    def check_all(self) -> list[SurfaceCompatibilityCheck]:
        return [self.check(rule.surface_id) for rule in self.rules()]

    def assert_compatible(self, surface_id: str) -> None:
        result = self.check(surface_id)
        if not result.compatible:
            raise IncompatibleSurfaceVersion(
                f"Incompatible surface {surface_id}: {result.reason}"
            )
