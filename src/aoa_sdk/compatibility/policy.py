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
