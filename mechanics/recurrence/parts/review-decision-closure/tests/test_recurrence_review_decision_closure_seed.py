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
                lane="skill",
                priority="medium",
                target_repo="aoa-skills",
                owner_repo="aoa-skills",
                component_ref="component:skills:bundle-and-activation-beacons",
                beacon_ref="skills.unused_skill.activation_gap",
                kind="unused_skill_opportunity",
                status="watch",
                decision_surface="docs/ADAPTIVE_SKILL_ORCHESTRATION.md",
                summary="Skill looked applicable but stayed unused.",
                evidence_refs=["receipt:001"],
                source_inputs=["generated/description_trigger_eval_cases.jsonl"],
                recommended_actions=["inspect trigger boundary"],
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
        reviewer="aoa-skills-review",
        cluster_ref="cluster:skills:unused:001",
    )

    assert decision.owner_repo == "aoa-skills"
    assert decision.input_beacon_refs == ["skills.unused_skill.activation_gap"]
    assert decision.lineage_bridge is not None
    assert decision.lineage_bridge.cluster_ref == "cluster:skills:unused:001"
    assert decision.lineage_bridge.owner_assigned_ref is None
    assert "sdk_does_not_accept_skill" in decision.forbidden_implications
    assert any("trigger" in boundary for boundary in decision.boundaries_preserved)


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


def test_close_report_records_suppression_and_unresolved_items() -> None:
    queue = _queue()
    decision = build_owner_review_decision_template(
        queue,
        beacon_ref="skills.unused_skill.activation_gap",
        decision="suppress",
        rationale="Noisy because this skill is explicit-only in this context.",
    )
    report = close_review_decisions(
        workspace_root="/tmp/workspace",
        queue=queue,
        decisions=[decision],
    )

    assert report.closed_item_refs == ["review-item:0001"]
    assert report.unresolved_item_refs == ["review-item:0002"]
    assert report.suppressed_beacon_refs == ["skills.unused_skill.activation_gap"]
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
