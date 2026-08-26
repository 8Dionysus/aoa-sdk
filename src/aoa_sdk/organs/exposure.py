"""Deterministic, candidate-only progressive exposure compilation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal, cast

from ..contracts.organ_exposure import (
    BASELINE_EVIDENCE_OWNER,
    BASELINE_EVIDENCE_REF,
    BASELINE_EVIDENCE_REVISION_PREFIX,
    ExposureAuthorizationCandidate,
    ExposureCapabilityBinding,
    ExposureFreshnessState,
    ExposureSelectionRequest,
    ExposureFreshness,
    ProgressiveExposurePlan,
    RenderedExposureSnapshot,
    VisibleTool,
    exposure_digest,
    exposure_tool_from_primitive,
)
from ..contracts.organs import (
    POLICY_RANK,
    CapabilityContract,
    FreshnessState,
    OrganProjectionEntry,
    OrganRegistryProjection,
    QualifiedEvidenceRef,
)
from .registry import OrganRegistryError


def _map_freshness(state: FreshnessState) -> ExposureFreshnessState:
    return cast(
        ExposureFreshnessState,
        {
            "exact": "fresh",
            "compatible_drift": "provider_reported",
            "stale_readable": "stale",
            "blocked": "unknown",
            "unknown": "unknown",
            "rollback_required": "expired",
        }[state],
    )


def _snapshot(
    *,
    source_digest: str,
    tools: tuple[VisibleTool, ...],
    observed_at: datetime,
    expires_at: datetime,
) -> RenderedExposureSnapshot:
    serialized_tools = [tool.model_dump(mode="json") for tool in tools]
    rendered_bytes = len(
        json.dumps(
            serialized_tools,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    if tools:
        rendered_tokens = max(1, (rendered_bytes + 3) // 4)
        token_count_posture = "estimated"
        token_count_method = "utf8_bytes_per_4_v1"
    else:
        rendered_tokens = None
        token_count_posture = "unknown"
        token_count_method = None
    unsigned = {
        "schema_version": "aoa_organ_exposure_snapshot_v1",
        "source_digest": source_digest,
        "tools": serialized_tools,
        "visible_tool_ids": [tool.tool_id for tool in tools],
        "rendered_schema_digest": exposure_digest(serialized_tools),
        "rendered_bytes": rendered_bytes,
        "rendered_tokens": rendered_tokens,
        "token_count_posture": token_count_posture,
        "token_count_method": token_count_method,
        "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "refusal_reasons": [],
    }
    return RenderedExposureSnapshot.model_validate(
        {"snapshot_id": exposure_digest(unsigned), **unsigned}
    )


def _capability_binding(
    projection: OrganRegistryProjection,
    entry: OrganProjectionEntry,
    capability: CapabilityContract,
) -> ExposureCapabilityBinding:
    evidence = entry.freshness_evidence
    observed_at = evidence.observed_at if evidence is not None else projection.compiled_at
    expires_at = (
        evidence.expires_at
        if evidence is not None and evidence.expires_at is not None
        else projection.expires_at
    )
    ttl_seconds = max(0, int((expires_at - observed_at).total_seconds()))
    state = _map_freshness(entry.freshness_state)
    reason_codes = () if state == "fresh" else (f"freshness_{state}",)
    if entry.endpoint is None or entry.endpoint.server_schema_digest is None:
        raise OrganRegistryError(
            "exposure requires an owner-authored server schema digest"
        )
    server_schema_digest = entry.endpoint.server_schema_digest
    return ExposureCapabilityBinding(
        organ_id=entry.organ_id,
        capability_id=capability.capability_id,
        qualified_capability_id=(
            f"{entry.owners.source_owner}:{entry.organ_id}:{capability.capability_id}"
        ),
        owners=entry.owners,
        capability_digest=exposure_digest(capability.model_dump(mode="json")),
        schema_digest=server_schema_digest,
        source_revision=entry.revisions.source,
        freshness=ExposureFreshness(
            state=state,
            source_ref=(
                evidence.evidence_ref
                if evidence is not None
                else f"aoa-sdk://organ-registry/{projection.registry_id}"
            ),
            source_digest=projection.source_digest,
            observed_at=observed_at,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds,
            provider_watermark=evidence.revision if evidence is not None else None,
            reason_codes=reason_codes,
        ),
        effect_ceiling=capability.policy_family,
        rollback_route=entry.rollback_route,
    )


def _baseline_evidence_is_valid(
    evidence: QualifiedEvidenceRef,
    *,
    evaluated_at: datetime,
) -> bool:
    """Accept only the canonical d0 baseline-ready evidence identity."""

    return (
        evidence.owner == BASELINE_EVIDENCE_OWNER
        and evidence.evidence_ref == BASELINE_EVIDENCE_REF
        and evidence.revision.startswith(BASELINE_EVIDENCE_REVISION_PREFIX)
        and evidence.expires_at is not None
        and evidence.expires_at > evaluated_at
    )


def _approval_rejection_reason(
    primitive,
    approval_ref: QualifiedEvidenceRef | None,
    *,
    evaluated_at: datetime,
) -> str | None:
    if not primitive.approval_required:
        return None
    if approval_ref is None:
        return "selected_tool_requires_approval"
    if approval_ref.owner != primitive.approval_owner:
        return "approval_owner_mismatch"
    if approval_ref.observed_at > evaluated_at:
        return "approval_evidence_from_future"
    if approval_ref.expires_at is None:
        return "approval_expiry_missing"
    if approval_ref.expires_at <= evaluated_at:
        return "approval_expired"
    return None


def compile_progressive_exposure(
    projection: OrganRegistryProjection,
    request: ExposureSelectionRequest,
    *,
    feature_enabled: bool,
    evaluated_at: datetime,
) -> ProgressiveExposurePlan:
    """Compile a deterministic disclosure candidate without activating it."""

    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise OrganRegistryError("exposure evaluation time must be timezone-aware")
    evaluated_at = evaluated_at.astimezone(timezone.utc)
    if request.requested_at > evaluated_at:
        raise OrganRegistryError("exposure request is from the future")
    if request.expires_at <= evaluated_at:
        raise OrganRegistryError("exposure request is expired")
    if request.expires_at > projection.expires_at:
        raise OrganRegistryError("exposure request outlives registry projection")
    entry = next(
        (item for item in projection.entries if item.organ_id == request.organ_id),
        None,
    )
    if entry is None or not entry.discoverable:
        raise OrganRegistryError(f"organ {request.organ_id!r} is not discoverable")
    capability = next(
        (item for item in entry.capabilities if item.capability_id == request.capability_id),
        None,
    )
    if capability is None:
        raise OrganRegistryError(
            f"unknown capability {request.capability_id!r} for organ {request.organ_id!r}"
        )
    if POLICY_RANK[request.requested_policy_family] > POLICY_RANK[capability.policy_family]:
        raise OrganRegistryError("requested exposure policy exceeds capability ceiling")
    binding = _capability_binding(
        projection,
        entry,
        capability,
    )
    freshness_expiry = binding.freshness.expires_at
    if freshness_expiry is None:
        raise OrganRegistryError("exposure freshness has no usable expiry")
    plan_expiry = min(request.expires_at, projection.expires_at, freshness_expiry)
    if request.baseline_ready:
        assert request.baseline_evidence is not None
        if not _baseline_evidence_is_valid(
            request.baseline_evidence,
            evaluated_at=evaluated_at,
        ):
            raise OrganRegistryError(
                "baseline evidence is not the canonical d0 baseline-ready receipt"
            )
        if request.baseline_evidence.observed_at > request.requested_at:
            raise OrganRegistryError("baseline evidence is from the future")
        if (
            request.baseline_evidence.expires_at is not None
            and request.baseline_evidence.expires_at <= evaluated_at
        ):
            raise OrganRegistryError("baseline evidence is expired")
        if request.baseline_evidence.expires_at is not None:
            plan_expiry = min(plan_expiry, request.baseline_evidence.expires_at)

    primitives = {item.primitive_id: item for item in capability.primitives}
    refusal_reasons: list[str] = []
    if not feature_enabled:
        refusal_reasons.append("progressive_exposure_disabled")
    if not request.baseline_ready:
        refusal_reasons.append("baseline_not_ready")
    if not request.reveal_schemas:
        refusal_reasons.append("schema_reveal_not_requested")
    if not request.selected_primitive_ids:
        refusal_reasons.append("explicit_tool_selection_required")
    if binding.freshness.state not in {"fresh", "provider_reported"}:
        refusal_reasons.append("capability_freshness_not_usable")

    selected: list[VisibleTool] = []
    for primitive_id in request.selected_primitive_ids:
        primitive = primitives.get(primitive_id)
        if primitive is None:
            refusal_reasons.append("unknown_selected_primitive")
            continue
        if primitive.kind != "tool":
            refusal_reasons.append("selected_primitive_is_not_a_tool")
            continue
        if POLICY_RANK[primitive.policy_family] > POLICY_RANK[request.requested_policy_family]:
            refusal_reasons.append("selected_tool_exceeds_requested_policy")
            continue
        approval_reason = _approval_rejection_reason(
            primitive,
            request.approval_ref,
            evaluated_at=evaluated_at,
        )
        if approval_reason is not None:
            refusal_reasons.append(approval_reason)
            continue
        selected.append(
            exposure_tool_from_primitive(
                capability,
                primitive,
                schema_digest=binding.schema_digest,
            )
        )

    can_reveal = not refusal_reasons
    tools = tuple(selected) if can_reveal else ()
    snapshot = _snapshot(
        source_digest=projection.source_digest,
        tools=tools,
        observed_at=evaluated_at,
        expires_at=plan_expiry,
    )
    plan_state: Literal["blocked", "candidate"] = (
        "candidate" if can_reveal else "blocked"
    )
    expansion_reasons = (
        (
            "baseline_gate_satisfied",
            "progressive_exposure_explicitly_enabled",
            "explicit_schema_reveal",
            "ordered_tool_selection",
            "visibility_budget_recorded",
        )
        if can_reveal
        else ()
    )
    unsigned = {
        "schema_version": "aoa_organ_exposure_plan_v1",
        "plan_state": plan_state,
        "execution_authorized": False,
        "activation_authorized": False,
        "feature_enabled": feature_enabled,
        "baseline_ready": request.baseline_ready,
        "request_id": request.request_id,
        "capability": binding.model_dump(mode="json"),
        "requested_policy_family": request.requested_policy_family,
        "requested_primitive_ids": list(request.selected_primitive_ids),
        "visible_tools": [tool.model_dump(mode="json") for tool in tools],
        "rendered_snapshot": snapshot.model_dump(mode="json"),
        "approval_ref": (
            request.approval_ref.model_dump(mode="json")
            if request.approval_ref is not None
            else None
        ),
        "rollback_route": binding.rollback_route,
        "requested_at": request.requested_at.isoformat().replace("+00:00", "Z"),
        "expires_at": plan_expiry.isoformat().replace("+00:00", "Z"),
        "expansion_reasons": list(expansion_reasons),
        "refusal_reasons": sorted(set(refusal_reasons)),
    }
    return ProgressiveExposurePlan.model_validate(
        {"plan_id": exposure_digest(unsigned), **unsigned}
    )


def prepare_exposure_authorization(
    plan: ProgressiveExposurePlan,
    *,
    approval_ref: QualifiedEvidenceRef | None = None,
) -> ExposureAuthorizationCandidate:
    """Return an external-owner handoff; this function never authorizes execution."""

    if plan.plan_state == "blocked":
        reasons = tuple(plan.refusal_reasons)
        state: Literal["blocked", "external_owner_required"] = "blocked"
    else:
        reasons = ("runtime_owner_activation_authorization_required",)
        state = "external_owner_required"
    return ExposureAuthorizationCandidate(
        plan_id=plan.plan_id,
        request_id=plan.request_id,
        authorization_state=state,
        rendered_snapshot_id=plan.rendered_snapshot.snapshot_id,
        visible_tool_ids=plan.rendered_snapshot.visible_tool_ids,
        visible_bytes=plan.rendered_snapshot.rendered_bytes,
        visible_tokens=plan.rendered_snapshot.rendered_tokens,
        reason_codes=reasons,
        approval_ref=approval_ref or plan.approval_ref,
        rollback_route=plan.rollback_route,
    )
