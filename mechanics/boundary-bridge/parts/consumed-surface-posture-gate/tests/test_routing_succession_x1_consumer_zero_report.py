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
EXPECTED_OWNER_LANDINGS = {
    "aoa-sdk": (
        "780ac06d1739246d6402445e6ec43ef39a97b90a",
        "https://github.com/8Dionysus/aoa-sdk/pull/239",
    ),
    "abyss-stack": (
        "c779d1413690ec11b5df7b6fc638e2a8b95510a5",
        "https://github.com/8Dionysus/abyss-stack/pull/336",
    ),
    "aoa-kag": (
        "15e1639740873f374faecb42029ae5cc8eb5375c",
        "https://github.com/8Dionysus/aoa-kag/pull/180",
    ),
    "aoa-stats": (
        "740c57d6ab2fe78d6a8440c19c2637431e039c6b",
        "https://github.com/8Dionysus/aoa-stats/pull/178",
    ),
    "aoa-agents": (
        "92dd79e6c79fef60faedf6b97f2c65ff89477d06",
        "https://github.com/8Dionysus/aoa-agents/pull/270",
    ),
    "aoa-evals": (
        "12b408727e40174dd10e1f9ad0fa2e7f7fd11eec",
        "https://github.com/8Dionysus/aoa-evals/pull/437",
    ),
    "Tree-of-Sophia": (
        "d95a583272acb84dcb5b7e6896801f0364c7b234",
        "https://github.com/8Dionysus/Tree-of-Sophia/pull/140",
    ),
    "aoa-playbooks": (
        "b72ca2d333bcdf516ed6656e34670fa93df88162",
        "https://github.com/8Dionysus/aoa-playbooks/pull/198",
    ),
    "Agents-of-Abyss": (
        "66d86b04e685cf06b03a95a3f9c74e7c8d607740",
        "https://github.com/8Dionysus/Agents-of-Abyss/pull/270",
    ),
    "8Dionysus": (
        "aa67908a137a9c9631a439f266d32a8918c7213c",
        "https://github.com/8Dionysus/8Dionysus/pull/136",
    ),
    "aoa-techniques": (
        "9a5222cc6a6b1fdc52b4df906f49dadfd0383c71",
        "https://github.com/8Dionysus/aoa-techniques/pull/497",
    ),
    "aoa-memo": (
        "bcda57fe47d5e3daaee8258cc4428dc6315ae239",
        "https://github.com/8Dionysus/aoa-memo/pull/291",
    ),
    "aoa-skills": (
        "5929ad000ff06750ced1c806766138dc11e54e5a",
        "https://github.com/8Dionysus/aoa-skills/pull/380",
    ),
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
    scope = evidence["scope"]
    accounting = evidence["consumer_accounting"]
    consumers = evidence["landed_consumers"]

    assert scope == {
        "r0_baseline_ref": (
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
            "evidence/routing-succession-r0-baseline.json"
        ),
        "r0_baseline_sha256": (
            "sha256:ee28bc71bd083c0e1a35ca42ea0debb326d8f1ca312189a9c854de447e0b8219"
        ),
        "candidate_ref": (
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
            "evidence/routing-succession-x1-consumer-zero-candidate.json"
        ),
        "candidate_sha256": (
            "sha256:4cbeb2945940e3a760c37e47dc0ff56d9e533155b66aca05ddf8baad5e3eaf21"
        ),
        "sdk_landed_control_plane_ref": (
            "780ac06d1739246d6402445e6ec43ef39a97b90a"
        ),
        "sdk_final_evidence_ref": "956c32cd4db6f49948a0ddeacfafb59fe8807ae7",
        "x1_report_landed_main_ref": (
            "9d10318e446304bb951a7c71aab0b5def961af72"
        ),
        "observation_class": (
            "exact landed main refs, owner PR and CI evidence, immutable-tag "
            "release replay artifacts, exact installed wheels, live "
            "SDK-canonical runtime health, post-repair Agent OS lifecycle cycles, "
            "and the landed X1 report's own successful main validation receipt"
        ),
        "claim_boundary": (
            "X1 proves landed direct-checkout consumer-zero, compatibility exit, "
            "operational predecessor rollback retirement, and every substantive "
            "archive-readiness prerequisite, including its own successful "
            "post-merge main validation. Archive readiness is true, but this "
            "receipt does not authorize a deprecation release, repository metadata "
            "mutation, GitHub archival, deletion, rename, or any other irreversible "
            "predecessor action; separate exact operator approval remains required."
        ),
    }
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
    assert census["patterns"] == [
        "AOA_ROUTING_ROOT",
        "/srv/AbyssOS/aoa-routing",
        "github.com/8Dionysus/aoa-routing",
        "repository: 8Dionysus/aoa-routing",
    ]
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


def test_x1_records_landed_report_and_successful_own_postmerge_cycle() -> None:
    evidence = load_evidence()
    validation = evidence["post_landing_validation"]
    package = evidence["package_compatibility"]

    assert {
        item["head_sha"]
        for item in validation["pre_migration_sdk_main_success_cycles"]
    } == {
        "ac6c1e5f7dd824ebaa6a583c4bb8965e3ca194a0",
        "eda623ecd8a77606414a29ea7102369e369b95be",
        "cbf225627f9f28d0470deb8a962ae12d1fe72375",
    }
    assert len(validation["sdk_main_success_cycles"]) == 6
    assert [item["head_sha"] for item in validation["sdk_main_success_cycles"]] == [
        "780ac06d1739246d6402445e6ec43ef39a97b90a",
        "b24800bf0e9d2fa8470d7bb674dd33f6ae9e6acb",
        "0d9efa61e3ab1fd3abf8facdd194a1b2025193b6",
        "35e01329763d68e148144d9f5b4be4bce43446b8",
        "956c32cd4db6f49948a0ddeacfafb59fe8807ae7",
        "9d10318e446304bb951a7c71aab0b5def961af72",
    ]
    assert all(
        item["conclusion"] == "success"
        for item in validation["sdk_main_success_cycles"]
    )
    assert {
        item["repo"]: (item["migration_ref"], item["pr"])
        for item in validation["consumer_owner_landings"]
    } == EXPECTED_OWNER_LANDINGS
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
    assert validation["x1_report_postmerge_validation"] == {
        "required": True,
        "status": "success",
        "landed_main_ref": "9d10318e446304bb951a7c71aab0b5def961af72",
        "run_id": 30464461615,
        "conclusion": "success",
        "url": "https://github.com/8Dionysus/aoa-sdk/actions/runs/30464461615",
        "runner_seconds": 215,
        "validated_x1_report_path": (
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
            "evidence/routing-succession-x1-consumer-zero-report.json"
        ),
        "claim_limit": validation["x1_report_postmerge_validation"]["claim_limit"],
    }
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
    assert runtime["archive_authorized"] is False

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
    assert compatibility["completed_post_landing_validation_cycles"] == 6
    assert compatibility["compatibility_window_exited"] is True
    assert compatibility["operational_predecessor_rollback_retired"] is True


def test_x1_is_archive_ready_and_supplies_no_archive_authority() -> None:
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
        ("archive_ready", False),
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

    ready_candidate = deepcopy(evidence)
    ready_candidate["verdict"]["archive_ready"] = False
    assert list(validator().iter_errors(ready_candidate))

    runtime_candidate = deepcopy(evidence)
    runtime_candidate["live_runtime_evidence"]["archive_authorized"] = True
    assert list(validator().iter_errors(runtime_candidate))

    operator_candidate = deepcopy(evidence)
    operator_candidate["remaining_external_gates"][0]["satisfied"] = True
    assert list(validator().iter_errors(operator_candidate))

    patterns_candidate = deepcopy(evidence)
    patterns_candidate["direct_dependency_census"]["patterns"] = []
    assert list(validator().iter_errors(patterns_candidate))

    scope_candidate = deepcopy(evidence)
    scope_candidate["scope"]["candidate_sha256"] = False
    assert list(validator().iter_errors(scope_candidate))

    consumer_membership_candidate = deepcopy(evidence)
    consumer_membership_candidate["landed_consumers"][1] = deepcopy(
        consumer_membership_candidate["landed_consumers"][0]
    )
    assert list(validator().iter_errors(consumer_membership_candidate))

    zero_membership_candidate = deepcopy(evidence)
    zero_membership_candidate["zero_reference_repositories"][1] = deepcopy(
        zero_membership_candidate["zero_reference_repositories"][0]
    )
    assert list(validator().iter_errors(zero_membership_candidate))

    pre_migration_candidate = deepcopy(evidence)
    pre_migration_candidate["post_landing_validation"][
        "pre_migration_sdk_main_success_cycles"
    ][0]["head_sha"] = "780ac06d1739246d6402445e6ec43ef39a97b90a"
    assert list(validator().iter_errors(pre_migration_candidate))

    post_landing_candidate = deepcopy(evidence)
    post_landing_candidate["post_landing_validation"]["sdk_main_success_cycles"][
        0
    ]["head_sha"] = "ac6c1e5f7dd824ebaa6a583c4bb8965e3ca194a0"
    assert list(validator().iter_errors(post_landing_candidate))

    landing_shape_candidate = deepcopy(evidence)
    landing_shape_candidate["post_landing_validation"]["consumer_owner_landings"][
        0
    ] = None
    assert list(validator().iter_errors(landing_shape_candidate))

    duplicate_landing_candidate = deepcopy(evidence)
    duplicate_landing_candidate["post_landing_validation"][
        "consumer_owner_landings"
    ][1] = deepcopy(
        duplicate_landing_candidate["post_landing_validation"][
            "consumer_owner_landings"
        ][0]
    )
    assert list(validator().iter_errors(duplicate_landing_candidate))
