from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Literal, cast

from ..compatibility import load_surface
from ..errors import SurfaceNotFound
from ..loaders import load_json, write_json
from ..models import (
    CloseoutBuildReport,
    CloseoutBuildRequest,
    CloseoutEnqueueReport,
    CloseoutInboxItemResult,
    CloseoutInboxReport,
    CloseoutManifest,
    CloseoutOwnerHandoff,
    CloseoutPublisherBatch,
    CloseoutPublisherRun,
    CloseoutRunReport,
    CloseoutStatusReport,
    CloseoutStatsRefresh,
    CloseoutSubmitReviewedReport,
    KernelNextStepBrief,
    OwnerFollowThroughBrief,
    ProjectCoreSkillKernelSurface,
    WorkflowFollowThroughBrief,
)
from ..workspace.discovery import Workspace


@dataclass(frozen=True, slots=True)
class PublisherSpec:
    publisher: str
    repo: str
    script_relative_path: str
    default_log_relative_path: str


PUBLISHER_SPECS = {
    "aoa-skills.session-harvest-family": PublisherSpec(
        publisher="aoa-skills.session-harvest-family",
        repo="aoa-skills",
        script_relative_path="scripts/publish_live_receipts.py",
        default_log_relative_path=".aoa/live_receipts/session-harvest-family.jsonl",
    ),
    "aoa-skills.core-kernel-applications": PublisherSpec(
        publisher="aoa-skills.core-kernel-applications",
        repo="aoa-skills",
        script_relative_path="scripts/publish_core_skill_receipts.py",
        default_log_relative_path=".aoa/live_receipts/core-skill-applications.jsonl",
    ),
    "aoa-evals.eval-result": PublisherSpec(
        publisher="aoa-evals.eval-result",
        repo="aoa-evals",
        script_relative_path="scripts/publish_live_receipts.py",
        default_log_relative_path=".aoa/live_receipts/eval-result-receipts.jsonl",
    ),
    "aoa-playbooks.reviewed-run": PublisherSpec(
        publisher="aoa-playbooks.reviewed-run",
        repo="aoa-playbooks",
        script_relative_path="scripts/publish_live_receipts.py",
        default_log_relative_path=".aoa/live_receipts/playbook-receipts.jsonl",
    ),
    "aoa-techniques.promotion": PublisherSpec(
        publisher="aoa-techniques.promotion",
        repo="aoa-techniques",
        script_relative_path="scripts/publish_live_receipts.py",
        default_log_relative_path=".aoa/live_receipts/technique-receipts.jsonl",
    ),
    "aoa-memo.writeback": PublisherSpec(
        publisher="aoa-memo.writeback",
        repo="aoa-memo",
        script_relative_path="scripts/publish_live_receipts.py",
        default_log_relative_path=".aoa/live_receipts/memo-writeback-receipts.jsonl",
    ),
}

PUBLISHER_EVENT_KINDS = {
    "aoa-skills.session-harvest-family": {
        "automation_candidate_receipt",
        "decision_fork_receipt",
        "harvest_packet_receipt",
        "progression_delta_receipt",
        "quest_promotion_receipt",
        "repair_cycle_receipt",
        "skill_run_receipt",
    },
    "aoa-skills.core-kernel-applications": {"core_skill_application_receipt"},
    "aoa-evals.eval-result": {"eval_result_receipt"},
    "aoa-playbooks.reviewed-run": {
        "playbook_publication_receipt",
        "playbook_review_harvest_receipt",
    },
    "aoa-techniques.promotion": {
        "technique_promotion_receipt",
        "technique_publication_receipt",
    },
    "aoa-memo.writeback": {"memo_writeback_receipt"},
}
EVENT_KIND_TO_PUBLISHER = {
    event_kind: publisher
    for publisher, event_kinds in PUBLISHER_EVENT_KINDS.items()
    for event_kind in event_kinds
}

PUBLISH_RESULT_RE = re.compile(
    r"\[ok\] appended (?P<appended>\d+) .*?\n\[skip\] duplicate event ids skipped: (?P<skipped>\d+)",
    re.DOTALL,
)
REFRESH_OK_RE = re.compile(
    r"\[ok\] refreshed live stats from (?P<sources>\d+) sources and (?P<receipts>\d+) receipts"
)
REFRESH_CLEARED_RE = re.compile(
    r"\[ok\] cleared live stats because no receipts were found across (?P<sources>\d+) sources"
)
FEED_OUTPUT_RE = re.compile(r"\[(?:feed|feed-cleared)\] (?P<path>.+)")
SUMMARY_OUTPUT_RE = re.compile(r"\[(?:summaries|summaries-cleared)\] (?P<path>.+)")


class CloseoutAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

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

    def run(
        self,
        manifest_path: str | Path,
        *,
        report_output: str | Path | None = None,
    ) -> CloseoutRunReport:
        resolved_manifest_path = Path(manifest_path).expanduser().resolve()
        manifest = self.load_manifest(resolved_manifest_path)
        if not manifest.reviewed:
            raise ValueError("session closeout manifests must set reviewed=true before orchestration")

        publisher_runs = [
            self._run_publisher_batch(manifest_path=resolved_manifest_path, batch=batch)
            for batch in manifest.batches
        ]
        stats_refresh = (
            self._skipped_stats_refresh(
                "audit-only closeout requested; no owner-local receipt publishers were invoked"
            )
            if manifest.audit_only
            else self._run_stats_refresh()
        )
        kernel_next_step_brief = (
            None
            if manifest.audit_only
            else self._build_kernel_next_step_brief(
                manifest_path=resolved_manifest_path,
                manifest=manifest,
            )
        )
        owner_follow_through_briefs = (
            []
            if manifest.audit_only
            else self._build_owner_follow_through_briefs(
                manifest_path=resolved_manifest_path,
                manifest=manifest,
            )
        )
        workflow_follow_through_briefs = (
            []
            if manifest.audit_only
            else self._build_workflow_follow_through_briefs(
                manifest_path=resolved_manifest_path,
                manifest=manifest,
                kernel_next_step_brief=kernel_next_step_brief,
            )
        )
        owner_handoff_path = (
            None
            if manifest.audit_only
            else self._write_owner_handoff(
                manifest_path=resolved_manifest_path,
                manifest=manifest,
                briefs=owner_follow_through_briefs,
                workflow_briefs=workflow_follow_through_briefs,
            )
        )
        report = CloseoutRunReport(
            schema_version=1,
            closeout_id=manifest.closeout_id,
            session_ref=manifest.session_ref,
            manifest_path=str(resolved_manifest_path),
            processed_at=datetime.now(timezone.utc),
            trigger=manifest.trigger,
            reviewed=manifest.reviewed,
            audit_only=manifest.audit_only,
            audit_refs=manifest.audit_refs,
            notes=manifest.notes,
            publisher_runs=publisher_runs,
            stats_refresh=stats_refresh,
            kernel_next_step_brief=kernel_next_step_brief,
            owner_handoff_path=str(owner_handoff_path) if owner_handoff_path is not None else None,
            owner_follow_through_briefs=owner_follow_through_briefs,
            workflow_follow_through_briefs=workflow_follow_through_briefs,
        )
        if report_output is not None:
            write_json(Path(report_output).expanduser().resolve(), report.model_dump(mode="json"))
        return report

    def enqueue(
        self,
        manifest_path: str | Path,
        *,
        inbox_dir: str | Path | None = None,
        overwrite: bool = False,
    ) -> CloseoutEnqueueReport:
        resolved_manifest_path = Path(manifest_path).expanduser().resolve()
        manifest = self.load_manifest(resolved_manifest_path)
        if not manifest.reviewed:
            raise ValueError("session closeout manifests must set reviewed=true before queueing")

        inbox = self._resolve_queue_dir(inbox_dir, leaf="inbox")
        inbox.mkdir(parents=True, exist_ok=True)
        queued_manifest_path = inbox / f"{self._safe_closeout_filename(manifest.closeout_id)}.json"
        overwritten = False
        if queued_manifest_path.exists():
            if not overwrite and queued_manifest_path.resolve() != resolved_manifest_path:
                raise FileExistsError(
                    f"{queued_manifest_path} already exists; rerun with overwrite=True to replace it"
                )
            overwritten = queued_manifest_path.resolve() != resolved_manifest_path

        queued_manifest = manifest.model_copy(
            update={
                "audit_refs": self._resolve_optional_paths(
                    resolved_manifest_path, manifest.audit_refs
                ),
                "batches": [
                    batch.model_copy(
                        update={
                            "input_paths": [
                                str(path)
                                for path in self._resolve_input_paths(
                                    resolved_manifest_path, batch.input_paths
                                )
                            ]
                        }
                    )
                    for batch in manifest.batches
                ],
            }
        )
        write_json(queued_manifest_path, queued_manifest.model_dump(mode="json"))
        queue_depth = len(list(inbox.glob("*.json")))
        return CloseoutEnqueueReport(
            schema_version=1,
            closeout_id=manifest.closeout_id,
            session_ref=manifest.session_ref,
            source_manifest_path=str(resolved_manifest_path),
            queued_manifest_path=str(queued_manifest_path),
            enqueued_at=datetime.now(timezone.utc),
            queue_depth=queue_depth,
            overwritten=overwritten,
        )

    def process_inbox(
        self,
        *,
        inbox_dir: str | Path | None = None,
        processed_dir: str | Path | None = None,
        failed_dir: str | Path | None = None,
        report_dir: str | Path | None = None,
    ) -> CloseoutInboxReport:
        inbox = self._resolve_queue_dir(inbox_dir, leaf="inbox")
        processed = self._resolve_queue_dir(processed_dir, leaf="processed")
        failed = self._resolve_queue_dir(failed_dir, leaf="failed")
        reports = self._resolve_queue_dir(report_dir, leaf="reports")
        handoffs = self._resolve_queue_dir(None, leaf="handoffs")

        inbox.mkdir(parents=True, exist_ok=True)
        processed.mkdir(parents=True, exist_ok=True)
        failed.mkdir(parents=True, exist_ok=True)
        reports.mkdir(parents=True, exist_ok=True)
        handoffs.mkdir(parents=True, exist_ok=True)

        items: list[CloseoutInboxItemResult] = []
        processed_count = 0
        failed_count = 0

        for manifest_path in sorted(inbox.glob("*.json")):
            report_path = reports / f"{manifest_path.stem}.report.json"
            try:
                report = self.run(manifest_path, report_output=report_path)
                archived_path = self._archive_manifest(manifest_path, processed)
                items.append(
                    CloseoutInboxItemResult(
                        manifest_path=str(manifest_path),
                        archived_manifest_path=str(archived_path),
                        report_path=str(report_path),
                        status="processed",
                        closeout_id=report.closeout_id,
                        session_ref=report.session_ref,
                        kernel_next_step_brief=report.kernel_next_step_brief,
                        owner_handoff_path=report.owner_handoff_path,
                        owner_follow_through_briefs=report.owner_follow_through_briefs,
                        workflow_follow_through_briefs=report.workflow_follow_through_briefs,
                    )
                )
                processed_count += 1
            except Exception as exc:
                archived_path = self._archive_manifest(manifest_path, failed)
                items.append(
                    CloseoutInboxItemResult(
                        manifest_path=str(manifest_path),
                        archived_manifest_path=str(archived_path),
                        report_path=None,
                        status="failed",
                        error=str(exc),
                    )
                )
                failed_count += 1

        return CloseoutInboxReport(
            schema_version=1,
            inbox_dir=str(inbox),
            processed_dir=str(processed),
            failed_dir=str(failed),
            report_dir=str(reports),
            processed_count=processed_count,
            failed_count=failed_count,
            items=items,
        )

    def status(
        self,
        *,
        request_dir: str | Path | None = None,
        manifest_dir: str | Path | None = None,
        inbox_dir: str | Path | None = None,
        processed_dir: str | Path | None = None,
        failed_dir: str | Path | None = None,
        report_dir: str | Path | None = None,
    ) -> CloseoutStatusReport:
        queue_paths = {
            "root": self.default_closeout_root(),
            "requests": self._resolve_queue_dir(request_dir, leaf="requests"),
            "manifests": self._resolve_queue_dir(manifest_dir, leaf="manifests"),
            "inbox": self._resolve_queue_dir(inbox_dir, leaf="inbox"),
            "processed": self._resolve_queue_dir(processed_dir, leaf="processed"),
            "failed": self._resolve_queue_dir(failed_dir, leaf="failed"),
            "reports": self._resolve_queue_dir(report_dir, leaf="reports"),
            "handoffs": self._resolve_queue_dir(None, leaf="handoffs"),
        }
        requests = sorted(queue_paths["requests"].glob("*.json"))
        manifests = sorted(queue_paths["manifests"].glob("*.json"))
        pending_manifests = sorted(queue_paths["inbox"].glob("*.json"))
        processed_manifests = sorted(queue_paths["processed"].glob("*.json"))
        failed_manifests = sorted(queue_paths["failed"].glob("*.json"))
        reports = sorted(queue_paths["reports"].glob("*.json"))
        handoffs = sorted(queue_paths["handoffs"].glob("*.json"))

        return CloseoutStatusReport(
            schema_version=1,
            root_dir=str(queue_paths["root"]),
            request_dir=str(queue_paths["requests"]),
            manifest_dir=str(queue_paths["manifests"]),
            inbox_dir=str(queue_paths["inbox"]),
            processed_dir=str(queue_paths["processed"]),
            failed_dir=str(queue_paths["failed"]),
            report_dir=str(queue_paths["reports"]),
            handoff_dir=str(queue_paths["handoffs"]),
            request_count=len(requests),
            manifest_count=len(manifests),
            pending_manifest_count=len(pending_manifests),
            processed_manifest_count=len(processed_manifests),
            failed_manifest_count=len(failed_manifests),
            report_count=len(reports),
            handoff_count=len(handoffs),
            pending_manifest_paths=[str(path) for path in pending_manifests],
            latest_request_path=self._latest_path(requests),
            latest_manifest_path=self._latest_path(manifests),
            latest_report_path=self._latest_path(reports),
            latest_handoff_path=self._latest_path(handoffs),
            latest_processed_manifest_path=self._latest_path(processed_manifests),
            latest_failed_manifest_path=self._latest_path(failed_manifests),
        )

    def default_closeout_root(self) -> Path:
        return self.workspace.repo_path("aoa-sdk") / ".aoa" / "closeout"

    def default_queue_paths(self) -> dict[str, Path]:
        root = self.default_closeout_root()
        return {
            "root": root,
            "requests": root / "requests",
            "manifests": root / "manifests",
            "inbox": root / "inbox",
            "processed": root / "processed",
            "failed": root / "failed",
            "reports": root / "reports",
            "handoffs": root / "handoffs",
        }

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

    def _resolve_queue_dir(self, candidate: str | Path | None, *, leaf: str) -> Path:
        if candidate is None:
            return self.default_closeout_root() / leaf
        return Path(candidate).expanduser().resolve()

    def _resolve_existing_path(self, manifest_path: Path, item: str) -> Path:
        path = Path(item).expanduser()
        if not path.is_absolute():
            path = (manifest_path.parent / path).resolve()
        else:
            path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"missing closeout input: {path}")
        return path

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

    def _resolve_input_paths(self, manifest_path: Path, input_paths: list[str]) -> list[Path]:
        resolved: list[Path] = []
        for item in input_paths:
            resolved.append(self._resolve_existing_path(manifest_path, item))
        return resolved

    def _resolve_optional_paths(self, manifest_path: Path, input_paths: list[str]) -> list[str]:
        resolved: list[str] = []
        for item in input_paths:
            path = Path(item).expanduser()
            if not path.is_absolute():
                path = (manifest_path.parent / path).resolve()
            else:
                path = path.resolve()
            resolved.append(str(path))
        return resolved

    def _run_publisher_batch(
        self,
        *,
        manifest_path: Path,
        batch,
    ) -> CloseoutPublisherRun:
        spec = PUBLISHER_SPECS[batch.publisher]
        repo_root = self.workspace.repo_path(spec.repo)
        script_path = repo_root / spec.script_relative_path
        log_path = repo_root / spec.default_log_relative_path
        if not script_path.exists():
            raise FileNotFoundError(f"missing publisher script: {script_path}")

        input_paths = self._resolve_input_paths(manifest_path, batch.input_paths)
        command = [sys.executable, str(script_path)]
        for input_path in input_paths:
            command.extend(["--input", str(input_path)])
        completed = self._run_command(command)
        appended_count, duplicate_skip_count = self._parse_publish_stdout(completed)
        return CloseoutPublisherRun(
            publisher=spec.publisher,
            repo=spec.repo,
            input_paths=[str(path) for path in input_paths],
            log_path=str(log_path),
            command=command,
            appended_count=appended_count,
            duplicate_skip_count=duplicate_skip_count,
            stdout=completed,
        )

    def _run_stats_refresh(self) -> CloseoutStatsRefresh:
        stats_root = self.workspace.repo_path("aoa-stats")
        script_path = stats_root / "scripts" / "refresh_live_stats.py"
        if not script_path.exists():
            raise FileNotFoundError(f"missing aoa-stats refresh script: {script_path}")
        command = [sys.executable, str(script_path)]
        completed = self._run_command(command)
        source_count, receipt_count, cleared = self._parse_refresh_stdout(completed)
        return CloseoutStatsRefresh(
            command=command,
            source_count=source_count,
            receipt_count=receipt_count,
            cleared=cleared,
            feed_output=self._parse_named_path(completed, FEED_OUTPUT_RE),
            summary_output_dir=self._parse_named_path(completed, SUMMARY_OUTPUT_RE),
            stdout=completed,
        )

    def _build_kernel_next_step_brief(
        self,
        *,
        manifest_path: Path,
        manifest: CloseoutManifest,
    ) -> KernelNextStepBrief:
        kernel = ProjectCoreSkillKernelSurface.model_validate(
            load_surface(self.workspace, "aoa-skills.project_core_skill_kernel.min")
        )
        detail_receipts, core_receipts = self._load_kernel_receipt_batches(
            manifest_path=manifest_path,
            manifest=manifest,
            kernel=kernel,
        )
        current_detail_event_kinds = self._collect_current_detail_event_kinds(
            detail_receipts=detail_receipts,
            core_receipts=core_receipts,
        )
        current_session_skill_names = self._collect_current_session_skill_names(
            kernel=kernel,
            detail_receipts=detail_receipts,
            core_receipts=core_receipts,
        )
        kernel_usage_counts = self._load_kernel_usage_counts(
            kernel_id=kernel.kernel_id,
            kernel_skills=kernel.skills,
        )
        missing_kernel_skill_names = [
            skill_name
            for skill_name in kernel.skills
            if skill_name not in set(current_session_skill_names)
        ]
        suggested_action, suggested_skill_name, suggested_owner_repo, reason = self._resolve_kernel_next_step(
            kernel=kernel,
            detail_receipts=detail_receipts,
            current_session_skill_names=current_session_skill_names,
            current_detail_event_kinds=current_detail_event_kinds,
            missing_kernel_skill_names=missing_kernel_skill_names,
        )
        return KernelNextStepBrief(
            kernel_id=kernel.kernel_id,
            current_session_skill_names=current_session_skill_names,
            current_session_detail_event_kinds=current_detail_event_kinds,
            missing_kernel_skill_names=missing_kernel_skill_names,
            kernel_usage_counts=kernel_usage_counts,
            suggested_action=suggested_action,
            suggested_skill_name=suggested_skill_name,
            suggested_owner_repo=suggested_owner_repo,
            reason=reason,
            stats_surface_ref=kernel.governance_contract.stats_surface,
        )

    def _build_owner_follow_through_briefs(
        self,
        *,
        manifest_path: Path,
        manifest: CloseoutManifest,
    ) -> list[OwnerFollowThroughBrief]:
        kernel = ProjectCoreSkillKernelSurface.model_validate(
            load_surface(self.workspace, "aoa-skills.project_core_skill_kernel.min")
        )
        detail_receipts, _ = self._load_kernel_receipt_batches(
            manifest_path=manifest_path,
            manifest=manifest,
            kernel=kernel,
        )
        briefs_by_key: dict[str, OwnerFollowThroughBrief] = {}
        for brief in self._build_harvest_follow_through_briefs(
            manifest_path=manifest_path,
            detail_receipts=detail_receipts,
        ):
            briefs_by_key[self._owner_follow_through_key(brief)] = brief
        for brief in self._build_quest_follow_through_briefs(
            manifest_path=manifest_path,
            detail_receipts=detail_receipts,
        ):
            briefs_by_key[self._owner_follow_through_key(brief)] = brief
        return sorted(
            briefs_by_key.values(),
            key=lambda item: (item.owner_repo, item.next_surface, item.unit_ref),
        )

    def _build_workflow_follow_through_briefs(
        self,
        *,
        manifest_path: Path,
        manifest: CloseoutManifest,
        kernel_next_step_brief: KernelNextStepBrief | None,
    ) -> list[WorkflowFollowThroughBrief]:
        kernel = ProjectCoreSkillKernelSurface.model_validate(
            load_surface(self.workspace, "aoa-skills.project_core_skill_kernel.min")
        )
        detail_receipts, _ = self._load_kernel_receipt_batches(
            manifest_path=manifest_path,
            manifest=manifest,
            kernel=kernel,
        )
        briefs_by_skill: dict[str, WorkflowFollowThroughBrief] = {}

        if (
            kernel_next_step_brief is not None
            and kernel_next_step_brief.suggested_action == "invoke-core-skill"
            and kernel_next_step_brief.suggested_skill_name is not None
        ):
            briefs_by_skill[kernel_next_step_brief.suggested_skill_name] = WorkflowFollowThroughBrief(
                source_kind="kernel-next-step",
                skill_name=kernel_next_step_brief.suggested_skill_name,
                suggested_action="invoke-core-skill",
                reason=kernel_next_step_brief.reason,
                evidence_refs=[kernel_next_step_brief.stats_surface_ref],
            )

        progression_receipt = self._latest_detail_receipt(
            detail_receipts,
            event_kind="progression_delta_receipt",
        )
        if progression_receipt is not None:
            payload = progression_receipt.get("payload")
            verdict = payload.get("verdict") if isinstance(payload, dict) else None
            axis_deltas = payload.get("axis_deltas") if isinstance(payload, dict) else None
            negative_axes = (
                sorted(
                    axis
                    for axis, delta in axis_deltas.items()
                    if isinstance(axis, str) and isinstance(delta, int) and delta < 0
                )
                if isinstance(axis_deltas, dict)
                else []
            )
            if verdict in {"reanchor", "downgrade"} and "aoa-session-self-diagnose" not in briefs_by_skill:
                detail = (
                    f"progression closed with {verdict} and negative axes in {', '.join(negative_axes)}"
                    if negative_axes
                    else f"progression closed with {verdict}"
                )
                briefs_by_skill["aoa-session-self-diagnose"] = WorkflowFollowThroughBrief(
                    source_kind="progression-caution",
                    skill_name="aoa-session-self-diagnose",
                    suggested_action="invoke-core-skill",
                    reason=(
                        f"{detail}, so the next honest workflow move is bounded self-diagnosis before the next mutation-heavy follow-through."
                    ),
                    evidence_refs=self._extract_evidence_ref_strings(progression_receipt.get("evidence_refs")),
                )

        diagnosis_receipt = self._latest_detail_receipt(
            detail_receipts,
            event_kind="skill_run_receipt",
        )
        repair_receipt = self._latest_detail_receipt(
            detail_receipts,
            event_kind="repair_cycle_receipt",
        )
        if diagnosis_receipt is not None and repair_receipt is None:
            payload = diagnosis_receipt.get("payload")
            diagnosis_types = payload.get("diagnosis_types") if isinstance(payload, dict) else None
            diagnosis_summary = (
                ", ".join(item for item in diagnosis_types if isinstance(item, str))
                if isinstance(diagnosis_types, list)
                else "an unresolved diagnosis packet"
            )
            briefs_by_skill["aoa-session-self-repair"] = WorkflowFollowThroughBrief(
                source_kind="diagnosis-gap",
                skill_name="aoa-session-self-repair",
                suggested_action="invoke-core-skill",
                reason=(
                    f"closeout already carries {diagnosis_summary}, but no repair_cycle_receipt landed yet, so the next honest workflow move is bounded self-repair."
                ),
                evidence_refs=self._extract_evidence_ref_strings(diagnosis_receipt.get("evidence_refs")),
            )

        workflow_order = {
            "aoa-automation-opportunity-scan": 0,
            "aoa-session-route-forks": 1,
            "aoa-session-self-diagnose": 2,
            "aoa-session-self-repair": 3,
            "aoa-session-progression-lift": 4,
            "aoa-quest-harvest": 5,
        }
        return sorted(
            briefs_by_skill.values(),
            key=lambda item: (workflow_order.get(item.skill_name, 99), item.skill_name),
        )

    def _build_harvest_follow_through_briefs(
        self,
        *,
        manifest_path: Path,
        detail_receipts: list[dict[str, Any]],
    ) -> list[OwnerFollowThroughBrief]:
        briefs: list[OwnerFollowThroughBrief] = []
        for receipt in detail_receipts:
            if receipt.get("event_kind") != "harvest_packet_receipt":
                continue
            packet_paths = self._resolve_receipt_evidence_paths(
                manifest_path=manifest_path,
                evidence_refs=receipt.get("evidence_refs"),
                preferred_kinds={"harvest_packet"},
            )
            for packet_path in packet_paths:
                try:
                    packet = load_json(packet_path)
                except (FileNotFoundError, json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(packet, dict):
                    continue
                for candidate in packet.get("accepted_candidates", []):
                    if not isinstance(candidate, dict):
                        continue
                    owner_repo = candidate.get("owner_repo_recommendation")
                    next_surface = candidate.get("chosen_next_artifact")
                    unit_ref = candidate.get("candidate_ref")
                    if not all(
                        isinstance(value, str) and value
                        for value in (owner_repo, next_surface, unit_ref)
                    ):
                        continue
                    owner_repo_str = cast(str, owner_repo)
                    next_surface_str = cast(str, next_surface)
                    unit_ref_str = cast(str, unit_ref)
                    owner_reason = candidate.get("owner_reason")
                    reason = (
                        owner_reason
                        if isinstance(owner_reason, str) and owner_reason
                        else "Harvest named this as a reusable owner-layer candidate, so the next honest move is a bounded owner-surface draft."
                    )
                    evidence_refs = [str(packet_path)]
                    evidence_anchors = candidate.get("evidence_anchors")
                    if isinstance(evidence_anchors, list):
                        evidence_refs.extend(
                            anchor
                            for anchor in evidence_anchors
                            if isinstance(anchor, str) and anchor
                        )
                    briefs.append(
                        OwnerFollowThroughBrief(
                            source_kind="harvest-candidate",
                            unit_ref=unit_ref_str,
                            unit_name=candidate.get("unit_name")
                            if isinstance(candidate.get("unit_name"), str)
                            else None,
                            owner_repo=owner_repo_str,
                            next_surface=next_surface_str,
                            suggested_action="draft-owner-artifact",
                            abstraction_shape=candidate.get("abstraction_shape")
                            if isinstance(candidate.get("abstraction_shape"), str)
                            else None,
                            nearest_wrong_target=candidate.get("nearest_wrong_target")
                            if isinstance(candidate.get("nearest_wrong_target"), str)
                            else None,
                            reason=reason,
                            evidence_refs=self._unique_strings(evidence_refs),
                        )
                    )
        return briefs

    def _build_quest_follow_through_briefs(
        self,
        *,
        manifest_path: Path,
        detail_receipts: list[dict[str, Any]],
    ) -> list[OwnerFollowThroughBrief]:
        briefs: list[OwnerFollowThroughBrief] = []
        for receipt in detail_receipts:
            if receipt.get("event_kind") != "quest_promotion_receipt":
                continue
            payload = receipt.get("payload")
            if not isinstance(payload, dict):
                continue
            owner_repo = payload.get("owner_repo")
            next_surface = payload.get("next_surface")
            promotion_verdict = payload.get("promotion_verdict")
            if not all(
                isinstance(value, str) and value
                for value in (owner_repo, next_surface, promotion_verdict)
            ):
                continue
            owner_repo_str = cast(str, owner_repo)
            next_surface_str = cast(str, next_surface)
            promotion_verdict_str = cast(str, promotion_verdict)
            unit_ref = payload.get("bounded_unit_ref")
            if not isinstance(unit_ref, str) or not unit_ref:
                event_id = receipt.get("event_id")
                unit_ref = event_id if isinstance(event_id, str) and event_id else next_surface
            unit_ref_str = cast(str, unit_ref)
            briefs.append(
                OwnerFollowThroughBrief(
                    source_kind="quest-promotion",
                    unit_ref=unit_ref_str,
                    unit_name=self._load_quest_unit_name(
                        manifest_path=manifest_path,
                        receipt=receipt,
                    ),
                    owner_repo=owner_repo_str,
                    next_surface=next_surface_str,
                    suggested_action="author-owner-artifact",
                    promotion_verdict=promotion_verdict_str,
                    nearest_wrong_target=payload.get("nearest_wrong_target")
                    if isinstance(payload.get("nearest_wrong_target"), str)
                    else None,
                    reason=(
                        f"Quest promotion closed with {promotion_verdict_str}, so the next honest move is to author the owner-layer artifact."
                    ),
                    evidence_refs=self._extract_evidence_ref_strings(receipt.get("evidence_refs")),
                )
            )
        return briefs

    def _load_quest_unit_name(
        self,
        *,
        manifest_path: Path,
        receipt: dict[str, Any],
    ) -> str | None:
        triage_paths = self._resolve_receipt_evidence_paths(
            manifest_path=manifest_path,
            evidence_refs=receipt.get("evidence_refs"),
            preferred_kinds={"quest_triage"},
        )
        for triage_path in triage_paths:
            try:
                payload = load_json(triage_path)
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                continue
            if not isinstance(payload, dict):
                continue
            quest_unit_name = payload.get("quest_unit_name")
            if isinstance(quest_unit_name, str) and quest_unit_name:
                return quest_unit_name
        return None

    def _owner_follow_through_key(self, brief: OwnerFollowThroughBrief) -> str:
        return brief.unit_ref or brief.next_surface

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

    def _write_owner_handoff(
        self,
        *,
        manifest_path: Path,
        manifest: CloseoutManifest,
        briefs: list[OwnerFollowThroughBrief],
        workflow_briefs: list[WorkflowFollowThroughBrief],
    ) -> Path | None:
        if not briefs and not workflow_briefs:
            return None
        handoff_dir = self._resolve_queue_dir(None, leaf="handoffs")
        handoff_dir.mkdir(parents=True, exist_ok=True)
        handoff_path = handoff_dir / f"{self._safe_closeout_filename(manifest.closeout_id)}.owner-handoff.json"
        payload = CloseoutOwnerHandoff(
            schema_version=1,
            closeout_id=manifest.closeout_id,
            session_ref=manifest.session_ref,
            manifest_path=str(manifest_path),
            generated_at=datetime.now(timezone.utc),
            items=briefs,
            workflow_items=workflow_briefs,
        )
        write_json(handoff_path, payload.model_dump(mode="json"))
        return handoff_path

    def _skipped_stats_refresh(self, reason: str) -> CloseoutStatsRefresh:
        return CloseoutStatsRefresh(
            command=[],
            source_count=None,
            receipt_count=None,
            cleared=False,
            feed_output=None,
            summary_output_dir=None,
            stdout=f"[skip] stats refresh skipped: {reason}",
        )

    def _run_command(self, command: list[str]) -> str:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            detail = stderr or stdout or f"exit code {completed.returncode}"
            raise RuntimeError(f"{' '.join(command)} failed: {detail}")
        return completed.stdout.strip()

    def _parse_publish_stdout(self, stdout: str) -> tuple[int | None, int | None]:
        match = PUBLISH_RESULT_RE.search(stdout)
        if match is None:
            return None, None
        return int(match.group("appended")), int(match.group("skipped"))

    def _parse_refresh_stdout(self, stdout: str) -> tuple[int | None, int | None, bool]:
        refreshed = REFRESH_OK_RE.search(stdout)
        if refreshed is not None:
            return int(refreshed.group("sources")), int(refreshed.group("receipts")), False
        cleared = REFRESH_CLEARED_RE.search(stdout)
        if cleared is not None:
            return int(cleared.group("sources")), 0, True
        return None, None, False

    def _parse_named_path(self, stdout: str, pattern: re.Pattern[str]) -> str | None:
        match = pattern.search(stdout)
        if match is None:
            return None
        return match.group("path").strip()

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

    def _collect_current_detail_event_kinds(
        self,
        *,
        detail_receipts: list[dict[str, Any]],
        core_receipts: list[dict[str, Any]],
    ) -> list[str]:
        event_kinds: list[str] = []
        for receipt in detail_receipts:
            event_kind = receipt.get("event_kind")
            if isinstance(event_kind, str) and event_kind and event_kind not in event_kinds:
                event_kinds.append(event_kind)
        for receipt in core_receipts:
            payload = receipt.get("payload")
            detail_event_kind = payload.get("detail_event_kind") if isinstance(payload, dict) else None
            if (
                isinstance(detail_event_kind, str)
                and detail_event_kind
                and detail_event_kind not in event_kinds
            ):
                event_kinds.append(detail_event_kind)
        return event_kinds

    def _collect_current_session_skill_names(
        self,
        *,
        kernel: ProjectCoreSkillKernelSurface,
        detail_receipts: list[dict[str, Any]],
        core_receipts: list[dict[str, Any]],
    ) -> list[str]:
        skill_contracts = {item.skill_name: item for item in kernel.skill_contracts}
        detail_event_to_skill = {
            item.detail_event_kind: item.skill_name for item in kernel.skill_contracts
        }
        detected_skill_names: set[str] = set()

        for receipt in core_receipts:
            payload = receipt.get("payload")
            skill_name = payload.get("skill_name") if isinstance(payload, dict) else None
            if isinstance(skill_name, str) and skill_name in skill_contracts:
                detected_skill_names.add(skill_name)

        for receipt in detail_receipts:
            event_kind = receipt.get("event_kind")
            if isinstance(event_kind, str) and event_kind in detail_event_to_skill:
                detected_skill_names.add(detail_event_to_skill[event_kind])
                continue
            object_ref = receipt.get("object_ref")
            object_id = object_ref.get("id") if isinstance(object_ref, dict) else None
            if isinstance(object_id, str) and object_id in skill_contracts:
                detected_skill_names.add(object_id)

        return [skill_name for skill_name in kernel.skills if skill_name in detected_skill_names]

    def _load_kernel_usage_counts(
        self,
        *,
        kernel_id: str,
        kernel_skills: list[str],
    ) -> dict[str, int]:
        usage_counts = {skill_name: 0 for skill_name in kernel_skills}
        try:
            summary = load_surface(self.workspace, "aoa-stats.core_skill_application_summary.min")
        except SurfaceNotFound:
            return usage_counts
        for item in summary.get("skills", []):
            if not isinstance(item, dict):
                continue
            if item.get("kernel_id") != kernel_id:
                continue
            skill_name = item.get("skill_name")
            application_count = item.get("application_count")
            if isinstance(skill_name, str) and skill_name in usage_counts and isinstance(application_count, int):
                usage_counts[skill_name] = application_count
        return usage_counts

    def _resolve_kernel_next_step(
        self,
        *,
        kernel: ProjectCoreSkillKernelSurface,
        detail_receipts: list[dict[str, Any]],
        current_session_skill_names: list[str],
        current_detail_event_kinds: list[str],
        missing_kernel_skill_names: list[str],
    ) -> tuple[
        Literal["invoke-core-skill", "shift-to-owner-layer", "hold"],
        str | None,
        str | None,
        str,
    ]:
        detail_event_kind_set = set(current_detail_event_kinds)
        quest_receipt = self._latest_detail_receipt(
            detail_receipts, event_kind="quest_promotion_receipt"
        )
        if quest_receipt is not None:
            payload = quest_receipt.get("payload")
            owner_repo = payload.get("owner_repo") if isinstance(payload, dict) else None
            return (
                "shift-to-owner-layer",
                None,
                owner_repo if isinstance(owner_repo, str) else None,
                "Current closeout already finished with quest promotion, so the next honest move is owner-layer follow-through.",
            )

        if "progression_delta_receipt" in detail_event_kind_set:
            return self._invoke_core_skill_brief(
                "aoa-quest-harvest",
                "Progression has been recorded for this session, so the next core step is final quest triage.",
            )
        if "repair_cycle_receipt" in detail_event_kind_set:
            return self._invoke_core_skill_brief(
                "aoa-session-progression-lift",
                "Repair has landed but progression has not, so the next core step is explicit progression lift.",
            )
        if "skill_run_receipt" in detail_event_kind_set:
            return self._invoke_core_skill_brief(
                "aoa-session-self-repair",
                "Diagnosis has landed but repair has not, so the next core step is bounded self-repair.",
            )
        automation_receipt = self._latest_detail_receipt(
            detail_receipts, event_kind="automation_candidate_receipt"
        )
        if automation_receipt is not None:
            payload = automation_receipt.get("payload")
            checkpoint_required = (
                payload.get("checkpoint_required") if isinstance(payload, dict) else None
            )
            if checkpoint_required is True:
                return self._invoke_core_skill_brief(
                    "aoa-session-self-diagnose",
                    "Automation scan raised a checkpoint-required candidate, so the next core step is self-diagnosis.",
                )
        if "decision_fork_receipt" in detail_event_kind_set:
            return self._invoke_core_skill_brief(
                "aoa-session-self-diagnose",
                "Route forks have been captured without diagnosis yet, so the next core step is self-diagnosis.",
            )
        if "automation_candidate_receipt" in detail_event_kind_set:
            return self._invoke_core_skill_brief(
                "aoa-session-route-forks",
                "Automation candidates exist without a fork decision yet, so the next core step is route selection.",
            )
        if "harvest_packet_receipt" in detail_event_kind_set:
            return self._invoke_core_skill_brief(
                "aoa-automation-opportunity-scan",
                "Harvest has landed without automation classification yet, so the next core step is automation opportunity scan.",
            )

        if missing_kernel_skill_names:
            highest_index = max(
                (kernel.skills.index(skill_name) for skill_name in current_session_skill_names),
                default=-1,
            )
            later_missing = [
                skill_name
                for skill_name in kernel.skills[highest_index + 1 :]
                if skill_name in missing_kernel_skill_names
            ]
            target_skill = later_missing[0] if later_missing else missing_kernel_skill_names[0]
            return self._invoke_core_skill_brief(
                target_skill,
                "Current closeout only covers part of the project-core kernel, so the next honest move is the next missing core skill in canonical order.",
            )

        return (
            "hold",
            None,
            None,
            "Current closeout already covers the full kernel without an unresolved next-step rule, so the honest next move is to hold.",
        )

    def _invoke_core_skill_brief(
        self, skill_name: str, reason: str
    ) -> tuple[Literal["invoke-core-skill"], str, None, str]:
        return (
            "invoke-core-skill",
            skill_name,
            None,
            reason,
        )

    def _latest_detail_receipt(
        self,
        detail_receipts: list[dict[str, Any]],
        *,
        event_kind: str,
    ) -> dict[str, Any] | None:
        matching = [
            receipt
            for receipt in detail_receipts
            if receipt.get("event_kind") == event_kind
        ]
        if not matching:
            return None
        return max(
            matching,
            key=lambda receipt: (
                str(receipt.get("observed_at", "")),
                str(receipt.get("event_id", "")),
            ),
        )

    def _archive_manifest(self, manifest_path: Path, destination_dir: Path) -> Path:
        destination_dir.mkdir(parents=True, exist_ok=True)
        candidate = destination_dir / manifest_path.name
        if candidate.exists():
            stem = manifest_path.stem
            suffix = manifest_path.suffix
            counter = 1
            while candidate.exists():
                candidate = destination_dir / f"{stem}-{counter}{suffix}"
                counter += 1
        shutil.move(str(manifest_path), str(candidate))
        return candidate

    def _latest_path(self, paths: list[Path]) -> str | None:
        if not paths:
            return None
        latest = max(paths, key=lambda path: path.stat().st_mtime)
        return str(latest)

    def _safe_closeout_filename(self, closeout_id: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", closeout_id).strip("-")
        return safe or "closeout"

    def _unique_strings(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique.append(item)
        return unique

    def _unique_paths(self, items: list[Path]) -> list[Path]:
        seen: set[str] = set()
        unique: list[Path] = []
        for item in items:
            key = str(item)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _derive_closeout_id(self, session_ref: str) -> str:
        return f"closeout-{self._safe_closeout_filename(session_ref)}"
