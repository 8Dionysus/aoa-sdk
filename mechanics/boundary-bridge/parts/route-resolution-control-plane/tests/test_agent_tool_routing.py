from __future__ import annotations

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


def test_local_result_routes_only_to_summon_compatibility_leaf() -> None:
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
    assert decision.status == "compatibility_local"
    assert decision.next_owner == "aoa-summon"
    assert decision.dispatch_posture == "allow_codex_local_after_classification"
    assert decision.built_in_codex_agent == "deferred_until_classified"


def test_compaction_resume_cannot_reuse_a_classification() -> None:
    with pytest.raises(ValidationError, match="fresh unresolved classification"):
        _intent(
            phase="compaction_resume",
            boundary="independent",
            result=_ref("aoa-agents", "obligation:route-proof", "agent-obligation-v1"),
        )


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
