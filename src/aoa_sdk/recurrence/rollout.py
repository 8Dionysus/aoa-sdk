from __future__ import annotations

from datetime import datetime, timezone

from ..workspace.discovery import Workspace
from .models import (
    ConnectivityGapReport,
    DriftTrigger,
    OwnerReviewSummary,
    RolloutWindow,
    RolloutWindowBundle,
    WiringPlan,
)


def build_rollout_window_bundle(
    workspace: Workspace,
    *,
    wiring_plan: WiringPlan,
    review_summary: OwnerReviewSummary | None = None,
    doctor_report: ConnectivityGapReport | None = None,
) -> RolloutWindowBundle:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    campaign_ref = f"CAMP-RECURRENCE-{stamp}"

    campaign_window = RolloutWindow(
        window_ref=f"campaign-window:{stamp}",
        campaign_ref=campaign_ref,
        phase="prepared",
        title="Recurrence control-plane rollout campaign",
        wiring_scopes=[snippet.scope for snippet in wiring_plan.snippets],
        review_surfaces=[
            ".aoa/recurrence/review-queues/*.latest.json",
            ".aoa/recurrence/review-summaries/*.latest.json",
            "generated/codex/rollout/rollout_latest.min.json",
        ],
        guard_commands=[
            "aoa recur doctor --root . --json",
            "aoa recur hooks list --root . --json",
        ],
        drift_triggers=build_drift_triggers(
            review_summary=review_summary, doctor_report=doctor_report
        ),
        rollback_anchors=[
            "docs/CODEX_PLANE_ROLLOUT.md",
            "generated/codex/rollout/rollback_windows.min.json",
            ".aoa/recurrence/review-summaries/*.latest.json",
        ],
        notes="Bound the rollout as one reviewable campaign. Do not turn cadence windows into a scheduler.",
    )

    drift_review_window = RolloutWindow(
        window_ref=f"drift-review-window:{stamp}",
        campaign_ref=campaign_ref,
        phase="monitoring" if not has_high_severity_gap(doctor_report) else "repairing",
        title="Recurrence drift review window",
        wiring_scopes=["session_stop", "pre_push", "ci"],
        review_surfaces=[
            ".aoa/recurrence/doctor/*.latest.json",
            ".aoa/recurrence/review-summaries/*.latest.json",
        ],
        guard_commands=[
            "aoa recur doctor --root . --json",
        ],
        drift_triggers=build_drift_triggers(
            review_summary=review_summary, doctor_report=doctor_report
        ),
        rollback_anchors=[
            "generated/codex/rollout/rollback_windows.min.json",
        ],
        notes="Name drift explicitly when wiring, hook activation, or review-surfaces stop lining up.",
    )

    rollback_followthrough_window = RolloutWindow(
        window_ref=f"rollback-followthrough-window:{stamp}",
        campaign_ref=campaign_ref,
        phase="rollback_open" if has_high_severity_gap(doctor_report) else "prepared",
        title="Recurrence rollback follow-through window",
        wiring_scopes=["session_start", "session_stop", "ci"],
        review_surfaces=[
            "generated/codex/rollout/rollback_windows.min.json",
            ".aoa/recurrence/doctor/*.latest.json",
        ],
        guard_commands=[
            "aoa recur doctor --root . --json",
        ],
        drift_triggers=build_drift_triggers(
            review_summary=review_summary, doctor_report=doctor_report
        ),
        rollback_anchors=[
            "docs/CODEX_TRUSTED_ROLLOUT_OPERATIONS.md",
            "generated/codex/rollout/rollback_windows.min.json",
            ".aoa/recurrence/review-queues/*.latest.json",
        ],
        notes="Open rollback follow-through when drift becomes material on startup, hook activation, or review-surface trust.",
    )

    return RolloutWindowBundle(
        bundle_ref=f"rollout-bundle:{stamp}",
        workspace_root=str(workspace.root),
        wiring_plan_ref=wiring_plan.plan_ref,
        campaign_window=campaign_window,
        drift_review_window=drift_review_window,
        rollback_followthrough_window=rollback_followthrough_window,
    )


def build_drift_triggers(
    *,
    review_summary: OwnerReviewSummary | None,
    doctor_report: ConnectivityGapReport | None,
) -> list[DriftTrigger]:
    triggers: list[DriftTrigger] = [
        DriftTrigger(
            signal="hook_wiring_missing_or_drifted",
            severity="medium",
            source="wiring-plan",
            notes="Use this when SessionStart, UserPromptSubmit, or Stop recurrence snippets are missing or stale.",
        ),
        DriftTrigger(
            signal="review_surfaces_missing",
            severity="medium",
            source="review-queue",
            notes="Use this when the session-stop path stops producing review queues or owner summaries.",
        ),
    ]
    if doctor_report is not None:
        for gap in doctor_report.gaps:
            triggers.append(
                DriftTrigger(
                    signal=gap.gap_kind,
                    severity=gap.severity,
                    source=gap.component_ref or "doctor",
                    notes=gap.recommendation,
                )
            )
    if review_summary is not None:
        for owner in review_summary.owners:
            if owner.total_items >= 4:
                triggers.append(
                    DriftTrigger(
                        signal="review_queue_pressure",
                        severity="medium",
                        source=owner.target_repo,
                        notes="The owner queue is filling faster than the current review cadence is clearing it.",
                    )
                )
            if owner.by_kind.get("overclaim_alarm", 0) > 0:
                triggers.append(
                    DriftTrigger(
                        signal="overclaim_alarm_present",
                        severity="high",
                        source=owner.target_repo,
                        notes="Proof wording is drifting stronger than the bounded evidence posture.",
                    )
                )
    return dedupe_triggers(triggers)


def dedupe_triggers(items: list[DriftTrigger]) -> list[DriftTrigger]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[DriftTrigger] = []
    for item in items:
        key = (item.signal, item.severity, item.source)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def has_high_severity_gap(doctor_report: ConnectivityGapReport | None) -> bool:
    if doctor_report is None:
        return False
    return any(item.severity == "high" for item in doctor_report.gaps)
