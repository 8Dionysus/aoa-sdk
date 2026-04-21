from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import (
    OwnerReviewDecision,
    ReviewDecisionAction,
    ReviewDecisionCloseReport,
    ReviewDecisionLedger,
    ReviewDecisionLedgerEntry,
    ReviewDecisionLineageBridge,
    ReviewDecisionSuppressionRule,
    ReviewQueue,
    ReviewQueueItem,
    ReviewSuppressionMemory,
)

DEFAULT_FORBIDDEN_IMPLICATIONS = [
    "sdk_does_not_promote_canon",
    "sdk_does_not_accept_skill",
    "sdk_does_not_approve_eval",
    "sdk_does_not_widen_playbook",
    "sdk_does_not_mint_owner_candidate_seed_or_object_ref",
]

LANE_BOUNDARIES = {
    "technique": [
        "technique status changes stay in aoa-techniques owner review",
        "overlap holds remain visible until separability is reviewed",
        "second-consumer pressure is evidence, not auto-canonical promotion",
    ],
    "skill": [
        "skill activation boundaries stay in authored skill surfaces",
        "trigger eval changes remain owner-reviewed",
        "omission signals distinguish genuine misses from explicit restraint",
    ],
    "eval": [
        "runtime evidence remains bounded sidecar until eval ownership gives it proof meaning",
        "claim wording and verdict semantics stay in aoa-evals",
        "overclaim alarms tighten interpretation rather than rank models",
    ],
    "playbook": [
        "scenario composition changes require explicit gate review",
        "subagent recipes stay helpers and not automatic spawning logic",
        "automation seeds remain examples until owner review accepts a live route",
    ],
    "general": [
        "review decisions close recurrence pressure without claiming unrelated owner truth",
    ],
}

DECISION_FOLLOWTHROUGH_HINTS = {
    "accept": "Record the accepted owner followthrough surface and leave the owner repo to mint any candidate or object refs.",
    "reject": "Record the bounded reason and consider a suppression rule if the same noisy pressure should stay quiet.",
    "defer": "Record the missing evidence and next review condition.",
    "reanchor": "Point to the better owner surface without claiming the unit has landed there.",
    "split": "Name the separable sub-pressures and keep each future owner candidate bounded.",
    "merge": "Name the existing owner surface that absorbs this pressure.",
    "suppress": "Write a narrow suppression rule with an expiry or scope limit.",
}


def find_queue_item(
    queue: ReviewQueue,
    *,
    item_ref: str | None = None,
    beacon_ref: str | None = None,
) -> ReviewQueueItem:
    if item_ref is None and beacon_ref is None:
        raise ValueError("Pass either item_ref or beacon_ref.")
    matches: list[ReviewQueueItem] = []
    for item in queue.items:
        if item_ref is not None and item.item_ref == item_ref:
            matches.append(item)
        elif beacon_ref is not None and item.beacon_ref == beacon_ref:
            matches.append(item)
    if not matches:
        needle = item_ref or beacon_ref
        raise ValueError(f"Review queue item not found: {needle}")
    if len(matches) > 1:
        refs = ", ".join(item.item_ref for item in matches)
        raise ValueError(f"Ambiguous review queue match for {beacon_ref!r}: {refs}")
    return matches[0]


def build_owner_review_decision_template(
    queue: ReviewQueue,
    *,
    item_ref: str | None = None,
    beacon_ref: str | None = None,
    decision: ReviewDecisionAction = "defer",
    reviewer: str = "owner-review",
    rationale: str = "",
    cluster_ref: str | None = None,
    next_review_after: str | None = None,
) -> OwnerReviewDecision:
    item = find_queue_item(queue, item_ref=item_ref, beacon_ref=beacon_ref)
    stamp = datetime.now(timezone.utc)
    short_beacon = item.beacon_ref.replace(":", ".").replace("/", ".")
    decision_ref = (
        f"decision:{item.target_repo}:{short_beacon}:{stamp.strftime('%Y%m%dT%H%M%SZ')}"
    )
    suppression_rules: list[ReviewDecisionSuppressionRule] = []
    if decision == "suppress":
        suppression_rules.append(
            ReviewDecisionSuppressionRule(
                rule_ref=f"suppress:{short_beacon}",
                scope="beacon",
                target_repo=item.target_repo,
                component_ref=item.component_ref,
                beacon_ref=item.beacon_ref,
                kind=item.kind,
                reason=rationale
                or "owner marked this beacon pressure as noisy or not actionable",
            )
        )

    lineage_bridge = ReviewDecisionLineageBridge(
        cluster_ref=cluster_ref,
        owner_shape=owner_shape_for_item(item),
        owner_assigned_ref=None,
        notes="SDK carries this lineage as provisional unless the owner repo fills owner_assigned_ref.",
    )

    return OwnerReviewDecision(
        decision_ref=decision_ref,
        decided_at=stamp,
        owner_repo=item.target_repo,
        target_repo=item.target_repo,
        reviewer=reviewer,
        queue_ref=queue.queue_ref,
        item_ref=item.item_ref,
        input_beacon_refs=[item.beacon_ref],
        lane=item.lane,
        kind=item.kind,
        component_ref=item.component_ref,
        decision=decision,
        rationale=rationale or DECISION_FOLLOWTHROUGH_HINTS[decision],
        decision_surface=item.decision_surface,
        evidence_refs=list(item.evidence_refs),
        source_inputs=list(item.source_inputs),
        recommended_actions=list(item.recommended_actions),
        applied_surfaces=[],
        followthrough=[],
        suppression_rules=suppression_rules,
        lineage_bridge=lineage_bridge,
        next_review_after=next_review_after,
        boundaries_preserved=LANE_BOUNDARIES.get(item.lane, LANE_BOUNDARIES["general"]),
        forbidden_implications=list(DEFAULT_FORBIDDEN_IMPLICATIONS),
        notes="Template only. Owner review must edit rationale/followthrough/applied_surfaces before treating this as closed.",
    )


def owner_shape_for_item(item: ReviewQueueItem) -> str:
    if item.lane == "technique":
        if item.kind == "canonical_pressure":
            return "technique_canonical_review_note_or_readiness_update"
        if item.kind == "technique_overlap_hold":
            return "technique_overlap_hold_decision"
        return "technique_candidate_intake_decision"
    if item.lane == "skill":
        if item.kind == "unused_skill_opportunity":
            return "skill_usage_gap_decision"
        if item.kind == "skill_trigger_drift":
            return "trigger_eval_or_activation_boundary_decision"
        return "skill_bundle_candidate_decision"
    if item.lane == "eval":
        if item.kind == "overclaim_alarm":
            return "eval_claim_boundary_tightening_decision"
        return "portable_eval_candidate_decision"
    if item.lane == "playbook":
        if item.kind == "subagent_recipe_candidate":
            return "playbook_subagent_recipe_gate_decision"
        if item.kind == "automation_seed_candidate":
            return "playbook_automation_seed_gate_decision"
        return "playbook_scenario_candidate_decision"
    return "owner_review_decision"


def build_review_decision_ledger(
    *,
    workspace_root: str,
    decisions: Iterable[OwnerReviewDecision],
    source_queue_ref: str | None = None,
) -> ReviewDecisionLedger:
    decision_list = list(decisions)
    stamp = datetime.now(timezone.utc)
    entries: list[ReviewDecisionLedgerEntry] = []
    for index, decision in enumerate(decision_list, start=1):
        entries.append(
            ReviewDecisionLedgerEntry(
                entry_ref=f"review-decision-entry:{index:04d}",
                recorded_at=stamp,
                decision_ref=decision.decision_ref,
                owner_repo=decision.owner_repo,
                target_repo=decision.target_repo,
                input_beacon_refs=list(decision.input_beacon_refs),
                decision=decision.decision,
                lane=decision.lane,
                kind=decision.kind,
                component_ref=decision.component_ref,
                decision_surface=decision.decision_surface,
                applied_surfaces=list(decision.applied_surfaces),
                followthrough_refs=[item.action_ref for item in decision.followthrough],
                suppression_rule_refs=[
                    item.rule_ref for item in decision.suppression_rules
                ],
                owner_assigned_ref=(
                    decision.lineage_bridge.owner_assigned_ref
                    if decision.lineage_bridge
                    else None
                ),
                notes=decision.rationale,
            )
        )
    by_decision = Counter(decision.decision for decision in decision_list)
    by_owner = Counter(decision.owner_repo for decision in decision_list)
    return ReviewDecisionLedger(
        ledger_ref=f"review-decision-ledger:{stamp.strftime('%Y%m%dT%H%M%SZ')}",
        workspace_root=workspace_root,
        source_queue_ref=source_queue_ref,
        entries=entries,
        by_decision=dict(sorted(by_decision.items())),
        by_owner=dict(sorted(by_owner.items())),
    )


def build_review_suppression_memory(
    *,
    workspace_root: str,
    decisions: Iterable[OwnerReviewDecision],
) -> ReviewSuppressionMemory:
    rules: list[ReviewDecisionSuppressionRule] = []
    for decision in decisions:
        rules.extend(decision.suppression_rules)
    stamp = datetime.now(timezone.utc)
    return ReviewSuppressionMemory(
        memory_ref=f"review-suppression-memory:{stamp.strftime('%Y%m%dT%H%M%SZ')}",
        workspace_root=workspace_root,
        rules=rules,
    )


def close_review_decisions(
    *,
    workspace_root: str,
    queue: ReviewQueue,
    decisions: Iterable[OwnerReviewDecision],
) -> ReviewDecisionCloseReport:
    decision_list = list(decisions)
    queue_by_item = {item.item_ref: item for item in queue.items}
    queue_by_beacon = {item.beacon_ref: item for item in queue.items}
    warnings: list[str] = []
    closed_item_refs: set[str] = set()
    suppressed_beacon_refs: list[str] = []

    for decision in decision_list:
        if decision.queue_ref and decision.queue_ref != queue.queue_ref:
            warnings.append(
                f"Decision {decision.decision_ref} points to queue {decision.queue_ref}, not {queue.queue_ref}."
            )
        queue_item = queue_by_item.get(decision.item_ref or "")
        if queue_item is None and decision.input_beacon_refs:
            queue_item = queue_by_beacon.get(decision.input_beacon_refs[0])
        if queue_item is None:
            warnings.append(
                f"Decision {decision.decision_ref} does not match any queue item."
            )
            continue
        closed_item_refs.add(queue_item.item_ref)
        if decision.owner_repo != queue_item.target_repo:
            warnings.append(
                f"Decision {decision.decision_ref} owner_repo={decision.owner_repo} differs from queue target_repo={queue_item.target_repo}."
            )
        for rule in decision.suppression_rules:
            if rule.beacon_ref:
                suppressed_beacon_refs.append(rule.beacon_ref)

    unresolved_items = [
        item.item_ref for item in queue.items if item.item_ref not in closed_item_refs
    ]
    ledger = build_review_decision_ledger(
        workspace_root=workspace_root,
        decisions=decision_list,
        source_queue_ref=queue.queue_ref,
    )
    memory = build_review_suppression_memory(
        workspace_root=workspace_root, decisions=decision_list
    )
    stamp = datetime.now(timezone.utc)
    return ReviewDecisionCloseReport(
        report_ref=f"review-decision-close:{stamp.strftime('%Y%m%dT%H%M%SZ')}",
        workspace_root=workspace_root,
        source_queue_ref=queue.queue_ref,
        decisions=[decision.decision_ref for decision in decision_list],
        ledger=ledger,
        suppression_memory=memory,
        closed_item_refs=sorted(closed_item_refs),
        unresolved_item_refs=unresolved_items,
        suppressed_beacon_refs=sorted(set(suppressed_beacon_refs)),
        warnings=warnings,
    )


def load_decisions_from_paths(paths: Iterable[str | Path]) -> list[OwnerReviewDecision]:
    import json

    decisions: list[OwnerReviewDecision] = []
    for path in paths:
        payload = json.loads(
            Path(path).expanduser().resolve().read_text(encoding="utf-8")
        )
        decisions.append(OwnerReviewDecision.model_validate(payload))
    return decisions
