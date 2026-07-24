from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "consumed-surface-posture-gate"
)
MODEL_PATH = PART_ROOT / "evidence" / "routing-succession-r1-target-operating-model.json"


def load_model() -> dict[str, object]:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def test_r1_accepts_target_without_switching_live_authority() -> None:
    model = load_model()
    scope = model["scope"]

    assert model["schema_version"] == "aoa_sdk_routing_succession_r1_operating_model_v1"
    assert model["status"] == "accepted_target_not_active"
    assert scope["current_canonical_producer"] == "aoa-routing"
    assert scope["target_canonical_producer_after_g5"] == "aoa-sdk"
    assert "remains canonical" in scope["authority_posture"]
    assert model["operating_states"][1]["runnable_producers"] == [
        "aoa-routing",
        "aoa-sdk shadow",
    ]
    assert model["operating_states"][1]["canonical_producer"] == "aoa-routing"


def test_r1_operation_matrix_has_one_explicit_authority_per_operation() -> None:
    model = load_model()
    operations = model["operation_matrix"]

    assert [row["operation"] for row in operations] == [
        "discover",
        "choose_candidate",
        "resolve_candidate",
        "authorize_candidate",
        "activate_candidate",
        "execute_candidate",
        "evaluate_result",
        "retain_result",
        "close_session",
    ]
    assert all(isinstance(row["authority_owner"], str) for row in operations)
    assert all(row["authority_owner"].strip() for row in operations)
    execute = next(row for row in operations if row["operation"] == "execute_candidate")
    assert execute["authority_owner"] == "the selected runtime owner"
    assert "executes no model or tool work" in execute["stop_line"]


def test_r1_preserves_routing_abi_and_namespace_during_owner_switch() -> None:
    model = load_model()
    policy = model["compatibility_policy"]

    assert policy["preserved_abi_epoch"] == "aoa_routing_thin_router_v1"
    assert len(policy["preserved_artifact_namespace"]) == 14
    assert policy["owner_only_switch"] == {
        "schema_or_semantic_break_allowed": False,
        "producer_provenance_change_required": True,
        "artifact_path_change_allowed": False,
        "separate_versioned_decision_required_for_break": True,
    }
    assert policy["window"]["premature_end_forbidden"] is True
    assert len(policy["window"]["exit_conditions"]) == 6


def test_r1_keeps_stronger_owners_and_archive_gate_explicit() -> None:
    model = load_model()
    gate = model["gate_g1"]
    roles = model["authority_roles"]

    assert gate["verdict"] == "pass"
    assert all(
        gate[key] is True
        for key in (
            "accepted_target_distinguished_from_live_authority",
            "one_authority_owner_per_operation",
            "source_organs_retain_semantic_authority",
            "runtime_owner_remains_external",
            "proof_owner_remains_external",
            "memory_owner_remains_external",
            "abi_and_owner_switch_are_separated",
            "paired_decisions_required_before_g5",
            "archive_requires_separate_operator_approval",
        )
    )
    assert gate["sdk_runtime_execution_claimed"] is False
    assert roles["activation_owner"] == "the selected runtime owner"
    assert roles["verdict_owner"] == "aoa-evals or a stronger proof owner"
    assert "Separate exact operator approval" in model["repository_succession_policy"][
        "archive_requirement"
    ]


def test_r1_active_routes_name_the_staged_decision() -> None:
    required = {
        REPO_ROOT / "AGENTS.md": "AOA-SDK-D-0071",
        REPO_ROOT / "DESIGN.md": "predecessor_canonical",
        REPO_ROOT / "ROADMAP.md": "routing producer succession",
        REPO_ROOT / "docs" / "boundaries.md": "AOA-SDK-D-0071",
        REPO_ROOT / "docs" / "versioning.md": "Owner-Only Routing Succession",
    }

    for path, marker in required.items():
        assert marker in path.read_text(encoding="utf-8"), path
