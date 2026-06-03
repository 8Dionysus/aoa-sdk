from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..loaders import write_json
from ..models import CloseoutRunReport


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
