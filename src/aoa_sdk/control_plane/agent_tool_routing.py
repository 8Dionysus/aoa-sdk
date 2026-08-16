"""Runtime-neutral pre-tool routing for responsibility boundaries."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..contracts.agent_tool_routing import (
    AGENT_TOOL_ROUTING_DECISION_VERSION,
    AgentToolDispatchPosture,
    AgentToolNextOwner,
    AgentToolRouteStatus,
    AgentToolRoutingDecision,
    AgentToolRoutingIntent,
    BuiltInCodexAgentPosture,
)
from ..contracts.control_plane import ContentRef, ProvenanceRef, canonical_digest


AGENT_TOOL_ROUTING_RESOLVER_VERSION = "aoa_pre_tool_agent_routing_v1"


def _decision(
    *,
    decision_id: str,
    correlation_id: str,
    intent_ref: ContentRef,
    status: AgentToolRouteStatus,
    next_owner: AgentToolNextOwner,
    dispatch_posture: AgentToolDispatchPosture,
    built_in_codex_agent: BuiltInCodexAgentPosture,
    must_reclassify: bool,
    reason_codes: tuple[str, ...],
    provenance: ProvenanceRef,
    responsibility_result_ref: ContentRef | None = None,
) -> AgentToolRoutingDecision:
    return AgentToolRoutingDecision(
        decision_id=decision_id,
        correlation_id=correlation_id,
        intent_ref=intent_ref,
        status=status,
        next_owner=next_owner,
        dispatch_posture=dispatch_posture,
        built_in_codex_agent=built_in_codex_agent,
        must_reclassify=must_reclassify,
        reason_codes=reason_codes,
        responsibility_result_ref=responsibility_result_ref,
        resolver_version=AGENT_TOOL_ROUTING_RESOLVER_VERSION,
        provenance=provenance,
    )


def default_agent_tool_routing_provenance() -> ProvenanceRef:
    source_file = Path(__file__).resolve()
    module_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="src/aoa_sdk/control_plane/agent_tool_routing.py",
        source_ref=(
            f"{AGENT_TOOL_ROUTING_RESOLVER_VERSION}@sha256:{module_digest}"
        ),
        artifact_digest=f"sha256:{module_digest}",
        schema_ref=(
            "docs/decisions/"
            "AOA-SDK-D-0100-pre-tool-agent-routing-owner.md"
        ),
        schema_version=AGENT_TOOL_ROUTING_DECISION_VERSION,
    )


def route_agent_tool_decision(
    intent: AgentToolRoutingIntent,
    *,
    resolver_provenance: ProvenanceRef | None = None,
) -> AgentToolRoutingDecision:
    """Return the next owner without selecting or invoking an agent tool."""

    intent_digest = canonical_digest(intent)
    intent_ref = ContentRef(
        object_id=intent.intent_id,
        owner_repo="aoa-sdk",
        schema_version=intent.schema_version,
        digest=intent_digest,
    )
    provenance = resolver_provenance or default_agent_tool_routing_provenance()
    decision_id = f"agent-tool-route:{intent_digest.removeprefix('sha256:')}"

    if not intent.agent_tool_requested:
        return _decision(
            decision_id=decision_id,
            correlation_id=intent.correlation_id,
            intent_ref=intent_ref,
            status="not_applicable",
            next_owner="none",
            dispatch_posture="no_agent_tool",
            built_in_codex_agent="not_requested",
            must_reclassify=False,
            reason_codes=("no_agent_tool_requested",),
            provenance=provenance,
        )

    if intent.boundary_state == "unresolved":
        reasons: tuple[str, ...] = (
            "fresh_classification_required"
            if intent.phase != "initial"
            else "responsibility_boundary_unresolved",
        )
        if intent.phase != "initial":
            reasons = ("reentry_requires_fresh_classification", *reasons)
        return _decision(
            decision_id=decision_id,
            correlation_id=intent.correlation_id,
            intent_ref=intent_ref,
            status="awaiting_classification",
            next_owner="aoa-agents-skills",
            dispatch_posture="present_responsibility_boundary",
            built_in_codex_agent="blocked",
            must_reclassify=True,
            reason_codes=tuple(dict.fromkeys(reasons)),
            provenance=provenance,
        )

    if intent.boundary_state == "independent":
        return _decision(
            decision_id=decision_id,
            correlation_id=intent.correlation_id,
            intent_ref=intent_ref,
            status="owner_route",
            next_owner="aoa-agents-skills",
            dispatch_posture="invoke_role_first_entry",
            built_in_codex_agent="blocked",
            must_reclassify=False,
            reason_codes=("independent_responsibility_classified",),
            provenance=provenance,
            responsibility_result_ref=intent.responsibility_result_ref,
        )

    return _decision(
        decision_id=decision_id,
        correlation_id=intent.correlation_id,
        intent_ref=intent_ref,
        status="compatibility_local",
        next_owner="aoa-summon",
        dispatch_posture="allow_codex_local_after_classification",
        built_in_codex_agent="deferred_until_classified",
        must_reclassify=False,
        reason_codes=(
            "not_independent_classified",
            "codex_local_is_compatibility_only",
        ),
        provenance=provenance,
        responsibility_result_ref=intent.responsibility_result_ref,
    )
