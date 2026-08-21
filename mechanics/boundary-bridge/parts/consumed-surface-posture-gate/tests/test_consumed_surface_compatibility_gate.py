import json
import re
from shutil import copytree, rmtree
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.compatibility.policy import SURFACE_COMPATIBILITY_RULES
from aoa_sdk.errors import IncompatibleSurfaceVersion
from aoa_sdk.routing.picker import ROUTING_ACTION_SURFACE_IDS


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError("could not resolve aoa-sdk repo root")


REPO_ROOT = _repo_root()


def seed_center_capsule_fixtures(workspace_root: Path) -> None:
    aoa_root = workspace_root / "Agents-of-Abyss"
    aoa_center = aoa_root / "generated" / "center_entry_map.min.json"
    aoa_center.parent.mkdir(parents=True, exist_ok=True)
    aoa_center.write_text(
        json.dumps(
            {
                "schema_version": "aoa_center_entry_map_v1",
                "schema_ref": "schemas/center-entry-map.schema.json",
                "owner_repo": "Agents-of-Abyss",
                "surface_kind": "center_entry_map",
                "authority_ref": "CHARTER.md",
                "public_root_ref": "README.md",
                "registry_ref": "generated/ecosystem_registry.min.json",
                "supporting_inventory_ref": "generated/federation_supporting_inventory.min.json",
                "validation_refs": ["scripts/build_center_entry_map.py"],
                "routes": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    tos_root = workspace_root / "Tree-of-Sophia"
    (tos_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (tos_root / "README.md").write_text("# Tree-of-Sophia\n", encoding="utf-8")
    tos_map = tos_root / "ToS" / "derived-exports" / "root_entry_map.min.json"
    tos_map.parent.mkdir(parents=True, exist_ok=True)
    tos_map.write_text(
        json.dumps(
            {
                "schema_version": "tos_root_entry_map_v1",
                "schema_ref": "schemas/root-entry-map.schema.json",
                "owner_repo": "Tree-of-Sophia",
                "surface_kind": "root_entry_map",
                "authority_ref": "CHARTER.md",
                "public_root_ref": "README.md",
                "current_tiny_entry_ref": "examples/tos_tiny_entry_route.example.json",
                "export_ref": "generated/kag_export.min.json",
                "validation_refs": ["scripts/build_root_entry_map.py"],
                "routes": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    dionysus_root = workspace_root / "Dionysus"
    (dionysus_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (dionysus_root / "README.md").write_text(
        "# Dionysus\n",
        encoding="utf-8",
    )
    dionysus_schemas = {
        "interview-session.schema.json": (
            "https://8dionysus.github.io/Dionysus/schemas/"
            "interview-session.schema.json"
        ),
        "portrait-claim.schema.json": (
            "https://8dionysus.github.io/Dionysus/schemas/"
            "portrait-claim.schema.json"
        ),
    }
    for filename, schema_id in dionysus_schemas.items():
        target = dionysus_root / "schemas" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": schema_id,
                    "title": filename,
                    "type": "object",
                    "properties": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )


def test_compatibility_report_includes_versioned_and_unversioned_surfaces(workspace_root: Path) -> None:
    seed_center_capsule_fixtures(workspace_root)

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = {entry.surface_id: entry for entry in sdk.compatibility.check_all()}

    assert report["aoa-sdk.workspace_control_plane.min"].compatible is True
    assert report["aoa-routing.federation_entrypoints.min"].compatible is True
    assert report["aoa-routing.return_navigation_hints.min"].compatible is True
    assert report["aoa-routing.owner_layer_shortlist.min"].compatible is True
    assert report["aoa-routing.stats_regrounding_hints.min"].compatible is True
    assert report["Dionysus.interview_session.schema"].compatible is True
    assert report["Dionysus.portrait_claim.schema"].compatible is True
    assert report["8Dionysus.public_route_map.min"].compatible is True
    assert (
        report["8Dionysus.public_route_map.min"].detected_version
        == "8dionysus_public_route_map_v3"
    )
    assert report["Agents-of-Abyss.center_entry_map.min"].compatible is True
    assert report["Tree-of-Sophia.root_entry_map.min"].compatible is True
    assert (
        report["Tree-of-Sophia.root_entry_map.min"].resolved_relative_path
        == "ToS/derived-exports/root_entry_map.min.json"
    )
    assert report["abyss-stack.diagnostic_surface_catalog.min"].compatible is True
    assert report["aoa-playbooks.playbook_activation_surfaces.min"].compatibility_mode == "unversioned"
    assert report["aoa-playbooks.playbook_activation_surfaces.min"].compatible is True
    assert report["aoa-playbooks.playbook_federation_surfaces.min"].compatibility_mode == "unversioned"
    assert report["aoa-playbooks.playbook_federation_surfaces.min"].compatible is True
    assert report["aoa-playbooks.playbook_review_status.min"].detected_version == 1
    assert report["aoa-playbooks.playbook_review_status.min"].compatible is True
    assert report["aoa-playbooks.playbook_review_packet_contracts.min"].detected_version == 1
    assert report["aoa-playbooks.playbook_review_packet_contracts.min"].compatible is True
    assert report["aoa-playbooks.playbook_review_intake.min"].detected_version == 1
    assert report["aoa-playbooks.playbook_review_intake.min"].compatible is True
    assert report["aoa-playbooks.playbook_landing_governance.min"].detected_version == 1
    assert report["aoa-playbooks.playbook_landing_governance.min"].compatible is True
    assert report["aoa-memo.checkpoint_to_memory_contract.example"].compatibility_mode == "unversioned"
    assert report["aoa-memo.checkpoint_to_memory_contract.example"].compatible is True
    assert report["aoa-memo.runtime_writeback_targets.min"].detected_version == 1
    assert report["aoa-memo.runtime_writeback_targets.min"].compatible is True
    assert report["aoa-memo.runtime_writeback_intake.min"].detected_version == 1
    assert report["aoa-memo.runtime_writeback_intake.min"].compatible is True
    assert report["aoa-memo.runtime_writeback_governance.min"].detected_version == 1
    assert report["aoa-memo.runtime_writeback_governance.min"].compatible is True
    assert report["aoa-techniques.technique_promotion_readiness.min"].detected_version == 1
    assert report["aoa-techniques.technique_promotion_readiness.min"].compatible is True
    assert report["aoa-evals.eval_catalog.min"].detected_version == 1
    assert report["aoa-evals.eval_catalog.min"].compatible is True
    assert report["aoa-evals.runtime_candidate_template_index.min"].detected_version == 1
    assert report["aoa-evals.runtime_candidate_template_index.min"].compatible is True
    assert report["aoa-evals.runtime_candidate_intake.min"].detected_version == 1
    assert report["aoa-evals.runtime_candidate_intake.min"].compatible is True
    assert (
        report["aoa-stats.source_coverage_summary.min"].detected_version
        == "aoa_stats_source_coverage_summary_v1"
    )
    assert report["aoa-skills.agent_skill_catalog"].detected_version == 2
    assert report["aoa-skills.agent_skill_catalog"].compatible is True
    assert report["aoa-skills.skill_pack_profiles.resolved"].detected_version == 2
    assert report["aoa-skills.skill_pack_profiles.resolved"].compatible is True
    assert (
        report["aoa-skills.capability_graph"].detected_version
        == "aoa-capability-graph-v1"
    )
    assert report["aoa-skills.capability_graph"].compatible is True
    assert report["aoa-skills.portable_export_map"].detected_version == 2
    assert report["aoa-skills.portable_export_map"].compatible is True
    assert report["aoa-skills.mcp_dependency_manifest"].detected_version == 2
    assert report["aoa-skills.mcp_dependency_manifest"].compatible is True
    for retired_surface_id in (
        "aoa-skills.runtime_discovery_index",
        "aoa-skills.project_foundation_profile.min",
        "aoa-skills.skill_capsules",
        "aoa-skills.skill_sections.full",
    ):
        assert retired_surface_id not in report
    assert report["aoa-agents.codex_projection_manifest"].detected_version == 2
    assert report["aoa-agents.codex_projection_manifest"].compatible is True
    assert report["aoa-kag.kag_registry.min"].detected_version == 1
    assert report["aoa-kag.federation_spine.min"].compatible is True


def test_diagnostic_surface_catalog_uses_part_local_path_not_old_root_path(
    workspace_root: Path,
) -> None:
    stack_root = workspace_root / "src" / "abyss-stack"
    old_root_path = stack_root / "generated" / "diagnostic_surface_catalog.min.json"
    old_root_path.write_text(
        json.dumps({"schema_version": "stale_old_root_diagnostic_surface_catalog_v0"}) + "\n",
        encoding="utf-8",
    )
    part_local_path = (
        stack_root
        / "mechanics"
        / "diagnostic-spine"
        / "parts"
        / "diagnostic-surfaces"
        / "generated"
        / "diagnostic_surface_catalog.min.json"
    )
    part_local_path.parent.mkdir(parents=True, exist_ok=True)
    part_local_path.write_text(
        json.dumps({"schema_version": "abyss_stack_diagnostic_surface_catalog_v1"}) + "\n",
        encoding="utf-8",
    )

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    rule = SURFACE_COMPATIBILITY_RULES["abyss-stack.diagnostic_surface_catalog.min"]
    report = sdk.compatibility.check("abyss-stack.diagnostic_surface_catalog.min")

    assert rule.relative_path == (
        "mechanics/diagnostic-spine/parts/diagnostic-surfaces/generated/"
        "diagnostic_surface_catalog.min.json"
    )
    assert rule.preferred_relative_paths == []
    assert report.compatible is True
    assert report.resolved_relative_path == (
        "mechanics/diagnostic-spine/parts/diagnostic-surfaces/generated/"
        "diagnostic_surface_catalog.min.json"
    )


def test_kag_compatibility_prefers_current_part_local_paths(
    workspace_root: Path,
) -> None:
    preferred_paths = {
        "aoa-kag.federation_spine.min": (
            "mechanics/boundary-bridge/parts/federation-spine/generated/"
            "federation_spine.min.json"
        ),
        "aoa-kag.tiny_consumer_bundle.min": (
            "mechanics/boundary-bridge/parts/tiny-consumer-bundle/generated/"
            "tiny_consumer_bundle.min.json"
        ),
        "aoa-kag.reasoning_handoff_pack.min": (
            "mechanics/checkpoint/parts/reasoning-handoff/generated/"
            "reasoning_handoff_pack.min.json"
        ),
        "aoa-kag.return_regrounding_pack.min": (
            "mechanics/recurrence/parts/return-regrounding/generated/"
            "return_regrounding_pack.min.json"
        ),
        "aoa-kag.tos_text_chunk_map.min": (
            "mechanics/distillation/parts/tos-text-chunk-map/generated/"
            "tos_text_chunk_map.min.json"
        ),
        "aoa-kag.tos_retrieval_axis_pack.min": (
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
            "tos_retrieval_axis_pack.min.json"
        ),
        "aoa-kag.cross_source_node_projection.min": (
            "mechanics/boundary-bridge/parts/cross-source-projection/generated/"
            "cross_source_node_projection.min.json"
        ),
        "aoa-kag.counterpart_federation_exposure_review.min": (
            "mechanics/audit/parts/exposure-review/generated/"
            "counterpart_federation_exposure_review.min.json"
        ),
        "aoa-kag.tos_zarathustra_route_retrieval_pack.min": (
            "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
            "tos_zarathustra_route_retrieval_pack.min.json"
        ),
    }
    kag_root = workspace_root / "aoa-kag"
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    for surface_id, preferred_path in preferred_paths.items():
        rule = SURFACE_COMPATIBILITY_RULES[surface_id]
        legacy_path = kag_root / rule.relative_path
        current_path = kag_root / preferred_path
        current_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.write_bytes(legacy_path.read_bytes())
        report = sdk.compatibility.check(surface_id)

        assert rule.preferred_relative_paths == [preferred_path]
        assert report.compatible is True
        assert report.resolved_relative_path == preferred_path

    inspect_result = sdk.kag.inspect("AOA-K-0011")
    query_result = sdk.kag.query_mode("local_search")
    assert inspect_result.source_files[-1].endswith(
        preferred_paths["aoa-kag.tos_zarathustra_route_retrieval_pack.min"]
    )
    assert query_result.source_files == [
        str(kag_root / preferred_paths["aoa-kag.reasoning_handoff_pack.min"]),
        str(kag_root / preferred_paths["aoa-kag.return_regrounding_pack.min"]),
    ]


def test_agent_runtime_seam_bindings_v2_is_compatible(workspace_root: Path) -> None:
    target = workspace_root / "aoa-agents" / "generated" / "runtime_seam_bindings.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["version"] = 2
    payload["artifact_identity"] = {
        "abi_epoch": "aoa_agents_runtime_seam_bindings_v2"
    }
    target.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.compatibility.check("aoa-agents.runtime_seam_bindings")

    assert report.compatible is True
    assert report.detected_version == 2


def test_workspace_control_plane_requires_artifact_identity(workspace_root: Path) -> None:
    target = workspace_root / "aoa-sdk" / "generated" / "workspace_control_plane.min.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload.pop("artifact_identity", None)
    target.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.compatibility.check("aoa-sdk.workspace_control_plane.min")

    assert report.compatible is False
    assert "artifact_identity" in report.reason


def test_workspace_control_plane_rejects_malformed_artifact_identity(workspace_root: Path) -> None:
    target = workspace_root / "aoa-sdk" / "generated" / "workspace_control_plane.min.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["artifact_identity"] = None
    target.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.compatibility.check("aoa-sdk.workspace_control_plane.min")

    assert report.compatible is False
    assert "artifact_identity" in report.reason
    assert "JSON objects" in report.reason


def test_diagnostic_surface_catalog_does_not_fallback_to_old_root_path(
    workspace_root: Path,
) -> None:
    stack_root = workspace_root / "src" / "abyss-stack"
    part_local_path = (
        stack_root
        / "mechanics"
        / "diagnostic-spine"
        / "parts"
        / "diagnostic-surfaces"
        / "generated"
        / "diagnostic_surface_catalog.min.json"
    )
    part_local_path.unlink()

    old_root_path = stack_root / "generated" / "diagnostic_surface_catalog.min.json"
    old_root_path.parent.mkdir(parents=True, exist_ok=True)
    old_root_path.write_text(
        json.dumps({"schema_version": "abyss_stack_diagnostic_surface_catalog_v1"}) + "\n",
        encoding="utf-8",
    )

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    report = sdk.compatibility.check("abyss-stack.diagnostic_surface_catalog.min")

    assert report.exists is False
    assert report.compatible is False
    assert report.resolved_relative_path is None


def test_memo_generated_readers_use_canonical_refactored_paths(
    workspace_root: Path,
) -> None:
    expected_paths = {
        "aoa-memo.memory_catalog.min": "generated/memory/memory_catalog.min.json",
        "aoa-memo.memory_capsules": "generated/memory/memory_capsules.json",
        "aoa-memo.memory_sections.full": "generated/memory/memory_sections.full.json",
        "aoa-memo.memory_object_catalog.min": "generated/memory-objects/memory_object_catalog.min.json",
        "aoa-memo.memory_object_capsules": "generated/memory-objects/memory_object_capsules.json",
        "aoa-memo.memory_object_sections.full": "generated/memory-objects/memory_object_sections.full.json",
    }
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    for surface_id, expected_path in expected_paths.items():
        rule = SURFACE_COMPATIBILITY_RULES[surface_id]
        assert rule.relative_path == expected_path
        assert rule.preferred_relative_paths == []
        report = sdk.compatibility.check(surface_id)
        assert report.compatible is True
        assert report.resolved_relative_path == expected_path


def test_memo_writeback_surfaces_use_canonical_mechanics_paths(
    workspace_root: Path,
) -> None:
    expected_paths = {
        "aoa-memo.runtime_writeback_targets.min": (
            "mechanics/writeback/parts/runtime-and-temperature/generated/"
            "runtime_writeback_targets.min.json"
        ),
        "aoa-memo.runtime_writeback_intake.min": (
            "mechanics/writeback/parts/runtime-and-temperature/generated/"
            "runtime_writeback_intake.min.json"
        ),
        "aoa-memo.runtime_writeback_governance.min": (
            "mechanics/writeback/parts/runtime-and-temperature/generated/"
            "runtime_writeback_governance.min.json"
        ),
    }

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    contract = sdk.compatibility.check("aoa-memo.checkpoint_to_memory_contract.example")

    contract_rule = SURFACE_COMPATIBILITY_RULES["aoa-memo.checkpoint_to_memory_contract.example"]
    assert contract_rule.preferred_relative_paths == []
    assert contract.compatible is True
    assert (
        contract.resolved_relative_path
        == "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/examples/"
        "checkpoint_to_memory_contract.example.json"
    )
    for surface_id, expected_path in expected_paths.items():
        rule = SURFACE_COMPATIBILITY_RULES[surface_id]
        assert rule.relative_path == expected_path
        assert rule.preferred_relative_paths == []
        report = sdk.compatibility.check(surface_id)
        assert report.compatible is True
        assert report.resolved_relative_path == expected_path


def test_eval_runtime_candidate_readers_use_canonical_audit_part_paths(
    workspace_root: Path,
) -> None:
    expected_paths = {
        "aoa-evals.runtime_candidate_template_index.min": (
            "mechanics/audit/parts/candidate-readers/generated/"
            "runtime_candidate_template_index.min.json"
        ),
        "aoa-evals.runtime_candidate_intake.min": "mechanics/audit/parts/candidate-readers/generated/runtime_candidate_intake.min.json",
    }
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    for surface_id, expected_path in expected_paths.items():
        rule = SURFACE_COMPATIBILITY_RULES[surface_id]
        assert rule.relative_path == expected_path
        assert rule.preferred_relative_paths == []
        report = sdk.compatibility.check(surface_id)
        assert report.compatible is True
        assert report.resolved_relative_path == expected_path


def test_center_entry_map_current_v2_is_compatible(workspace_root: Path) -> None:
    seed_center_capsule_fixtures(workspace_root)
    surface_path = workspace_root / "Agents-of-Abyss" / "generated" / "center_entry_map.min.json"
    payload = json.loads(surface_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "aoa_center_entry_map_v2"
    payload["route_contract_ref"] = "docs/START_HERE_ROUTE_CONTRACT.md"
    surface_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.compatibility.check("Agents-of-Abyss.center_entry_map.min")

    assert report.compatible is True
    assert report.detected_version == "aoa_center_entry_map_v2"


def test_public_route_map_v2_remains_compatible(workspace_root: Path) -> None:
    target = workspace_root / "8Dionysus" / "generated" / "public_route_map.min.json"
    target.write_text(
        json.dumps({"schema_version": "8dionysus_public_route_map_v2"}) + "\n",
        encoding="utf-8",
    )

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.compatibility.check("8Dionysus.public_route_map.min")

    assert report.compatible is True
    assert report.detected_version == "8dionysus_public_route_map_v2"


def test_public_route_map_requires_the_declared_route_shape(workspace_root: Path) -> None:
    target = workspace_root / "8Dionysus" / "generated" / "public_route_map.min.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload.pop("routes")
    target.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.compatibility.check("8Dionysus.public_route_map.min")

    assert report.compatible is False
    assert "routes" in report.reason


def test_assert_compatible_raises_on_version_mismatch(workspace_root: Path) -> None:
    target = (
        workspace_root
        / "aoa-skills"
        / "generated"
        / "skill_pack_profiles.resolved.json"
    )
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["schema_version"] = 99
    target.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    with pytest.raises(IncompatibleSurfaceVersion):
        sdk.compatibility.assert_compatible("aoa-skills.skill_pack_profiles.resolved")


def test_compatibility_rules_cover_every_literal_sdk_surface_load() -> None:
    pattern = re.compile(r'\bload_surface\(\s*[^,]+,\s*"([^"]+)"\s*\)')
    loaded_surface_ids: set[str] = set()

    for path in (REPO_ROOT / "src" / "aoa_sdk").rglob("*.py"):
        loaded_surface_ids.update(pattern.findall(path.read_text(encoding="utf-8")))

    expected_surface_ids = loaded_surface_ids | set(ROUTING_ACTION_SURFACE_IDS.values())

    assert expected_surface_ids.issubset(SURFACE_COMPATIBILITY_RULES)


def test_routing_action_surfaces_are_compatibility_checked(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    available_rule_ids = set(SURFACE_COMPATIBILITY_RULES)

    routed_surface_ids: set[str] = set()
    for hint in sdk.routing.hints():
        for action_name in ("inspect", "expand"):
            action = hint.actions.get(action_name)
            if action is None or not action.surface_file:
                continue
            action_repo = action.surface_repo or hint.source_repo
            surface_id = ROUTING_ACTION_SURFACE_IDS.get((action_repo, action.surface_file))
            if surface_id is not None:
                routed_surface_ids.add(surface_id)

    assert not any(repo == "aoa-skills" for repo, _ in ROUTING_ACTION_SURFACE_IDS)
    assert "aoa-skills.skill_capsules" not in routed_surface_ids
    assert "aoa-skills.skill_sections.full" not in routed_surface_ids
    assert routed_surface_ids.issubset(available_rule_ids)


def test_non_skill_routing_inspect_rejects_unmapped_action_surface(
    workspace_root: Path,
) -> None:
    hints_path = (
        workspace_root
        / "aoa-routing"
        / "generated"
        / "task_to_surface_hints.json"
    )
    payload = json.loads(hints_path.read_text(encoding="utf-8"))
    payload["hints"][0]["kind"] = "technique"
    hints_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    with pytest.raises(ValueError, match="add a compatibility rule before exposing it"):
        sdk.routing.inspect(kind="technique", id_or_name="aoa-change-protocol")


def test_repo_filtered_compatibility_covers_playbook_memo_technique_and_kag_surfaces(workspace_root: Path) -> None:
    seed_center_capsule_fixtures(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    playbook_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-playbooks")}
    kag_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-kag")}
    memo_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-memo")}
    technique_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-techniques")}
    routing_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-routing")}
    agent_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-agents")}
    aoa_center_checks = {
        entry.surface_id: entry for entry in sdk.compatibility.check_repo("Agents-of-Abyss")
    }
    tos_checks = {
        entry.surface_id: entry for entry in sdk.compatibility.check_repo("Tree-of-Sophia")
    }

    assert playbook_checks["aoa-playbooks.playbook_federation_surfaces.min"].compatible is True
    assert routing_checks["aoa-routing.federation_entrypoints.min"].compatible is True
    assert routing_checks["aoa-routing.return_navigation_hints.min"].compatible is True
    assert routing_checks["aoa-routing.owner_layer_shortlist.min"].compatible is True
    assert routing_checks["aoa-routing.stats_regrounding_hints.min"].compatible is True
    assert agent_checks["aoa-agents.codex_projection_manifest"].detected_version == 2
    assert agent_checks["aoa-agents.codex_projection_manifest"].compatible is True
    assert aoa_center_checks["Agents-of-Abyss.center_entry_map.min"].compatible is True
    assert tos_checks["Tree-of-Sophia.root_entry_map.min"].compatible is True
    assert playbook_checks["aoa-playbooks.playbook_automation_seeds"].detected_version == 1
    assert playbook_checks["aoa-playbooks.playbook_composition_manifest"].compatible is True
    assert playbook_checks["aoa-playbooks.playbook_review_status.min"].detected_version == 1
    assert playbook_checks["aoa-playbooks.playbook_review_packet_contracts.min"].detected_version == 1
    assert playbook_checks["aoa-playbooks.playbook_review_intake.min"].detected_version == 1
    assert playbook_checks["aoa-playbooks.playbook_landing_governance.min"].detected_version == 1
    assert memo_checks["aoa-memo.checkpoint_to_memory_contract.example"].compatible is True
    assert memo_checks["aoa-memo.runtime_writeback_targets.min"].detected_version == 1
    assert memo_checks["aoa-memo.runtime_writeback_intake.min"].detected_version == 1
    assert memo_checks["aoa-memo.runtime_writeback_intake.min"].compatible is True
    assert memo_checks["aoa-memo.runtime_writeback_governance.min"].detected_version == 1
    assert memo_checks["aoa-memo.runtime_writeback_governance.min"].compatible is True
    eval_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-evals")}
    assert eval_checks["aoa-evals.runtime_candidate_intake.min"].detected_version == 1
    assert eval_checks["aoa-evals.runtime_candidate_intake.min"].compatible is True
    assert technique_checks["aoa-techniques.technique_promotion_readiness.min"].detected_version == 1
    assert technique_checks["aoa-techniques.technique_promotion_readiness.min"].compatible is True
    assert kag_checks["aoa-kag.kag_registry.min"].detected_version == 1
    assert kag_checks["aoa-kag.tos_zarathustra_route_retrieval_pack.min"].compatible is True


def test_routing_compatibility_prefers_runtime_bundle_without_predecessor_checkout(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predecessor_root = workspace_root / "aoa-routing"
    bundle_root = workspace_root / "runtime-routing-bundle"
    copytree(predecessor_root / "generated", bundle_root / "generated")
    rmtree(predecessor_root)
    monkeypatch.setenv("AOA_SDK_ROUTING_BUNDLE_ROOT", str(bundle_root))

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    routing_checks = {
        entry.surface_id: entry
        for entry in sdk.compatibility.check_repo("aoa-routing")
    }

    assert sdk.workspace.has_repo("aoa-routing") is False
    assert sdk.routing.hints()
    assert routing_checks["aoa-routing.task_to_surface_hints"].compatible is True
    assert routing_checks["aoa-routing.cross_repo_registry.min"].compatible is True


def test_compatibility_accepts_legacy_and_v2_stats_and_routing_capsules(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    stats_catalog = workspace_root / "aoa-stats" / "generated" / "summary_surface_catalog.min.json"
    stats_catalog.write_text(
        json.dumps(
            {
                "schema_version": "aoa_stats_summary_surface_catalog_v1",
                "generated_from": {
                    "receipt_input_paths": ["receipts.json"],
                    "total_receipts": 1,
                    "latest_observed_at": "2026-04-05T10:35:00Z",
                },
                "surfaces": [
                    {
                        "name": "core_skill_application_summary",
                        "path": "generated/core_skill_application_summary.min.json",
                        "schema_ref": "schemas/core-skill-application-summary.schema.json",
                        "primary_question": "Which project-core kernel skills are actually finishing and how often, without inferring usage from general receipt volume?",
                        "derivation_rule": "aggregate core_skill_application_receipt payloads by kernel_id and skill_name",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    federation = workspace_root / "aoa-routing" / "generated" / "federation_entrypoints.min.json"
    federation.write_text('{"version":1}\n', encoding="utf-8")
    returns = workspace_root / "aoa-routing" / "generated" / "return_navigation_hints.min.json"
    returns.write_text('{"version":1}\n', encoding="utf-8")

    assert sdk.compatibility.check("aoa-stats.summary_surface_catalog.min").compatible is True
    assert sdk.compatibility.check("aoa-routing.federation_entrypoints.min").compatible is True
    assert sdk.compatibility.check("aoa-routing.return_navigation_hints.min").compatible is True


def test_unversioned_checkpoint_writeback_contract_requires_required_keys(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    contract_path = (
        workspace_root
        / "aoa-memo"
        / "mechanics"
        / "checkpoint"
        / "parts"
        / "checkpoint-to-memory-mapping"
        / "examples"
        / "checkpoint_to_memory_contract.example.json"
    )
    contract_path.write_text(
        json.dumps(
            {
                "contract_type": "checkpoint_to_memory_contract",
                "mapping_rules": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    check = sdk.compatibility.check("aoa-memo.checkpoint_to_memory_contract.example")

    assert check.compatibility_mode == "unversioned"
    assert check.compatible is False
    assert "contract_id" in check.reason


def test_unversioned_playbook_surfaces_require_json_arrays(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    activation_path = workspace_root / "aoa-playbooks" / "generated" / "playbook_activation_surfaces.min.json"
    activation_path.write_text(json.dumps({"unexpected": "object"}) + "\n", encoding="utf-8")

    check = sdk.compatibility.check("aoa-playbooks.playbook_activation_surfaces.min")

    assert check.compatibility_mode == "unversioned"
    assert check.compatible is False
    assert "JSON array" in check.reason
