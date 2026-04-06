from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import sys

from ..loaders import load_json, write_json
from ..models import (
    CloseoutInboxItemResult,
    CloseoutInboxReport,
    CloseoutManifest,
    CloseoutPublisherRun,
    CloseoutRunReport,
    CloseoutStatsRefresh,
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
    "aoa-evals.eval-result": PublisherSpec(
        publisher="aoa-evals.eval-result",
        repo="aoa-evals",
        script_relative_path="scripts/publish_live_receipts.py",
        default_log_relative_path=".aoa/live_receipts/eval-result-receipts.jsonl",
    ),
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

    def load_manifest(self, manifest_path: str | Path) -> CloseoutManifest:
        path = Path(manifest_path).expanduser().resolve()
        manifest = CloseoutManifest.model_validate(load_json(path))
        self._validate_manifest(manifest)
        return manifest

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
        stats_refresh = self._run_stats_refresh()
        report = CloseoutRunReport(
            schema_version=1,
            closeout_id=manifest.closeout_id,
            session_ref=manifest.session_ref,
            manifest_path=str(resolved_manifest_path),
            processed_at=datetime.now(timezone.utc),
            trigger=manifest.trigger,
            reviewed=manifest.reviewed,
            audit_refs=manifest.audit_refs,
            notes=manifest.notes,
            publisher_runs=publisher_runs,
            stats_refresh=stats_refresh,
        )
        if report_output is not None:
            write_json(Path(report_output).expanduser().resolve(), report.model_dump(mode="json"))
        return report

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

    def default_closeout_root(self) -> Path:
        return self.workspace.repo_path("aoa-sdk") / ".aoa" / "closeout"

    def default_queue_paths(self) -> dict[str, Path]:
        root = self.default_closeout_root()
        return {
            "root": root,
            "inbox": root / "inbox",
            "processed": root / "processed",
            "failed": root / "failed",
            "reports": root / "reports",
        }

    def _validate_manifest(self, manifest: CloseoutManifest) -> None:
        if manifest.schema_version != 1:
            raise ValueError(f"unsupported closeout schema_version {manifest.schema_version!r}")
        if not manifest.closeout_id.strip():
            raise ValueError("closeout_id must be a non-empty string")
        if not manifest.session_ref.strip():
            raise ValueError("session_ref must be a non-empty string")
        if not manifest.trigger.strip():
            raise ValueError("trigger must be a non-empty string")
        if not manifest.batches:
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

    def _resolve_input_paths(self, manifest_path: Path, input_paths: list[str]) -> list[Path]:
        resolved: list[Path] = []
        for item in input_paths:
            path = Path(item).expanduser()
            if not path.is_absolute():
                path = (manifest_path.parent / path).resolve()
            else:
                path = path.resolve()
            if not path.exists():
                raise FileNotFoundError(f"missing closeout input: {path}")
            resolved.append(path)
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
