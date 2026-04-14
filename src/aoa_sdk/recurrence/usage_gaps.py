from __future__ import annotations

from datetime import datetime, timezone

from .models import BeaconPacket, UsageGapItem, UsageGapReport


USAGE_GAP_KINDS = {"unused_skill_opportunity", "skill_trigger_drift"}


def build_usage_gap_report(packet: BeaconPacket) -> UsageGapReport:
    items: list[UsageGapItem] = []
    counter = 0
    for entry in packet.entries:
        if entry.kind not in USAGE_GAP_KINDS:
            continue
        counter += 1
        items.append(
            UsageGapItem(
                gap_ref=f"usage-gap:{counter:04d}",
                component_ref=entry.component_ref,
                owner_repo=entry.owner_repo,
                beacon_ref=entry.beacon_ref,
                status=entry.status,
                reason=entry.reason,
                decision_surface=entry.decision_surface,
                evidence_refs=list(entry.evidence_refs),
                recommended_actions=list(entry.recommended_actions),
            )
        )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return UsageGapReport(
        report_ref=f"usage-gaps:{stamp}",
        workspace_root=packet.workspace_root,
        signal_ref=packet.signal_ref,
        items=items,
    )
