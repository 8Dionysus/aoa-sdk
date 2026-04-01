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


def _evaluate_data(
    rule: SurfaceCompatibilityRule,
    data,
) -> SurfaceCompatibilityCheck:
    if rule.version_field is None:
        return SurfaceCompatibilityCheck(
            surface_id=rule.surface_id,
            repo=rule.repo,
            relative_path=rule.relative_path,
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
        compatibility_mode="versioned",
        version_field=rule.version_field,
        supported_versions=rule.supported_versions,
        detected_version=detected_version,
        compatible=compatible,
        reason=reason,
    )


def load_surface(workspace: Workspace, surface_id: str):
    rule = get_rule(surface_id)
    data = load_json(workspace.surface_path(rule.repo, rule.relative_path))
    result = _evaluate_data(rule, data)
    if not result.compatible:
        raise IncompatibleSurfaceVersion(
            f"Incompatible surface {surface_id}: {result.reason}"
        )
    return data


class CompatibilityAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def rules(self) -> list[SurfaceCompatibilityRule]:
        return list(SURFACE_COMPATIBILITY_RULES.values())

    def check(self, surface_id: str) -> SurfaceCompatibilityCheck:
        rule = get_rule(surface_id)
        try:
            data = load_json(self.workspace.surface_path(rule.repo, rule.relative_path))
        except (RepoNotFound, SurfaceNotFound):
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

        return _evaluate_data(rule, data)

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
