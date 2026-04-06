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
    playbooks_root = workspace_root / "aoa-playbooks"
    techniques_root = workspace_root / "aoa-techniques"
    memo_root = workspace_root / "aoa-memo"
    stats_root = workspace_root / "aoa-stats"

    for root in (skills_root, evals_root, playbooks_root, techniques_root, memo_root, stats_root):
        root.mkdir(parents=True, exist_ok=True)
        (root / "README.md").write_text(f"# {root.name}\n", encoding="utf-8")

    publisher_script_template = """#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT_LOG_PATH = Path(__file__).resolve().parents[1] / ".aoa" / "live_receipts" / "__LOG_NAME__"

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
print(f"[ok] appended {appended} __LABEL__ receipts to {log_path}")
print(f"[skip] duplicate event ids skipped: {skipped}")
"""
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
                    "aoa-playbooks/.aoa/live_receipts/playbook-receipts.jsonl",
                    "aoa-techniques/.aoa/live_receipts/technique-receipts.jsonl",
                    "aoa-memo/.aoa/live_receipts/memo-writeback-receipts.jsonl",
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
    (playbooks_root / "scripts").mkdir(parents=True, exist_ok=True)
    (techniques_root / "scripts").mkdir(parents=True, exist_ok=True)
    (memo_root / "scripts").mkdir(parents=True, exist_ok=True)
    (stats_root / "scripts").mkdir(parents=True, exist_ok=True)
    (stats_root / "config").mkdir(parents=True, exist_ok=True)
    (skills_root / "scripts" / "publish_live_receipts.py").write_text(
        publisher_script_template.replace("__LOG_NAME__", "session-harvest-family.jsonl").replace("__LABEL__", "session"),
        encoding="utf-8",
    )
    (evals_root / "scripts" / "publish_live_receipts.py").write_text(
        publisher_script_template.replace("__LOG_NAME__", "eval-result-receipts.jsonl").replace("__LABEL__", "eval"),
        encoding="utf-8",
    )
    (playbooks_root / "scripts" / "publish_live_receipts.py").write_text(
        publisher_script_template.replace("__LOG_NAME__", "playbook-receipts.jsonl").replace("__LABEL__", "playbook"),
        encoding="utf-8",
    )
    (techniques_root / "scripts" / "publish_live_receipts.py").write_text(
        publisher_script_template.replace("__LOG_NAME__", "technique-receipts.jsonl").replace("__LABEL__", "technique"),
        encoding="utf-8",
    )
    (memo_root / "scripts" / "publish_live_receipts.py").write_text(
        publisher_script_template.replace("__LOG_NAME__", "memo-writeback-receipts.jsonl").replace("__LABEL__", "memo"),
        encoding="utf-8",
    )
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
            {
                "name": "playbooks-live-log",
                "repo": "aoa-playbooks",
                "relative_path": ".aoa/live_receipts/playbook-receipts.jsonl",
                "required": True,
            },
            {
                "name": "techniques-live-log",
                "repo": "aoa-techniques",
                "relative_path": ".aoa/live_receipts/technique-receipts.jsonl",
                "required": True,
            },
            {
                "name": "memo-live-log",
                "repo": "aoa-memo",
                "relative_path": ".aoa/live_receipts/memo-writeback-receipts.jsonl",
                "required": True,
            },
        ],
    }
    (stats_root / "config" / "live_receipt_sources.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )

    manifest_dir = sdk_root / ".aoa" / "closeout" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    requests_dir = sdk_root / ".aoa" / "closeout" / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    receipts_dir = manifest_dir / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = manifest_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    reviewed_artifact_path = notes_dir / "reviewed_session_artifact.md"
    reviewed_artifact_path.write_text("# Reviewed session artifact\n", encoding="utf-8")
    route_summary_path = notes_dir / "route_summary.md"
    route_summary_path.write_text("# Route summary\n", encoding="utf-8")

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
    playbook_receipt = {
        "event_kind": "playbook_review_harvest_receipt",
        "event_id": "event-playbook-001",
        "observed_at": "2026-04-06T18:06:00Z",
        "run_ref": "run-playbook-001",
        "session_ref": "session:test-closeout",
        "actor_ref": {"repo": "aoa-playbooks", "kind": "playbook", "id": "AOA-P-0021"},
        "object_ref": {"repo": "aoa-playbooks", "kind": "playbook", "id": "AOA-P-0021"},
        "evidence_refs": ["tmp/PLAYBOOK_REVIEW.md"],
        "payload": {"gate_verdict": "composition-landed"},
    }
    technique_receipt = {
        "event_kind": "technique_promotion_receipt",
        "event_id": "event-technique-001",
        "observed_at": "2026-04-06T18:07:00Z",
        "run_ref": "run-technique-001",
        "session_ref": "session:test-closeout",
        "actor_ref": {"repo": "aoa-techniques", "kind": "technique", "id": "AOA-T-0089"},
        "object_ref": {"repo": "aoa-techniques", "kind": "technique", "id": "AOA-T-0089"},
        "evidence_refs": ["tmp/TECHNIQUE.md"],
        "payload": {"promotion_state": "promoted"},
    }
    memo_receipt = {
        "event_kind": "memo_writeback_receipt",
        "event_id": "event-memo-001",
        "observed_at": "2026-04-06T18:08:00Z",
        "run_ref": "run-memo-001",
        "session_ref": "session:test-closeout",
        "actor_ref": {"repo": "aoa-memo", "kind": "memory_object", "id": "memo.decision.test-closeout"},
        "object_ref": {"repo": "aoa-memo", "kind": "memory_object", "id": "memo.decision.test-closeout"},
        "evidence_refs": ["tmp/MEMO.json"],
        "payload": {"target_kind": "decision"},
    }
    skill_receipt_path = receipts_dir / "skill.json"
    eval_receipt_path = receipts_dir / "eval.json"
    playbook_receipt_path = receipts_dir / "playbook.json"
    technique_receipt_path = receipts_dir / "technique.json"
    memo_receipt_path = receipts_dir / "memo.json"
    skill_receipt_path.write_text(json.dumps(skill_receipt, indent=2) + "\n", encoding="utf-8")
    eval_receipt_path.write_text(json.dumps(eval_receipt, indent=2) + "\n", encoding="utf-8")
    playbook_receipt_path.write_text(json.dumps(playbook_receipt, indent=2) + "\n", encoding="utf-8")
    technique_receipt_path.write_text(json.dumps(technique_receipt, indent=2) + "\n", encoding="utf-8")
    memo_receipt_path.write_text(json.dumps(memo_receipt, indent=2) + "\n", encoding="utf-8")

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
            {
                "publisher": "aoa-playbooks.reviewed-run",
                "input_paths": ["receipts/playbook.json"],
            },
            {
                "publisher": "aoa-techniques.promotion",
                "input_paths": ["receipts/technique.json"],
            },
            {
                "publisher": "aoa-memo.writeback",
                "input_paths": ["receipts/memo.json"],
            },
        ],
    }
    manifest_path = manifest_dir / "closeout-test-001.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    build_request = {
        "schema_version": 1,
        "closeout_id": "closeout-build-001",
        "session_ref": "session:test-closeout-build",
        "reviewed": True,
        "reviewed_artifact_path": "../manifests/notes/reviewed_session_artifact.md",
        "trigger": "reviewed-closeout",
        "audit_refs": ["../manifests/notes/route_summary.md"],
        "batches": [
            {
                "publisher": "aoa-skills.session-harvest-family",
                "input_paths": ["../manifests/receipts/skill.json"],
            },
            {
                "publisher": "aoa-evals.eval-result",
                "input_paths": ["../manifests/receipts/eval.json"],
            },
        ],
    }
    build_request_path = requests_dir / "closeout-build-001.request.json"
    build_request_path.write_text(json.dumps(build_request, indent=2) + "\n", encoding="utf-8")

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
        "build_request_path": build_request_path,
        "reviewed_artifact_path": reviewed_artifact_path,
        "route_summary_path": route_summary_path,
        "built_manifest_path": manifest_dir / "closeout-build-001.json",
        "queue_manifest_path": queue_manifest_path,
        "skill_receipt_path": skill_receipt_path,
        "eval_receipt_path": eval_receipt_path,
        "playbook_receipt_path": playbook_receipt_path,
        "technique_receipt_path": technique_receipt_path,
        "memo_receipt_path": memo_receipt_path,
        "skill_log_path": skills_root / ".aoa" / "live_receipts" / "session-harvest-family.jsonl",
        "eval_log_path": evals_root / ".aoa" / "live_receipts" / "eval-result-receipts.jsonl",
        "playbook_log_path": playbooks_root / ".aoa" / "live_receipts" / "playbook-receipts.jsonl",
        "technique_log_path": techniques_root / ".aoa" / "live_receipts" / "technique-receipts.jsonl",
        "memo_log_path": memo_root / ".aoa" / "live_receipts" / "memo-writeback-receipts.jsonl",
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
    assert len(report.publisher_runs) == 5
    assert report.publisher_runs[0].appended_count == 1
    assert report.publisher_runs[1].appended_count == 1
    assert report.publisher_runs[2].appended_count == 1
    assert report.publisher_runs[3].appended_count == 1
    assert report.publisher_runs[4].appended_count == 1
    assert report.stats_refresh.receipt_count == 5
    assert fixture["skill_log_path"].exists()
    assert fixture["eval_log_path"].exists()
    assert fixture["playbook_log_path"].exists()
    assert fixture["technique_log_path"].exists()
    assert fixture["memo_log_path"].exists()
    assert fixture["feed_path"].exists()
    assert fixture["summary_catalog_path"].exists()


def test_closeout_api_enqueue_rewrites_relative_inputs_for_inbox_processing(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.enqueue(fixture["manifest_path"])

    queued_manifest_path = Path(report.queued_manifest_path)
    queued_manifest = json.loads(queued_manifest_path.read_text(encoding="utf-8"))
    assert report.closeout_id == "closeout-test-001"
    assert report.queue_depth == 2
    assert queued_manifest_path.parent == workspace_root / "aoa-sdk" / ".aoa" / "closeout" / "inbox"
    assert all(Path(item).is_absolute() for item in queued_manifest["audit_refs"])
    assert all(
        Path(item).is_absolute()
        for batch in queued_manifest["batches"]
        for item in batch["input_paths"]
    )


def test_closeout_api_build_manifest_can_enqueue_built_manifest(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.build_manifest(fixture["build_request_path"], enqueue=True)

    built_manifest_path = Path(report.manifest_path)
    built_manifest = json.loads(built_manifest_path.read_text(encoding="utf-8"))
    assert report.closeout_id == "closeout-build-001"
    assert report.reviewed_artifact_path == str(fixture["reviewed_artifact_path"])
    assert built_manifest_path == fixture["built_manifest_path"]
    assert built_manifest["audit_refs"] == [
        str(fixture["reviewed_artifact_path"]),
        str(fixture["route_summary_path"]),
    ]
    assert built_manifest["batches"][0]["input_paths"] == [
        str((workspace_root / "aoa-sdk" / ".aoa" / "closeout" / "manifests" / "receipts" / "skill.json").resolve())
    ]
    assert report.enqueue_report is not None
    assert Path(report.enqueue_report.queued_manifest_path).exists()


def test_closeout_api_submit_reviewed_builds_request_and_manifest(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.submit_reviewed(
        fixture["reviewed_artifact_path"],
        session_ref="session:test-submit-reviewed",
        receipt_paths=[fixture["skill_receipt_path"], fixture["eval_receipt_path"]],
        audit_refs=[fixture["route_summary_path"]],
        closeout_id="closeout-submit-001",
        enqueue=False,
    )

    request_path = Path(report.request_path)
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert report.closeout_id == "closeout-submit-001"
    assert report.detected_publishers == [
        "aoa-evals.eval-result",
        "aoa-skills.session-harvest-family",
    ]
    assert request_path == workspace_root / "aoa-sdk" / ".aoa" / "closeout" / "requests" / "closeout-submit-001.request.json"
    assert request_payload["reviewed_artifact_path"] == str(fixture["reviewed_artifact_path"])
    assert request_payload["audit_refs"] == [str(fixture["route_summary_path"])]
    assert report.build_report.manifest_path.endswith(".aoa/closeout/manifests/closeout-submit-001.json")
    assert report.build_report.enqueue_report is None


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


def test_closeout_cli_status_reports_queue_state(workspace_root: Path) -> None:
    install_closeout_fixture(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["closeout", "status", str(workspace_root / "aoa-sdk"), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["request_count"] == 1
    assert payload["manifest_count"] == 1
    assert payload["pending_manifest_count"] == 1
    assert payload["processed_manifest_count"] == 0
    assert payload["failed_manifest_count"] == 0
    assert payload["report_count"] == 0
    assert payload["pending_manifest_paths"]
    assert payload["latest_request_path"].endswith(
        ".aoa/closeout/requests/closeout-build-001.request.json"
    )
    assert payload["latest_manifest_path"].endswith(".aoa/closeout/manifests/closeout-test-001.json")
