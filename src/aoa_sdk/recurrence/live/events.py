from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from ...workspace.discovery import Workspace
from ..models import ObservationRecord
from ..registry import RecurrenceRegistry
from .common import _component_ref_for, _evidence, _glob, _obs, _read_json


def _collect_recurrence_event_repetition(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    producer = "recurrence_event_repetition_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    event_paths = _glob(
        Path(workspace.federation_root),
        [".aoa/recurrence/events/*.json", "*/.aoa/recurrence/events/*.json"],
    )
    signal_counts: Counter[tuple[str, str]] = Counter()
    evidence_by_key: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path in event_paths:
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        repo = str(
            payload.get("repo_name")
            or payload.get("owner_repo")
            or _repo_from_path(workspace, path)
            or "unknown"
        )
        for item in (
            payload.get("unmatched_paths", [])
            if isinstance(payload.get("unmatched_paths"), list)
            else []
        ):
            if isinstance(item, str):
                key = (repo, item)
                signal_counts[key] += 1
                evidence_by_key[key].append(_event_evidence(workspace, path))
        for item in (
            payload.get("changed_paths", [])
            if isinstance(payload.get("changed_paths"), list)
            else []
        ):
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                key = (repo, item["path"])
                signal_counts[key] += 1
                evidence_by_key[key].append(_event_evidence(workspace, path))
    for (repo, changed_path), count in sorted(signal_counts.items()):
        if count < 2:
            continue
        component_ref = _component_ref_for(registry, repo)
        counter += 1
        observations.append(
            _obs(
                producer=producer,
                counter=counter,
                component_ref=component_ref,
                owner_repo=repo,
                category="repeat_pattern",
                signal="repeated_patch_pattern",
                source_inputs=["change_signal", "recurrence-event-history"],
                evidence_refs=evidence_by_key[(repo, changed_path)][:10],
                attributes={"path": changed_path, "repeat_count": count},
                notes="the same changed/unmatched path recurred across saved recurrence events; consider owner law, skill, playbook, or technique extraction",
            )
        )
    return observations

def _repo_from_path(workspace: Workspace, path: Path) -> str | None:
    for repo, root in workspace.repo_roots.items():
        try:
            path.relative_to(root)
        except ValueError:
            continue
        return repo
    return None

def _event_evidence(workspace: Workspace, path: Path) -> str:
    repo = _repo_from_path(workspace, path) or "workspace"
    root = workspace.repo_roots.get(repo, Path(workspace.federation_root))
    return _evidence(repo, root, path)
