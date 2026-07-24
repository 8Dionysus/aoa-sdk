from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "consumed-surface-posture-gate"
)
EVIDENCE_PATH = PART_ROOT / "evidence" / "routing-succession-r3-migration-rehearsal.json"


def load_evidence() -> dict[str, object]:
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def test_r3_keeps_predecessor_canonical_and_discards_candidate() -> None:
    evidence = load_evidence()
    scope = evidence["scope"]
    rollback = evidence["rollback"]

    assert evidence["schema_version"] == "aoa_sdk_routing_succession_r3_rehearsal_v1"
    assert evidence["status"] == "rehearsal_passed_disposable_removed"
    assert scope["canonical_producer_before_and_after"] == "aoa-routing"
    assert rollback["canonical_files_mutated"] is False
    assert rollback["runtime_consumers_mutated"] is False
    assert rollback["removal_verified"] is True


def test_r3_preserves_all_outputs_with_hash_and_route_count_parity() -> None:
    evidence = load_evidence()
    contract = evidence["preserved_contract"]
    parity = evidence["parity_evidence"]

    assert contract["abi_epoch"] == "aoa_routing_thin_router_v1"
    assert len(contract["artifact_namespace"]) == 14
    assert set(contract["artifact_namespace"]) == set(contract["output_sha256"])
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", digest)
        for digest in contract["output_sha256"].values()
    )
    assert len(contract["route_counts"]) == 14
    assert parity["predecessor_rebuild_matches_checked_in_outputs"] == (
        "14/14 byte-identical"
    )
    assert parity["sdk_source_candidate_matches_predecessor_rebuild"] == (
        "14/14 byte-identical"
    )
    assert parity["installed_sdk_wheel_matches_predecessor_rebuild"] == (
        "14/14 byte-identical"
    )


def test_r3_proves_clean_build_consumer_compatibility_and_rollback() -> None:
    evidence = load_evidence()
    topology = evidence["rehearsed_target_topology"]
    parity = evidence["parity_evidence"]
    rollback = evidence["rollback"]

    assert topology["compatibility_facade_changed"] is False
    assert topology["minimum_slice"]["repository_topology_copied"] is False
    assert topology["runtime_or_model_client_imported"] is False
    assert parity["clean_environment"] == {
        "package_source": "installed aoa_sdk-0.5.1 wheel in a fresh venv",
        "working_root_contains_aoa_routing_checkout": False,
        "producer_module_loaded_from": "venv site-packages",
        "result": "passed",
    }
    assert parity["sdk_consumer_tests"] == "21 passed"
    assert rollback["predecessor_rebuild_after_sdk_trial"] == "14/14 byte-identical"


def test_r3_records_provenance_split_and_m1_debt_without_false_release_claim() -> None:
    evidence = load_evidence()
    provenance = evidence["provenance_posture"]
    entry = evidence["m1_entry_conditions"]

    assert provenance["embedded_owner_during_rehearsal"] == "aoa-routing"
    assert provenance["actual_shadow_producer_evidence"] == "this R3 sidecar receipt"
    assert "dual-producer" in provenance["m1_requirement"]
    assert entry["release_gate_claimed"] is False
    assert len(entry["required_before_shadow_merge"]) == 7
    assert entry["observed_mypy_result"].startswith("21 errors")


def test_r3_fixes_real_pr_order_and_gate_stop_lines() -> None:
    evidence = load_evidence()
    gate = evidence["gate_g3"]
    order = evidence["real_pr_order"]

    assert [row["order"] for row in order] == list(range(1, 8))
    assert [row["id"] for row in order] == [
        "SDK_M1_SHADOW",
        "SDK_M1_SHADOW_RELEASE",
        "ROUTING_M1_PARITY_CONSUMER",
        "SDK_G4_EVIDENCE",
        "ROUTING_M2_CONDITIONAL_HANDOFF",
        "SDK_M2_G5_SWITCH",
        "ROUTING_M3_COMPATIBILITY",
    ]
    assert gate["verdict"] == "pass"
    assert all(
        gate[key] is True
        for key in (
            "byte_parity",
            "schema_parity",
            "route_count_parity",
            "canonical_provenance_preserved",
            "actual_shadow_provenance_recorded",
            "sdk_independent_build",
            "rollback_reproducible",
            "disposable_rehearsal_removed",
            "m1_shadow_authorized",
        )
    )
    assert gate["consumer_changes_required"] is False
    assert gate["hidden_semantic_or_runtime_ownership"] is False
    assert gate["canonical_producer_switch_authorized"] is False
    assert gate["runtime_mutation_authorized"] is False
    assert gate["repository_archive_authorized"] is False
