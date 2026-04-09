import json
import re
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.compatibility.policy import SURFACE_COMPATIBILITY_RULES
from aoa_sdk.errors import IncompatibleSurfaceVersion
from aoa_sdk.routing.picker import ROUTING_ACTION_SURFACE_IDS


REPO_ROOT = Path(__file__).resolve().parents[1]


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
    tos_map = tos_root / "generated" / "root_entry_map.min.json"
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


def test_compatibility_report_includes_versioned_and_unversioned_surfaces(workspace_root: Path) -> None:
    seed_center_capsule_fixtures(workspace_root)
    dionysus_surface = workspace_root / "Dionysus" / "generated" / "seed_route_map.min.json"
    dionysus_surface.parent.mkdir(parents=True, exist_ok=True)
    dionysus_surface.write_text(
        json.dumps(
            {
                "schema_version": "dionysus_seed_route_map_v2",
                "schema_ref": "schemas/seed-route-map.schema.json",
                "owner_repo": "Dionysus",
                "surface_kind": "seed",
                "authority_ref": "docs/codex/planting-protocol.md",
                "next_live_seed_ref": "seed_expansion/example.md#seed",
                "validation_refs": ["scripts/validate_seed_route_map.py"],
                "routes": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = {entry.surface_id: entry for entry in sdk.compatibility.check_all()}

    assert report["aoa-sdk.workspace_control_plane.min"].compatible is True
    assert report["aoa-routing.federation_entrypoints.min"].compatible is True
    assert report["aoa-routing.return_navigation_hints.min"].compatible is True
    assert report["aoa-routing.owner_layer_shortlist.min"].compatible is True
    assert report["Dionysus.seed_route_map.min"].compatible is True
    assert report["8Dionysus.public_route_map.min"].compatible is True
    assert report["Agents-of-Abyss.center_entry_map.min"].compatible is True
    assert report["Tree-of-Sophia.root_entry_map.min"].compatible is True
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
    assert report["aoa-skills.project_core_skill_kernel.min"].detected_version == 1
    assert report["aoa-skills.project_core_skill_kernel.min"].compatible is True
    assert report["aoa-skills.project_foundation_profile.min"].detected_version == 1
    assert report["aoa-skills.project_foundation_profile.min"].compatible is True
    assert report["aoa-skills.project_core_outer_ring.min"].detected_version == 1
    assert report["aoa-skills.project_core_outer_ring.min"].compatible is True
    assert report["aoa-skills.project_core_outer_ring_readiness.min"].detected_version == 1
    assert report["aoa-skills.project_core_outer_ring_readiness.min"].compatible is True
    assert report["aoa-skills.project_risk_guard_ring.min"].detected_version == 1
    assert report["aoa-skills.project_risk_guard_ring.min"].compatible is True
    assert report["aoa-skills.project_risk_guard_ring_governance.min"].detected_version == 1
    assert report["aoa-skills.project_risk_guard_ring_governance.min"].compatible is True
    assert report["aoa-skills.tiny_router_candidate_bands"].detected_version == 1
    assert report["aoa-skills.tiny_router_candidate_bands"].compatible is True
    assert report["aoa-skills.tiny_router_capsules.min"].detected_version == 1
    assert report["aoa-skills.tiny_router_capsules.min"].compatible is True
    assert report["aoa-skills.skill_trigger_collision_matrix"].detected_version == 1
    assert report["aoa-skills.skill_trigger_collision_matrix"].compatible is True
    assert report["aoa-kag.kag_registry.min"].detected_version == 1
    assert report["aoa-kag.federation_spine.min"].compatible is True


def test_assert_compatible_raises_on_version_mismatch(workspace_root: Path) -> None:
    target = workspace_root / "aoa-skills" / "generated" / "runtime_discovery_index.json"
    target.write_text(
        target.read_text(encoding="utf-8").replace('"schema_version": 1', '"schema_version": 99'),
        encoding="utf-8",
    )
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    with pytest.raises(IncompatibleSurfaceVersion):
        sdk.compatibility.assert_compatible("aoa-skills.runtime_discovery_index")


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

    assert "aoa-skills.skill_capsules" in routed_surface_ids
    assert "aoa-skills.skill_sections.full" in routed_surface_ids
    assert routed_surface_ids.issubset(available_rule_ids)


def test_routing_inspect_rejects_unmapped_action_surface(workspace_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    monkeypatch.delitem(
        ROUTING_ACTION_SURFACE_IDS,
        ("aoa-skills", "generated/skill_capsules.json"),
        raising=False,
    )

    with pytest.raises(ValueError, match="add a compatibility rule before exposing it"):
        sdk.routing.inspect(kind="skill", id_or_name="aoa-change-protocol")


def test_repo_filtered_compatibility_covers_playbook_memo_technique_and_kag_surfaces(workspace_root: Path) -> None:
    seed_center_capsule_fixtures(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    playbook_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-playbooks")}
    kag_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-kag")}
    memo_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-memo")}
    technique_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-techniques")}
    routing_checks = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-routing")}
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
