from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..workspace.discovery import Workspace
from .models import ObservationCategory, ObservationPacket, ObservationRecord
from .observations import _dedupe_and_sort
from .registry import RecurrenceRegistry, load_registry, normalize_path

LiveProducerName = str

LIVE_PRODUCERS: tuple[LiveProducerName, ...] = (
    "generated_staleness_watch",
    "technique_intake_watch",
    "technique_readiness_watch",
    "skill_trigger_surface_watch",
    "runtime_evidence_selection_watch",
    "playbook_harvest_watch",
    "recurrence_event_repetition_watch",
)

DEFAULT_COMPONENT_REFS: dict[str, str] = {
    "aoa-techniques": "component:techniques:canon-and-intake-beacons",
    "aoa-skills": "component:skills:bundle-and-activation-beacons",
    "aoa-evals": "component:evals:portable-proof-beacons",
    "aoa-playbooks": "component:playbooks:scenario-composition-beacons",
}

OVERCLAIM_PHRASES: tuple[str, ...] = (
    "is the best",
    "is smarter",
    "proves better agent quality",
    "proves general reasoning growth",
    "global model ranking",
    "capability ranking",
)

SKILL_POSITIVE_CASES: set[str] = {"should-trigger", "explicit-handle", "invoke-skill"}
SKILL_COLLISION_CASES: set[str] = {"prefer-other-skill"}
SKILL_MANUAL_CASES: set[str] = {"manual-invocation-required"}


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
    if "generated_staleness_watch" in selected:
        observations.extend(
            _limit(
                _collect_generated_staleness(workspace, registry),
                max_observations_per_producer,
            )
        )
    if "technique_intake_watch" in selected:
        observations.extend(
            _limit(
                _collect_technique_intake(workspace, registry),
                max_observations_per_producer,
            )
        )
    if "technique_readiness_watch" in selected:
        observations.extend(
            _limit(
                _collect_technique_readiness(workspace, registry),
                max_observations_per_producer,
            )
        )
    if "skill_trigger_surface_watch" in selected:
        observations.extend(
            _limit(
                _collect_skill_trigger_surface(workspace, registry),
                max_observations_per_producer,
            )
        )
    if "runtime_evidence_selection_watch" in selected:
        observations.extend(
            _limit(
                _collect_runtime_evidence_selection(workspace, registry),
                max_observations_per_producer,
            )
        )
    if "playbook_harvest_watch" in selected:
        observations.extend(
            _limit(
                _collect_playbook_harvest(workspace, registry),
                max_observations_per_producer,
            )
        )
    if "recurrence_event_repetition_watch" in selected:
        observations.extend(
            _limit(
                _collect_recurrence_event_repetition(workspace, registry),
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


def _collect_generated_staleness(
    workspace: Workspace, registry: RecurrenceRegistry
) -> list[ObservationRecord]:
    producer = "generated_staleness_watch"
    observations: list[ObservationRecord] = []
    counter = 0
    for loaded in registry.iter_components():
        component = loaded.component
        repo_root = _repo_root(workspace, component.owner_repo)
        if repo_root is None or not component.generated_surfaces:
            continue
        sources = _glob(
            repo_root,
            [
                *component.source_inputs,
                *component.contract_surfaces,
                *component.documentation_surfaces,
            ],
        )
        generated = _glob(repo_root, component.generated_surfaces)
        if not sources or not generated:
            continue
        newest_source = max(sources, key=lambda path: path.stat().st_mtime)
        for generated_path in generated:
            if newest_source.stat().st_mtime <= generated_path.stat().st_mtime:
                continue
            counter += 1
            observations.append(
                _obs(
                    producer=producer,
                    counter=counter,
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    category="change_pressure",
                    signal="generated_surface_stale",
                    source_inputs=["generated-staleness", "change_signal"],
                    evidence_refs=[
                        _evidence(
                            component.owner_repo,
                            repo_root,
                            newest_source,
                            "#newer-source",
                        ),
                        _evidence(
                            component.owner_repo,
                            repo_root,
                            generated_path,
                            "#stale-generated",
                        ),
                    ],
                    attributes={
                        "source_path": _rel(repo_root, newest_source),
                        "generated_path": _rel(repo_root, generated_path),
                        "source_mtime": newest_source.stat().st_mtime,
                        "generated_mtime": generated_path.stat().st_mtime,
                    },
                    notes="source/contract/docs surface is newer than a generated surface; review regeneration before downstream projection",
                )
            )
    return observations


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
                "latest graduation wave",
                "evidence_pressure",
                "canonical_graduation_seen",
                "graduation wave evidence is visible",
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
            "fallback",
            "fallback_pattern_repeated",
            "repeat_pattern",
            "fallback pattern repeated; scenario may need playbook boundary",
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
