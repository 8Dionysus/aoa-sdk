"""Deterministic, explainable RouteIntent resolution without activation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ...contracts.control_plane import (
    ApprovalRequirement,
    CandidateExplanation,
    CapabilityRef,
    ContentRef,
    ProvenanceRef,
    RouteCandidate,
    RouteConstraint,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    candidate_explanation_disposition,
    canonical_digest,
)
from ...contracts.routing import RegistryEntry
from ...contracts.skills import (
    CapabilityNode,
    CapabilityRetrievalDocument,
)
from .snapshot import RoutingResolutionSnapshot


ROUTE_RESOLVER_VERSION = "aoa_control_plane_route_resolver_v2"
_TOKEN_RE = re.compile(r"[\w.-]+", re.UNICODE)
_SELECTABLE_LIFECYCLE_STATES = frozenset({"active", "candidate"})
_FORBIDDEN_LIFECYCLE_STATES = frozenset(
    {"deprecated", "retired", "suspended", "disabled"}
)
_SELECTABLE_BINDING_AVAILABILITY = frozenset({"available", "external"})
_EFFECT_CEILINGS = {
    "none": frozenset({"none"}),
    "read_only": frozenset({"none", "read_only"}),
    "repo_mutation": frozenset(
        {"none", "read_only", "generated_write", "repo_write", "repo_mutation"}
    ),
    "runtime_mutation": frozenset(
        {
            "none",
            "read_only",
            "generated_write",
            "repo_write",
            "repo_mutation",
            "runtime_mutation",
        }
    ),
    "external": None,
}


@dataclass(frozen=True, slots=True)
class _ScoredCandidate:
    candidate: RouteCandidate
    score: int


@dataclass(frozen=True, slots=True)
class _RegistryInvocationPosture:
    capability_id: str
    invocation_mode: Literal["invoke", "suggest"]
    allow_implicit_invocation: bool
    candidate_only: bool
    requires_human_approval: bool


def resolve_route_intent(
    intent: RouteIntent,
    snapshot: RoutingResolutionSnapshot,
    *,
    resolver_provenance: ProvenanceRef | None = None,
) -> RouteDecision:
    """Resolve one intent against the exact canonical routing snapshot."""

    snapshot = snapshot.validated_for_resolution()
    provenance = resolver_provenance or default_resolver_provenance()
    intent_digest = canonical_digest(intent)
    blockers = _intent_blockers(intent)
    explicit_required = _constraint_values(intent.constraints, "required_capability")
    forbidden_capabilities = _constraint_values(
        intent.constraints, "forbidden_capability"
    )
    required_owners = _constraint_values(intent.constraints, "required_owner")
    forbidden_owners = _constraint_values(intent.constraints, "forbidden_owner")

    hint = snapshot.routing_hints.get("skill")
    if hint is None or not hint.enabled or not _pick_enabled(hint.actions):
        blockers.append("routing_skill_discovery_disabled")

    nodes = {node.id: node for node in snapshot.capability_graph.nodes}
    retrieval = {
        document.id: document
        for document in snapshot.capability_graph.retrieval_documents
    }
    if len(nodes) != len(snapshot.capability_graph.nodes):
        blockers.append("duplicate_capability_graph_node_ids")
    if len(retrieval) != len(snapshot.capability_graph.retrieval_documents):
        blockers.append("duplicate_capability_retrieval_document_ids")
    scored: list[_ScoredCandidate] = []
    missing_owner_projections: list[str] = []
    inconsistent_owner_projections: list[str] = []
    for entry in sorted(
        (item for item in snapshot.registry_entries if item.kind == "skill"),
        key=lambda item: (item.repo, item.id),
    ):
        invocation_posture = _registry_invocation_posture(entry)
        if invocation_posture is None:
            inconsistent_owner_projections.append(entry.id)
            continue
        node = nodes.get(invocation_posture.capability_id)
        document = retrieval.get(invocation_posture.capability_id)
        if node is None or document is None:
            missing_owner_projections.append(entry.id)
            continue
        if (
            entry.status not in _SELECTABLE_LIFECYCLE_STATES
            or entry.name != entry.id
            or entry.path != node.binding.get("ref")
            or entry.status != node.lifecycle.state
            or node.kind != "skill"
            or node.contract_level != "executable"
            or node.owner.repo != entry.repo
            or node.binding.get("kind") != "skill"
            or document.kind != "skill"
            or document.visibility != node.lifecycle.visibility
            or entry.attributes.get("capability_graph_ref")
            != snapshot.source_lock.capability_graph.relative_path
            or entry.attributes.get("capability_source_path") != node.source_path
            or entry.attributes.get("target_owner") != node.owner.repo
            or not isinstance(
                node.trust.get("requires_human_approval"),
                bool,
            )
            or node.trust.get("requires_human_approval")
            != invocation_posture.requires_human_approval
        ):
            inconsistent_owner_projections.append(entry.id)
            continue
        score, match_reasons, negative_match = _score_candidate(
            intent.objective,
            entry,
            node,
            document,
            explicitly_required=_matches_capability(entry, node, explicit_required),
        )
        compatibility, policy_posture, posture_reasons = _candidate_posture(
            intent=intent,
            entry=entry,
            node=node,
            negative_match=negative_match,
            explicitly_required=_matches_capability(entry, node, explicit_required),
            invocation_posture=invocation_posture,
            required_capabilities=explicit_required,
            forbidden_capabilities=forbidden_capabilities,
            required_owners=required_owners,
            forbidden_owners=forbidden_owners,
        )
        capability_provenance = ProvenanceRef(
            owner_repo="aoa-skills",
            artifact_ref=(
                f"{snapshot.source_lock.capability_graph.relative_path}#nodes/{node.id}"
            ),
            source_ref=snapshot.source_lock.capability_graph.source_ref,
            artifact_digest=canonical_digest(node),
            schema_ref=snapshot.source_lock.capability_graph.schema_ref,
            schema_version=snapshot.source_lock.capability_graph.schema_version,
        )
        reasons = tuple(
            dict.fromkeys(
                (
                    *match_reasons,
                    *posture_reasons,
                    f"owner_lifecycle_state:{node.lifecycle.state}",
                    f"owner_lifecycle_visibility:{node.lifecycle.visibility}",
                    f"capability_source_owner:{node.owner.repo}",
                )
            )
        )
        scored.append(
            _ScoredCandidate(
                candidate=RouteCandidate(
                    candidate_id=f"{entry.repo}:{entry.kind}:{entry.id}",
                    capability=CapabilityRef(
                        capability_id=node.id,
                        capability_kind=node.kind,
                        provenance=capability_provenance,
                    ),
                    agent=intent.requested_by,
                    scenario=intent.scenario,
                    rank=0,
                    compatibility=compatibility,
                    policy_posture=policy_posture,
                    reason_codes=reasons,
                    evidence_refs=(
                        capability_provenance,
                        snapshot.capability_graph_provenance,
                        snapshot.routing_registry_provenance,
                        snapshot.runtime_mirror_provenance,
                    ),
                ),
                score=score,
            )
        )

    if missing_owner_projections:
        blockers.append(
            "routing_candidates_missing_owner_projection:"
            + ",".join(sorted(missing_owner_projections))
        )
    if inconsistent_owner_projections:
        blockers.append(
            "routing_candidates_inconsistent_owner_projection:"
            + ",".join(sorted(inconsistent_owner_projections))
        )
    scored.sort(
        key=lambda item: (
            -item.score,
            item.candidate.capability.capability_id,
            item.candidate.candidate_id,
        )
    )
    ranked: list[_ScoredCandidate] = []
    prior_score: int | None = None
    dense_rank = -1
    for item in scored:
        if item.score != prior_score:
            dense_rank += 1
            prior_score = item.score
        ranked.append(
            _ScoredCandidate(
                candidate=item.candidate.model_copy(update={"rank": dense_rank}),
                score=item.score,
            )
        )

    eligible = [
        item
        for item in ranked
        if item.score > 0
        and item.candidate.compatibility != "incompatible"
        and item.candidate.policy_posture != "forbidden"
    ]
    selected: _ScoredCandidate | None = None
    decision_reasons = list(dict.fromkeys(blockers))
    status: Literal["resolved", "degraded", "blocked"] = "blocked"
    if blockers:
        decision_reasons.append("intent_failed_closed")
    elif not eligible:
        decision_reasons.append("no_eligible_capability")
    elif len(eligible) > 1 and eligible[0].score == eligible[1].score:
        top_ids = sorted(
            item.candidate.capability.capability_id
            for item in eligible
            if item.score == eligible[0].score
        )
        decision_reasons.append("ambiguous_top_rank:" + ",".join(top_ids))
    else:
        selected = eligible[0]
        status = (
            "degraded"
            if selected.candidate.compatibility == "degraded"
            or selected.candidate.policy_posture == "approval_required"
            else "resolved"
        )
        decision_reasons.append("selected_unique_top_rank")
        if status == "degraded":
            decision_reasons.append("selected_candidate_requires_degraded_posture")

    approval_requirements: tuple[ApprovalRequirement, ...] = ()
    if (
        selected is not None
        and selected.candidate.policy_posture == "approval_required"
    ):
        approval_requirements = (
            ApprovalRequirement(
                requirement_id=(
                    "route-approval:" + selected.candidate.capability.capability_id
                ),
                approval_owner=selected.candidate.capability.provenance,
                operation=(
                    "select_route_candidate:"
                    + selected.candidate.capability.capability_id
                ),
                risk_class="owner_declared_human_approval",
                required_evidence_refs=selected.candidate.evidence_refs,
            ),
        )

    decision_seed = {
        "resolver_version": ROUTE_RESOLVER_VERSION,
        "resolver_provenance_digest": canonical_digest(provenance),
        "intent_digest": intent_digest,
        "input_snapshot_digest": snapshot.input_snapshot_digest,
    }
    decision_id = "route-decision:" + _hex_digest(decision_seed)
    return RouteDecision(
        decision_id=decision_id,
        correlation_id=intent.correlation_id,
        intent_ref=ContentRef(
            object_id=intent.intent_id,
            owner_repo=intent.provenance.owner_repo,
            schema_version=intent.schema_version,
            digest=intent_digest,
        ),
        status=status,
        candidates=tuple(item.candidate for item in ranked),
        selected_candidate_id=(
            selected.candidate.candidate_id if selected is not None else None
        ),
        approval_requirements=approval_requirements,
        resolver_version=ROUTE_RESOLVER_VERSION,
        reason_codes=tuple(decision_reasons),
        input_snapshot_digest=snapshot.input_snapshot_digest,
        provenance=provenance,
    )


def explain_route_decision(
    decision: RouteDecision,
    *,
    resolver_provenance: ProvenanceRef | None = None,
) -> RouteExplanation:
    """Account for every candidate without inventing or replaying routing."""

    provenance = resolver_provenance or default_resolver_provenance()
    explanations: list[CandidateExplanation] = []
    for candidate in decision.candidates:
        explanations.append(
            CandidateExplanation(
                candidate_id=candidate.candidate_id,
                disposition=candidate_explanation_disposition(
                    candidate,
                    selected_candidate_id=decision.selected_candidate_id,
                ),
                reason_codes=candidate.reason_codes,
                evidence_refs=candidate.evidence_refs,
            )
        )
    decision_digest = canonical_digest(decision)
    ambiguity_codes = tuple(
        reason for reason in decision.reason_codes if reason.startswith("ambiguous_")
    )
    return RouteExplanation(
        explanation_id="route-explanation:"
        + _hex_digest(
            {
                "resolver_version": ROUTE_RESOLVER_VERSION,
                "decision_digest": decision_digest,
            }
        ),
        correlation_id=decision.correlation_id,
        decision_ref=ContentRef(
            object_id=decision.decision_id,
            owner_repo=decision.provenance.owner_repo,
            schema_version=decision.schema_version,
            digest=decision_digest,
        ),
        decision_status=decision.status,
        candidate_explanations=tuple(explanations),
        selected_candidate_id=decision.selected_candidate_id,
        fallback_used=False,
        ambiguity_codes=ambiguity_codes,
        provenance=provenance,
    )


def default_resolver_provenance() -> ProvenanceRef:
    source_file = Path(__file__).resolve()
    module_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="src/aoa_sdk/control_plane/routing/resolver.py",
        source_ref=(f"{ROUTE_RESOLVER_VERSION}@sha256:{module_digest}"),
        artifact_digest=f"sha256:{module_digest}",
        schema_ref="docs/decisions/AOA-SDK-D-0077-route-resolution-from-owner-projections.md",
        schema_version=ROUTE_RESOLVER_VERSION,
    )


def _intent_blockers(intent: RouteIntent) -> list[str]:
    blockers: list[str] = []
    kinds = tuple(dict.fromkeys(intent.requested_capability_kinds))
    if not kinds:
        blockers.append("missing_requested_capability_kind")
    unsupported_kinds = sorted(set(kinds) - {"skill"})
    if unsupported_kinds:
        blockers.append("unsupported_capability_kinds:" + ",".join(unsupported_kinds))
    required = _constraint_values(intent.constraints, "required_capability")
    if len(required) > 1:
        blockers.append(
            "conflicting_required_capability_constraints:" + ",".join(sorted(required))
        )
    required_owners = _constraint_values(intent.constraints, "required_owner")
    if len(required_owners) > 1:
        blockers.append(
            "conflicting_required_owner_constraints:"
            + ",".join(sorted(required_owners))
        )
    for kind in (
        "effect_ceiling",
        "approval_requirement",
        "compatibility_requirement",
    ):
        values = _constraint_values(intent.constraints, kind)
        if len(values) > 1:
            blockers.append(
                f"conflicting_{kind}_constraints:" + ",".join(sorted(values))
            )
    for constraint in intent.constraints:
        if constraint.kind in {
            "risk_ceiling",
            "runtime_requirement",
        }:
            blockers.append(
                f"constraint_not_resolvable_in_c1:{constraint.constraint_id}"
            )
        elif (
            constraint.kind == "effect_ceiling"
            and constraint.value not in _EFFECT_CEILINGS
        ):
            blockers.append(
                f"unsupported_effect_ceiling:{constraint.constraint_id}:{constraint.value}"
            )
        elif constraint.kind == "approval_requirement" and constraint.value not in {
            "none",
            "required",
        }:
            blockers.append(
                f"unsupported_approval_requirement:{constraint.constraint_id}:{constraint.value}"
            )
        elif (
            constraint.kind == "compatibility_requirement"
            and constraint.value not in {"compatible", "degraded_allowed"}
        ):
            blockers.append(
                "unsupported_compatibility_requirement:"
                f"{constraint.constraint_id}:{constraint.value}"
            )
    return blockers


def _candidate_posture(
    *,
    intent: RouteIntent,
    entry: RegistryEntry,
    node: CapabilityNode,
    negative_match: bool,
    explicitly_required: bool,
    invocation_posture: _RegistryInvocationPosture,
    required_capabilities: set[str],
    forbidden_capabilities: set[str],
    required_owners: set[str],
    forbidden_owners: set[str],
) -> tuple[
    Literal["compatible", "degraded", "incompatible"],
    Literal["eligible", "approval_required", "forbidden"],
    tuple[str, ...],
]:
    reasons: list[str] = []
    lifecycle_state = node.lifecycle.state.casefold()
    health = (node.lifecycle.health or "").casefold()
    compatibility: Literal["compatible", "degraded", "incompatible"]
    if health == "healthy":
        compatibility = "compatible"
    elif health == "challenger":
        compatibility = "degraded"
        reasons.append("owner_health_challenger")
    elif health == "degraded":
        compatibility = "degraded"
        reasons.append("owner_health_degraded")
    else:
        compatibility = "incompatible"
        reasons.append("owner_health_missing_or_unrecognized")
    if lifecycle_state in _FORBIDDEN_LIFECYCLE_STATES:
        compatibility = "incompatible"
        reasons.append("owner_lifecycle_not_selectable")
    elif lifecycle_state not in _SELECTABLE_LIFECYCLE_STATES:
        if compatibility != "incompatible":
            compatibility = "degraded"
        reasons.append("owner_lifecycle_unrecognized")

    policy: Literal["eligible", "approval_required", "forbidden"] = "eligible"
    availability = str(node.binding.get("availability", "")).casefold()
    if availability not in _SELECTABLE_BINDING_AVAILABILITY:
        policy = "forbidden"
        reasons.append("owner_binding_unavailable")
    if negative_match:
        policy = "forbidden"
        reasons.append("owner_negative_applicability_match")
    if required_capabilities and not explicitly_required:
        policy = "forbidden"
        reasons.append("required_capability_constraint_mismatch")
    if _matches_capability(entry, node, forbidden_capabilities):
        policy = "forbidden"
        reasons.append("forbidden_capability_constraint")
    if required_owners and node.owner.repo not in required_owners:
        policy = "forbidden"
        reasons.append("required_owner_constraint_mismatch")
    if node.owner.repo in forbidden_owners:
        policy = "forbidden"
        reasons.append("forbidden_owner_constraint")

    if not explicitly_required and (
        not invocation_posture.allow_implicit_invocation
        or invocation_posture.candidate_only
        or invocation_posture.invocation_mode == "suggest"
        or node.lifecycle.visibility.casefold() == "deferred"
    ):
        policy = "forbidden"
        reasons.append("explicit_capability_constraint_required")

    human_approval = invocation_posture.requires_human_approval
    approval_constraints = _constraint_values(
        intent.constraints, "approval_requirement"
    )
    if "none" in approval_constraints and human_approval:
        policy = "forbidden"
        reasons.append("approval_forbidden_by_intent")
    elif "required" in approval_constraints and not human_approval:
        policy = "forbidden"
        reasons.append("required_approval_not_declared_by_owner")
    elif human_approval and policy != "forbidden":
        policy = "approval_required"
        reasons.append("owner_declared_human_approval")

    effect_ceilings = _constraint_values(intent.constraints, "effect_ceiling")
    raw_effects = (
        node.execution.get("effects") if isinstance(node.execution, dict) else None
    )
    if (
        not isinstance(raw_effects, list)
        or not raw_effects
        or any(
            not isinstance(effect, str) or not _normalize_effect(effect)
            for effect in raw_effects
        )
    ):
        effects: set[str] = set()
        policy = "forbidden"
        reasons.append("owner_effect_posture_missing_or_invalid")
    else:
        effects = {_normalize_effect(effect) for effect in raw_effects}
    if effect_ceilings:
        ceiling = sorted(effect_ceilings)[0]
        allowed = _EFFECT_CEILINGS.get(ceiling)
        if allowed is not None and not effects.issubset(allowed):
            policy = "forbidden"
            reasons.append("effect_ceiling_exceeded")

    compatibility_constraints = _constraint_values(
        intent.constraints, "compatibility_requirement"
    )
    if "compatible" in compatibility_constraints and compatibility != "compatible":
        policy = "forbidden"
        reasons.append("strict_compatibility_constraint_failed")
    if not reasons:
        reasons.append("owner_projection_eligible")
    return compatibility, policy, tuple(reasons)


def _registry_invocation_posture(
    entry: RegistryEntry,
) -> _RegistryInvocationPosture | None:
    capability_id = entry.attributes.get("capability_id")
    invocation_mode = entry.attributes.get("invocation_mode")
    allow_implicit = entry.attributes.get("allow_implicit_invocation")
    candidate_only = entry.attributes.get("candidate_only")
    approval_required = entry.attributes.get("requires_human_approval")
    if (
        not isinstance(capability_id, str)
        or capability_id != f"skill.{entry.id}"
        or not isinstance(invocation_mode, str)
        or invocation_mode not in {"invoke", "suggest"}
        or not isinstance(allow_implicit, bool)
        or not isinstance(candidate_only, bool)
        or not isinstance(approval_required, bool)
    ):
        return None
    typed_invocation_mode: Literal["invoke", "suggest"] = (
        "invoke" if invocation_mode == "invoke" else "suggest"
    )
    return _RegistryInvocationPosture(
        capability_id=capability_id,
        invocation_mode=typed_invocation_mode,
        allow_implicit_invocation=allow_implicit,
        candidate_only=candidate_only,
        requires_human_approval=approval_required,
    )


def _score_candidate(
    objective: str,
    entry: RegistryEntry,
    node: CapabilityNode,
    document: CapabilityRetrievalDocument,
    *,
    explicitly_required: bool,
) -> tuple[int, tuple[str, ...], bool]:
    query = objective.casefold()
    query_token_sequence = _tokens(objective)
    query_tokens = set(query_token_sequence)
    positive = query_tokens.intersection(
        token.casefold() for token in document.positive_tokens
    )
    routing = query_tokens.intersection(
        token.casefold() for token in document.routing_tokens
    )
    general = query_tokens.intersection(token.casefold() for token in document.tokens)
    negative = query_tokens.intersection(
        token.casefold() for token in document.negative_tokens
    )
    negative_phrases = tuple(
        phrase
        for phrase in document.negative_phrases
        if _contains_token_phrase(
            query_token_sequence,
            _tokens(phrase),
        )
    )
    score = (
        len(positive) * 40
        + len(routing) * 20
        + len(general) * 5
        - len(negative) * 50
        - len(negative_phrases) * 200
    )
    exact_names = {
        entry.id.casefold(),
        entry.name.casefold(),
        node.id.casefold(),
    }
    if query.strip() in exact_names:
        score += 1000
    if explicitly_required:
        score += 2000

    reasons = [
        f"resolver_score:{score}",
        "matched_positive_tokens:" + ",".join(sorted(positive))
        if positive
        else "matched_positive_tokens:none",
        "matched_routing_tokens:" + ",".join(sorted(routing))
        if routing
        else "matched_routing_tokens:none",
        "matched_general_tokens:" + ",".join(sorted(general))
        if general
        else "matched_general_tokens:none",
    ]
    if negative:
        reasons.append("matched_negative_tokens:" + ",".join(sorted(negative)))
    if negative_phrases:
        reasons.append(
            "matched_negative_phrases:"
            + ",".join(sorted(phrase.casefold() for phrase in negative_phrases))
        )
    if explicitly_required:
        reasons.append("explicit_required_capability_match")
    return score, tuple(reasons), bool(negative_phrases)


def _constraint_values(
    constraints: tuple[RouteConstraint, ...],
    kind: str,
) -> set[str]:
    return {constraint.value for constraint in constraints if constraint.kind == kind}


def _matches_capability(
    entry: RegistryEntry,
    node: CapabilityNode,
    values: set[str],
) -> bool:
    return bool(
        {
            entry.id,
            entry.name,
            node.id,
        }.intersection(values)
    )


def _pick_enabled(actions: dict) -> bool:
    pick = actions.get("pick")
    return bool(pick is not None and pick.enabled)


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in _TOKEN_RE.findall(text))


def _contains_token_phrase(
    tokens: tuple[str, ...],
    phrase_tokens: tuple[str, ...],
) -> bool:
    if not phrase_tokens or len(phrase_tokens) > len(tokens):
        return False
    width = len(phrase_tokens)
    return any(
        tokens[index : index + width] == phrase_tokens
        for index in range(len(tokens) - width + 1)
    )


def _normalize_effect(value: str) -> str:
    return value.strip().casefold().replace("-", "_")


def _hex_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
