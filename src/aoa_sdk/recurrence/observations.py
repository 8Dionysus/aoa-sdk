from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..workspace.discovery import Workspace
from .models import (
    ChangeSignal,
    HookRunReport,
    ObservationCategory,
    ObservationPacket,
    ObservationRecord,
)
from .registry import RecurrenceRegistry, load_registry


CATEGORY_BY_SIGNAL: dict[str, ObservationCategory] = {
    "source_changed": "change_pressure",
    "generated_changed": "change_pressure",
    "projection_changed": "change_pressure",
    "contract_changed": "change_pressure",
    "docs_changed": "change_pressure",
    "tests_changed": "change_pressure",
    "proof_changed": "change_pressure",
    "receipt_changed": "evidence_pressure",
    "other_changed": "change_pressure",
}


def build_observation_packet(
    workspace: Workspace,
    *,
    signal: ChangeSignal | None = None,
    registry: RecurrenceRegistry | None = None,
    supplemental_paths: list[str] | None = None,
    hook_run_paths: list[str] | None = None,
) -> ObservationPacket:
    registry = registry or load_registry(workspace)
    observations: list[ObservationRecord] = []

    if signal is not None:
        observations.extend(_observations_from_change_signal(signal, registry=registry))

    for path in supplemental_paths or []:
        observations.extend(load_observations_from_path(path))

    for path in hook_run_paths or []:
        observations.extend(load_observations_from_path(path))

    observations = _dedupe_and_sort(observations)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ObservationPacket(
        packet_ref=f"observations:{stamp}",
        workspace_root=str(workspace.federation_root),
        signal_ref=signal.signal_ref if signal is not None else None,
        observations=observations,
    )


def _observations_from_change_signal(
    signal: ChangeSignal,
    *,
    registry: RecurrenceRegistry,
) -> list[ObservationRecord]:
    observations: list[ObservationRecord] = []
    counter = 0

    for item in signal.direct_components:
        loaded = registry.get(item.component_ref)
        evidence_refs = [f"{signal.repo_name or item.owner_repo}:{path}" for path in item.matched_paths]
        notes = "derived from direct change detection"
        if loaded is not None and loaded.component.beacon_rules:
            notes = (
                "derived from direct change detection; supplemental review signals may raise this into a beacon"
            )
        for inferred in item.inferred_signals:
            counter += 1
            observations.append(
                ObservationRecord(
                    observation_ref=f"obs:signal:{counter:04d}",
                    component_ref=item.component_ref,
                    owner_repo=item.owner_repo,
                    observed_at=signal.observed_at,
                    category=CATEGORY_BY_SIGNAL.get(inferred, "change_pressure"),
                    signal=inferred,
                    source_inputs=["change_signal"],
                    evidence_refs=evidence_refs,
                    attributes={
                        "match_class": item.match_class,
                        "matched_path_count": len(item.matched_paths),
                        "repo_name": signal.repo_name or item.owner_repo,
                    },
                    notes=notes,
                )
            )
    return observations


def load_observations_from_path(path: str | Path) -> list[ObservationRecord]:
    resolved = Path(path).expanduser().resolve()
    if resolved.suffix == ".jsonl":
        records: list[ObservationRecord] = []
        with resolved.open("r", encoding="utf-8") as handle:
            for raw in handle:
                stripped = raw.strip()
                if not stripped:
                    continue
                records.append(ObservationRecord.model_validate_json(stripped))
        return records

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and payload.get("schema_version") == "aoa_observation_packet_v1":
        packet = ObservationPacket.model_validate(payload)
        return list(packet.observations)
    if isinstance(payload, dict) and payload.get("schema_version") == "aoa_hook_run_report_v1":
        report = HookRunReport.model_validate(payload)
        return list(report.observations)
    if isinstance(payload, list):
        return [ObservationRecord.model_validate(item) for item in payload]
    return [ObservationRecord.model_validate(payload)]


def _dedupe_and_sort(observations: list[ObservationRecord]) -> list[ObservationRecord]:
    seen: set[tuple[str, str, str, tuple[str, ...], tuple[str, ...]]] = set()
    result: list[ObservationRecord] = []
    for item in sorted(
        observations,
        key=lambda obs: (
            obs.owner_repo,
            obs.component_ref,
            obs.signal,
            obs.observed_at,
            obs.observation_ref,
        ),
    ):
        key = (
            item.component_ref,
            item.signal,
            item.category,
            tuple(sorted(item.source_inputs)),
            tuple(sorted(item.evidence_refs)),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
