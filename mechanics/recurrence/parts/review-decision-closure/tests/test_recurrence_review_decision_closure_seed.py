from __future__ import annotations

from aoa_sdk.recurrence.decisions import (
    build_review_decision_ledger,
    build_owner_review_decision_template,
    close_review_decisions,
)
from aoa_sdk.recurrence.models import ReviewQueue, ReviewQueueItem


def _queue() -> ReviewQueue:
    return ReviewQueue(
        queue_ref="review-queue:test",
        workspace_root="/tmp/workspace",
        signal_ref="signal:test",
        items=[
            ReviewQueueItem(
                item_ref="review-item:0001",
                lane="technique",
                priority="medium",
                target_repo="aoa-techniques",
                owner_repo="aoa-techniques",
                component_ref="component:techniques:canon-and-intake-beacons",
                beacon_ref="technique.canonical.second_consumer_pressure",
                kind="canonical_pressure",
                status="watch",
                decision_surface="docs/PROMOTION_READINESS_MATRIX.md",
                summary="A second consumer appeared but promotion remains owner-reviewed.",
                evidence_refs=["receipt:001"],
                source_inputs=["technique-live-receipts"],
                recommended_actions=["refresh promotion-readiness evidence"],
            ),
            ReviewQueueItem(
                item_ref="review-item:0002",
                lane="eval",
                priority="critical",
                target_repo="aoa-evals",
                owner_repo="aoa-evals",
                component_ref="component:evals:portable-proof-beacons",
                beacon_ref="evals.overclaim.runtime_claim",
                kind="overclaim_alarm",
                status="review_ready",
                decision_surface="docs/RUNTIME_BENCH_PROMOTION_GUIDE.md",
                summary="Runtime evidence was being read too broadly.",
                evidence_refs=["runtime:bench:001"],
                source_inputs=["runtime evidence selection"],
                recommended_actions=["tighten claim boundary"],
            ),
        ],
    )


def test_decision_template_carries_owner_boundaries_without_minting_owner_refs() -> (
    None
):
    decision = build_owner_review_decision_template(
        _queue(),
        item_ref="review-item:0001",
        decision="defer",
        reviewer="aoa-techniques-review",
        cluster_ref="cluster:techniques:second-consumer:001",
    )

    assert decision.owner_repo == "aoa-techniques"
    assert decision.input_beacon_refs == ["technique.canonical.second_consumer_pressure"]
    assert decision.lineage_bridge is not None
    assert decision.lineage_bridge.cluster_ref == "cluster:techniques:second-consumer:001"
    assert decision.lineage_bridge.owner_assigned_ref is None
    assert "sdk_does_not_mint_owner_candidate_seed_or_object_ref" in decision.forbidden_implications
    assert any("technique" in boundary for boundary in decision.boundaries_preserved)


def test_decision_template_preserves_source_owner_when_target_differs() -> None:
    queue = ReviewQueue(
        queue_ref="review-queue:cross-owner",
        workspace_root="/tmp/workspace",
        items=[
            ReviewQueueItem(
                item_ref="review-item:cross-owner",
                lane="technique",
                priority="medium",
                target_repo="aoa-routing",
                owner_repo="aoa-techniques",
                component_ref="component:techniques:intake",
                beacon_ref="techniques.intake.routing_pressure",
                kind="canonical_pressure",
                status="watch",
                decision_surface="docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
                summary="Routing pressure points back to technique ownership.",
            )
        ],
    )
    decision = build_owner_review_decision_template(
        queue,
        item_ref="review-item:cross-owner",
        decision="defer",
    )
    ledger = build_review_decision_ledger(
        workspace_root="/tmp/workspace",
        decisions=[decision],
        source_queue_ref=queue.queue_ref,
    )

    assert decision.owner_repo == "aoa-techniques"
    assert decision.target_repo == "aoa-routing"
    assert ledger.by_owner == {"aoa-techniques": 1}


def test_explicit_skill_drift_routes_to_owner_review_without_activation_claim() -> None:
    queue = ReviewQueue(
        queue_ref="review-queue:owner-authored-skill-evidence",
        workspace_root="/tmp/workspace",
        items=[
            ReviewQueueItem(
                item_ref="review-item:owner-authored-skill-drift",
                lane="skill",
                priority="medium",
                target_repo="example-skill-owner",
                owner_repo="example-skill-owner",
                component_ref="component:example:owner-authored-skill-evidence",
                beacon_ref="skills.owner_authored.applicability_drift",
                kind="skill_trigger_drift",
                status="watch",
                decision_surface="skills/example/SKILL.md",
                summary="Owner comparison found an applicability-boundary candidate.",
                evidence_refs=["session-evidence:reviewed-case-002"],
            )
        ],
    )

    decision = build_owner_review_decision_template(
        queue,
        item_ref="review-item:owner-authored-skill-drift",
        decision="defer",
    )

    assert decision.lineage_bridge is not None
    assert (
        decision.lineage_bridge.owner_shape
        == "skill_applicability_and_routing_review_decision"
    )
    assert any("do not prove invocation" in item for item in decision.boundaries_preserved)


def test_close_report_records_suppression_and_unresolved_items() -> None:
    queue = _queue()
    decision = build_owner_review_decision_template(
        queue,
        beacon_ref="technique.canonical.second_consumer_pressure",
        decision="suppress",
        rationale="The same consumer was counted twice in this context.",
    )
    report = close_review_decisions(
        workspace_root="/tmp/workspace",
        queue=queue,
        decisions=[decision],
    )

    assert report.closed_item_refs == ["review-item:0001"]
    assert report.unresolved_item_refs == ["review-item:0002"]
    assert report.suppressed_beacon_refs == ["technique.canonical.second_consumer_pressure"]
    assert report.ledger.by_decision == {"suppress": 1}
    assert report.suppression_memory.rules[0].scope == "beacon"
    assert not report.warnings


def test_close_report_warns_when_decision_points_at_a_different_queue() -> None:
    queue = _queue()
    decision = build_owner_review_decision_template(
        queue, item_ref="review-item:0002", decision="accept"
    )
    decision.queue_ref = "review-queue:other"
    report = close_review_decisions(
        workspace_root="/tmp/workspace", queue=queue, decisions=[decision]
    )

    assert report.closed_item_refs == ["review-item:0002"]
    assert report.warnings
