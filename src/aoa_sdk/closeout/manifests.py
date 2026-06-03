from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from ..loaders import load_json, write_json
from ..models import (
    CloseoutBuildReport,
    CloseoutBuildRequest,
    CloseoutManifest,
    CloseoutPublisherBatch,
    CloseoutSubmitReviewedReport,
)
from .publishers import PUBLISHER_SPECS


def load_build_request(self, request_path: str | Path) -> CloseoutBuildRequest:
    path = Path(request_path).expanduser().resolve()
    request = CloseoutBuildRequest.model_validate(load_json(path))
    self._validate_build_request(request)
    return request

def submit_reviewed(
    self,
    reviewed_artifact_path: str | Path,
    *,
    session_ref: str,
    receipt_paths: Sequence[str | Path] | None = None,
    receipt_dirs: Sequence[str | Path] | None = None,
    closeout_id: str | None = None,
    audit_refs: Sequence[str | Path] | None = None,
    trigger: str = "reviewed-closeout",
    notes: str | None = None,
    request_dir: str | Path | None = None,
    manifest_dir: str | Path | None = None,
    inbox_dir: str | Path | None = None,
    enqueue: bool = True,
    overwrite: bool = False,
    allow_empty: bool = False,
) -> CloseoutSubmitReviewedReport:
    reviewed_artifact = Path(reviewed_artifact_path).expanduser().resolve()
    if not reviewed_artifact.exists():
        raise FileNotFoundError(f"missing reviewed artifact: {reviewed_artifact}")

    resolved_receipt_paths = self._collect_receipt_paths(
        receipt_paths=receipt_paths or [],
        receipt_dirs=receipt_dirs or [],
    )
    if not resolved_receipt_paths and not allow_empty:
        raise ValueError("submit-reviewed requires at least one receipt file")

    batches_by_publisher: dict[str, list[str]] = {}
    for receipt_path in resolved_receipt_paths:
        publisher = self._publisher_for_receipt_path(
            receipt_path,
            expected_session_ref=session_ref,
        )
        batches_by_publisher.setdefault(publisher, []).append(str(receipt_path))
    audit_only = not resolved_receipt_paths

    resolved_closeout_id = closeout_id or self._derive_closeout_id(session_ref)
    resolved_request_dir = self._resolve_queue_dir(request_dir, leaf="requests")
    resolved_request_dir.mkdir(parents=True, exist_ok=True)
    request_path = resolved_request_dir / f"{self._safe_closeout_filename(resolved_closeout_id)}.request.json"
    if request_path.exists() and not overwrite:
        raise FileExistsError(
            f"{request_path} already exists; rerun with overwrite=True to replace it"
        )

    build_request = CloseoutBuildRequest(
        schema_version=1,
        closeout_id=resolved_closeout_id,
        session_ref=session_ref,
        reviewed=True,
        audit_only=audit_only,
        reviewed_artifact_path=str(reviewed_artifact),
        trigger=trigger,
        batches=[
            CloseoutPublisherBatch(
                publisher=publisher,
                input_paths=paths,
            )
            for publisher, paths in sorted(batches_by_publisher.items())
        ],
        audit_refs=self._resolve_optional_paths(
            reviewed_artifact,
            [str(path) for path in (audit_refs or [])],
        ),
        notes=notes,
    )
    write_json(request_path, build_request.model_dump(mode="json"))
    build_report = self.build_manifest(
        request_path,
        manifest_dir=manifest_dir,
        enqueue=enqueue,
        inbox_dir=inbox_dir,
        overwrite=overwrite,
    )
    return CloseoutSubmitReviewedReport(
        schema_version=1,
        closeout_id=resolved_closeout_id,
        session_ref=session_ref,
        request_path=str(request_path),
        submitted_at=datetime.now(timezone.utc),
        reviewed_artifact_path=str(reviewed_artifact),
        audit_only=audit_only,
        receipt_paths=[str(path) for path in resolved_receipt_paths],
        detected_publishers=sorted(batches_by_publisher),
        build_report=build_report,
    )

def load_manifest(self, manifest_path: str | Path) -> CloseoutManifest:
    path = Path(manifest_path).expanduser().resolve()
    manifest = CloseoutManifest.model_validate(load_json(path))
    self._validate_manifest(manifest)
    return manifest

def build_manifest(
    self,
    request_path: str | Path,
    *,
    manifest_dir: str | Path | None = None,
    enqueue: bool = False,
    inbox_dir: str | Path | None = None,
    overwrite: bool = False,
) -> CloseoutBuildReport:
    resolved_request_path = Path(request_path).expanduser().resolve()
    request = self.load_build_request(resolved_request_path)
    reviewed_artifact_path = self._resolve_existing_path(
        resolved_request_path, request.reviewed_artifact_path
    )
    audit_refs = self._unique_strings(
        [
            str(reviewed_artifact_path),
            *self._resolve_optional_paths(resolved_request_path, request.audit_refs),
        ]
    )
    manifest = CloseoutManifest(
        schema_version=1,
        closeout_id=request.closeout_id,
        session_ref=request.session_ref,
        reviewed=True,
        audit_only=request.audit_only,
        trigger=request.trigger,
        batches=[
            batch.model_copy(
                update={
                    "input_paths": [
                        str(path)
                        for path in self._resolve_input_paths(
                            resolved_request_path, batch.input_paths
                        )
                    ]
                }
            )
            for batch in request.batches
        ],
        audit_refs=audit_refs,
        notes=request.notes,
    )

    resolved_manifest_dir = self._resolve_queue_dir(manifest_dir, leaf="manifests")
    resolved_manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = resolved_manifest_dir / f"{self._safe_closeout_filename(request.closeout_id)}.json"
    if manifest_path.exists() and not overwrite:
        raise FileExistsError(
            f"{manifest_path} already exists; rerun with overwrite=True to replace it"
        )
    write_json(manifest_path, manifest.model_dump(mode="json"))

    enqueue_report = None
    if enqueue:
        enqueue_report = self.enqueue(
            manifest_path,
            inbox_dir=inbox_dir,
            overwrite=overwrite,
        )

    return CloseoutBuildReport(
        schema_version=1,
        closeout_id=request.closeout_id,
        session_ref=request.session_ref,
        request_path=str(resolved_request_path),
        manifest_path=str(manifest_path),
        built_at=datetime.now(timezone.utc),
        reviewed_artifact_path=str(reviewed_artifact_path),
        audit_only=request.audit_only,
        enqueue_report=enqueue_report,
    )

def _validate_build_request(self, request: CloseoutBuildRequest) -> None:
    if request.schema_version != 1:
        raise ValueError(f"unsupported closeout build schema_version {request.schema_version!r}")
    if not request.closeout_id.strip():
        raise ValueError("closeout_id must be a non-empty string")
    if not request.session_ref.strip():
        raise ValueError("session_ref must be a non-empty string")
    if not request.reviewed:
        raise ValueError("closeout build requests must set reviewed=true before manifest assembly")
    if not request.reviewed_artifact_path.strip():
        raise ValueError("reviewed_artifact_path must be a non-empty string")
    if not request.trigger.strip():
        raise ValueError("trigger must be a non-empty string")
    if not request.audit_only and not request.batches:
        raise ValueError("closeout build request must include at least one publisher batch")
    for batch in request.batches:
        if batch.publisher not in PUBLISHER_SPECS:
            raise ValueError(f"unknown closeout publisher {batch.publisher!r}")
        if not batch.input_paths:
            raise ValueError(f"{batch.publisher}: input_paths must be non-empty")

def _validate_manifest(self, manifest: CloseoutManifest) -> None:
    if manifest.schema_version != 1:
        raise ValueError(f"unsupported closeout schema_version {manifest.schema_version!r}")
    if not manifest.closeout_id.strip():
        raise ValueError("closeout_id must be a non-empty string")
    if not manifest.session_ref.strip():
        raise ValueError("session_ref must be a non-empty string")
    if not manifest.trigger.strip():
        raise ValueError("trigger must be a non-empty string")
    if not manifest.audit_only and not manifest.batches:
        raise ValueError("closeout manifest must include at least one publisher batch")
    for batch in manifest.batches:
        if batch.publisher not in PUBLISHER_SPECS:
            raise ValueError(f"unknown closeout publisher {batch.publisher!r}")
        if not batch.input_paths:
            raise ValueError(f"{batch.publisher}: input_paths must be non-empty")
