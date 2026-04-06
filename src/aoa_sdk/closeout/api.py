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

from ..loaders import load_json, write_json
from ..models import (
    CloseoutBuildReport,
    CloseoutBuildRequest,
    CloseoutEnqueueReport,
    CloseoutInboxItemResult,
    CloseoutInboxReport,
    CloseoutManifest,
    CloseoutPublisherBatch,
    CloseoutPublisherRun,
    CloseoutRunReport,
    CloseoutStatusReport,
    CloseoutStatsRefresh,
    CloseoutSubmitReviewedReport,
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
            publisher = self._publisher_for_receipt_path(receipt_path)
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
            audit_refs=[
                str(self._resolve_existing_path(reviewed_artifact, str(path)))
                for path in (audit_refs or [])
            ],
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
                *[
                    str(path)
                    for path in self._resolve_input_paths(
                        resolved_request_path, request.audit_refs
                    )
                ],
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

        inbox.mkdir(parents=True, exist_ok=True)
        processed.mkdir(parents=True, exist_ok=True)
        failed.mkdir(parents=True, exist_ok=True)
        reports.mkdir(parents=True, exist_ok=True)

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
        }
        requests = sorted(queue_paths["requests"].glob("*.json"))
        manifests = sorted(queue_paths["manifests"].glob("*.json"))
        pending_manifests = sorted(queue_paths["inbox"].glob("*.json"))
        processed_manifests = sorted(queue_paths["processed"].glob("*.json"))
        failed_manifests = sorted(queue_paths["failed"].glob("*.json"))
        reports = sorted(queue_paths["reports"].glob("*.json"))

        return CloseoutStatusReport(
            schema_version=1,
            root_dir=str(queue_paths["root"]),
            request_dir=str(queue_paths["requests"]),
            manifest_dir=str(queue_paths["manifests"]),
            inbox_dir=str(queue_paths["inbox"]),
            processed_dir=str(queue_paths["processed"]),
            failed_dir=str(queue_paths["failed"]),
            report_dir=str(queue_paths["reports"]),
            request_count=len(requests),
            manifest_count=len(manifests),
            pending_manifest_count=len(pending_manifests),
            processed_manifest_count=len(processed_manifests),
            failed_manifest_count=len(failed_manifests),
            report_count=len(reports),
            pending_manifest_paths=[str(path) for path in pending_manifests],
            latest_request_path=self._latest_path(requests),
            latest_manifest_path=self._latest_path(manifests),
            latest_report_path=self._latest_path(reports),
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

    def _publisher_for_receipt_path(self, receipt_path: Path) -> str:
        publisher: str | None = None
        for receipt in self._load_receipt_file(receipt_path):
            event_kind = receipt.get("event_kind")
            if not isinstance(event_kind, str) or not event_kind:
                raise ValueError(f"{receipt_path}: receipt is missing a non-empty event_kind")
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
