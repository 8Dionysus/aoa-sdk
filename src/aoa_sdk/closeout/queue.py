from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..loaders import write_json
from ..models import (
    CloseoutEnqueueReport,
    CloseoutInboxItemResult,
    CloseoutInboxReport,
    CloseoutStatusReport,
)


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
