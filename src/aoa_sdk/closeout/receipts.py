from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
import json

from ..models import CloseoutManifest, ProjectCoreSkillKernelSurface
from .publishers import EVENT_KIND_TO_PUBLISHER


def _collect_receipt_paths(
    self,
    *,
    receipt_paths: Sequence[str | Path],
    receipt_dirs: Sequence[str | Path],
) -> list[Path]:
    collected: list[Path] = []
    for item in receipt_paths:
        path = Path(item).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"missing closeout input: {path}")
        if not path.is_file():
            raise ValueError(f"receipt path must be a file: {path}")
        collected.append(path)
    for item in receipt_dirs:
        directory = Path(item).expanduser().resolve()
        if not directory.exists():
            raise FileNotFoundError(f"missing closeout receipt directory: {directory}")
        if not directory.is_dir():
            raise ValueError(f"receipt directory must be a directory: {directory}")
        for candidate in sorted(directory.iterdir()):
            if candidate.is_file() and candidate.suffix in {".json", ".jsonl"}:
                collected.append(candidate)
    return self._unique_paths(collected)

def _publisher_for_receipt_path(
    self,
    receipt_path: Path,
    *,
    expected_session_ref: str | None = None,
) -> str:
    publisher: str | None = None
    detected_session_ref: str | None = None
    for receipt in self._load_receipt_file(receipt_path):
        event_kind = receipt.get("event_kind")
        if not isinstance(event_kind, str) or not event_kind:
            raise ValueError(f"{receipt_path}: receipt is missing a non-empty event_kind")
        session_ref = receipt.get("session_ref")
        if not isinstance(session_ref, str) or not session_ref:
            raise ValueError(f"{receipt_path}: receipt is missing a non-empty session_ref")
        if detected_session_ref is None:
            detected_session_ref = session_ref
        elif session_ref != detected_session_ref:
            raise ValueError(
                f"{receipt_path}: mixed session_ref values are not supported in one receipt file"
            )
        if expected_session_ref is not None and session_ref != expected_session_ref:
            raise ValueError(
                f"{receipt_path}: receipt session_ref {session_ref!r} does not match expected "
                f"{expected_session_ref!r}"
            )
        detected = EVENT_KIND_TO_PUBLISHER.get(event_kind)
        if detected is None:
            raise ValueError(f"{receipt_path}: unsupported closeout receipt kind {event_kind!r}")
        if publisher is None:
            publisher = detected
            continue
        if publisher != detected:
            raise ValueError(
                f"{receipt_path}: mixed publisher families are not supported in one receipt file"
            )
    if publisher is None:
        raise ValueError(f"{receipt_path}: receipt file does not contain any receipts")
    return publisher

def _load_receipt_file(self, path: Path) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    if path.suffix == ".jsonl":
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: receipt must be an object")
            receipts.append(item)
        return receipts
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return [payload]
    if not isinstance(payload, list):
        raise ValueError(f"{path}: receipt payload must be an object or list")
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path}[{index}]: receipt must be an object")
        receipts.append(item)
    return receipts

def _resolve_receipt_evidence_paths(
    self,
    *,
    manifest_path: Path,
    evidence_refs: Any,
    preferred_kinds: set[str] | None = None,
) -> list[Path]:
    resolved: list[Path] = []
    for item in evidence_refs if isinstance(evidence_refs, list) else []:
        kind: str | None = None
        ref: str | None = None
        if isinstance(item, dict):
            kind_value = item.get("kind")
            ref_value = item.get("ref")
            kind = kind_value if isinstance(kind_value, str) and kind_value else None
            ref = ref_value if isinstance(ref_value, str) and ref_value else None
        elif isinstance(item, str) and item:
            ref = item
        if ref is None:
            continue
        if preferred_kinds is not None and kind is not None and kind not in preferred_kinds:
            continue
        path = self._resolve_evidence_path(manifest_path, ref)
        if path is not None:
            resolved.append(path)
    return self._unique_paths(resolved)

def _extract_evidence_ref_strings(self, evidence_refs: Any) -> list[str]:
    values: list[str] = []
    for item in evidence_refs if isinstance(evidence_refs, list) else []:
        if isinstance(item, dict):
            ref = item.get("ref")
            if isinstance(ref, str) and ref:
                values.append(ref)
        elif isinstance(item, str) and item:
            values.append(item)
    return self._unique_strings(values)

def _resolve_evidence_path(self, manifest_path: Path, ref: str) -> Path | None:
    raw = Path(ref).expanduser()
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw.resolve())
    else:
        candidates.append((manifest_path.parent / raw).resolve())
        candidates.append((self.workspace.root / raw).resolve())
        if raw.parts and raw.parts[0] == "tmp":
            candidates.append((Path("/") / raw).resolve())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None

def _load_kernel_receipt_batches(
    self,
    *,
    manifest_path: Path,
    manifest: CloseoutManifest,
    kernel: ProjectCoreSkillKernelSurface,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    detail_receipts: list[dict[str, Any]] = []
    core_receipts: list[dict[str, Any]] = []
    for batch in manifest.batches:
        resolved_paths = self._resolve_input_paths(manifest_path, batch.input_paths)
        loaded_receipts: list[dict[str, Any]] = []
        for path in resolved_paths:
            loaded_receipts.extend(self._load_receipt_file(path))
        if batch.publisher == kernel.governance_contract.detail_publisher:
            detail_receipts.extend(loaded_receipts)
        elif batch.publisher == kernel.governance_contract.core_publisher:
            core_receipts.extend(loaded_receipts)
    return detail_receipts, core_receipts
