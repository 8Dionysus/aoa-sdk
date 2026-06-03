from __future__ import annotations

from collections import defaultdict
from typing import Any
import json

from ...workspace.discovery import Workspace
from ..models import ObservationCategory, ObservationRecord
from ..registry import RecurrenceRegistry
from .common import _component_ref_for, _evidence, _line_matches, _obs, _read_json, _repo_root


def _collect_technique_intake(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    repo = "aoa-techniques"
    repo_root = _repo_root(workspace, repo)
    if repo_root is None:
        return []
    component_ref = _component_ref_for(registry, repo, "techniques")
    path = repo_root / "docs" / "CROSS_LAYER_TECHNIQUE_CANDIDATES.md"
    if not path.is_file():
        return []
    producer = "technique_intake_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    patterns: list[tuple[str, ObservationCategory, str, list[str], str]] = [
        (
            "future import here",
            "review_signal",
            "cross_layer_candidate_seen",
            ["cross-layer-technique-candidates"],
            "candidate lane is present but remains decision-only",
        ),
        (
            "hold because overlap",
            "review_signal",
            "overlap_hold_open",
            ["cross-layer-technique-candidates"],
            "overlap hold must suppress premature distillation",
        ),
        (
            "needs layer incubation before distillation here",
            "repeat_pattern",
            "layer_incubation_needed",
            ["cross-layer-technique-candidates"],
            "candidate needs sibling layer proof before technique extraction",
        ),
        (
            "substrate or architecture pattern, not yet a technique",
            "review_signal",
            "not_yet_technique_shaped",
            ["cross-layer-technique-candidates"],
            "candidate is still too infra-shaped for technique canon",
        ),
        (
            "landed technique",
            "evidence_pressure",
            "technique_landed_from_candidate",
            ["cross-layer-technique-candidates"],
            "candidate line points at a landed technique bundle",
        ),
    ]
    for needle, category, signal, source_inputs, note in patterns:
        for line_no, line, _matched in _line_matches(path, [needle])[:12]:
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component_ref,
                    owner_repo=repo,
                    category=category,
                    signal=signal,
                    source_inputs=source_inputs,
                    evidence_refs=[_evidence(repo, repo_root, path, f"#L{line_no}")],
                    attributes={"line": line, "needle": needle},
                    notes=note,
                )
            )
    return observations

def _collect_technique_readiness(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    repo = "aoa-techniques"
    repo_root = _repo_root(workspace, repo)
    if repo_root is None:
        return []
    component_ref = _component_ref_for(registry, repo, "techniques")
    paths = [
        repo_root / "docs" / "PROMOTION_READINESS_MATRIX.md",
        repo_root / "generated" / "technique_promotion_readiness.min.json",
    ]
    producer = "technique_readiness_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    md_path = paths[0]
    if md_path.is_file():
        patterns: list[tuple[str, ObservationCategory, str, str]] = [
            (
                "second-consumer",
                "review_signal",
                "second_consumer_pressure_seen",
                "readiness matrix mentions second-consumer pressure",
            ),
            (
                "live downstream adopter",
                "review_signal",
                "second_consumer_missing",
                "readiness matrix says another live adopter is still missing",
            ),
            (
                "approve-now queue",
                "review_signal",
                "canonical_review_queue_seen",
                "readiness queue surface is visible",
            ),
            (
                "latest graduation",
                "evidence_pressure",
                "canonical_graduation_seen",
                "graduation evidence is visible",
            ),
            (
                "dominant blocker",
                "review_signal",
                "canonical_blocker_seen",
                "dominant blocker should shape canonical pressure",
            ),
        ]
        for needle, category, signal, note in patterns:
            for line_no, line, _matched in _line_matches(md_path, [needle])[:8]:
                counter += 1
                observations.append(
                    _obs(
                        producer=producer,
                        counter=counter,
                        component_ref=component_ref,
                        owner_repo=repo,
                        category=category,
                        signal=signal,
                        source_inputs=["promotion-readiness"],
                        evidence_refs=[
                            _evidence(repo, repo_root, md_path, f"#L{line_no}")
                        ],
                        attributes={"line": line, "needle": needle},
                        notes=note,
                    )
                )
    generated_path = paths[1]
    payload = _read_json(generated_path) if generated_path.is_file() else None
    for signal, records in _readiness_generated_signals(payload).items():
        for index, record in enumerate(records[:20], start=1):
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component_ref,
                    owner_repo=repo,
                    category="evidence_pressure"
                    if signal == "second_consumer_confirmed"
                    else "review_signal",
                    signal=signal,
                    source_inputs=["promotion-readiness"],
                    evidence_refs=[
                        _evidence(repo, repo_root, generated_path, f"#{index}")
                    ],
                    attributes={"readiness_record": record},
                    notes="generated readiness record converted into advisory recurrence observation",
                )
            )
    return observations

def _readiness_generated_signals(
    payload: Any | None,
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    records: list[dict[str, Any]] = []
    if isinstance(payload, list):
        records = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        for key in ("items", "techniques", "records", "bundles"):
            if isinstance(payload.get(key), list):
                records = [item for item in payload[key] if isinstance(item, dict)]
                break
    for record in records:
        text = json.dumps(record, ensure_ascii=False).lower()
        if any(
            needle in text
            for needle in (
                "second_consumer_confirmed",
                "second consumer confirmed",
                "approve",
                "ready",
            )
        ):
            result["second_consumer_confirmed"].append(record)
        if any(
            needle in text
            for needle in (
                "missing",
                "needs another",
                "live adopter",
                "second-consumer",
            )
        ):
            result["canonical_pressure_observed"].append(record)
    return result
