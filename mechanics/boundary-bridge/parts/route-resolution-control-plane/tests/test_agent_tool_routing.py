from __future__ import annotations

import hashlib
import json

import pytest
from pydantic import ValidationError

from aoa_sdk.contracts.agent_tool_routing import AgentToolRoutingIntent
from aoa_sdk.contracts.control_plane import ContentRef, ProvenanceRef
from aoa_sdk.control_plane.agent_tool_routing import route_agent_tool_decision


ZERO_DIGEST = "sha256:" + "0" * 64


def _ref(owner: str, object_id: str, schema: str) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo=owner,
        schema_version=schema,
        digest=ZERO_DIGEST,
    )


def _provenance() -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="current-holder",
        artifact_ref="goal-pressure.json",
        source_ref="goal-pressure-v1@local",
        artifact_digest=ZERO_DIGEST,
        schema_ref="goal-pressure-v1",
        schema_version="goal-pressure-v1",
    )


def _intent(
    *,
    requested: bool = True,
    phase: str = "initial",
    boundary: str = "unresolved",
    result: ContentRef | None = None,
    local_next_route: str | None = None,
    route_anchor: str = "goal:route-proof",
    responsibility_changed: bool = False,
) -> AgentToolRoutingIntent:
    return AgentToolRoutingIntent(
        intent_id="intent:route-proof",
        correlation_id="corr:route-proof",
        goal_ref=_ref("current-holder", "goal:route-proof", "goal-v1"),
        current_holder_ref=_ref("current-holder", "holder:route-proof", "holder-v1"),
        route_anchor=route_anchor,
        phase=phase,  # type: ignore[arg-type]
        agent_tool_requested=requested,
        boundary_state=boundary,  # type: ignore[arg-type]
        responsibility_changed=responsibility_changed,
        responsibility_result_ref=result,
        local_next_route=local_next_route,  # type: ignore[arg-type]
        provenance=_provenance(),
    )


def test_non_agent_request_is_not_applicable() -> None:
    decision = route_agent_tool_decision(
        _intent(requested=False, boundary="not_present")
    )
    assert decision.status == "not_applicable"
    assert decision.next_owner == "none"
    assert decision.built_in_codex_agent == "not_requested"


def test_unresolved_boundary_routes_to_aoa_agents_and_blocks_builtin_tool() -> None:
    decision = route_agent_tool_decision(_intent())
    assert decision.status == "awaiting_classification"
    assert decision.next_owner == "aoa-agents-skills"
    assert decision.dispatch_posture == "present_responsibility_boundary"
    assert decision.built_in_codex_agent == "blocked"
    assert decision.must_reclassify is True


def test_independent_result_stays_with_role_first_owner() -> None:
    result = _ref("aoa-agents", "obligation:route-proof", "agent-obligation-v1")
    decision = route_agent_tool_decision(
        _intent(boundary="independent", result=result)
    )
    assert decision.status == "owner_route"
    assert decision.next_owner == "aoa-agents-skills"
    assert decision.dispatch_posture == "invoke_role_first_entry"
    assert decision.built_in_codex_agent == "blocked"
    assert decision.responsibility_result_ref == result


def test_independent_result_requires_exact_obligation_schema() -> None:
    with pytest.raises(ValidationError, match="agent-obligation-v1"):
        _intent(
            boundary="independent",
            result=_ref("aoa-agents", "obligation:route-proof", "phase-binding-v1"),
        )


@pytest.mark.parametrize("phase", ["initial", "compaction_resume", "reentry", "plan_change"])
def test_native_helper_needs_no_owner_classification(phase: str) -> None:
    decision = route_agent_tool_decision(_intent(phase=phase, boundary="not_present"))
    assert decision.schema_version == "aoa_agent_tool_routing_decision_v2"
    assert decision.status == "native_codex"
    assert decision.next_owner == "none"
    assert decision.dispatch_posture == "native_codex"
    assert decision.built_in_codex_agent == "native"
    assert decision.must_reclassify is False
    assert decision.responsibility_result_ref is None


def test_explicit_negative_classification_returns_to_native_codex() -> None:
    result = _ref(
        "aoa-agents",
        "classification:route-proof",
        "responsibility-classification-v1",
    )
    decision = route_agent_tool_decision(
        _intent(
            boundary="not_independent",
            result=result,
            local_next_route="codex_local",
        )
    )
    assert decision.status == "native_codex"
    assert decision.next_owner == "none"
    assert decision.dispatch_posture == "native_codex"
    assert decision.built_in_codex_agent == "native"
    assert decision.responsibility_result_ref == result


@pytest.mark.parametrize("phase", ["compaction_resume", "reentry", "plan_change"])
def test_reentry_preserves_existing_responsibility(phase: str) -> None:
    result = _ref("aoa-agents", "obligation:route-proof", "agent-obligation-v1")
    decision = route_agent_tool_decision(
        _intent(phase=phase, boundary="independent", result=result)
    )
    assert decision.status == "owner_route"
    assert decision.next_owner == "aoa-agents-skills"
    assert decision.dispatch_posture == "inspect_existing_responsibility"
    assert decision.responsibility_result_ref == result
    assert decision.must_reclassify is False
    assert decision.built_in_codex_agent == "blocked"


def test_changed_responsibility_cannot_reuse_prior_classification() -> None:
    with pytest.raises(ValidationError, match="changed responsibility"):
        _intent(
            phase="plan_change",
            boundary="independent",
            result=_ref("aoa-agents", "obligation:route-proof", "agent-obligation-v1"),
            responsibility_changed=True,
        )
    decision = route_agent_tool_decision(
        _intent(phase="plan_change", responsibility_changed=True)
    )
    assert decision.status == "awaiting_classification"
    assert decision.must_reclassify is True
    assert decision.reason_codes == ("responsibility_changed",)


def test_absent_boundary_cannot_discard_an_existing_owner_ref() -> None:
    with pytest.raises(ValidationError, match="absent responsibility boundary"):
        _intent(
            boundary="not_present",
            result=_ref("aoa-agents", "obligation:route-proof", "agent-obligation-v1"),
        )
    with pytest.raises(ValidationError, match="absent responsibility boundary"):
        _intent(boundary="not_present", local_next_route="codex_local")


def test_v1_input_remains_readable_but_new_decisions_use_v2() -> None:
    payload = _intent().model_dump(mode="json")
    payload["schema_version"] = "aoa_agent_tool_routing_intent_v1"
    payload.pop("responsibility_changed")
    intent = AgentToolRoutingIntent.model_validate(payload)
    decision = route_agent_tool_decision(intent)
    assert decision.intent_ref.schema_version == "aoa_agent_tool_routing_intent_v1"
    expected_digest = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert decision.intent_ref.digest == expected_digest
    assert decision.schema_version == "aoa_agent_tool_routing_decision_v2"
    assert decision.status == "awaiting_classification"
    with pytest.raises(ValidationError, match="requires the v2 intent"):
        AgentToolRoutingIntent.model_validate(dict(payload, responsibility_changed=True))


def test_route_anchor_is_bound_to_goal() -> None:
    with pytest.raises(ValidationError, match="route_anchor"):
        _intent(route_anchor="goal:other")


def test_same_typed_input_produces_same_decision_identity() -> None:
    first = route_agent_tool_decision(_intent())
    second = route_agent_tool_decision(_intent())
    assert first == second
    assert first.decision_id == second.decision_id


def test_routing_contracts_are_available_from_public_models_module() -> None:
    from aoa_sdk.models import (
        AgentToolRoutingDecision as PublicDecision,
        AgentToolRoutingIntent as PublicIntent,
    )

    assert PublicIntent is AgentToolRoutingIntent
    assert PublicDecision.__name__ == "AgentToolRoutingDecision"
