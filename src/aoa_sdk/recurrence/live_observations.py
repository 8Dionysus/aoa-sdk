from __future__ import annotations

from collections.abc import Callable, Sequence

from ..workspace.discovery import Workspace
from .live.common import _limit, _stamp
from .live.events import _collect_recurrence_event_repetition
from .live.generated import _collect_generated_staleness
from .live.playbooks import _collect_playbook_harvest
from .live.runtime import _collect_runtime_evidence_selection
from .live.techniques import _collect_technique_intake, _collect_technique_readiness
from .models import ObservationPacket, ObservationRecord
from .observations import _dedupe_and_sort
from .registry import RecurrenceRegistry, load_registry


LiveProducerName = str

LIVE_PRODUCERS: tuple[LiveProducerName, ...] = (
    "generated_staleness_watch",
    "technique_intake_watch",
    "technique_readiness_watch",
    "runtime_evidence_selection_watch",
    "playbook_harvest_watch",
    "recurrence_event_repetition_watch",
)

LIVE_PRODUCER_COLLECTORS: dict[
    str, Callable[[Workspace, RecurrenceRegistry], list[ObservationRecord]]
] = {
    "generated_staleness_watch": _collect_generated_staleness,
    "technique_intake_watch": _collect_technique_intake,
    "technique_readiness_watch": _collect_technique_readiness,
    "runtime_evidence_selection_watch": _collect_runtime_evidence_selection,
    "playbook_harvest_watch": _collect_playbook_harvest,
    "recurrence_event_repetition_watch": _collect_recurrence_event_repetition,
}


def list_live_producers() -> list[str]:
    """Return stable producer names for CLI/help surfaces."""
    return list(LIVE_PRODUCERS)


def build_live_observation_packet(
    workspace: Workspace,
    *,
    registry: RecurrenceRegistry | None = None,
    producers: Sequence[str] | None = None,
    max_observations_per_producer: int = 200,
) -> ObservationPacket:
    """Collect owner-authored runtime/publication evidence as recurrence observations.

    This layer reads already-authored artifacts and emits `ObservationRecord` entries.
    It does not promote techniques, activate skills, author evals, create playbooks,
    mutate generated surfaces, or spawn agents.
    """

    registry = registry or load_registry(workspace)
    selected = tuple(producers or LIVE_PRODUCERS)
    unknown = sorted(set(selected) - set(LIVE_PRODUCERS))
    if unknown:
        raise ValueError(f"unknown live observation producers: {', '.join(unknown)}")

    observations: list[ObservationRecord] = []
    for producer in selected:
        observations.extend(
            _limit(
                LIVE_PRODUCER_COLLECTORS[producer](workspace, registry),
                max_observations_per_producer,
            )
        )

    observations = _dedupe_and_sort(observations)
    stamp = _stamp()
    return ObservationPacket(
        packet_ref=f"observations:live:{stamp}",
        workspace_root=str(workspace.federation_root),
        signal_ref=None,
        observations=observations,
    )
