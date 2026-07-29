from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


PART_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    PART_ROOT / "evidence" / "routing-succession-x1-consumer-zero-report.json"
)
SCHEMA_PATH = (
    PART_ROOT / "schemas" / "routing-succession-x1-consumer-zero-report.schema.json"
)

MIGRATED_REPOS = {
    "aoa-sdk",
    "abyss-stack",
    "aoa-kag",
    "aoa-stats",
    "aoa-agents",
    "aoa-evals",
    "Tree-of-Sophia",
    "aoa-playbooks",
    "Agents-of-Abyss",
    "8Dionysus",
    "aoa-techniques",
    "aoa-memo",
    "aoa-skills",
}
UNCHANGED_REPOS = {
    "abyss-machine",
    "Dionysus",
    "aoa-session-memory",
    "ATM10-Agent",
}
ZERO_REFERENCE_REPOS = {
    "aoa-4pda-connector",
    "aoa-course-connector",
    "aoa-discord-connector",
    "aoa-editing",
    "aoa-stackoverflow-connector",
    "aoa-telegram-connector",
    "aoa-xda-connector",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(
        load_json(SCHEMA_PATH),
        format_checker=FormatChecker(),
    )


def load_evidence() -> dict[str, object]:
    evidence = load_json(EVIDENCE_PATH)
    errors = sorted(validator().iter_errors(evidence), key=lambda item: list(item.path))
    assert errors == []
    return evidence


def test_x1_final_report_accounts_for_every_landed_or_classified_consumer() -> None:
    evidence = load_evidence()
    accounting = evidence["consumer_accounting"]
    consumers = evidence["landed_consumers"]

    assert accounting == {
        "r0_registered_consumers": 16,
        "post_r0_discovered_consumers": 1,
        "total_accounted_consumers": 17,
        "landed_migrations": 13,
        "unchanged_classifications": 4,
        "all_known_consumers_accounted": True,
        "all_known_consumers_landed_or_classified": True,
    }
    assert {
        item["repo"] for item in consumers if item["change_mode"] == "landed_migration"
    } == MIGRATED_REPOS
    assert {
        item["repo"]
        for item in consumers
        if item["change_mode"] == "unchanged_classification"
    } == UNCHANGED_REPOS
    assert all(item["landed_or_classified"] is True for item in consumers)
    assert all(
        item["direct_predecessor_checkout_dependencies"] == 0 for item in consumers
    )


def test_x1_final_report_proves_current_main_consumer_zero() -> None:
    evidence = load_evidence()
    zero_reference = evidence["zero_reference_repositories"]
    census = evidence["direct_dependency_census"]

    assert {item["repo"] for item in zero_reference} == ZERO_REFERENCE_REPOS
    assert all(
        item["direct_predecessor_checkout_dependencies"] == 0 for item in zero_reference
    )
    assert census["current_main_heads_checked"] == 24
    assert census["active_direct_predecessor_checkout_dependencies"] == 0
    assert census["post_candidate_drift_rescanned"] is True
    assert {
        item["repo"]: item["current_main_ref"]
        for item in census["drifted_heads_rescanned"]
    } == {
        "abyss-stack": "5fb7d6925ff502ac0b29f2213b42f27d22b6b083",
        "aoa-course-connector": "5a5219ef027df029313fc527c71a8764cfbd193e",
        "aoa-evals": "58bf49d374b008ef6625a9fd6893c61096777b4d",
        "aoa-memo": "c7c83081b7db0a0e908f14888b7438b5ecdde3bf",
        "aoa-stats": "5627c41efe9f766a4b3437da857060847cb4f0f1",
    }
    assert census["result"] == "landed_consumer_zero"


def test_x1_requires_landed_postmerge_validation_and_exact_package_cycle() -> None:
    evidence = load_evidence()
    validation = evidence["post_landing_validation"]
    package = evidence["package_compatibility"]

    assert len(validation["sdk_main_success_cycles"]) == 8
    assert all(
        item["conclusion"] == "success"
        for item in validation["sdk_main_success_cycles"]
    )
    assert len(validation["consumer_owner_landings"]) == 13
    assert validation["aoa_kag_postmerge"] == {
        "run_id": 30445769702,
        "head_sha": "15e1639740873f374faecb42029ae5cc8eb5375c",
        "conclusion": "success",
        "url": "https://github.com/8Dionysus/aoa-kag/actions/runs/30445769702",
    }
    assert validation["release_artifact_replay"] == {
        "run_id": 30456244099,
        "workflow_head_sha": "956c32cd4db6f49948a0ddeacfafb59fe8807ae7",
        "package_source_ref": "b24800bf0e9d2fa8470d7bb674dd33f6ae9e6acb",
        "runner_seconds": 143,
        "conclusion": "success",
        "url": "https://github.com/8Dionysus/aoa-sdk/actions/runs/30456244099",
    }
    assert validation["strict_postpublish_audit_passed"] is True
    assert validation["all_required_validation_green"] is True

    assert package["sdk_source_ref"] == ("b24800bf0e9d2fa8470d7bb674dd33f6ae9e6acb")
    assert package["new_wheel_sha256"] == (
        "sha256:e9af2e6674e30bc1fd81d142cd70b3149c12d11dfc6db5d1564d30028ec5d236"
    )
    assert package["predecessor_wheel_sha256"] == (
        "sha256:fe89ca58f1291119123f74fdbedf6e462bd43ccb840d5d7a08fa2dbcdb691f37"
    )
    assert package["new_version"] == "0.9.0"
    assert package["predecessor_version"] == "0.8.0"
    assert [item["operation"] for item in package["steps"]] == [
        "clean_install",
        "upgrade",
        "downgrade",
        "restore",
    ]
    assert package["clean_install_passed"] is True
    assert package["upgrade_passed"] is True
    assert package["downgrade_passed"] is True
    assert package["restore_passed"] is True

    release_artifact = package["release_artifact"]
    assert release_artifact["workflow_run_id"] == 30456244099
    assert release_artifact["workflow_head_ref"] == (
        "956c32cd4db6f49948a0ddeacfafb59fe8807ae7"
    )
    assert release_artifact["package_source_ref"] == (
        "b24800bf0e9d2fa8470d7bb674dd33f6ae9e6acb"
    )
    assert release_artifact["wheel_sha256"] == package["new_wheel_sha256"]
    assert release_artifact["sdist_sha256"] == (
        "sha256:a05670ecdc30ab6a769b7cb203114a0f6bd493312fe6f1fcbb523f6a466be40f"
    )
    assert release_artifact["local_clean_build_wheel_sha256"] == (
        "sha256:4d9a76f8be7b47e52321dd4c08299561944547a1eff0a2c510efe061ce8aa9b2"
    )
    assert release_artifact["local_clean_build_sdist_sha256"] == (
        "sha256:0b394adeb247c1b509001bfc0d8586862997ab945b5563aad92c1a7096bad0b4"
    )
    assert release_artifact["cross_environment_carrier_hash_parity"] is False
    assert release_artifact["wheel_unpacked_content_parity"] is True
    assert release_artifact["sdist_unpacked_content_parity"] is True
    assert release_artifact["sdist_external_verifier_checkout_present"] is False
    assert release_artifact["workflow_package_bundle_validation_passed"] is True
    assert release_artifact["local_exact_bundle_record_id"] == (
        "sha256:b3025e37622c12f8604639d0be7e81a408be6c41456665711d4bb9fcafe30b74"
    )
    assert release_artifact["local_exact_bundle_subject_digest"] == (
        "sha256:1d005aa8fe8cabef923f91776064b63619f489485207de6911e1e9525fc3bbf4"
    )
    assert release_artifact["local_exact_bundle_subjects_digest"] == (
        "sha256:5c492ea3bcb1c9f43fb9f84789792fb9086f6aebe722c91514894db0aa09ef9e"
    )
    assert release_artifact["verified_controls"] == [
        "abi_signature",
        "sbom",
        "slsa_in_toto",
    ]
    assert release_artifact["agent_consumer_trust_verdict"] == "allow"
    assert (
        release_artifact["release_consumer_trust_verdict"]
        == "manual_review_required"
    )
    assert release_artifact["release_consumer_manual_review_reason"] == (
        "production_consumer_requires_release_trust_root"
    )
    assert (
        release_artifact["public_release_python_distribution_consumption_claimed"]
        is False
    )


def test_x1_binds_three_post_repair_agent_os_cycles() -> None:
    window = load_evidence()["agent_os_execution_window"]
    cycles = {item["case"]: item for item in window["cycles"]}

    assert window["sdk_source_ref"] == ("b24800bf0e9d2fa8470d7bb674dd33f6ae9e6acb")
    assert window["runtime_owner_ref"] == ("c779d1413690ec11b5df7b6fc638e2a8b95510a5")
    assert window["release_workflow_run_id"] == 30456244099
    assert window["installed_wheel_sha256"] == (
        "sha256:e9af2e6674e30bc1fd81d142cd70b3149c12d11dfc6db5d1564d30028ec5d236"
    )
    assert window["installed_artifact_byte_identical_to_final_release_replay"] is True
    assert window["routing_bundle_source_ref"] == (
        "e4ffd26ed9e50125be584c00839ee6a8f7016a0d"
    )
    assert {name: item["junit_sha256"] for name, item in cycles.items()} == {
        "governed_runtime": (
            "sha256:156e13b8be7d58656ce3e7378da13dd7a2ab5da11c65d1e7f53ed1869e9cd671"
        ),
        "a2a_return": (
            "sha256:1266919ec0fc8236c6ed47ea31d1b5b80ce348e8df5ff5b55104d3bdb3036d93"
        ),
        "runtime_degradation": (
            "sha256:f05510e74105050e9328cde34cfd1ad9322ac8288b7b0ab4aa00e4e9091d13c2"
        ),
    }
    assert window["execution_cycles_passed"] == 3
    assert window["evidence_complete_closeouts"] == 3
    assert window["portability_regression_found"] is True
    assert window["portability_regression_repaired"] is True
    assert window["repair_decision"] == "AOA-SDK-D-0091"
    assert window["post_repair_cycles_passed"] is True


def test_x1_exits_compatibility_with_sdk_only_operational_rollback() -> None:
    evidence = load_evidence()
    runtime = evidence["live_runtime_evidence"]
    e1 = evidence["e1_outcome"]
    compatibility = evidence["compatibility_exit"]

    assert runtime["route_api_healthy"] is True
    assert runtime["rag_api_healthy"] is True
    assert runtime["producer_posture"] == "sdk_canonical"
    assert runtime["activation_mode"] == "authorized_live_cutover"
    assert runtime["trust_verdict"] == "allow"
    assert runtime["predecessor_operationally_required"] is False
    assert runtime["sdk_runtime_rollback_primary"] is True
    assert runtime["predecessor_implementation_required_for_rollback"] is False

    assert e1["status"] == "complete_mixed_verdict"
    assert e1["structural_process_cost_reduced"] is True
    assert e1["direct_ci_runner_time_reduced"] is False
    assert e1["direct_ci_runner_time_regression_fraction"] == 0.231
    assert e1["g13_gate"] == "pass_with_ci_runner_time_regression"

    assert len(compatibility["criteria"]) == 6
    assert {item["id"] for item in compatibility["criteria"]} == {
        "all_registered_consumers_green",
        "direct_checkout_consumer_zero",
        "install_upgrade_downgrade_rollback",
        "two_consecutive_sdk_validation_cycles",
        "runtime_mirror_and_trust_identify_sdk",
        "no_high_severity_regression",
    }
    assert all(item["exit_satisfied"] is True for item in compatibility["criteria"])
    assert compatibility["completed_post_landing_validation_cycles"] == 8
    assert compatibility["compatibility_window_exited"] is True
    assert compatibility["operational_predecessor_rollback_retired"] is True


def test_x1_is_archive_ready_but_supplies_no_archive_authority() -> None:
    evidence = load_evidence()
    predecessor = evidence["predecessor"]
    gates = evidence["remaining_external_gates"]
    verdict = evidence["verdict"]

    assert predecessor["repo"] == "8Dionysus/aoa-routing"
    assert predecessor["repository_id"] == 1186624390
    assert predecessor["repository_node_id"] == "R_kgDORrpzhg"
    assert predecessor["current_main_ref"] == (
        "19c2629a207978a118f7db81d89f44748b2e5235"
    )
    assert predecessor["latest_release_tag"] == "v0.3.0"
    assert predecessor["latest_release_url"] == (
        "https://github.com/8Dionysus/aoa-routing/releases/tag/v0.3.0"
    )
    assert predecessor["github_archived"] is False
    assert predecessor["preserved"] is True
    assert predecessor["archive_ready"] is True
    assert predecessor["archive_authorized"] is False
    assert predecessor["deprecation_release_executed"] is False
    assert predecessor["github_archive_executed"] is False
    assert predecessor["irreversible_action_taken"] is False

    assert gates == [
        {
            "id": "exact_operator_archive_approval",
            "kind": "irreversible_external_authority",
            "target": "github:repository:1186624390:8Dionysus/aoa-routing",
            "required": True,
            "satisfied": False,
            "reason": gates[0]["reason"],
        }
    ]
    assert verdict["landed_direct_checkout_consumer_zero"] is True
    assert verdict["all_consumers_landed_green"] is True
    assert verdict["compatibility_window_exited"] is True
    assert verdict["archive_ready"] is True
    assert verdict["archive_authorized"] is False
    assert verdict["irreversible_action_taken"] is False


def test_x1_schema_rejects_archive_authorization_or_executed_actions() -> None:
    evidence = load_evidence()

    mutations = [
        ("github_archived", True),
        ("archive_authorized", True),
        ("deprecation_release_executed", True),
        ("github_archive_executed", True),
        ("irreversible_action_taken", True),
    ]
    for field, value in mutations:
        candidate = deepcopy(evidence)
        candidate["predecessor"][field] = value
        assert list(validator().iter_errors(candidate))

    verdict_candidate = deepcopy(evidence)
    verdict_candidate["verdict"]["archive_authorized"] = True
    assert list(validator().iter_errors(verdict_candidate))

    approved_candidate = deepcopy(evidence)
    approved_candidate["remaining_external_gates"][0]["satisfied"] = True
    assert list(validator().iter_errors(approved_candidate))
