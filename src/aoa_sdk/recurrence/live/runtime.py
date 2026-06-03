from __future__ import annotations

from typing import Any
import json

from ...workspace.discovery import Workspace
from ..models import ObservationCategory, ObservationRecord
from ..registry import RecurrenceRegistry
from .common import _component_ref_for, _evidence, _glob, _line_matches, _obs, _read_json, _rel, _repo_root


OVERCLAIM_PHRASES: tuple[str, ...] = (
    "is the best",
    "is smarter",
    "proves better agent quality",
    "proves general reasoning growth",
    "global model ranking",
    "capability ranking",
)


def _collect_runtime_evidence_selection(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    repo = "aoa-evals"
    repo_root = _repo_root(workspace, repo)
    if repo_root is None:
        return []
    component_ref = _component_ref_for(registry, repo, "eval")
    producer = "runtime_evidence_selection_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    paths = _glob(
        repo_root,
        [
            "examples/runtime_evidence_selection*.json",
            "examples/**/*runtime*evidence*.json",
            "generated/**/*runtime*evidence*.json",
            ".aoa/recurrence/runtime_evidence/*.json",
        ],
    )
    for path in paths:
        payload = _read_json(path)
        if payload is None:
            continue
        text = json.dumps(payload, ensure_ascii=False).lower()
        signal = None
        category: ObservationCategory = "evidence_pressure"
        if any(
            needle in text
            for needle in (
                "bundle-candidate",
                "bundle_candidate",
                "portable",
                "evidence-sidecar",
            )
        ):
            signal = "runtime_candidate_selected"
        if any(phrase in text for phrase in OVERCLAIM_PHRASES):
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component_ref,
                    owner_repo=repo,
                    category="overclaim_risk",
                    signal="overclaim_phrase_seen",
                    source_inputs=["runtime-candidate-guide", "trace-eval-bridge"],
                    evidence_refs=[_evidence(repo, repo_root, path)],
                    attributes={
                        "phrases": [
                            phrase for phrase in OVERCLAIM_PHRASES if phrase in text
                        ]
                    },
                    notes="runtime evidence selection contains language that may overread bounded runtime posture",
                )
            )
        if signal is not None:
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component_ref,
                    owner_repo=repo,
                    category=category,
                    signal=signal,
                    source_inputs=["runtime-candidate-guide", "trace-eval-bridge"],
                    evidence_refs=[_evidence(repo, repo_root, path)],
                    attributes={
                        "target_class": _target_class(payload),
                        "path": _rel(repo_root, path),
                    },
                    notes="selected runtime evidence is candidate input for bounded portable eval review, not proof canon",
                )
            )
    guide = repo_root / "docs" / "RUNTIME_BENCH_PROMOTION_GUIDE.md"
    if guide.is_file():
        for line_no, line, _matched in _line_matches(
            guide, ["bundle-candidate", "do-not-overread", "human review required"]
        )[:8]:
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component_ref,
                    owner_repo=repo,
                    category="review_signal",
                    signal="portable_eval_boundary_seen",
                    source_inputs=["runtime-candidate-guide"],
                    evidence_refs=[_evidence(repo, repo_root, guide, f"#L{line_no}")],
                    attributes={"line": line},
                    notes="runtime promotion guide marks a bounded review boundary",
                )
            )
    return observations

def _target_class(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("target_class", "promotion_target", "target", "class"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
    return None
