from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from .models import (
    BeaconEntry,
    BeaconKind,
    BeaconPacket,
    CandidateDossier,
    CandidateDossierPacket,
    DossierQuestion,
    OwnerReviewSummary,
    OwnerReviewSummaryItem,
    ReviewLane,
    ReviewPriority,
    ReviewQueue,
    ReviewQueueItem,
    UsageGapReport,
)

USAGE_GAP_KINDS = {"unused_skill_opportunity", "skill_trigger_drift"}
DEFAULT_VISIBLE_STATUSES = {"candidate", "review_ready"}


def build_review_queue(
    packet: BeaconPacket,
    *,
    usage_gaps: UsageGapReport | None = None,
    include_lower_status: bool = False,
    include_watch_usage_gaps: bool = True,
) -> ReviewQueue:
    visible: list[BeaconEntry] = []
    usage_gap_refs = (
        {item.beacon_ref for item in usage_gaps.items}
        if usage_gaps is not None
        else set()
    )
    for entry in packet.entries:
        if include_lower_status or entry.status in DEFAULT_VISIBLE_STATUSES:
            visible.append(entry)
            continue
        if (
            include_watch_usage_gaps
            and entry.kind in USAGE_GAP_KINDS
            and entry.status == "watch"
            and (not usage_gap_refs or entry.beacon_ref in usage_gap_refs)
        ):
            visible.append(entry)

    items: list[ReviewQueueItem] = []
    seen: set[tuple[str, str, str, str]] = set()
    for index, entry in enumerate(
        sorted(
            visible,
            key=lambda item: (
                item.target_repo,
                lane_for_kind(item.kind),
                priority_rank(priority_for_entry(item)),
                item.component_ref,
                item.kind,
            ),
        ),
        start=1,
    ):
        dedupe_key = (
            entry.target_repo,
            entry.component_ref,
            entry.beacon_ref,
            entry.status,
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        items.append(
            ReviewQueueItem(
                item_ref=f"review-item:{index:04d}",
                lane=lane_for_kind(entry.kind),
                priority=priority_for_entry(entry),
                target_repo=entry.target_repo,
                owner_repo=entry.owner_repo,
                component_ref=entry.component_ref,
                beacon_ref=entry.beacon_ref,
                kind=entry.kind,
                status=entry.status,
                decision_surface=entry.decision_surface,
                summary=entry.reason,
                evidence_refs=list(entry.evidence_refs),
                source_inputs=list(entry.source_inputs),
                recommended_actions=list(entry.recommended_actions),
            )
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ReviewQueue(
        queue_ref=f"review-queue:{stamp}",
        workspace_root=packet.workspace_root,
        signal_ref=packet.signal_ref,
        items=items,
    )


def build_candidate_dossier_packet(queue: ReviewQueue) -> CandidateDossierPacket:
    dossiers: list[CandidateDossier] = []
    for index, item in enumerate(queue.items, start=1):
        dossiers.append(
            CandidateDossier(
                dossier_ref=f"dossier:{index:04d}",
                lane=item.lane,
                target_repo=item.target_repo,
                owner_repo=item.owner_repo,
                component_ref=item.component_ref,
                beacon_ref=item.beacon_ref,
                kind=item.kind,
                status=item.status,
                decision_surface=item.decision_surface,
                title=title_for_item(item),
                summary=item.summary,
                evidence_refs=list(item.evidence_refs),
                source_inputs=list(item.source_inputs),
                recommended_actions=list(item.recommended_actions),
                review_questions=questions_for_item(item),
            )
        )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return CandidateDossierPacket(
        packet_ref=f"candidate-dossiers:{stamp}",
        workspace_root=queue.workspace_root,
        signal_ref=queue.signal_ref,
        dossiers=dossiers,
    )


def build_owner_review_summary(queue: ReviewQueue) -> OwnerReviewSummary:
    grouped: dict[str, list[ReviewQueueItem]] = defaultdict(list)
    for item in queue.items:
        grouped[item.target_repo].append(item)

    owners: list[OwnerReviewSummaryItem] = []
    for target_repo, items in sorted(grouped.items()):
        by_lane = Counter(item.lane for item in items)
        by_status = Counter(item.status for item in items)
        by_kind = Counter(item.kind for item in items)
        decision_surfaces = sorted(
            {item.decision_surface for item in items if item.decision_surface}
        )
        owners.append(
            OwnerReviewSummaryItem(
                target_repo=target_repo,
                total_items=len(items),
                by_lane=dict(sorted(by_lane.items())),
                by_status=dict(sorted(by_status.items())),
                by_kind=dict(sorted(by_kind.items())),
                decision_surfaces=decision_surfaces,
            )
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OwnerReviewSummary(
        summary_ref=f"owner-review-summary:{stamp}",
        workspace_root=queue.workspace_root,
        signal_ref=queue.signal_ref,
        owners=owners,
    )


def lane_for_kind(kind: BeaconKind) -> ReviewLane:
    if kind in {
        "new_technique_candidate",
        "technique_overlap_hold",
        "canonical_pressure",
    }:
        return "technique"
    if kind in {
        "unused_skill_opportunity",
        "skill_trigger_drift",
        "skill_bundle_candidate",
    }:
        return "skill"
    if kind in {
        "portable_eval_candidate",
        "progression_evidence_candidate",
        "overclaim_alarm",
    }:
        return "eval"
    if kind in {
        "playbook_candidate",
        "subagent_recipe_candidate",
        "automation_seed_candidate",
    }:
        return "playbook"
    return "general"


def priority_for_entry(entry: BeaconEntry) -> ReviewPriority:
    if entry.kind == "overclaim_alarm":
        return "critical" if entry.status in {"candidate", "review_ready"} else "high"
    if entry.status == "review_ready":
        return "critical"
    if entry.kind in USAGE_GAP_KINDS and entry.status == "watch":
        return "medium"
    if entry.status == "candidate":
        return "high"
    if entry.status == "watch":
        return "medium"
    return "low"


def priority_rank(priority: ReviewPriority) -> int:
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order[priority]


def title_for_item(item: ReviewQueueItem) -> str:
    noun = {
        "technique": "Technique",
        "skill": "Skill",
        "eval": "Eval",
        "playbook": "Playbook",
        "general": "Recurrence",
    }[item.lane]
    return f"{noun} review for {item.component_ref} ({item.kind}, {item.status})"


def questions_for_item(item: ReviewQueueItem) -> list[DossierQuestion]:
    common = [
        DossierQuestion(
            prompt="Does the evidence stay bounded to the owning repo and decision surface?",
            why="Recurrence should surface pressure without quietly widening ownership.",
        ),
        DossierQuestion(
            prompt="Do the cited evidence refs justify the current status, or is the signal still early?",
            why="Hints and candidates should not pretend to be a decision.",
        ),
    ]
    per_lane: dict[ReviewLane, list[DossierQuestion]] = {
        "technique": [
            DossierQuestion(
                prompt="Is the pattern separable from nearby techniques and layer-owned implementation details?",
                why="Technique canon should keep bounded public contracts, not absorb orchestration or substrate behavior.",
            ),
            DossierQuestion(
                prompt="Is this a new technique pressure or canonical-strengthening pressure on an existing one?",
                why="Distillation and promotion readiness are related, but they are not the same judgment.",
            ),
        ],
        "skill": [
            DossierQuestion(
                prompt="Was a relevant skill omitted, deferred, or blocked by an explicit boundary?",
                why="Usage-gap signals should distinguish genuine misses from intentional restraint.",
            ),
            DossierQuestion(
                prompt="Do trigger descriptions and collision tests still match the intended activation boundary?",
                why="Trigger drift often hides as routing intuition until the evals go stale.",
            ),
        ],
        "eval": [
            DossierQuestion(
                prompt="Is the underlying claim portable and bounded enough for aoa-evals, or should it remain runtime-local evidence?",
                why="A repeated artifact is not automatically a public proof surface.",
            ),
            DossierQuestion(
                prompt="Do any phrases here overclaim what the evidence actually supports?",
                why="Recurrence should tighten proof, not inflate it.",
            ),
        ],
        "playbook": [
            DossierQuestion(
                prompt="Is the repeated shape scenario-owned and reviewable, rather than a hidden automation lane?",
                why="Playbooks keep explicit composition and resist becoming a scheduler.",
            ),
            DossierQuestion(
                prompt="Can the main thread merge back short ledgers instead of raw traces?",
                why="That boundary keeps subagent recipes bounded when they are later introduced.",
            ),
        ],
        "general": [],
    }
    return common + per_lane.get(item.lane, [])
