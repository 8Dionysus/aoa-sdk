from __future__ import annotations

import json

from ...workspace.discovery import Workspace
from ..models import ObservationCategory, ObservationRecord
from ..registry import RecurrenceRegistry
from .common import _component_ref_for, _evidence, _glob, _iter_json_records, _line_matches, _obs, _repo_root


def _collect_playbook_harvest(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    repo = "aoa-playbooks"
    repo_root = _repo_root(workspace, repo)
    if repo_root is None:
        return []
    component_ref = _component_ref_for(registry, repo, "playbook")
    producer = "playbook_harvest_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    paths = _glob(
        repo_root,
        [
            "examples/harvests/*",
            "examples/harvests/**/*",
            "docs/real-runs/*",
            "docs/real-runs/**/*",
            "docs/PLAYBOOK_REAL_RUN_HARVEST.md",
            ".aoa/live_receipts/playbook-receipts.jsonl",
        ],
    )
    signal_terms: list[tuple[str, str, ObservationCategory, str, list[str]]] = [
        (
            "repeated",
            "repeated_scenario_shape",
            "repeat_pattern",
            "recurring scenario shape appears in harvest evidence",
            ["real-run-harvests"],
        ),
        (
            "recurring",
            "repeated_scenario_shape",
            "repeat_pattern",
            "recurring scenario shape appears in harvest evidence",
            ["real-run-harvests"],
        ),
        (
            "subagent",
            "subagent_handoff_receipt_ready",
            "review_signal",
            "subagent handoff/recipe pressure appears in harvest evidence",
            ["real-run-harvests", "composition-gates"],
        ),
        (
            "automation seed",
            "automation_readiness_signal",
            "review_signal",
            "automation-seed readiness appears in reviewable harvest evidence",
            ["real-run-harvests", "composition-gates"],
        ),
        (
            "alternate path",
            "alternate_path_pattern_repeated",
            "repeat_pattern",
            "alternate path pattern repeated; scenario may need playbook boundary",
            ["real-run-harvests"],
        ),
        (
            "gate",
            "composition_gate_pressure",
            "review_signal",
            "composition gate pressure appears in harvest evidence",
            ["composition-gates"],
        ),
    ]
    for path in paths:
        if path.suffix in {".json", ".jsonl"}:
            records = _iter_json_records(path)
            for index, record in enumerate(records, start=1):
                text = json.dumps(record, ensure_ascii=False).lower()
                for term, signal, category, note, source_inputs in signal_terms:
                    if term in text:
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
                                evidence_refs=[
                                    _evidence(repo, repo_root, path, f"#{index}")
                                ],
                                attributes={"term": term, "record_index": index},
                                notes=note,
                            )
                        )
        else:
            for term, signal, category, note, source_inputs in signal_terms:
                for line_no, line, _matched in _line_matches(path, [term])[:10]:
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
                            evidence_refs=[
                                _evidence(repo, repo_root, path, f"#L{line_no}")
                            ],
                            attributes={"term": term, "line": line},
                            notes=note,
                        )
                    )
    return observations
