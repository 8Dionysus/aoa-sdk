from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..workspace.discovery import Workspace
from .hook_registry import HookRegistry, load_hook_registry
from .models import (
    ChangeSignal,
    HookBinding,
    HookEvent,
    HookRunReport,
    HookRunWarning,
    HookSignalRule,
    ObservationCategory,
    ObservationRecord,
)
from .observations import _dedupe_and_sort
from .registry import RecurrenceRegistry, load_registry, normalize_path


DEFAULT_RUNTIME_OVERCLAIM_PHRASES: tuple[str, ...] = (
    " is the best",
    " proves general reasoning growth",
    " proves better agent quality",
    " is smarter",
)


def list_hook_bindings(
    workspace: Workspace,
    *,
    event: HookEvent | None = None,
    registry: HookRegistry | None = None,
) -> list[HookBinding]:
    registry = registry or load_hook_registry(workspace)
    return sorted(
        list(registry.iter_bindings(event=event)),
        key=lambda binding: (binding.owner_repo, binding.component_ref, binding.event, binding.binding_ref),
    )


def build_hook_run_report(
    workspace: Workspace,
    *,
    event: HookEvent,
    signal: ChangeSignal | None = None,
    registry: HookRegistry | None = None,
    recurrence_registry: RecurrenceRegistry | None = None,
    binding_refs: list[str] | None = None,
) -> HookRunReport:
    registry = registry or load_hook_registry(workspace)
    recurrence_registry = recurrence_registry or load_registry(workspace)

    selected = list(list_hook_bindings(workspace, event=event, registry=registry))
    if binding_refs:
        allowed = set(binding_refs)
        selected = [binding for binding in selected if binding.binding_ref in allowed]

    observations: list[ObservationRecord] = []
    missing_paths: list[str] = []
    warnings: list[HookRunWarning] = []

    for binding in selected:
        if recurrence_registry.get(binding.component_ref) is None:
            warnings.append(
                HookRunWarning(
                    binding_ref=binding.binding_ref,
                    message="binding component_ref is not present in the recurrence registry",
                    paths=[],
                )
            )
        produced, missing, binding_warnings = _run_binding(
            workspace,
            binding=binding,
            signal=signal,
        )
        observations.extend(produced)
        missing_paths.extend(missing)
        warnings.extend(binding_warnings)

    observations = _dedupe_and_sort(observations)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return HookRunReport(
        run_ref=f"hooks:{event}:{stamp}",
        workspace_root=str(workspace.federation_root),
        event=event,
        signal_ref=signal.signal_ref if signal is not None else None,
        bindings_run=[binding.binding_ref for binding in selected],
        missing_paths=sorted(set(missing_paths)),
        warnings=warnings,
        observations=observations,
    )


def _run_binding(
    workspace: Workspace,
    *,
    binding: HookBinding,
    signal: ChangeSignal | None,
) -> tuple[list[ObservationRecord], list[str], list[HookRunWarning]]:
    repo_root = workspace.repo_roots.get(binding.owner_repo)
    if repo_root is None:
        return (
            [],
            [],
            [
                HookRunWarning(
                    binding_ref=binding.binding_ref,
                    message=f"owner repo {binding.owner_repo!r} is not present in the workspace",
                    paths=[],
                )
            ],
        )

    match binding.producer:
        case "jsonl_receipt_watch":
            return _run_jsonl_receipt_watch(repo_root, binding=binding)
        case "skill_trigger_gap_watch":
            return _run_skill_trigger_gap_watch(repo_root, binding=binding)
        case "harvest_pattern_watch":
            return _run_harvest_pattern_watch(repo_root, binding=binding)
        case "runtime_candidate_watch":
            return _run_runtime_candidate_watch(repo_root, binding=binding)
        case _:
            return (
                [],
                [],
                [
                    HookRunWarning(
                        binding_ref=binding.binding_ref,
                        message=f"unsupported producer {binding.producer!r}",
                        paths=[],
                    )
                ],
            )


def _run_jsonl_receipt_watch(
    repo_root: Path,
    *,
    binding: HookBinding,
) -> tuple[list[ObservationRecord], list[str], list[HookRunWarning]]:
    files, missing = _resolve_paths(repo_root, binding.path_globs)
    warnings: list[HookRunWarning] = []
    observations: list[ObservationRecord] = []
    counter = 0

    for file_path in files:
        try:
            records = _read_jsonl_records(file_path)
        except Exception as exc:  # pragma: no cover - defensive seed path
            warnings.append(
                HookRunWarning(
                    binding_ref=binding.binding_ref,
                    message=f"failed to parse JSONL receipt file: {exc}",
                    paths=[_relative_path(repo_root, file_path)],
                )
            )
            continue

        record_id_field = str(binding.config.get("record_id_field") or "receipt_ref")
        for index, record in enumerate(records, start=1):
            record_id = _string_or_none(_get_field(record, record_id_field)) or f"line-{index}"
            for rule in binding.signal_rules:
                if not _rule_matches_record(record, rule):
                    continue
                counter += 1
                observations.append(
                    _make_observation(
                        binding=binding,
                        signal=rule.signal,
                        category=rule.category,
                        source_inputs=[binding.input_ref, *rule.source_inputs],
                        evidence_refs=[f"{binding.owner_repo}:{_relative_path(repo_root, file_path)}#{record_id}"],
                        attributes=_extract_attributes(record, rule.attributes_from_fields)
                        | {
                            "binding_ref": binding.binding_ref,
                            "producer": binding.producer,
                            "record_id": record_id,
                        },
                        notes=rule.notes or binding.notes or "emitted from JSONL receipt watch",
                        counter=counter,
                    )
                )
    return observations, missing, warnings


def _run_skill_trigger_gap_watch(
    repo_root: Path,
    *,
    binding: HookBinding,
) -> tuple[list[ObservationRecord], list[str], list[HookRunWarning]]:
    case_files, missing = _resolve_paths(repo_root, binding.path_globs)
    receipt_globs = [str(item) for item in binding.config.get("receipt_globs", [])]
    receipt_files, receipt_missing = _resolve_paths(repo_root, receipt_globs)
    missing.extend(receipt_missing)

    warnings: list[HookRunWarning] = []
    observations: list[ObservationRecord] = []
    counter = 0

    case_class_field = str(binding.config.get("case_class_field") or "case_class")
    skill_field = str(binding.config.get("skill_field") or "skill_name")
    record_id_field = str(binding.config.get("record_id_field") or "case_id")
    positive_values = {str(item) for item in binding.config.get("positive_case_values", ["should-trigger", "explicit-handle"])}
    prefer_other_values = {str(item) for item in binding.config.get("prefer_other_case_values", ["prefer-other-skill"])}
    manual_values = {str(item) for item in binding.config.get("manual_case_values", ["manual-invocation-required"])}
    receipt_skill_fields = [str(item) for item in binding.config.get("receipt_skill_fields", ["skill_name", "skill_ref", "skill_refs", "applied_skills", "applied_skill_refs"])]

    skill_case_refs: dict[str, list[str]] = defaultdict(list)
    skill_modes: dict[str, set[str]] = defaultdict(set)

    for file_path in case_files:
        try:
            records = _read_records_from_file(file_path)
        except Exception as exc:  # pragma: no cover - defensive seed path
            warnings.append(
                HookRunWarning(
                    binding_ref=binding.binding_ref,
                    message=f"failed to parse trigger case file: {exc}",
                    paths=[_relative_path(repo_root, file_path)],
                )
            )
            continue

        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue
            skill_name = _string_or_none(_get_field(record, skill_field))
            case_class = _string_or_none(_get_field(record, case_class_field))
            if not skill_name or not case_class:
                continue

            record_id = _string_or_none(_get_field(record, record_id_field)) or f"record-{index}"
            evidence_ref = f"{binding.owner_repo}:{_relative_path(repo_root, file_path)}#{record_id}"
            skill_case_refs[skill_name].append(evidence_ref)
            skill_modes[skill_name].add(case_class)

            if case_class in manual_values:
                counter += 1
                observations.append(
                    _make_observation(
                        binding=binding,
                        signal="manual_invocation_boundary_seen",
                        category="review_signal",
                        source_inputs=[binding.input_ref],
                        evidence_refs=[evidence_ref],
                        attributes={
                            "binding_ref": binding.binding_ref,
                            "producer": binding.producer,
                            "skill_name": skill_name,
                            "case_class": case_class,
                        },
                        notes="manual invocation remains an explicit boundary in the trigger suite",
                        counter=counter,
                    )
                )

    seen_skills: set[str] = set()
    for file_path in receipt_files:
        try:
            records = _read_records_from_file(file_path)
        except Exception as exc:  # pragma: no cover - defensive seed path
            warnings.append(
                HookRunWarning(
                    binding_ref=binding.binding_ref,
                    message=f"failed to parse skill receipt surface: {exc}",
                    paths=[_relative_path(repo_root, file_path)],
                )
            )
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            seen_skills.update(_extract_skill_names(record, receipt_skill_fields))

    for skill_name, case_modes in sorted(skill_modes.items()):
        evidence_refs = skill_case_refs.get(skill_name, [])
        if positive_values.intersection(case_modes) and skill_name not in seen_skills:
            counter += 1
            observations.append(
                _make_observation(
                    binding=binding,
                    signal="should_trigger_missing",
                    category="usage_gap",
                    source_inputs=[binding.input_ref, "skill-live-receipts"],
                    evidence_refs=evidence_refs[:3],
                    attributes={
                        "binding_ref": binding.binding_ref,
                        "producer": binding.producer,
                        "skill_name": skill_name,
                    },
                    notes="trigger suite suggests this skill should fire, but no recent skill evidence was seen",
                    counter=counter,
                )
            )
        if prefer_other_values.intersection(case_modes) and skill_name not in seen_skills:
            counter += 1
            observations.append(
                _make_observation(
                    binding=binding,
                    signal="prefer_other_skill_gap",
                    category="usage_gap",
                    source_inputs=[binding.input_ref, "skill-live-receipts"],
                    evidence_refs=evidence_refs[:3],
                    attributes={
                        "binding_ref": binding.binding_ref,
                        "producer": binding.producer,
                        "skill_name": skill_name,
                    },
                    notes="trigger suite shows neighboring-skill pressure, but no confirming skill evidence was seen",
                    counter=counter,
                )
            )
    return observations, missing, warnings


def _run_harvest_pattern_watch(
    repo_root: Path,
    *,
    binding: HookBinding,
) -> tuple[list[ObservationRecord], list[str], list[HookRunWarning]]:
    files, missing = _resolve_paths(repo_root, binding.path_globs)
    warnings: list[HookRunWarning] = []
    observations: list[ObservationRecord] = []
    counter = 0

    phrase_rules = list(binding.config.get("phrase_signals", []))
    json_rules = list(binding.config.get("json_field_signals", []))
    record_id_field = str(binding.config.get("record_id_field") or "record_ref")

    for file_path in files:
        relative = _relative_path(repo_root, file_path)
        suffix = file_path.suffix.lower()

        if suffix in {".json", ".jsonl"}:
            try:
                records = _read_records_from_file(file_path)
            except Exception as exc:  # pragma: no cover - defensive seed path
                warnings.append(
                    HookRunWarning(
                        binding_ref=binding.binding_ref,
                        message=f"failed to parse harvest pattern file: {exc}",
                        paths=[relative],
                    )
                )
                continue

            for index, record in enumerate(records, start=1):
                if not isinstance(record, dict):
                    continue
                record_id = _string_or_none(_get_field(record, record_id_field)) or f"record-{index}"
                for rule in json_rules:
                    signal_rule = HookSignalRule.model_validate(rule)
                    if not _rule_matches_record(record, signal_rule):
                        continue
                    counter += 1
                    observations.append(
                        _make_observation(
                            binding=binding,
                            signal=signal_rule.signal,
                            category=signal_rule.category,
                            source_inputs=[binding.input_ref, *signal_rule.source_inputs],
                            evidence_refs=[f"{binding.owner_repo}:{relative}#{record_id}"],
                            attributes=_extract_attributes(record, signal_rule.attributes_from_fields)
                            | {
                                "binding_ref": binding.binding_ref,
                                "producer": binding.producer,
                                "record_id": record_id,
                            },
                            notes=signal_rule.notes or binding.notes or "emitted from harvest pattern watch",
                            counter=counter,
                        )
                    )
            continue

        text = file_path.read_text(encoding="utf-8").lower()
        for rule in phrase_rules:
            signal = str(rule["signal"])
            category = str(rule["category"])
            phrases = [str(item).lower() for item in rule.get("phrases", [])]
            mode = str(rule.get("mode", "any"))
            source_inputs = [binding.input_ref, *[str(item) for item in rule.get("source_inputs", [])]]
            if not phrases:
                continue
            matched = all(phrase in text for phrase in phrases) if mode == "all" else any(
                phrase in text for phrase in phrases
            )
            if not matched:
                continue
            counter += 1
            observations.append(
                _make_observation(
                    binding=binding,
                    signal=signal,
                    category=category,  # type: ignore[arg-type]
                    source_inputs=source_inputs,
                    evidence_refs=[f"{binding.owner_repo}:{relative}"],
                    attributes={
                        "binding_ref": binding.binding_ref,
                        "producer": binding.producer,
                        "phrases": phrases,
                    },
                    notes=str(rule.get("notes") or binding.notes or "emitted from harvest phrase watch"),
                    counter=counter,
                )
            )
    return observations, missing, warnings


def _run_runtime_candidate_watch(
    repo_root: Path,
    *,
    binding: HookBinding,
) -> tuple[list[ObservationRecord], list[str], list[HookRunWarning]]:
    files, missing = _resolve_paths(repo_root, binding.path_globs)
    warnings: list[HookRunWarning] = []
    observations: list[ObservationRecord] = []
    counter = 0

    claim_fields = [str(item) for item in binding.config.get("claim_fields", ["claim_family", "claim", "bounded_claim"])]
    candidate_class_field = str(binding.config.get("candidate_class_field") or "target_class")
    candidate_class_values = {str(item) for item in binding.config.get("candidate_class_values", ["bundle-candidate", "evidence-sidecar"])}
    evidence_fields = [str(item) for item in binding.config.get("evidence_fields", ["selected_evidence", "evidence_refs", "trace_refs"])]
    record_id_field = str(binding.config.get("record_id_field") or "artifact_ref")
    overclaim_phrases = tuple(
        str(item).lower()
        for item in binding.config.get("overclaim_phrases", list(DEFAULT_RUNTIME_OVERCLAIM_PHRASES))
    )

    claim_buckets: dict[str, list[str]] = defaultdict(list)

    for file_path in files:
        relative = _relative_path(repo_root, file_path)
        suffix = file_path.suffix.lower()

        if suffix in {".json", ".jsonl"}:
            try:
                records = _read_records_from_file(file_path)
            except Exception as exc:  # pragma: no cover - defensive seed path
                warnings.append(
                    HookRunWarning(
                        binding_ref=binding.binding_ref,
                        message=f"failed to parse runtime candidate file: {exc}",
                        paths=[relative],
                    )
                )
                continue

            for index, record in enumerate(records, start=1):
                if not isinstance(record, dict):
                    continue
                record_id = _string_or_none(_get_field(record, record_id_field)) or f"record-{index}"
                evidence_ref = f"{binding.owner_repo}:{relative}#{record_id}"

                claim_text = ""
                for field_name in claim_fields:
                    value = _get_field(record, field_name)
                    if value is not None:
                        claim_text = str(value).strip()
                        break
                if claim_text:
                    claim_buckets[_normalize_claim(claim_text)].append(evidence_ref)

                if any(_field_has_value(record, field_name) for field_name in evidence_fields):
                    counter += 1
                    observations.append(
                        _make_observation(
                            binding=binding,
                            signal="trace_bridge_receipt_ready",
                            category="evidence_pressure",
                            source_inputs=[binding.input_ref],
                            evidence_refs=[evidence_ref],
                            attributes={
                                "binding_ref": binding.binding_ref,
                                "producer": binding.producer,
                            },
                            notes="runtime evidence looks selected enough to enter a bounded proof review",
                            counter=counter,
                        )
                    )

                candidate_class = _string_or_none(_get_field(record, candidate_class_field))
                if candidate_class in candidate_class_values:
                    counter += 1
                    observations.append(
                        _make_observation(
                            binding=binding,
                            signal="runtime_candidate_selected",
                            category="review_signal",
                            source_inputs=[binding.input_ref],
                            evidence_refs=[evidence_ref],
                            attributes={
                                "binding_ref": binding.binding_ref,
                                "producer": binding.producer,
                                "target_class": candidate_class,
                            },
                            notes="runtime artifact is marked as a bounded candidate rather than a local-only dump",
                            counter=counter,
                        )
                    )

                claim_lower = claim_text.lower()
                if claim_lower and any(phrase in claim_lower for phrase in overclaim_phrases):
                    counter += 1
                    observations.append(
                        _make_observation(
                            binding=binding,
                            signal="overclaim_detected",
                            category="overclaim_risk",
                            source_inputs=[binding.input_ref],
                            evidence_refs=[evidence_ref],
                            attributes={
                                "binding_ref": binding.binding_ref,
                                "producer": binding.producer,
                                "claim_text": claim_text,
                            },
                            notes="runtime claim crosses the bounded-proof line and should be reviewed for overclaim",
                            counter=counter,
                        )
                    )
            continue

        text = file_path.read_text(encoding="utf-8").lower()
        if any(phrase in text for phrase in overclaim_phrases):
            counter += 1
            observations.append(
                _make_observation(
                    binding=binding,
                    signal="overclaim_detected",
                    category="overclaim_risk",
                    source_inputs=[binding.input_ref],
                    evidence_refs=[f"{binding.owner_repo}:{relative}"],
                    attributes={
                        "binding_ref": binding.binding_ref,
                        "producer": binding.producer,
                    },
                    notes="runtime review text contains an overclaim phrase that should stay candidate-only",
                    counter=counter,
                )
            )

    for claim_key, evidence_refs in sorted(claim_buckets.items()):
        if not claim_key or len(evidence_refs) < 2:
            continue
        counter += 1
        observations.append(
            _make_observation(
                binding=binding,
                signal="portable_claim_repeat",
                category="repeat_pattern",
                source_inputs=[binding.input_ref],
                evidence_refs=evidence_refs[:6],
                attributes={
                    "binding_ref": binding.binding_ref,
                    "producer": binding.producer,
                    "claim_key": claim_key,
                    "repeat_count": len(evidence_refs),
                },
                notes="the same bounded runtime claim now appears in more than one artifact",
                counter=counter,
            )
        )
    return observations, missing, warnings


def _resolve_paths(repo_root: Path, patterns: Iterable[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing: list[str] = []
    seen: set[Path] = set()
    for pattern in patterns:
        matches = sorted(repo_root.glob(pattern))
        if not matches:
            missing.append(f"{repo_root.name}:{normalize_path(pattern)}")
            continue
        for match in matches:
            if match.is_file() and match not in seen:
                files.append(match)
                seen.add(match)
    return files, missing


def _read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _read_records_from_file(path: Path) -> list[Any]:
    if path.suffix.lower() == ".jsonl":
        return _read_jsonl_records(path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "items", "entries", "cases", "observations", "artifacts"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload]
    return []


def _relative_path(repo_root: Path, path: Path) -> str:
    return normalize_path(path.relative_to(repo_root))


def _make_observation(
    *,
    binding: HookBinding,
    signal: str,
    category: ObservationCategory,
    source_inputs: list[str],
    evidence_refs: list[str],
    attributes: dict[str, Any],
    notes: str,
    counter: int,
) -> ObservationRecord:
    return ObservationRecord(
        observation_ref=f"obs:hook:{binding.binding_ref}:{counter:04d}",
        component_ref=binding.component_ref,
        owner_repo=binding.owner_repo,
        observed_at=datetime.now(timezone.utc),
        category=category,
        signal=signal,
        source_inputs=sorted(set(source_inputs)),
        evidence_refs=evidence_refs,
        attributes=attributes,
        notes=notes,
    )


def _rule_matches_record(record: dict[str, Any], rule: HookSignalRule) -> bool:
    if rule.match == "always":
        return True
    if rule.field is None:
        return False
    value = _get_field(record, rule.field)
    if rule.match == "exists":
        return value is not None
    if rule.match == "equals":
        return value == rule.value
    if rule.match == "contains":
        if isinstance(value, list):
            return rule.value in value
        if isinstance(value, str) and rule.value is not None:
            return str(rule.value) in value
        return False
    return False


def _extract_attributes(record: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields:
        value = _get_field(record, field)
        if value is None:
            continue
        payload[field] = value
    return payload


def _extract_skill_names(record: dict[str, Any], fields: list[str]) -> set[str]:
    names: set[str] = set()
    for field in fields:
        value = _get_field(record, field)
        if value is None:
            continue
        if isinstance(value, str):
            names.add(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    names.add(item)
                elif isinstance(item, dict):
                    for key in ("skill_name", "skill_ref", "name", "ref"):
                        if isinstance(item.get(key), str):
                            names.add(item[key])
    return names


def _get_field(payload: Any, dotted: str) -> Any:
    current = payload
    for part in dotted.split("."):
        if isinstance(current, dict):
            current = current.get(part)
            continue
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return None
            if not (0 <= index < len(current)):
                return None
            current = current[index]
            continue
        return None
    return current


def _field_has_value(record: dict[str, Any], field_name: str) -> bool:
    value = _get_field(record, field_name)
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return True


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_claim(value: str) -> str:
    return " ".join(value.lower().split())
