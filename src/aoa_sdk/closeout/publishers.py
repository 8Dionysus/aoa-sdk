from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys

from ..models import CloseoutPublisherRun, CloseoutStatsRefresh


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
        "diagnosis_packet_receipt",
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
