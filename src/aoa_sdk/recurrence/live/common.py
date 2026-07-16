from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ...workspace.discovery import Workspace
from ..models import ObservationCategory, ObservationRecord
from ..registry import RecurrenceRegistry, normalize_path


DEFAULT_COMPONENT_REFS: dict[str, str] = {
    "aoa-techniques": "component:techniques:canon-and-intake-beacons",
    "aoa-evals": "component:evals:portable-proof-beacons",
    "aoa-playbooks": "component:playbooks:scenario-composition-beacons",
}


def _limit(
    items: Iterable[ObservationRecord], max_items: int
) -> list[ObservationRecord]:
    return list(items)[:max_items]

def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _repo_root(workspace: Workspace, repo: str) -> Path | None:
    return workspace.repo_roots.get(repo)

def _component_ref_for(registry: RecurrenceRegistry, repo: str, *needles: str) -> str:
    default = DEFAULT_COMPONENT_REFS.get(repo)
    loaded = list(registry.iter_components())
    if default and registry.get(default) is not None:
        return default
    lowered_needles = tuple(item.lower() for item in needles)
    for item in loaded:
        component = item.component
        if component.owner_repo != repo:
            continue
        haystack = " ".join(
            [component.component_ref, component.description, *component.tags]
        ).lower()
        if all(needle in haystack for needle in lowered_needles):
            return component.component_ref
    for item in loaded:
        if item.component.owner_repo == repo:
            return item.component.component_ref
    return default or f"component:{repo}:live-observation"

def _obs(
    *,
    producer: str,
    counter: int,
    component_ref: str,
    owner_repo: str,
    category: ObservationCategory,
    signal: str,
    source_inputs: list[str],
    evidence_refs: list[str],
    attributes: dict[str, Any] | None = None,
    notes: str = "",
) -> ObservationRecord:
    return ObservationRecord(
        observation_ref=f"obs:live:{producer}:{counter:04d}",
        component_ref=component_ref,
        owner_repo=owner_repo,
        observed_at=_now(),
        category=category,
        signal=signal,
        source_inputs=source_inputs,
        evidence_refs=evidence_refs,
        attributes={"producer": producer, **(attributes or {})},
        notes=notes,
    )

def _rel(repo_root: Path, path: Path) -> str:
    try:
        return normalize_path(path.relative_to(repo_root))
    except ValueError:
        return normalize_path(path)

def _evidence(repo: str, repo_root: Path, path: Path, suffix: str | None = None) -> str:
    ref = f"{repo}:{_rel(repo_root, path)}"
    if suffix:
        ref += suffix
    return ref

def _glob(repo_root: Path, patterns: Iterable[str]) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        normalized = normalize_path(pattern)
        if not normalized:
            continue
        if any(token in normalized for token in "*?["):
            found.extend(path for path in repo_root.glob(normalized) if path.is_file())
        else:
            path = repo_root / normalized
            if path.is_file():
                found.append(path)
            elif path.is_dir():
                found.extend(child for child in path.rglob("*") if child.is_file())
    return sorted(set(found))

def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    item = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    records.append(item)
    except OSError:
        return []
    return records

def _iter_json_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return _read_jsonl(path)
    payload = _read_json(path)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("cases"), list):
            return [item for item in payload["cases"] if isinstance(item, dict)]
        if isinstance(payload.get("records"), list):
            return [item for item in payload["records"] if isinstance(item, dict)]
        return [payload]
    return []

def _line_matches(path: Path, needles: Iterable[str]) -> list[tuple[int, str, str]]:
    lowered = [(needle, needle.lower()) for needle in needles]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    matches: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(lines, start=1):
        low = line.lower()
        for original, needle in lowered:
            if needle in low:
                matches.append((line_no, line.strip(), original))
                break
    return matches
