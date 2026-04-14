from __future__ import annotations

from datetime import datetime, timezone

from .models import BeaconPacket, CandidateLedger, CandidateLedgerEntry


def build_candidate_ledger(
    packet: BeaconPacket,
    *,
    include_lower_status: bool = True,
) -> CandidateLedger:
    recorded_at = datetime.now(timezone.utc)
    entries: list[CandidateLedgerEntry] = []
    counter = 0
    for item in packet.entries:
        if not include_lower_status and item.status not in {"candidate", "review_ready"}:
            continue
        counter += 1
        entries.append(
            CandidateLedgerEntry(
                entry_ref=f"ledger:{counter:04d}",
                recorded_at=recorded_at,
                beacon_ref=item.beacon_ref,
                kind=item.kind,
                status=item.status,
                component_ref=item.component_ref,
                owner_repo=item.owner_repo,
                target_repo=item.target_repo,
                decision_surface=item.decision_surface,
                evidence_refs=list(item.evidence_refs),
                source_inputs=list(item.source_inputs),
                notes=item.reason,
            )
        )
    stamp = recorded_at.strftime("%Y%m%dT%H%M%SZ")
    return CandidateLedger(
        ledger_ref=f"candidate-ledger:{stamp}",
        workspace_root=packet.workspace_root,
        signal_ref=packet.signal_ref,
        entries=entries,
    )
