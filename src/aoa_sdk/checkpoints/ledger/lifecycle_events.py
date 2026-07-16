"""Checkpoint lifecycle ledger event helpers."""

from __future__ import annotations

from ...models import SessionCheckpointLifecycleEvent
from ..timestamps import with_local_timestamp_default


def normalize_lifecycle_event(payload: object) -> SessionCheckpointLifecycleEvent:
    event = SessionCheckpointLifecycleEvent.model_validate(payload)
    observed_at_local, observed_tz = with_local_timestamp_default(
        utc_value=event.observed_at,
        local_value=event.observed_at_local,
        tz_name=event.observed_tz,
    )
    if observed_at_local == event.observed_at_local and observed_tz == event.observed_tz:
        return event
    return event.model_copy(
        update={
            "observed_at_local": observed_at_local,
            "observed_tz": observed_tz,
        }
    )


def lifecycle_evidence_refs(events: list[SessionCheckpointLifecycleEvent]) -> set[str]:
    refs: set[str] = set()
    for event in events:
        refs.update(event.evidence_refs)
        if event.closeout_context_ref:
            refs.add(event.closeout_context_ref)
        if event.closeout_materialization_report_ref:
            refs.add(event.closeout_materialization_report_ref)
        if event.session_memory_archive_ref:
            refs.add(event.session_memory_archive_ref)
    return refs


def lifecycle_closed(events: list[SessionCheckpointLifecycleEvent]) -> bool:
    return any(event.lifecycle_state == "closed" for event in events)
