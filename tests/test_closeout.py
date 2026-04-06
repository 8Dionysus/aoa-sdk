from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk import AoASDK
from aoa_sdk.cli.main import app


def install_closeout_fixture(workspace_root: Path) -> dict[str, Path]:
    sdk_root = workspace_root / "aoa-sdk"
    skills_root = workspace_root / "aoa-skills"
    evals_root = workspace_root / "aoa-evals"
    stats_root = workspace_root / "aoa-stats"

    for root in (skills_root, evals_root, stats_root):
        root.mkdir(parents=True, exist_ok=True)
        (root / "README.md").write_text(f"# {root.name}\n", encoding="utf-8")

    skill_script = """#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT_LOG_PATH = Path(__file__).resolve().parents[1] / ".aoa" / "live_receipts" / "session-harvest-family.jsonl"

parser = argparse.ArgumentParser()
parser.add_argument("--input", action="append", default=[])
parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH))
args = parser.parse_args()

log_path = Path(args.log_path).expanduser().resolve()
log_path.parent.mkdir(parents=True, exist_ok=True)
existing = set()
if log_path.exists():
    for raw in log_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        existing.add(json.loads(raw)["event_id"])
appended = 0
skipped = 0
with log_path.open("a", encoding="utf-8") as handle:
    for input_path in args.input:
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
        event_id = payload["event_id"]
        if event_id in existing:
            skipped += 1
            continue
        handle.write(json.dumps(payload, sort_keys=True) + "\\n")
        existing.add(event_id)
        appended += 1
print(f"[ok] appended {appended} session receipts to {log_path}")
print(f"[skip] duplicate event ids skipped: {skipped}")
"""
    eval_script = skill_script.replace(
        "session-harvest-family.jsonl", "eval-result-receipts.jsonl"
    ).replace(
        "session receipts", "eval receipts"
    )
    refresh_script = """#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((REPO_ROOT / "config" / "live_receipt_sources.json").read_text(encoding="utf-8"))
feed_output = REPO_ROOT / "state" / "live_receipts.min.json"
summary_dir = REPO_ROOT / "state" / "generated"
receipts = []
source_count = 0
for source in registry["sources"]:
    path = REPO_ROOT.parent / source["repo"] / source["relative_path"]
    source_count += 1
    if not path.exists():
        continue
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line:
            receipts.append(json.loads(line))
if not receipts:
    if feed_output.exists():
        feed_output.unlink()
    print(f"[ok] cleared live stats because no receipts were found across {source_count} sources")
    print(f"[feed-cleared] {feed_output}")
    print(f"[summaries-cleared] {summary_dir}")
    raise SystemExit(0)
feed_output.parent.mkdir(parents=True, exist_ok=True)
summary_dir.mkdir(parents=True, exist_ok=True)
feed_output.write_text(json.dumps(receipts, indent=2) + "\\n", encoding="utf-8")
(summary_dir / "summary_surface_catalog.min.json").write_text(
    json.dumps(
        {
            "schema_version": "aoa_stats_summary_surface_catalog_v1",
            "generated_from": {
                "receipt_input_paths": [
                    "aoa-skills/.aoa/live_receipts/session-harvest-family.jsonl",
                    "aoa-evals/.aoa/live_receipts/eval-result-receipts.jsonl",
                ],
                "total_receipts": len(receipts),
                "latest_observed_at": receipts[-1]["observed_at"],
            },
            "surfaces": [],
        },
        indent=2,
    )
    + "\\n",
    encoding="utf-8",
)
print(f"[ok] refreshed live stats from {source_count} sources and {len(receipts)} receipts")
print(f"[feed] {feed_output}")
print(f"[summaries] {summary_dir}")
"""

    (skills_root / "scripts").mkdir(parents=True, exist_ok=True)
    (evals_root / "scripts").mkdir(parents=True, exist_ok=True)
    (stats_root / "scripts").mkdir(parents=True, exist_ok=True)
    (stats_root / "config").mkdir(parents=True, exist_ok=True)
    (skills_root / "scripts" / "publish_live_receipts.py").write_text(skill_script, encoding="utf-8")
    (evals_root / "scripts" / "publish_live_receipts.py").write_text(eval_script, encoding="utf-8")
    (stats_root / "scripts" / "refresh_live_stats.py").write_text(refresh_script, encoding="utf-8")

    registry = {
        "schema_version": 1,
        "sources": [
            {
                "name": "skills-live-log",
                "repo": "aoa-skills",
                "relative_path": ".aoa/live_receipts/session-harvest-family.jsonl",
                "required": True,
            },
            {
                "name": "evals-live-log",
                "repo": "aoa-evals",
                "relative_path": ".aoa/live_receipts/eval-result-receipts.jsonl",
                "required": True,
            },
        ],
    }
    (stats_root / "config" / "live_receipt_sources.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )

    manifest_dir = sdk_root / ".aoa" / "closeout" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    receipts_dir = manifest_dir / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    skill_receipt = {
        "event_kind": "harvest_packet_receipt",
        "event_id": "event-skill-001",
        "observed_at": "2026-04-06T18:00:00Z",
        "run_ref": "run-skill-001",
        "session_ref": "session:test-closeout",
        "actor_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "evidence_refs": ["tmp/HARVEST_PACKET.json"],
        "payload": {"route_ref": "route:test-closeout"},
    }
    eval_receipt = {
        "event_kind": "eval_result_receipt",
        "event_id": "event-eval-001",
        "observed_at": "2026-04-06T18:05:00Z",
        "run_ref": "run-eval-001",
        "session_ref": "session:test-closeout",
        "actor_ref": {"repo": "aoa-evals", "kind": "eval", "id": "aoa-bounded-change-quality"},
        "object_ref": {"repo": "aoa-evals", "kind": "eval", "id": "aoa-bounded-change-quality"},
        "evidence_refs": ["tmp/EVAL_RESULT.json"],
        "payload": {"verdict": "green"},
    }
    skill_receipt_path = receipts_dir / "skill.json"
    eval_receipt_path = receipts_dir / "eval.json"
    skill_receipt_path.write_text(json.dumps(skill_receipt, indent=2) + "\n", encoding="utf-8")
    eval_receipt_path.write_text(json.dumps(eval_receipt, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "closeout_id": "closeout-test-001",
        "session_ref": "session:test-closeout",
        "reviewed": True,
        "trigger": "reviewed-closeout",
        "audit_refs": ["notes/reviewed_session_artifact.md"],
        "batches": [
            {
                "publisher": "aoa-skills.session-harvest-family",
                "input_paths": ["receipts/skill.json"],
            },
            {
                "publisher": "aoa-evals.eval-result",
                "input_paths": ["receipts/eval.json"],
            },
        ],
    }
    manifest_path = manifest_dir / "closeout-test-001.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    queue_manifest = {
        "schema_version": 1,
        "closeout_id": "closeout-test-queue-001",
        "session_ref": "session:test-closeout-queue",
        "reviewed": True,
        "trigger": "reviewed-closeout",
        "batches": [
            {
                "publisher": "aoa-skills.session-harvest-family",
                "input_paths": ["../manifests/receipts/skill.json"],
            }
        ],
    }
    inbox_dir = sdk_root / ".aoa" / "closeout" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    queue_manifest_path = inbox_dir / "closeout-test-queue-001.json"
    queue_manifest_path.write_text(json.dumps(queue_manifest, indent=2) + "\n", encoding="utf-8")

    return {
        "manifest_path": manifest_path,
        "queue_manifest_path": queue_manifest_path,
        "skill_log_path": skills_root / ".aoa" / "live_receipts" / "session-harvest-family.jsonl",
        "eval_log_path": evals_root / ".aoa" / "live_receipts" / "eval-result-receipts.jsonl",
        "feed_path": stats_root / "state" / "live_receipts.min.json",
        "summary_catalog_path": stats_root / "state" / "generated" / "summary_surface_catalog.min.json",
        "report_path": sdk_root / ".aoa" / "closeout" / "reports" / "closeout-test-queue-001.report.json",
        "processed_manifest_path": sdk_root / ".aoa" / "closeout" / "processed" / "closeout-test-queue-001.json",
    }


def test_closeout_api_run_publishes_receipts_and_refreshes_stats(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.run(fixture["manifest_path"])

    assert report.closeout_id == "closeout-test-001"
    assert len(report.publisher_runs) == 2
    assert report.publisher_runs[0].appended_count == 1
    assert report.publisher_runs[1].appended_count == 1
    assert report.stats_refresh.receipt_count == 2
    assert fixture["skill_log_path"].exists()
    assert fixture["eval_log_path"].exists()
    assert fixture["feed_path"].exists()
    assert fixture["summary_catalog_path"].exists()


def test_closeout_cli_process_inbox_archives_manifest_and_writes_report(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["closeout", "process-inbox", str(workspace_root / "aoa-sdk"), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["processed_count"] == 1
    assert payload["failed_count"] == 0
    assert payload["items"][0]["status"] == "processed"
    assert fixture["processed_manifest_path"].exists()
    assert fixture["report_path"].exists()
