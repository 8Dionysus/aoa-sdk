from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from ...workspace.discovery import Workspace
from ..models import ObservationRecord
from ..registry import RecurrenceRegistry
from .common import _component_ref_for, _evidence, _glob, _iter_json_records, _obs, _repo_root


SKILL_POSITIVE_CASES: set[str] = {"should-trigger", "explicit-handle", "invoke-skill"}
SKILL_COLLISION_CASES: set[str] = {"prefer-other-skill"}
SKILL_MANUAL_CASES: set[str] = {"manual-invocation-required"}


def _collect_skill_trigger_surface(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    repo = "aoa-skills"
    repo_root = _repo_root(workspace, repo)
    if repo_root is None:
        return []
    component_ref = _component_ref_for(registry, repo, "skills")
    producer = "skill_trigger_surface_watch"
    observations: list[ObservationRecord] = []
    counter = 0

    case_paths = _glob(
        repo_root,
        [
            "generated/description_trigger_eval_cases.jsonl",
            "generated/description_trigger_eval_cases.json",
            "data/**/*trigger*eval*.jsonl",
            "evals/**/*trigger*.jsonl",
        ],
    )
    receipt_paths = _glob(
        repo_root, [".aoa/live_receipts/*.jsonl", ".aoa/recurrence/receipts/*.jsonl"]
    )
    seen_skills = _skills_seen_in_receipts(receipt_paths)
    positive_cases: dict[str, list[str]] = defaultdict(list)
    collision_cases: dict[str, list[str]] = defaultdict(list)
    manual_cases: dict[str, list[str]] = defaultdict(list)

    for path in case_paths:
        for index, record in enumerate(_iter_json_records(path), start=1):
            skill = _first_string(
                record, ["skill_name", "skill", "expected_skill", "skill_ref"]
            )
            case_class = _first_string(
                record, ["case_class", "mode", "expected_behavior", "class"]
            )
            case_id = (
                _first_string(record, ["case_id", "id", "name"]) or f"record-{index}"
            )
            if not skill or not case_class:
                continue
            ref = _evidence(repo, repo_root, path, f"#{case_id}")
            if case_class in SKILL_POSITIVE_CASES:
                positive_cases[skill].append(ref)
            elif case_class in SKILL_COLLISION_CASES:
                collision_cases[skill].append(ref)
            elif case_class in SKILL_MANUAL_CASES:
                manual_cases[skill].append(ref)

    for skill, refs in sorted(positive_cases.items()):
        if skill not in seen_skills:
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component_ref,
                    owner_repo=repo,
                    category="usage_gap",
                    signal="skill_trigger_gap",
                    source_inputs=["description-trigger-evals", "skill-live-receipts"],
                    evidence_refs=refs[:8],
                    attributes={
                        "skill": skill,
                        "case_count": len(refs),
                        "receipt_skill_seen": False,
                    },
                    notes="positive trigger-eval cases exist but no matching skill usage receipt was found in live receipt surfaces",
                )
            )
    for skill, refs in sorted(collision_cases.items()):
        counter += 1
        observations.append(
            _obs(
                producer=producer,
                counter=counter,
                component_ref=component_ref,
                owner_repo=repo,
                category="review_signal",
                signal="skill_collision_pressure",
                source_inputs=["description-trigger-evals"],
                evidence_refs=refs[:8],
                attributes={"skill": skill, "case_count": len(refs)},
                notes="prefer-other-skill cases are present; keep activation boundary narrow",
            )
        )
    for skill, refs in sorted(manual_cases.items()):
        counter += 1
        observations.append(
            _obs(
                producer=producer,
                counter=counter,
                component_ref=component_ref,
                owner_repo=repo,
                category="review_signal",
                signal="manual_invocation_boundary_seen",
                source_inputs=["description-trigger-evals"],
                evidence_refs=refs[:8],
                attributes={"skill": skill, "case_count": len(refs)},
                notes="manual-invocation cases are present; do not convert semantic match into auto-use",
            )
        )

    trigger_doc = repo_root / "docs" / "TRIGGER_EVALS.md"
    generated_manifest = (
        repo_root / "generated" / "description_trigger_eval_manifest.json"
    )
    if trigger_doc.is_file() and (
        not generated_manifest.is_file()
        or trigger_doc.stat().st_mtime > generated_manifest.stat().st_mtime
    ):
        counter += 1
        evidence = [_evidence(repo, repo_root, trigger_doc)]
        if generated_manifest.is_file():
            evidence.append(_evidence(repo, repo_root, generated_manifest))
        observations.append(
            _obs(
                producer=producer,
                counter=counter,
                component_ref=component_ref,
                owner_repo=repo,
                category="change_pressure",
                signal="skill_trigger_drift",
                source_inputs=["description-trigger-evals", "change_signal"],
                evidence_refs=evidence,
                attributes={
                    "trigger_doc_newer_than_manifest": generated_manifest.is_file()
                },
                notes="trigger doctrine changed or generated trigger manifest is missing/stale",
            )
        )
    return observations

def _skills_seen_in_receipts(paths: list[Path]) -> set[str]:
    seen: set[str] = set()
    fields = (
        "skill_name",
        "skill",
        "skill_ref",
        "expected_skill",
        "applied_skill",
        "applied_skills",
        "skill_refs",
    )
    for path in paths:
        for record in _iter_json_records(path):
            for field in fields:
                value = record.get(field)
                if isinstance(value, str):
                    seen.add(value)
                elif isinstance(value, list):
                    seen.update(item for item in value if isinstance(item, str))
    return seen

def _first_string(record: dict[str, Any], fields: Iterable[str]) -> str | None:
    for field in fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
