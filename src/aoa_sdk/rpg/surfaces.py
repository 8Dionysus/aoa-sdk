from __future__ import annotations

from ..errors import IncompatibleSurfaceVersion, RepoNotFound, SurfaceNotFound
from ..loaders.json_file import load_json
from ..models import SurfaceCompatibilityCheck, SurfaceCompatibilityRule
from ..workspace.discovery import Workspace


RPG_SURFACE_COMPATIBILITY_RULES = {
    "Agents-of-Abyss.dual_vocabulary_overlay": SurfaceCompatibilityRule(
        surface_id="Agents-of-Abyss.dual_vocabulary_overlay",
        repo="Agents-of-Abyss",
        relative_path="generated/dual_vocabulary_overlay.json",
        version_field="schema_version",
        supported_versions=["dual_vocabulary_overlay_v1"],
    ),
    "abyss-stack.rpg_build_snapshots": SurfaceCompatibilityRule(
        surface_id="abyss-stack.rpg_build_snapshots",
        repo="abyss-stack",
        relative_path="generated/rpg/agent_build_snapshots.json",
        version_field="schema_version",
        supported_versions=["agent_build_snapshot_collection_v1"],
    ),
    "abyss-stack.rpg_reputation_ledgers": SurfaceCompatibilityRule(
        surface_id="abyss-stack.rpg_reputation_ledgers",
        repo="abyss-stack",
        relative_path="generated/rpg/reputation_ledgers.json",
        version_field="schema_version",
        supported_versions=["reputation_ledger_collection_v1"],
    ),
    "abyss-stack.rpg_quest_run_results": SurfaceCompatibilityRule(
        surface_id="abyss-stack.rpg_quest_run_results",
        repo="abyss-stack",
        relative_path="generated/rpg/quest_run_results.json",
        version_field="schema_version",
        supported_versions=["quest_run_result_collection_v1"],
    ),
    "abyss-stack.rpg_frontend_projection_bundles": SurfaceCompatibilityRule(
        surface_id="abyss-stack.rpg_frontend_projection_bundles",
        repo="abyss-stack",
        relative_path="generated/rpg/frontend_projection_bundles.json",
        version_field="schema_version",
        supported_versions=["frontend_projection_bundle_collection_v1"],
    ),
}


def get_rule(surface_id: str) -> SurfaceCompatibilityRule:
    try:
        return RPG_SURFACE_COMPATIBILITY_RULES[surface_id]
    except KeyError as exc:
        raise SurfaceNotFound(f"Unknown RPG surface id: {surface_id}") from exc


def _evaluate_data(rule: SurfaceCompatibilityRule, data: object) -> SurfaceCompatibilityCheck:
    if rule.version_field is None:
        return SurfaceCompatibilityCheck(
            surface_id=rule.surface_id,
            repo=rule.repo,
            relative_path=rule.relative_path,
            compatibility_mode="unversioned",
            version_field=None,
            supported_versions=[],
            compatible=True,
            reason=rule.notes or "Unversioned surface accepted.",
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
        else (
            f"Detected unsupported version {detected_version!r}; "
            f"supported versions: {rule.supported_versions!r}."
        )
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


def load_rpg_surface(workspace: Workspace, surface_id: str) -> object:
    rule = get_rule(surface_id)
    data = load_json(workspace.surface_path(rule.repo, rule.relative_path))
    result = _evaluate_data(rule, data)
    if not result.compatible:
        raise IncompatibleSurfaceVersion(f"Incompatible RPG surface {surface_id}: {result.reason}")
    return data


class RpgCompatibilityAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def rules(self) -> list[SurfaceCompatibilityRule]:
        return list(RPG_SURFACE_COMPATIBILITY_RULES.values())

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

    def check_all(self) -> list[SurfaceCompatibilityCheck]:
        return [self.check(rule.surface_id) for rule in self.rules()]

    def assert_compatible(self, surface_id: str) -> None:
        result = self.check(surface_id)
        if not result.compatible:
            raise IncompatibleSurfaceVersion(f"Incompatible RPG surface {surface_id}: {result.reason}")
