"""Read-only checkpoint bridge into the AoA session-memory archive."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from ..contracts.checkpoints import (
    CheckpointSessionMemoryFreshness,
    CheckpointSessionMemoryRef,
    CheckpointSessionMemoryRouteSignalSummary,
)
from ..loaders import load_json
from ..workspace.discovery import Workspace

SESSION_MEMORY_ROOT_ENV = "AOA_SESSION_MEMORY_ROOT"
ROUTE_SIGNAL_TOP_KEY_LIMIT = 8


def resolve_checkpoint_session_memory(
    *,
    workspace: Workspace,
    session_trace_thread_id: str | None,
    session_trace_ref: str | None,
) -> tuple[CheckpointSessionMemoryRef | None, CheckpointSessionMemoryFreshness]:
    checked_at = datetime.now(UTC)
    aoa_root = _first_existing_aoa_root(workspace)
    if aoa_root is None:
        return None, CheckpointSessionMemoryFreshness(
            status="unavailable",
            checked_at=checked_at,
            cautions=["no aoa-session-memory root was found for this workspace"],
        )

    session_path = _find_session_archive_path(
        aoa_root=aoa_root,
        session_trace_thread_id=session_trace_thread_id,
        session_trace_ref=session_trace_ref,
    )
    if session_path is None:
        return None, CheckpointSessionMemoryFreshness(
            status="missing",
            checked_at=checked_at,
            cautions=[
                "no aoa-session-memory archive matched the active Codex thread or rollout trace"
            ],
        )

    manifest_path = session_path / "session.manifest.json"
    index_path = session_path / "session.index.json"
    manifest = _load_json_object(manifest_path)
    session_index = _load_json_object(index_path)
    raw_path = _raw_path_from_manifest(manifest, aoa_root=aoa_root)
    raw_blocks_index_path = _raw_blocks_index_path_from_manifest(manifest, aoa_root=aoa_root)

    local_manifest_status: Literal["current", "missing", "not_checked"] = (
        "current" if manifest is not None else "missing"
    )
    local_index_status: Literal["current", "missing", "not_checked"] = (
        "current" if session_index is not None else "missing"
    )
    local_raw_status: Literal["current", "missing", "not_checked"] = (
        "current" if raw_path is not None and raw_path.exists() else "missing"
    )
    status: Literal["current", "partial", "missing", "unavailable"] = "current"
    if local_manifest_status == "missing":
        status = "partial"
    elif local_index_status == "missing" or local_raw_status == "missing":
        status = "partial"

    cautions = [
        "global session-memory search, atlas, and graph freshness are not checked by aoa-sdk; use aoa-session-memory freshness gates before global retrieval synthesis"
    ]
    if status != "current":
        cautions.append("session-local aoa-session-memory archive refs are incomplete")

    source_payload = _dict_value(manifest, "source")
    display_payload = _dict_value(manifest, "display")
    session_id = _string_value(manifest, "session_id") or _safe_unknown_session_id(session_path)
    session_label = _string_value(manifest, "session_label") or _string_value(display_payload, "label")
    session_title = _string_value(manifest, "session_title") or _string_value(display_payload, "title")
    route_signal_summary = _route_signal_summary(session_index)
    route_signal_layers = [summary.layer for summary in route_signal_summary]
    conversation_act_counts = _int_mapping(_dict_value(session_index, "conversation_act_counts"))
    session_act_counts = _int_mapping(_dict_value(session_index, "session_act_counts"))

    ref = CheckpointSessionMemoryRef(
        aoa_root=str(aoa_root),
        session_id=session_id,
        session_label=session_label,
        session_title=session_title,
        archive_path=str(session_path),
        manifest_ref=str(manifest_path),
        session_index_ref=str(index_path) if index_path.exists() else None,
        raw_ref=str(raw_path) if raw_path is not None else None,
        raw_blocks_index_ref=(
            str(raw_blocks_index_path) if raw_blocks_index_path is not None else None
        ),
        source_trace_ref=(
            _string_value(source_payload, "transcript_path") or session_trace_ref
        ),
        archive_status=_string_value(manifest, "archive_status"),
        distillation_status=_string_value(manifest, "distillation_status"),
        review_status=_string_value(manifest, "review_status"),
        event_count=_int_value(session_index, "event_count")
        or _int_value(manifest, "event_count")
        or _int_value(_dict_value(manifest, "raw"), "line_count"),
        segment_count=_segment_count(manifest, session_index),
        updated_at=_string_value(session_index, "updated_at")
        or _string_value(manifest, "updated_at"),
        work_context=_dict_value(session_index, "work_context") or _dict_value(manifest, "work_context"),
        conversation_act_counts=conversation_act_counts,
        session_act_counts=session_act_counts,
        route_signal_layers=route_signal_layers,
        route_signal_summary=route_signal_summary,
        evidence_refs=_dedupe_strings(
            [
                str(manifest_path),
                *(str(index_path) if index_path.exists() else None,),
                *(str(raw_path) if raw_path is not None else None,),
                *(str(raw_blocks_index_path) if raw_blocks_index_path is not None else None,),
            ]
        ),
        cautions=cautions,
    )
    freshness = CheckpointSessionMemoryFreshness(
        status=status,
        local_manifest_status=local_manifest_status,
        local_session_index_status=local_index_status,
        local_raw_status=local_raw_status,
        checked_at=checked_at,
        cautions=cautions,
    )
    return ref, freshness


def resolve_checkpoint_session_memory_for_runtime_session(
    *,
    workspace: Workspace,
    runtime_session_id: str | None,
) -> tuple[CheckpointSessionMemoryRef | None, CheckpointSessionMemoryFreshness]:
    checked_at = datetime.now(UTC)
    if not isinstance(runtime_session_id, str) or not runtime_session_id.strip():
        return None, CheckpointSessionMemoryFreshness(
            status="missing",
            checked_at=checked_at,
            cautions=["checkpoint runtime session id is missing"],
        )

    runtime_session_ref = _runtime_session_ref_for_id(
        workspace=workspace,
        runtime_session_id=runtime_session_id,
    )
    if runtime_session_ref is None:
        return None, CheckpointSessionMemoryFreshness(
            status="missing",
            checked_at=checked_at,
            cautions=[
                "no aoa-sdk skill runtime session file matched this checkpoint runtime session"
            ],
        )

    ref, freshness = resolve_checkpoint_session_memory(
        workspace=workspace,
        session_trace_thread_id=_string_value(runtime_session_ref.payload, "codex_thread_id"),
        session_trace_ref=_string_value(runtime_session_ref.payload, "codex_rollout_path"),
    )
    if ref is not None:
        ref = ref.model_copy(
            update={
                "evidence_refs": _dedupe_strings(
                    [*ref.evidence_refs, str(runtime_session_ref.path)]
                )
            }
        )
    return ref, freshness


def session_memory_evidence_from_ref(
    ref: CheckpointSessionMemoryRef | None,
) -> dict[str, object] | None:
    if ref is None:
        return None
    route_parts = []
    for summary in ref.route_signal_summary:
        top_keys = " ".join(
            f"{key}:{count}" for key, count in summary.top_keys.items()
        )
        route_parts.append(f"{summary.layer}:{summary.signal_count} {top_keys}".strip())
    text = "\n".join(
        [
            "session_memory_ref",
            f"session_id: {ref.session_id}",
            f"session_label: {ref.session_label or ''}",
            f"archive_status: {ref.archive_status or ''}",
            f"distillation_status: {ref.distillation_status or ''}",
            f"review_status: {ref.review_status or ''}",
            f"work_context: {_compact_mapping_text(ref.work_context)}",
            f"conversation_acts: {_compact_mapping_text(ref.conversation_act_counts)}",
            f"session_acts: {_compact_mapping_text(ref.session_act_counts)}",
            "route_signals: " + " | ".join(route_parts),
            "authority_contract: archive indexes are route evidence, not reviewed truth",
        ]
    )
    tokens = set(re.findall(r"[a-z0-9_:-]+", text.lower()))
    return {
        "text": text,
        "payload": ref.model_dump(mode="json"),
        "ref": ref.archive_path,
        "refs": list(ref.evidence_refs),
        "tokens": tokens,
    }


def _first_existing_aoa_root(workspace: Workspace) -> Path | None:
    for candidate in _candidate_aoa_roots(workspace):
        if _looks_like_session_memory_root(candidate):
            return candidate
    return None


def _candidate_aoa_roots(workspace: Workspace) -> list[Path]:
    candidates: list[Path] = []
    env_root = os.environ.get(SESSION_MEMORY_ROOT_ENV)
    if isinstance(env_root, str) and env_root.strip():
        candidates.append(Path(env_root).expanduser().resolve(strict=False))
    candidates.append((workspace.federation_root / ".aoa").resolve(strict=False))
    candidates.append((workspace.root / ".aoa").resolve(strict=False))
    if workspace.has_repo("aoa-sdk"):
        candidates.append((workspace.repo_path("aoa-sdk").parent / ".aoa").resolve(strict=False))
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


class _RuntimeSessionRef:
    def __init__(self, *, path: Path, payload: dict[str, Any]) -> None:
        self.path = path
        self.payload = payload


def _runtime_session_ref_for_id(
    *,
    workspace: Workspace,
    runtime_session_id: str,
) -> _RuntimeSessionRef | None:
    if not workspace.has_repo("aoa-sdk"):
        return None
    aoa_root = workspace.repo_path("aoa-sdk") / ".aoa"
    candidate_paths: list[Path] = []
    session_root = aoa_root / "skill-runtime-sessions"
    if session_root.is_dir():
        candidate_paths.extend(sorted(session_root.glob("*.json")))
    if aoa_root.is_dir():
        candidate_paths.extend(sorted(aoa_root.glob("*.json")))
    for path in candidate_paths:
        payload = _load_json_object(path)
        if payload is None:
            continue
        if _string_value(payload, "session_id") == runtime_session_id:
            return _RuntimeSessionRef(path=path, payload=payload)
    return None


def _looks_like_session_memory_root(path: Path) -> bool:
    return path.is_dir() and (
        (path / "session-registry.json").exists()
        or (path / "sessions").is_dir()
    )


def _find_session_archive_path(
    *,
    aoa_root: Path,
    session_trace_thread_id: str | None,
    session_trace_ref: str | None,
) -> Path | None:
    registry_path = aoa_root / "session-registry.json"
    if registry_path.exists():
        registry_payload = _load_json_payload(registry_path)
        for entry in _registry_entries(registry_payload):
            if not _entry_matches_trace(
                entry,
                session_trace_thread_id=session_trace_thread_id,
                session_trace_ref=session_trace_ref,
            ):
                continue
            archive_path = _entry_archive_path(entry, aoa_root=aoa_root)
            if archive_path is not None:
                return archive_path

    sessions_root = aoa_root / "sessions"
    if not sessions_root.is_dir():
        return None
    for manifest_path in sorted(sessions_root.glob("*/session.manifest.json")):
        manifest = _load_json_object(manifest_path)
        if manifest is None:
            continue
        if _entry_matches_trace(
            manifest,
            session_trace_thread_id=session_trace_thread_id,
            session_trace_ref=session_trace_ref,
        ):
            return manifest_path.parent.resolve(strict=False)
    return None


def _entry_matches_trace(
    entry: dict[str, Any],
    *,
    session_trace_thread_id: str | None,
    session_trace_ref: str | None,
) -> bool:
    thread_id = session_trace_thread_id.strip() if isinstance(session_trace_thread_id, str) else ""
    trace_ref = session_trace_ref.strip() if isinstance(session_trace_ref, str) else ""
    if thread_id:
        if _string_value(entry, "session_id") == thread_id:
            return True
        for value in _candidate_trace_strings(entry):
            if thread_id in value:
                return True
    if trace_ref:
        trace_path = Path(trace_ref).expanduser().resolve(strict=False).as_posix()
        for value in _candidate_trace_strings(entry):
            candidate = Path(value).expanduser().resolve(strict=False).as_posix()
            if candidate == trace_path:
                return True
    return False


def _candidate_trace_strings(entry: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("transcript_path", "source_path", "path", "navigation_path"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    for parent_key in ("source", "raw", "display"):
        nested = entry.get(parent_key)
        if not isinstance(nested, dict):
            continue
        for key in ("transcript_path", "source_path", "path", "archive_path", "navigation_path"):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                values.append(value.strip())
    return values


def _entry_archive_path(entry: dict[str, Any], *, aoa_root: Path) -> Path | None:
    display = _dict_value(entry, "display")
    for value in (
        entry.get("path"),
        entry.get("navigation_path"),
        display.get("path"),
        display.get("archive_path"),
        display.get("navigation_path"),
    ):
        if isinstance(value, str) and value.strip():
            return _resolve_aoa_path(value, aoa_root=aoa_root)
    label = _string_value(entry, "session_label") or _string_value(display, "label")
    if label:
        return (aoa_root / "sessions" / label).resolve(strict=False)
    return None


def _resolve_aoa_path(value: str, *, aoa_root: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = aoa_root / path
    return path.resolve(strict=False)


def _raw_path_from_manifest(manifest: dict[str, Any] | None, *, aoa_root: Path) -> Path | None:
    raw = _dict_value(manifest, "raw")
    raw_path = _string_value(raw, "path")
    return _resolve_aoa_path(raw_path, aoa_root=aoa_root) if raw_path else None


def _raw_blocks_index_path_from_manifest(
    manifest: dict[str, Any] | None,
    *,
    aoa_root: Path,
) -> Path | None:
    raw_blocks = _dict_value(manifest, "raw_blocks")
    index_path = _string_value(raw_blocks, "index")
    if index_path:
        return _resolve_aoa_path(index_path, aoa_root=aoa_root)
    raw = _dict_value(manifest, "raw")
    raw_index_path = _string_value(raw, "blocks_index")
    return _resolve_aoa_path(raw_index_path, aoa_root=aoa_root) if raw_index_path else None


def _route_signal_summary(
    session_index: dict[str, Any] | None,
) -> list[CheckpointSessionMemoryRouteSignalSummary]:
    route_signal_counts = _dict_value(session_index, "route_signal_counts")
    summaries: list[CheckpointSessionMemoryRouteSignalSummary] = []
    for layer, raw_counts in sorted(route_signal_counts.items()):
        if not isinstance(layer, str) or not isinstance(raw_counts, dict):
            continue
        counts = _int_mapping(raw_counts)
        top_keys = dict(
            sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
                :ROUTE_SIGNAL_TOP_KEY_LIMIT
            ]
        )
        summaries.append(
            CheckpointSessionMemoryRouteSignalSummary(
                layer=layer,
                signal_count=sum(counts.values()),
                top_keys=top_keys,
            )
        )
    return summaries


def _segment_count(
    manifest: dict[str, Any] | None,
    session_index: dict[str, Any] | None,
) -> int | None:
    value = _int_value(session_index, "segment_count") or _int_value(manifest, "segment_count")
    if value is not None:
        return value
    segments = manifest.get("segments") if isinstance(manifest, dict) else None
    return len(segments) if isinstance(segments, list) else None


def _registry_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]
    if isinstance(payload, dict):
        for key in ("sessions", "entries", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [entry for entry in value if isinstance(entry, dict)]
    return []


def _load_json_payload(path: Path) -> Any:
    try:
        return load_json(path)
    except Exception:
        return None


def _load_json_object(path: Path) -> dict[str, Any] | None:
    payload = _load_json_payload(path)
    return payload if isinstance(payload, dict) else None


def _dict_value(payload: dict[str, Any] | None, key: str) -> dict[str, Any]:
    value = payload.get(key) if isinstance(payload, dict) else None
    return value if isinstance(value, dict) else {}


def _string_value(payload: dict[str, Any] | None, key: str) -> str | None:
    value = payload.get(key) if isinstance(payload, dict) else None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _int_value(payload: dict[str, Any] | None, key: str) -> int | None:
    value = payload.get(key) if isinstance(payload, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _int_mapping(payload: dict[str, Any]) -> dict[str, int]:
    return {
        key: value
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, int) and not isinstance(value, bool)
    }


def _dedupe_strings(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        stripped = value.strip()
        if stripped in seen:
            continue
        seen.add(stripped)
        result.append(stripped)
    return result


def _safe_unknown_session_id(session_path: Path) -> str:
    return f"unknown:{session_path.name}"


def _compact_mapping_text(mapping: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in sorted(mapping.items())[:ROUTE_SIGNAL_TOP_KEY_LIMIT]:
        if isinstance(value, dict):
            parts.append(f"{key}=dict")
        elif isinstance(value, list):
            parts.append(f"{key}=list:{len(value)}")
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)
