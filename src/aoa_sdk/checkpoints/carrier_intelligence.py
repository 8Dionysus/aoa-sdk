"""Checkpoint ecosystem carrier-candidate route evidence.

This module reads checkpoint action signatures and derives a second axis:
what carrier shape the repeated action may need. It does not install, register,
execute, or accept mechanics, tools, MCP services, hooks, or automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

from ..models import (
    ActionSignature,
    CandidateIntelligenceReport,
    CarrierCandidate,
    CarrierIntelligenceReport,
    CarrierIntelligenceSample,
    CarrierReadiness,
    ExistingCarrierFit,
    RepetitionCluster,
)
from .naming import safe_checkpoint_name

CarrierKind: TypeAlias = Literal[
    "mechanic",
    "tool",
    "mcp",
    "hook",
    "script",
    "daemon",
    "service",
    "index",
    "unknown",
]
OwnerScope: TypeAlias = Literal["center", "owner_repo", "cross_repo", "sdk_local", "unknown"]
ExecutionPosture: TypeAlias = Literal[
    "descriptive_only",
    "manual_only",
    "review_required",
    "install_blocked",
    "callable_blocked",
]
Installability: TypeAlias = Literal[
    "not_installable",
    "candidate_only",
    "review_required",
    "owner_required",
    "install_blocked",
]
ExecutionRisk: TypeAlias = Literal["low", "medium", "high", "critical"]

DEFAULT_CARRIER_STOP_LINES = (
    "no_owner_verdict",
    "no_single_event_promotion",
    "no_install_or_registration",
    "no_hidden_automation",
    "no_memory_or_proof_claim",
    "no_rag_or_graphrag_authority",
)

CENTER_REFS = {"Agents-of-Abyss", "agents-of-abyss", "aoa-center", "center"}
SDK_REFS = {"aoa-sdk"}


@dataclass(frozen=True)
class CarrierProfile:
    kind: CarrierKind
    owner_scope: OwnerScope
    execution_posture: ExecutionPosture
    installability: Installability
    execution_risk: ExecutionRisk
    route_signals: tuple[str, ...]
    blockers: tuple[str, ...]
    stop_lines: tuple[str, ...]


def build_carrier_intelligence_from_candidate_report(
    *,
    candidate_report: CandidateIntelligenceReport,
    sample_limit: int = 0,
) -> CarrierIntelligenceReport:
    clusters_by_signature = {
        cluster.signature_id: cluster for cluster in candidate_report.repetition_clusters
    }
    candidates = [
        _carrier_candidate_for_signature(
            signature=signature,
            cluster=clusters_by_signature.get(signature.signature_id),
            repo_label=candidate_report.repo_label,
        )
        for signature in candidate_report.action_signatures
    ]
    candidates = sorted(candidates, key=lambda item: item.candidate_id)
    samples = _sample_audit(candidates=candidates, limit=sample_limit)
    return CarrierIntelligenceReport(
        repo_root=candidate_report.repo_root,
        repo_label=candidate_report.repo_label,
        generated_at=candidate_report.generated_at,
        generated_at_local=candidate_report.generated_at_local,
        generated_tz=candidate_report.generated_tz,
        source=_report_source(candidate_report.source),
        carrier_candidates=candidates,
        existing_carrier_fits=[candidate.existing_carrier_fit for candidate in candidates],
        sample_audit=samples,
        source_candidate_intelligence_ref=candidate_report.report_type,
    )


def _carrier_candidate_for_signature(
    *,
    signature: ActionSignature,
    cluster: RepetitionCluster | None,
    repo_label: str,
) -> CarrierCandidate:
    profile = _profile_for_signature(signature=signature, repo_label=repo_label)
    fit = _existing_fit(signature=signature, profile=profile)
    repeat_count = cluster.repeat_count if cluster is not None else 1
    cross_session_count = cluster.cross_session_count if cluster is not None else 0
    readiness = _readiness(
        signature=signature,
        profile=profile,
        fit=fit,
        repeat_count=repeat_count,
        cross_session_count=cross_session_count,
    )
    return CarrierCandidate(
        candidate_id=(
            "carrier-candidate:"
            + safe_checkpoint_name(f"{profile.kind}:{signature.signature_id}")[:120]
        ),
        signature_id=signature.signature_id,
        carrier_kind=profile.kind,
        owner_scope=profile.owner_scope,
        source_wrapper_family=signature.wrapper_family_hint,
        action_family=signature.family,
        action=signature.action,
        object=signature.object,
        trigger=signature.trigger,
        route_signals=list(profile.route_signals),
        owner_pressure=list(signature.owner_pressure),
        cross_repo_pressure=profile.owner_scope == "cross_repo",
        execution_risk=profile.execution_risk,
        execution_posture=profile.execution_posture,
        installability=profile.installability,
        existing_carrier_fit=fit,
        carrier_readiness=readiness,
        evidence_refs=list(signature.evidence_refs),
        stop_lines=list(profile.stop_lines),
    )


def _profile_for_signature(*, signature: ActionSignature, repo_label: str) -> CarrierProfile:
    text = _signature_text(signature)
    owner_scope = _owner_scope(signature=signature, repo_label=repo_label)
    kind = _carrier_kind(signature=signature, text=text)
    if kind == "mcp":
        return CarrierProfile(
            kind=kind,
            owner_scope=owner_scope,
            execution_posture="install_blocked",
            installability="owner_required",
            execution_risk="high",
            route_signals=(
                "carrier_kind:mcp",
                "carrier_axis:external_capability_boundary",
                "execution_gate:no_mcp_registration",
            ),
            blockers=("mcp_registration_requires_owner_review",),
            stop_lines=(
                *DEFAULT_CARRIER_STOP_LINES,
                "no_mcp_registration",
                "no_service_installation",
            ),
        )
    if kind == "hook":
        return CarrierProfile(
            kind=kind,
            owner_scope=owner_scope,
            execution_posture="install_blocked",
            installability="install_blocked",
            execution_risk="high",
            route_signals=(
                "carrier_kind:hook",
                "carrier_axis:event_triggered_automation",
                "execution_gate:no_hook_installation",
            ),
            blockers=("hook_installation_requires_owner_review",),
            stop_lines=(
                *DEFAULT_CARRIER_STOP_LINES,
                "no_hook_installation",
                "no_event_trigger_activation",
            ),
        )
    if kind in {"daemon", "service"}:
        return CarrierProfile(
            kind=kind,
            owner_scope=owner_scope,
            execution_posture="install_blocked",
            installability="install_blocked",
            execution_risk="critical",
            route_signals=(
                f"carrier_kind:{kind}",
                "carrier_axis:persistent_automation",
                "execution_gate:no_daemon_service_activation",
            ),
            blockers=("persistent_automation_requires_separate_owner_decision",),
            stop_lines=(
                *DEFAULT_CARRIER_STOP_LINES,
                "no_daemon_service_activation",
                "no_timer_or_scheduler_activation",
            ),
        )
    if kind in {"tool", "script"}:
        return CarrierProfile(
            kind=kind,
            owner_scope=owner_scope,
            execution_posture="callable_blocked",
            installability="review_required",
            execution_risk="medium" if kind == "tool" else "high",
            route_signals=(
                f"carrier_kind:{kind}",
                "carrier_axis:callable_operation",
                "execution_gate:no_callable_execution",
            ),
            blockers=("callable_execution_requires_explicit_invocation",),
            stop_lines=(*DEFAULT_CARRIER_STOP_LINES, "no_callable_execution"),
        )
    if kind == "index":
        return CarrierProfile(
            kind=kind,
            owner_scope=owner_scope,
            execution_posture="descriptive_only",
            installability="not_installable",
            execution_risk="low",
            route_signals=(
                "carrier_kind:index",
                "carrier_axis:generated_navigation",
                "execution_gate:no_generated_authority",
            ),
            blockers=(),
            stop_lines=(*DEFAULT_CARRIER_STOP_LINES, "no_generated_authority"),
        )
    if kind == "mechanic":
        stop_lines: tuple[str, ...] = DEFAULT_CARRIER_STOP_LINES
        if owner_scope == "sdk_local":
            stop_lines = (*stop_lines, "no_sdk_local_as_head_pattern")
        return CarrierProfile(
            kind=kind,
            owner_scope=owner_scope,
            execution_posture="review_required",
            installability="candidate_only",
            execution_risk="medium",
            route_signals=(
                "carrier_kind:mechanic",
                "carrier_axis:route_topology_operation",
                f"owner_scope:{owner_scope}",
            ),
            blockers=() if owner_scope != "unknown" else ("owner_scope_unclear",),
            stop_lines=stop_lines,
        )
    return CarrierProfile(
        kind="unknown",
        owner_scope=owner_scope,
        execution_posture="descriptive_only",
        installability="candidate_only",
        execution_risk="medium",
        route_signals=("carrier_kind:unknown", "carrier_axis:unclassified_pressure"),
        blockers=("carrier_kind_unclear",),
        stop_lines=DEFAULT_CARRIER_STOP_LINES,
    )


def _carrier_kind(*, signature: ActionSignature, text: str) -> CarrierKind:
    if _contains_any(text, ("mcp", "access plane", "access-plane", "stdio service")):
        return "mcp"
    if _contains_any(
        text,
        (
            "hook",
            "event-triggered",
            "event triggered",
            "precompact",
            "postcompact",
            "sessionstart",
            "userpromptsubmit",
            "after_commit",
            "after-commit",
            "git hook",
            "notifications/",
        ),
    ):
        return "hook"
    if _contains_any(text, ("daemon", "timer", "scheduler", "persistent worker")):
        return "daemon"
    if _contains_any(text, ("service worker", "runtime service", "mcp service")):
        return "service"
    if _contains_any(
        text,
        (
            "generated index",
            "generated reader",
            "readiness reader",
            "navigation index",
            "graph-ready",
        ),
    ):
        return "index"
    if _contains_any(text, ("script inventory", "script home", "python script")):
        return "script"
    if _contains_any(
        text,
        (
            "tool",
            "callable",
            "publish",
            "publisher",
            "append",
            "generate",
            "builder",
            "validator",
            "scaffold",
            "execute",
            "run command",
        ),
    ):
        return "tool"
    if signature.wrapper_family_hint in {
        "playbook",
        "technique",
        "eval",
        "memo",
        "sdk_mechanic",
        "owner_local",
    }:
        return "mechanic"
    if signature.family in {"owner_routing", "wrapper_gap", "context_memory", "verification"}:
        return "mechanic"
    if _contains_any(
        text,
        (
            "mechanic",
            "route",
            "topology",
            "owner split",
            "owner route",
            "atlas",
            "card",
            "validation lane",
        ),
    ):
        return "mechanic"
    return "unknown"


def _owner_scope(*, signature: ActionSignature, repo_label: str) -> OwnerScope:
    owners = _dedupe(_normalize_owner(owner) for owner in signature.owner_pressure)
    refs = _dedupe(_owner_from_ref(ref) for ref in signature.evidence_refs + signature.inputs)
    all_owners = _dedupe([*owners, *refs])
    known_owners = [owner for owner in all_owners if owner != "unknown"]
    if any(owner in CENTER_REFS for owner in all_owners):
        return "center"
    if signature.wrapper_family_hint == "sdk_mechanic" and set(known_owners or [repo_label]) <= SDK_REFS:
        return "sdk_local"
    if len(known_owners) > 1:
        return "cross_repo"
    if any(owner.startswith("aoa-") or owner == "abyss-stack" for owner in known_owners):
        return "owner_repo"
    if repo_label in SDK_REFS and signature.wrapper_family_hint == "sdk_mechanic":
        return "sdk_local"
    return "unknown"


def _existing_fit(*, signature: ActionSignature, profile: CarrierProfile) -> ExistingCarrierFit:
    surface = _nearest_surface(signature=signature, kind=profile.kind)
    if surface is None:
        return ExistingCarrierFit(
            carrier_kind=profile.kind,
            fit_status="none",
            fit_reason="no existing carrier surface matched this action signature",
            evidence_refs=list(signature.evidence_refs),
        )
    if profile.blockers:
        fit_status: Literal["strong", "weak", "none"] = "weak"
        reason = "surface resemblance exists, but carrier gates keep this as candidate-only route evidence"
    else:
        fit_status = "strong"
        reason = "existing owner surface matches the proposed carrier shape"
    return ExistingCarrierFit(
        carrier_kind=profile.kind,
        fit_status=fit_status,
        existing_surface_ref=surface,
        nearest_existing_carrier=surface,
        fit_reason=reason,
        evidence_refs=list(signature.evidence_refs),
    )


def _readiness(
    *,
    signature: ActionSignature,
    profile: CarrierProfile,
    fit: ExistingCarrierFit,
    repeat_count: int,
    cross_session_count: int,
) -> CarrierReadiness:
    score = 0
    score += min(repeat_count, 3)
    score += min(cross_session_count, 2)
    score += 1 if profile.owner_scope != "unknown" else 0
    score += 1 if fit.fit_status != "none" else 0
    score -= 1 if profile.execution_risk in {"high", "critical"} else 0
    blockers = list(profile.blockers)
    if repeat_count < 2:
        blockers.append("single_event_cannot_promote")
    draftability: Literal["observe", "reviewable", "draftable", "blocked"] = "observe"
    if profile.execution_risk == "critical":
        draftability = "blocked"
    elif profile.kind in {"mcp", "hook", "tool", "script", "daemon", "service"}:
        draftability = "reviewable" if repeat_count >= 2 and profile.owner_scope != "unknown" else "observe"
    elif profile.kind == "mechanic" and repeat_count >= 3 and score >= 5:
        draftability = "draftable"
    elif profile.kind == "mechanic" and repeat_count >= 2 and profile.owner_scope != "unknown":
        draftability = "reviewable"
    elif profile.kind == "unknown" and blockers:
        draftability = "blocked" if repeat_count >= 2 else "observe"
    return CarrierReadiness(
        proposed_carrier_kind=profile.kind,
        owner_scope=profile.owner_scope,
        draftability=draftability,
        execution_posture=profile.execution_posture,
        installability=profile.installability,
        score=max(score, 0),
        reasons=[
            f"repeat_count={repeat_count}",
            f"cross_session_count={cross_session_count}",
            f"owner_scope={profile.owner_scope}",
            f"execution_risk={profile.execution_risk}",
            f"existing_fit={fit.fit_status}",
            f"source_wrapper_family={signature.wrapper_family_hint}",
        ],
        blockers=_dedupe(blockers),
        stop_lines=list(profile.stop_lines),
    )


def _nearest_surface(*, signature: ActionSignature, kind: CarrierKind) -> str | None:
    refs = [*signature.inputs, *signature.evidence_refs]
    keywords_by_kind: dict[CarrierKind, tuple[str, ...]] = {
        "mechanic": ("mechanics/", "OWNER_MAP.md", "PARTS.md", "ROADMAP.md"),
        "tool": ("scripts/", "tools/", "publisher", "validator", "builder"),
        "mcp": ("MCP", "mcp", "access-plane", "access plane"),
        "hook": ("hooks/", ".hooks.json", "hook"),
        "script": ("scripts/", ".py"),
        "daemon": ("daemon", "timer", "scheduler"),
        "service": ("service", "services/"),
        "index": ("generated/", "index", ".min.json"),
        "unknown": (),
    }
    keywords = keywords_by_kind.get(kind, ())
    for ref in refs:
        if any(keyword in ref for keyword in keywords):
            return ref
    return refs[0] if refs and kind != "unknown" else None


def _sample_audit(*, candidates: list[CarrierCandidate], limit: int) -> list[CarrierIntelligenceSample]:
    if limit <= 0:
        return []
    samples: list[CarrierIntelligenceSample] = []
    for candidate in candidates[:limit]:
        samples.append(
            CarrierIntelligenceSample(
                sample_id=f"sample:{safe_checkpoint_name(candidate.candidate_id)[:96]}",
                target_ref=candidate.candidate_id,
                sample_kind="carrier_candidate",
                reason=(
                    "review whether this carrier candidate should be accepted, "
                    "rejected, weakened, split, or converted into a classifier rule"
                ),
                evidence_refs=list(candidate.evidence_refs),
            )
        )
    return samples


def _signature_text(signature: ActionSignature) -> str:
    return " ".join(
        [
            signature.signature_id,
            signature.family,
            signature.action,
            signature.object,
            signature.trigger,
            signature.wrapper_family_hint,
            *signature.inputs,
            *signature.outputs,
            *signature.verification,
            *signature.failure_modes,
            *signature.stop_lines,
            *signature.owner_pressure,
            *signature.evidence_refs,
        ]
    ).lower()


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in value for needle in needles)


def _normalize_owner(value: str) -> str:
    if not value:
        return "unknown"
    if value.startswith("context:"):
        return value.removeprefix("context:")
    return value.split(":", 1)[0].split(".", 1)[0]


def _owner_from_ref(value: str) -> str:
    if not value:
        return "unknown"
    normalized = value.strip()
    if normalized.startswith("context:"):
        return normalized.removeprefix("context:")
    for center_ref in CENTER_REFS:
        if center_ref in normalized:
            return "Agents-of-Abyss"
    if normalized.startswith("aoa-"):
        return normalized.split(":", 1)[0].split(".", 1)[0].split("/", 1)[0]
    if normalized.startswith("abyss-stack") or "/abyss-stack/" in normalized:
        return "abyss-stack"
    return "unknown"


def _report_source(value: str) -> Literal["candidate_intelligence_report", "checkpoint_note", "surface_detection", "lifecycle_audit"]:
    if value in {"checkpoint_note", "surface_detection", "lifecycle_audit"}:
        return cast(
            Literal["candidate_intelligence_report", "checkpoint_note", "surface_detection", "lifecycle_audit"],
            value,
        )
    return "candidate_intelligence_report"


def _dedupe(values) -> list[str]:  # type: ignore[no-untyped-def]
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
