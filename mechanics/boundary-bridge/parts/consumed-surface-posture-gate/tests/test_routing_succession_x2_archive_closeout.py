from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


PART_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    PART_ROOT / "evidence" / "routing-succession-x2-archive-closeout.json"
)
SCHEMA_PATH = (
    PART_ROOT / "schemas" / "routing-succession-x2-archive-closeout.schema.json"
)
X1_PATH = (
    PART_ROOT / "evidence" / "routing-succession-x1-consumer-zero-report.json"
)

X1_SHA256 = "354a4e55d9be56e4801271daec3dd7b661ff6ba8fdb23da41cb32e2ce9c8a09d"
PREDECESSOR_MAIN = "5142b0176f136c7703c2c0d5d8526d106132e84e"
SDK_RUNTIME_SOURCE = "e4ffd26ed9e50125be584c00839ee6a8f7016a0d"
KAG_SUCCESSION_MAIN = "15e1639740873f374faecb42029ae5cc8eb5375c"


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


def test_x2_is_schema_valid_and_keeps_x1_immutable() -> None:
    evidence = load_evidence()
    x1_bytes = X1_PATH.read_bytes()
    x1 = json.loads(x1_bytes)
    provenance = evidence["x1_provenance"]

    assert hashlib.sha256(x1_bytes).hexdigest() == X1_SHA256
    assert provenance == {
        "evidence_ref": (
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
            "evidence/routing-succession-x1-consumer-zero-report.json"
        ),
        "evidence_sha256": f"sha256:{X1_SHA256}",
        "landed_main_ref": "9d10318e446304bb951a7c71aab0b5def961af72",
        "landed_main_validation_run_id": 30464461615,
        "landed_main_validation_url": (
            "https://github.com/8Dionysus/aoa-sdk/actions/runs/30464461615"
        ),
        "archive_readiness_ref": (
            "37c5aab075c115b50bb47fc431785b2c2b6e0d86"
        ),
        "archive_readiness_validation_run_id": 30466542840,
        "archive_readiness_validation_url": (
            "https://github.com/8Dionysus/aoa-sdk/actions/runs/30466542840"
        ),
        "immutable_historical_receipt": True,
        "historical_archive_authorized": False,
        "historical_archive_executed": False,
    }
    assert x1["predecessor"]["github_archived"] is False
    assert x1["predecessor"]["archive_authorized"] is False
    assert x1["predecessor"]["github_archive_executed"] is False
    assert x1["verdict"]["archive_authorized"] is False


def test_x2_binds_exact_operator_scope_and_predecessor_landing() -> None:
    evidence = load_evidence()
    authorization = evidence["operator_authorization"]
    landing = evidence["predecessor_landing"]

    expected_repository = {
        "id": 1186624390,
        "node_id": "R_kgDORrpzhg",
        "full_name": "8Dionysus/aoa-routing",
    }
    assert authorization["granted"] is True
    assert authorization["repository"] == expected_repository
    assert authorization["approved_actions"] == [
        "publish_final_deprecation_release",
        "update_repository_about_metadata",
        "archive_repository",
    ]
    assert authorization["forbidden_actions"] == [
        "delete_repository",
        "rename_repository",
    ]
    assert authorization["approval_scope_exact"] is True

    assert landing["pull_request"] == {
        "number": 158,
        "url": "https://github.com/8Dionysus/aoa-routing/pull/158",
        "title": "Final aoa-routing deprecation release boundary",
        "head_ref": "a7e9d60c40593b2efaee85f2a2bd2ef8eee66963",
        "exact_head_validation_run_id": 30475000557,
        "exact_head_validation_url": (
            "https://github.com/8Dionysus/aoa-routing/actions/runs/30475000557"
        ),
        "merged_at": "2026-07-29T17:27:55Z",
    }
    assert landing["landed_main_ref"] == PREDECESSOR_MAIN
    assert landing["main_validation_run_id"] == 30475444327
    assert landing["main_validation_conclusion"] == "success"
    assert landing["full_gate"] == {
        "passed_tests": 325,
        "skipped_tests": 2,
        "passed_subtests": 950,
        "result": "passed",
    }
    assert landing["final_review_result"] == "no_major_issues"


def test_x2_binds_final_release_archive_and_public_preservation() -> None:
    evidence = load_evidence()
    release = evidence["deprecation_release"]
    archive = evidence["github_archive_state"]

    assert release["tag"] == "v0.4.0"
    assert release["target_commit"] == PREDECESSOR_MAIN
    assert release["draft"] is False
    assert release["prerelease"] is False
    assert release["adds_routing_behavior"] is False
    assert release["routes_future_work_to"] == "8Dionysus/aoa-sdk"

    assert archive["repository"] == {
        "id": 1186624390,
        "node_id": "R_kgDORrpzhg",
        "full_name": "8Dionysus/aoa-routing",
    }
    assert archive["archived"] is True
    assert archive["disabled"] is False
    assert archive["visibility"] == "public"
    assert archive["renamed"] is False
    assert archive["deleted"] is False
    assert archive["homepage"] == "https://github.com/8Dionysus/aoa-sdk"
    assert {"aoa-sdk", "archived", "deprecated", "historical"} <= set(
        archive["topics"]
    )
    assert {
        (item["surface"], item["status"])
        for item in archive["public_http_checks"]
    } == {
        ("repository", 200),
        ("readme", 200),
        ("release", 200),
    }


def test_x2_live_runtime_remains_sdk_canonical_after_archive() -> None:
    evidence = load_evidence()
    runtime = evidence["live_runtime"]
    route_api = runtime["route_api"]
    mirror = runtime["runtime_mirror"]

    assert runtime["runtime_owner"] == "abyss-stack"
    assert route_api == {
        "healthy": True,
        "all_layers_ready": True,
        "layer_count": 7,
        "router_owner_repo": "aoa-sdk",
        "router_version": 1,
        "route_entry_count": 170,
    }
    assert runtime["rag_api"] == {
        "healthy": True,
        "route_api_dependency_healthy": True,
    }
    assert mirror["canonical_owner_repo"] == "aoa-sdk"
    assert mirror["canonical_source_ref"] == SDK_RUNTIME_SOURCE
    assert mirror["producer_posture"] == "sdk_canonical"
    assert mirror["activation_mode"] == "authorized_live_cutover"
    assert mirror["trust_verdict"] == "allow"
    assert runtime["predecessor_checkout_mounted"] is False
    assert runtime["predecessor_runtime_dependency_active"] is False
    assert runtime["historical_g5_archive_authorized"] is False
    assert "G5 owner-switch receipt" in (
        runtime["historical_g5_field_interpretation"]
    )


def test_x2_distinguishes_canonical_kag_succession_from_runtime_residual() -> None:
    evidence = load_evidence()
    kag = evidence["kag_posture"]
    succession = kag["canonical_provider_succession"]
    observation = kag["live_projection_observation"]
    residual = kag["residual"]

    assert succession == {
        "owner_repo": "aoa-kag",
        "decision": "AOA-KAG-D-0020",
        "pull_request_url": "https://github.com/8Dionysus/aoa-kag/pull/180",
        "landed_main_ref": KAG_SUCCESSION_MAIN,
        "main_validation_run_id": 30445769702,
        "main_validation_url": (
            "https://github.com/8Dionysus/aoa-kag/actions/runs/30445769702"
        ),
        "aoa_routing_active_provider": False,
        "current_routing_owner_route": "aoa-sdk",
    }
    assert observation["freshness_state"] == "source_unavailable"
    assert observation["predecessor_canonical_source_digest"] == ""
    assert observation["historical_runtime_slice_present"] is True
    assert residual["classification"] == "derived_projection_refresh_pending"
    assert residual["active_consumer_dependency"] is False
    assert residual["source_owner_route_correct"] is True
    assert residual["blocks_succession_closeout"] is False


def test_x2_closes_only_the_claims_its_evidence_supports() -> None:
    evidence = load_evidence()
    verdict = evidence["verdict"]

    assert verdict == {
        "sdk_single_canonical_routing_owner": True,
        "runtime_uses_sdk_artifact": True,
        "active_predecessor_checkout_consumers": 0,
        "compatibility_window_exited": True,
        "predecessor_archived": True,
        "predecessor_preserved": True,
        "deprecation_release_published": True,
        "operator_scope_respected": True,
        "delete_or_rename_executed": False,
        "succession_complete": True,
        "claim_limit": (
            "X2 closes the operator-approved hosting succession: the exact "
            "predecessor was released, preserved, and archived while the live "
            "route and RAG path stayed SDK-canonical and healthy. The old KAG "
            "runtime slice remains a flagged derived-projection refresh "
            "residual, not an active provider, consumer, producer, or rollback "
            "dependency. X2 does not rewrite X1 or retroactively change the "
            "historical G5 receipt."
        ),
    }
    assert evidence["sdk_release_audit"]["passed"] is True


def test_x2_schema_rejects_authority_identity_and_closeout_substitution() -> None:
    evidence = load_evidence()
    rejected = [
        ("operator_authorization", "granted", False),
        ("operator_authorization", "approval_scope_exact", False),
        ("github_archive_state", "archived", False),
        ("github_archive_state", "deleted", True),
        ("live_runtime", "predecessor_runtime_dependency_active", True),
        ("verdict", "succession_complete", False),
    ]
    for section, field, value in rejected:
        mutated = deepcopy(evidence)
        mutated[section][field] = value
        assert list(validator().iter_errors(mutated)), f"{section}.{field}"

    mutated = deepcopy(evidence)
    mutated["operator_authorization"]["repository"]["id"] = 1
    assert list(validator().iter_errors(mutated))

    mutated = deepcopy(evidence)
    mutated["live_runtime"]["runtime_mirror"]["canonical_owner_repo"] = "aoa-routing"
    assert list(validator().iter_errors(mutated))

    mutated = deepcopy(evidence)
    mutated["kag_posture"]["residual"]["active_consumer_dependency"] = True
    assert list(validator().iter_errors(mutated))
