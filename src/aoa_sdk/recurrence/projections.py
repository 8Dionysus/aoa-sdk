from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

from .models import (
    BeaconPacket,
    ConnectivityGapReport,
    DownstreamProjectionBundle,
    DownstreamProjectionGuardReport,
    DownstreamProjectionSurface,
    KagDonorRefreshObligation,
    KagRetrievalInvalidationHint,
    KagSourceStrengthHint,
    OwnerReviewSummary,
    ProjectionGuardViolation,
    PropagationPlan,
    RecurrenceKagProjection,
    RecurrenceRoutingProjection,
    RecurrenceStatsProjection,
    ReturnHandoff,
    ReviewDecisionCloseReport,
    ReviewQueue,
    RoutingGapHint,
    RoutingOwnerHint,
    RoutingReturnHint,
    StatsRecurrenceCountBucket,
)


def _stamp(prefix: str) -> str:
    return f"{prefix}:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _workspace_root(workspace: Any) -> str:
    return str(getattr(workspace, "root", "."))


def _packet_refs(*packets: Any) -> list[str]:
    refs: list[str] = []
    for packet in packets:
        if packet is None:
            continue
        for attr in (
            "plan_ref",
            "report_ref",
            "handoff_ref",
            "packet_ref",
            "queue_ref",
            "summary_ref",
            "snapshot_ref",
            "bundle_ref",
            "projection_ref",
        ):
            value = getattr(packet, attr, None)
            if value:
                refs.append(str(value))
                break
    return sorted(set(refs))


def _counter_bucket(
    name: str,
    total: int,
    *,
    kinds: Iterable[str] = (),
    owners: Iterable[str] = (),
    statuses: Iterable[str] = (),
    severities: Iterable[str] = (),
) -> StatsRecurrenceCountBucket:
    return StatsRecurrenceCountBucket(
        name=name,
        total=total,
        by_kind=dict(Counter(kinds)),
        by_owner=dict(Counter(owners)),
        by_status=dict(Counter(statuses)),
        by_severity=dict(Counter(severities)),
    )


def build_routing_projection(
    workspace: Any,
    *,
    plan: PropagationPlan | None = None,
    gap_report: ConnectivityGapReport | None = None,
    return_handoff: ReturnHandoff | None = None,
    review_queue: ReviewQueue | None = None,
    max_hints: int = 200,
) -> RecurrenceRoutingProjection:
    """Build thin routing hints from recurrence packets.

    The projection is deliberately small: it names owners and source-facing surfaces,
    but it does not export the full recurrence graph or decide return/proof meaning.
    """

    source_packet_refs = _packet_refs(plan, gap_report, return_handoff, review_queue)
    owner_hints: list[RoutingOwnerHint] = []
    return_hints: list[RoutingReturnHint] = []
    gap_hints: list[RoutingGapHint] = []

    if plan is not None:
        seen_components: set[str] = set()
        for step in plan.ordered_steps:
            if step.component_ref in seen_components:
                continue
            seen_components.add(step.component_ref)
            surfaces = [
                ref
                for ref in step.surface_refs
                if not ref.startswith("generated/recurrence/graph")
            ]
            owner_hints.append(
                RoutingOwnerHint(
                    hint_ref=f"routing-owner-hint:{len(owner_hints) + 1:04d}",
                    owner_repo=step.owner_repo,
                    component_ref=step.component_ref,
                    reason=f"recurrence plan step requires owner-facing {step.action}",
                    inspect_surfaces=surfaces[:10],
                    source_refs=[step.step_ref, plan.plan_ref],
                )
            )
            if len(owner_hints) >= max_hints:
                break

    if review_queue is not None:
        for item in review_queue.items:
            if len(owner_hints) >= max_hints:
                break
            owner_hints.append(
                RoutingOwnerHint(
                    hint_ref=f"routing-review-owner-hint:{len(owner_hints) + 1:04d}",
                    owner_repo=item.target_repo,
                    component_ref=item.component_ref,
                    reason=f"review queue item {item.item_ref} needs owner inspection, not routing judgment",
                    inspect_surfaces=[item.decision_surface]
                    if item.decision_surface
                    else [],
                    source_refs=[
                        item.item_ref,
                        item.beacon_ref,
                        review_queue.queue_ref,
                    ],
                )
            )

    if return_handoff is not None:
        for target in return_handoff.targets:
            return_hints.append(
                RoutingReturnHint(
                    hint_ref=f"routing-return-hint:{len(return_hints) + 1:04d}",
                    owner_repo=target.owner_repo,
                    component_ref=target.component_ref,
                    target=target.target,
                    target_kind=target.target_kind,
                    reason=target.reason,
                    source_refs=[return_handoff.handoff_ref, return_handoff.plan_ref],
                )
            )
            if len(return_hints) >= max_hints:
                break

    if gap_report is not None:
        for gap in gap_report.gaps:
            gap_hints.append(
                RoutingGapHint(
                    hint_ref=f"routing-gap-hint:{len(gap_hints) + 1:04d}",
                    gap_kind=gap.gap_kind,
                    severity=gap.severity,
                    owner_repo=gap.owner_repo,
                    component_ref=gap.component_ref,
                    recommendation=gap.recommendation,
                    evidence_refs=[
                        gap.gap_ref,
                        *gap.evidence_refs,
                        gap_report.report_ref,
                    ],
                )
            )
            if len(gap_hints) >= max_hints:
                break

    return RecurrenceRoutingProjection(
        projection_ref=_stamp("recurrence-routing-projection"),
        workspace_root=_workspace_root(workspace),
        source_packet_refs=source_packet_refs,
        owner_hints=owner_hints,
        return_hints=return_hints,
        gap_hints=gap_hints,
        boundary_notes=[
            "aoa-routing receives bounded owner and return hints only.",
            "This projection must not export full recurrence graph traversal or author source meaning.",
        ],
    )


def build_stats_projection(
    workspace: Any,
    *,
    gap_report: ConnectivityGapReport | None = None,
    beacon_packet: BeaconPacket | None = None,
    review_queue: ReviewQueue | None = None,
    review_summary: OwnerReviewSummary | None = None,
    decision_report: ReviewDecisionCloseReport | None = None,
    loaded_components: list[str] | None = None,
) -> RecurrenceStatsProjection:
    source_packet_refs = _packet_refs(
        gap_report, beacon_packet, review_queue, review_summary, decision_report
    )
    gaps = list(gap_report.gaps if gap_report is not None else [])
    beacons = list(beacon_packet.entries if beacon_packet is not None else [])
    reviews = list(review_queue.items if review_queue is not None else [])
    decisions = list(
        decision_report.ledger.entries if decision_report is not None else []
    )
    coverage_count = len(loaded_components or [])
    if coverage_count == 0 and gap_report is not None:
        coverage_count = len(gap_report.components_checked)

    return RecurrenceStatsProjection(
        projection_ref=_stamp("recurrence-stats-projection"),
        workspace_root=_workspace_root(workspace),
        source_packet_refs=source_packet_refs,
        coverage=_counter_bucket(
            "component_coverage",
            coverage_count,
            owners=[
                ref.split(":")[1] if ":" in ref else ref
                for ref in (loaded_components or [])
            ],
        ),
        gaps=_counter_bucket(
            "connectivity_gaps",
            len(gaps),
            kinds=[gap.gap_kind for gap in gaps],
            owners=[gap.owner_repo or "unknown" for gap in gaps],
            severities=[gap.severity for gap in gaps],
        ),
        beacons=_counter_bucket(
            "beacon_pressure",
            len(beacons),
            kinds=[entry.kind for entry in beacons],
            owners=[entry.target_repo for entry in beacons],
            statuses=[entry.status for entry in beacons],
        ),
        review=_counter_bucket(
            "review_queue",
            len(reviews),
            kinds=[item.kind for item in reviews],
            owners=[item.target_repo for item in reviews],
            statuses=[item.status for item in reviews],
            severities=[item.priority for item in reviews],
        ),
        decisions=_counter_bucket(
            "review_decisions",
            len(decisions),
            kinds=[entry.kind for entry in decisions],
            owners=[entry.target_repo for entry in decisions],
            statuses=[entry.decision for entry in decisions],
        ),
        boundary_notes=[
            "aoa-stats receives counts, windows, and movement summaries only.",
            "This projection must not become workflow, proof, canon, or verdict authority.",
        ],
    )


def build_kag_projection(
    workspace: Any,
    *,
    plan: PropagationPlan | None = None,
    gap_report: ConnectivityGapReport | None = None,
    return_handoff: ReturnHandoff | None = None,
    beacon_packet: BeaconPacket | None = None,
    review_queue: ReviewQueue | None = None,
    max_hints: int = 200,
) -> RecurrenceKagProjection:
    source_packet_refs = _packet_refs(
        plan, gap_report, return_handoff, beacon_packet, review_queue
    )
    donor_obligations: list[KagDonorRefreshObligation] = []
    invalidation_hints: list[KagRetrievalInvalidationHint] = []
    source_strength_hints: list[KagSourceStrengthHint] = []

    if plan is not None:
        for step in plan.ordered_steps:
            if step.action != "reground" and not any(
                "kag" in ref.lower() for ref in step.surface_refs
            ):
                continue
            donor_obligations.append(
                KagDonorRefreshObligation(
                    obligation_ref=f"kag-donor-refresh:{len(donor_obligations) + 1:04d}",
                    owner_repo=step.owner_repo,
                    component_ref=step.component_ref,
                    donor_surface_refs=step.surface_refs[:10],
                    reason=f"recurrence plan step {step.step_ref} asks for KAG-facing regrounding or donor refresh",
                    mode="owner_boundary_reentry",
                )
            )
            if len(donor_obligations) >= max_hints:
                break

    if gap_report is not None:
        for gap in gap_report.gaps:
            gap_text = f"{gap.gap_kind} {gap.recommendation}".lower()
            if not any(
                token in gap_text for token in ("kag", "reground", "derived", "donor")
            ):
                continue
            invalidation_hints.append(
                KagRetrievalInvalidationHint(
                    hint_ref=f"kag-invalidation:{len(invalidation_hints) + 1:04d}",
                    affected_surface_ref=gap.component_ref or gap.gap_ref,
                    reason=gap.recommendation,
                    replacement_source_refs=[*gap.evidence_refs, gap_report.report_ref],
                    mode="projection_boundary_reentry",
                )
            )
            if len(invalidation_hints) >= max_hints:
                break

    if return_handoff is not None:
        for target in return_handoff.targets:
            source_strength_hints.append(
                KagSourceStrengthHint(
                    hint_ref=f"kag-source-strength:{len(source_strength_hints) + 1:04d}",
                    owner_repo=target.owner_repo,
                    stronger_source_refs=[target.target],
                    weaker_derived_refs=[return_handoff.handoff_ref],
                    reason=target.reason,
                    mode="source_export_reentry"
                    if target.target_kind in {"source", "contract", "docs"}
                    else "owner_boundary_reentry",
                )
            )
            if len(source_strength_hints) >= max_hints:
                break

    if beacon_packet is not None:
        for entry in beacon_packet.entries:
            if entry.kind not in {
                "overclaim_alarm",
                "portable_eval_candidate",
                "canonical_pressure",
            }:
                continue
            source_strength_hints.append(
                KagSourceStrengthHint(
                    hint_ref=f"kag-beacon-strength:{len(source_strength_hints) + 1:04d}",
                    owner_repo=entry.target_repo,
                    stronger_source_refs=entry.source_inputs[:10],
                    weaker_derived_refs=[entry.beacon_ref],
                    reason=f"beacon {entry.kind} should reground derived consumers toward owner surfaces",
                    mode="handoff_guardrail_reentry"
                    if entry.kind == "overclaim_alarm"
                    else "owner_boundary_reentry",
                )
            )
            if len(source_strength_hints) >= max_hints:
                break

    modes = sorted(
        {item.mode for item in donor_obligations}
        | {item.mode for item in invalidation_hints}
        | {item.mode for item in source_strength_hints}
    )
    return RecurrenceKagProjection(
        projection_ref=_stamp("recurrence-kag-projection"),
        workspace_root=_workspace_root(workspace),
        source_packet_refs=source_packet_refs,
        donor_refresh_obligations=donor_obligations,
        retrieval_invalidation_hints=invalidation_hints,
        source_strength_hints=source_strength_hints,
        regrounding_modes=modes,
        boundary_notes=[
            "aoa-kag receives regrounding and donor-refresh obligations only.",
            "This projection must not become source truth, proof authority, routing policy, or graph sovereignty.",
        ],
    )


def build_projection_guard_report(
    workspace: Any,
    *,
    routing: RecurrenceRoutingProjection | None = None,
    stats: RecurrenceStatsProjection | None = None,
    kag: RecurrenceKagProjection | None = None,
) -> DownstreamProjectionGuardReport:
    refs = _packet_refs(routing, stats, kag)
    violations: list[ProjectionGuardViolation] = []

    if routing is not None:
        for hint in [*routing.owner_hints, *routing.return_hints, *routing.gap_hints]:
            evidence = list(
                getattr(hint, "source_refs", getattr(hint, "evidence_refs", []))
            )
            if any(
                ref.startswith("generated/recurrence/graph") or "graph_snapshot" in ref
                for ref in evidence
            ):
                violations.append(
                    ProjectionGuardViolation(
                        violation_ref=f"projection-guard:routing-full-graph:{len(violations) + 1:04d}",
                        target_repo="aoa-routing",
                        kind="routing_full_graph_export",
                        severity="blocked",
                        message="Routing projection attempted to carry full recurrence graph evidence.",
                        evidence_refs=evidence,
                        recommended_action="Replace full graph evidence with owner surface refs or a bounded return hint.",
                    )
                )
            if getattr(hint, "advisory_only", True) is not True:
                violations.append(
                    ProjectionGuardViolation(
                        violation_ref=f"projection-guard:routing-authority:{len(violations) + 1:04d}",
                        target_repo="aoa-routing",
                        kind="routing_authority_transfer",
                        severity="critical",
                        message="Routing hint is not marked advisory_only=true.",
                        evidence_refs=evidence,
                        recommended_action="Keep recurrence routing outputs advisory and source-referring.",
                    )
                )

    if stats is not None:
        joined_notes = " ".join(stats.boundary_notes).lower()
        if (
            "verdict authority" in joined_notes or "canon authority" in joined_notes
        ) and "must not" not in joined_notes:
            violations.append(
                ProjectionGuardViolation(
                    violation_ref=f"projection-guard:stats-authority:{len(violations) + 1:04d}",
                    target_repo="aoa-stats",
                    kind="stats_verdict_transfer",
                    severity="critical",
                    message="Stats projection boundary text suggests verdict or canon authority.",
                    evidence_refs=stats.source_packet_refs,
                    recommended_action="Rewrite stats output as derived observability only.",
                )
            )
        if stats.surface_strength != "derived_observability_only":
            violations.append(
                ProjectionGuardViolation(
                    violation_ref=f"projection-guard:stats-strength:{len(violations) + 1:04d}",
                    target_repo="aoa-stats",
                    kind="stats_source_truth_claim",
                    severity="blocked",
                    message="Stats projection surface_strength must remain derived_observability_only.",
                    evidence_refs=stats.source_packet_refs,
                    recommended_action="Restore derived-only posture before publishing stats projection.",
                )
            )

    if kag is not None:
        joined_notes = " ".join(kag.boundary_notes).lower()
        if (
            "source truth authority" in joined_notes
            or "canon authority" in joined_notes
        ):
            violations.append(
                ProjectionGuardViolation(
                    violation_ref=f"projection-guard:kag-authority:{len(violations) + 1:04d}",
                    target_repo="aoa-kag",
                    kind="kag_canon_transfer",
                    severity="critical",
                    message="KAG projection boundary text risks canon/source authority transfer.",
                    evidence_refs=kag.source_packet_refs,
                    recommended_action="Keep KAG projection in regrounding-only posture.",
                )
            )

    return DownstreamProjectionGuardReport(
        report_ref=_stamp("downstream-projection-guard"),
        workspace_root=_workspace_root(workspace),
        source_packet_refs=refs,
        violations=violations,
        boundary_notes=[
            "Projection guards check downstream posture, not owner semantic correctness.",
            "Blocked or critical violations should stop publication of generated downstream projections.",
        ],
    )


def build_downstream_projection_bundle(
    workspace: Any,
    *,
    plan: PropagationPlan | None = None,
    gap_report: ConnectivityGapReport | None = None,
    return_handoff: ReturnHandoff | None = None,
    beacon_packet: BeaconPacket | None = None,
    review_queue: ReviewQueue | None = None,
    review_summary: OwnerReviewSummary | None = None,
    decision_report: ReviewDecisionCloseReport | None = None,
    loaded_components: list[str] | None = None,
    include_routing: bool = True,
    include_stats: bool = True,
    include_kag: bool = True,
) -> DownstreamProjectionBundle:
    routing = (
        build_routing_projection(
            workspace,
            plan=plan,
            gap_report=gap_report,
            return_handoff=return_handoff,
            review_queue=review_queue,
        )
        if include_routing
        else None
    )
    stats = (
        build_stats_projection(
            workspace,
            gap_report=gap_report,
            beacon_packet=beacon_packet,
            review_queue=review_queue,
            review_summary=review_summary,
            decision_report=decision_report,
            loaded_components=loaded_components,
        )
        if include_stats
        else None
    )
    kag = (
        build_kag_projection(
            workspace,
            plan=plan,
            gap_report=gap_report,
            return_handoff=return_handoff,
            beacon_packet=beacon_packet,
            review_queue=review_queue,
        )
        if include_kag
        else None
    )
    guard_report = build_projection_guard_report(
        workspace, routing=routing, stats=stats, kag=kag
    )
    refs = _packet_refs(
        plan,
        gap_report,
        return_handoff,
        beacon_packet,
        review_queue,
        review_summary,
        decision_report,
    )

    surfaces: list[DownstreamProjectionSurface] = []
    if routing is not None:
        surfaces.extend(
            [
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-routing:recurrence-owner-hints",
                    target_repo="aoa-routing",
                    path="generated/recurrence_owner_hints.min.json",
                    posture="hint_only",
                    source_packet_refs=routing.source_packet_refs,
                ),
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-routing:recurrence-return-hints",
                    target_repo="aoa-routing",
                    path="generated/recurrence_return_hints.min.json",
                    posture="hint_only",
                    source_packet_refs=routing.source_packet_refs,
                ),
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-routing:recurrence-gap-hints",
                    target_repo="aoa-routing",
                    path="generated/recurrence_gap_hints.min.json",
                    posture="hint_only",
                    source_packet_refs=routing.source_packet_refs,
                ),
            ]
        )
    if stats is not None:
        surfaces.extend(
            [
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-stats:recurrence-coverage-summary",
                    target_repo="aoa-stats",
                    path="generated/recurrence_coverage_summary.min.json",
                    posture="derived_summary_only",
                    source_packet_refs=stats.source_packet_refs,
                ),
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-stats:recurrence-pressure-summary",
                    target_repo="aoa-stats",
                    path="generated/recurrence_pressure_summary.min.json",
                    posture="derived_summary_only",
                    source_packet_refs=stats.source_packet_refs,
                ),
            ]
        )
    if kag is not None:
        surfaces.extend(
            [
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-kag:recurrence-regrounding-pack",
                    target_repo="aoa-kag",
                    path="generated/recurrence_regrounding_pack.min.json",
                    posture="regrounding_only",
                    source_packet_refs=kag.source_packet_refs,
                ),
                DownstreamProjectionSurface(
                    surface_ref="surface:aoa-kag:donor-refresh-obligations",
                    target_repo="aoa-kag",
                    path="generated/donor_refresh_obligations.min.json",
                    posture="regrounding_only",
                    source_packet_refs=kag.source_packet_refs,
                ),
            ]
        )

    return DownstreamProjectionBundle(
        bundle_ref=_stamp("downstream-projection-bundle"),
        workspace_root=_workspace_root(workspace),
        source_packet_refs=refs,
        surfaces=surfaces,
        routing=routing,
        stats=stats,
        kag=kag,
        guard_report=guard_report,
        boundary_notes=[
            "Downstream projections are narrow projections, not recurrence authority transfer.",
            "Owner repos still own meaning; downstream repos receive only the subset they are allowed to consume.",
        ],
    )
