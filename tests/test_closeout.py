from __future__ import annotations

import json
from pathlib import Path

import pytest
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
from collections import defaultdict
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
(core_summary := defaultdict(lambda: {
    "application_count": 0,
    "latest_observed_at": "",
    "latest_session_ref": "",
    "latest_run_ref": "",
    "detail_event_kind_counts": defaultdict(int),
}))  # type: ignore[call-arg]
for receipt in receipts:
    if receipt.get("event_kind") != "core_skill_application_receipt":
        continue
    payload = receipt.get("payload", {})
    kernel_id = payload.get("kernel_id", "unknown-kernel")
    skill_name = payload.get("skill_name", "unknown-skill")
    detail_event_kind = payload.get("detail_event_kind", "unknown-detail-event")
    key = (kernel_id, skill_name)
    entry = core_summary[key]
    entry["application_count"] += 1
    entry["latest_observed_at"] = receipt["observed_at"]
    entry["latest_session_ref"] = receipt["session_ref"]
    entry["latest_run_ref"] = receipt["run_ref"]
    entry["detail_event_kind_counts"][detail_event_kind] += 1
(summary_dir / "core_skill_application_summary.min.json").write_text(
    json.dumps(
        {
            "schema_version": "aoa_stats_core_skill_application_summary_v1",
            "generated_from": {
                "receipt_input_paths": [
                    "aoa-skills/.aoa/live_receipts/session-harvest-family.jsonl",
                    "aoa-skills/.aoa/live_receipts/core-skill-applications.jsonl",
                    "aoa-evals/.aoa/live_receipts/eval-result-receipts.jsonl",
                    "aoa-playbooks/.aoa/live_receipts/playbook-receipts.jsonl",
                    "aoa-techniques/.aoa/live_receipts/technique-receipts.jsonl",
                    "aoa-memo/.aoa/live_receipts/memo-writeback-receipts.jsonl",
                ],
                "total_receipts": len(receipts),
                "latest_observed_at": receipts[-1]["observed_at"],
            },
            "skills": [
                {
                    "kernel_id": kernel_id,
                    "skill_name": skill_name,
                    "application_count": entry["application_count"],
                    "latest_observed_at": entry["latest_observed_at"],
                    "latest_session_ref": entry["latest_session_ref"],
                    "latest_run_ref": entry["latest_run_ref"],
                    "detail_event_kind_counts": dict(entry["detail_event_kind_counts"]),
                }
                for (kernel_id, skill_name), entry in sorted(core_summary.items())
            ],
        },
        indent=2,
    )
    + "\\n",
    encoding="utf-8",
)
(summary_dir / "summary_surface_catalog.min.json").write_text(
    json.dumps(
        {
            "schema_version": "aoa_stats_summary_surface_catalog_v1",
            "generated_from": {
                "receipt_input_paths": [
                    "aoa-skills/.aoa/live_receipts/session-harvest-family.jsonl",
                    "aoa-skills/.aoa/live_receipts/core-skill-applications.jsonl",
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
    (skills_root / "scripts" / "publish_core_skill_receipts.py").write_text(
        publisher_script_template.replace("__LOG_NAME__", "core-skill-applications.jsonl").replace("__LABEL__", "core skill"),
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

    (skills_root / "generated").mkdir(parents=True, exist_ok=True)
    (skills_root / "generated" / "project_core_skill_kernel.min.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_config": "config/project_core_skill_kernel.json",
                "kernel_id": "project-core-session-growth-v1",
                "owner_repo": "aoa-skills",
                "description": "Canonical project-core kernel for explicit reviewed session growth work.",
                "canonical_install_profile": "repo-project-core-kernel",
                "backward_compatible_aliases": ["repo-session-harvest-family"],
                "skill_count": 7,
                "skills": [
                    "aoa-session-donor-harvest",
                    "aoa-automation-opportunity-scan",
                    "aoa-session-route-forks",
                    "aoa-session-self-diagnose",
                    "aoa-session-self-repair",
                    "aoa-session-progression-lift",
                    "aoa-quest-harvest",
                ],
                "governance_contract": {
                    "core_receipt_kind": "core_skill_application_receipt",
                    "core_receipt_schema_ref": "references/core-skill-application-receipt-schema.yaml",
                    "detail_publisher": "aoa-skills.session-harvest-family",
                    "core_publisher": "aoa-skills.core-kernel-applications",
                    "stats_surface": "aoa-stats.core_skill_application_summary.min",
                    "application_stage": "finish",
                },
                "skill_contracts": [
                    {
                        "skill_name": "aoa-session-donor-harvest",
                        "detail_event_kind": "harvest_packet_receipt",
                        "detail_receipt_schema_ref": "references/harvest-packet-receipt-schema.yaml",
                    },
                    {
                        "skill_name": "aoa-automation-opportunity-scan",
                        "detail_event_kind": "automation_candidate_receipt",
                        "detail_receipt_schema_ref": "references/automation-candidate-receipt-schema.yaml",
                    },
                    {
                        "skill_name": "aoa-session-route-forks",
                        "detail_event_kind": "decision_fork_receipt",
                        "detail_receipt_schema_ref": "references/decision-fork-receipt-schema.yaml",
                    },
                    {
                        "skill_name": "aoa-session-self-diagnose",
                        "detail_event_kind": "diagnosis_packet_receipt",
                        "detail_receipt_schema_ref": "references/diagnosis-packet-receipt-schema.yaml",
                    },
                    {
                        "skill_name": "aoa-session-self-repair",
                        "detail_event_kind": "repair_cycle_receipt",
                        "detail_receipt_schema_ref": "references/repair-cycle-receipt-schema.yaml",
                    },
                    {
                        "skill_name": "aoa-session-progression-lift",
                        "detail_event_kind": "progression_delta_receipt",
                        "detail_receipt_schema_ref": "references/progression-delta-receipt-schema.yaml",
                    },
                    {
                        "skill_name": "aoa-quest-harvest",
                        "detail_event_kind": "quest_promotion_receipt",
                        "detail_receipt_schema_ref": "references/quest-promotion-receipt-schema.yaml",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

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
                "name": "skills-core-kernel-live-log",
                "repo": "aoa-skills",
                "relative_path": ".aoa/live_receipts/core-skill-applications.jsonl",
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
        "actor_ref": "aoa-skills:aoa-session-donor-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "evidence_refs": ["tmp/HARVEST_PACKET.json"],
        "payload": {"route_ref": "route:test-closeout"},
    }
    core_skill_receipt = {
        "event_kind": "core_skill_application_receipt",
        "event_id": "event-core-skill-001",
        "observed_at": "2026-04-06T18:00:01Z",
        "run_ref": "run-skill-001",
        "session_ref": "session:test-closeout",
        "actor_ref": "aoa-skills:aoa-session-donor-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "evidence_refs": ["tmp/HARVEST_PACKET_RECEIPT.json"],
        "payload": {
            "kernel_id": "project-core-session-growth-v1",
            "skill_name": "aoa-session-donor-harvest",
            "application_stage": "finish",
            "detail_event_kind": "harvest_packet_receipt",
            "detail_receipt_ref": "tmp/HARVEST_PACKET_RECEIPT.json",
            "route_ref": "route:test-closeout",
        },
    }
    eval_receipt = {
        "event_kind": "eval_result_receipt",
        "event_id": "event-eval-001",
        "observed_at": "2026-04-06T18:05:00Z",
        "run_ref": "run-eval-001",
        "session_ref": "session:test-closeout",
        "actor_ref": "aoa-evals:aoa-bounded-change-quality",
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
        "actor_ref": "aoa-playbooks:AOA-P-0021",
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
        "actor_ref": "aoa-techniques:AOA-T-0089",
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
        "actor_ref": "aoa-memo:memo.decision.test-closeout",
        "object_ref": {"repo": "aoa-memo", "kind": "memory_object", "id": "memo.decision.test-closeout"},
        "evidence_refs": ["tmp/MEMO.json"],
        "payload": {"target_kind": "decision"},
    }
    skill_receipt_path = receipts_dir / "skill.json"
    core_skill_receipt_path = receipts_dir / "skill-core.json"
    eval_receipt_path = receipts_dir / "eval.json"
    playbook_receipt_path = receipts_dir / "playbook.json"
    technique_receipt_path = receipts_dir / "technique.json"
    memo_receipt_path = receipts_dir / "memo.json"
    skill_receipt_path.write_text(json.dumps(skill_receipt, indent=2) + "\n", encoding="utf-8")
    core_skill_receipt_path.write_text(
        json.dumps(core_skill_receipt, indent=2) + "\n", encoding="utf-8"
    )
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
                "publisher": "aoa-skills.core-kernel-applications",
                "input_paths": ["receipts/skill-core.json"],
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
                "publisher": "aoa-skills.core-kernel-applications",
                "input_paths": ["../manifests/receipts/skill-core.json"],
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
        "core_skill_receipt_path": core_skill_receipt_path,
        "eval_receipt_path": eval_receipt_path,
        "playbook_receipt_path": playbook_receipt_path,
        "technique_receipt_path": technique_receipt_path,
        "memo_receipt_path": memo_receipt_path,
        "skill_log_path": skills_root / ".aoa" / "live_receipts" / "session-harvest-family.jsonl",
        "core_skill_log_path": skills_root / ".aoa" / "live_receipts" / "core-skill-applications.jsonl",
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
    assert len(report.publisher_runs) == 6
    assert report.publisher_runs[0].appended_count == 1
    assert report.publisher_runs[1].appended_count == 1
    assert report.publisher_runs[2].appended_count == 1
    assert report.publisher_runs[3].appended_count == 1
    assert report.publisher_runs[4].appended_count == 1
    assert report.publisher_runs[5].appended_count == 1
    assert report.stats_refresh.receipt_count == 6
    assert report.kernel_next_step_brief is not None
    assert report.kernel_next_step_brief.suggested_action == "invoke-core-skill"
    assert report.kernel_next_step_brief.suggested_skill_name == "aoa-automation-opportunity-scan"
    assert report.kernel_next_step_brief.kernel_usage_counts["aoa-session-donor-harvest"] == 1
    assert fixture["skill_log_path"].exists()
    assert fixture["core_skill_log_path"].exists()
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


def test_closeout_api_build_manifest_keeps_missing_optional_audit_refs(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    build_request_path = fixture["build_request_path"]
    payload = json.loads(build_request_path.read_text(encoding="utf-8"))
    payload["audit_refs"].append("../manifests/notes/missing_optional_audit.md")
    build_request_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    report = sdk.closeout.build_manifest(build_request_path, enqueue=False, overwrite=True)

    built_manifest = json.loads(Path(report.manifest_path).read_text(encoding="utf-8"))
    assert built_manifest["audit_refs"] == [
        str(fixture["reviewed_artifact_path"]),
        str(fixture["route_summary_path"]),
        str(
            (
                workspace_root
                / "aoa-sdk"
                / ".aoa"
                / "closeout"
                / "manifests"
                / "notes"
                / "missing_optional_audit.md"
            ).resolve()
        ),
    ]


def test_closeout_api_submit_reviewed_builds_request_and_manifest(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.submit_reviewed(
        fixture["reviewed_artifact_path"],
        session_ref="session:test-closeout",
        receipt_paths=[
            fixture["skill_receipt_path"],
            fixture["core_skill_receipt_path"],
            fixture["eval_receipt_path"],
        ],
        audit_refs=[fixture["route_summary_path"]],
        closeout_id="closeout-submit-001",
        enqueue=False,
    )

    request_path = Path(report.request_path)
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert report.closeout_id == "closeout-submit-001"
    assert report.detected_publishers == [
        "aoa-evals.eval-result",
        "aoa-skills.core-kernel-applications",
        "aoa-skills.session-harvest-family",
    ]
    assert request_path == workspace_root / "aoa-sdk" / ".aoa" / "closeout" / "requests" / "closeout-submit-001.request.json"
    assert request_payload["reviewed_artifact_path"] == str(fixture["reviewed_artifact_path"])
    assert request_payload["audit_refs"] == [str(fixture["route_summary_path"])]
    assert report.build_report.manifest_path.endswith(".aoa/closeout/manifests/closeout-submit-001.json")
    assert report.build_report.enqueue_report is None


def test_closeout_api_submit_reviewed_accepts_diagnosis_packet_receipts(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipts_dir = fixture["skill_receipt_path"].parent

    diagnosis_receipt_path = receipts_dir / "diagnosis.json"
    diagnosis_core_receipt_path = receipts_dir / "diagnosis-core.json"
    diagnosis_receipt_path.write_text(
        json.dumps(
            {
                "event_kind": "diagnosis_packet_receipt",
                "event_id": "event-diagnosis-submit-reviewed-001",
                "observed_at": "2026-04-06T09:00:00Z",
                "run_ref": "run-diagnosis-submit-reviewed-001",
                "session_ref": "session:test-closeout",
                "actor_ref": "aoa-skills:aoa-session-self-diagnose",
                "object_ref": {
                    "repo": "aoa-skills",
                    "kind": "skill",
                    "id": "aoa-session-self-diagnose",
                    "version": "main",
                },
                "evidence_refs": [
                    {
                        "kind": "diagnosis_packet",
                        "ref": str(fixture["reviewed_artifact_path"]),
                        "role": "primary",
                    }
                ],
                "payload": {
                    "route_ref": "route:test-closeout",
                    "skill_name": "aoa-session-self-diagnose",
                    "result_kind": "diagnosis_packet",
                    "diagnosis_types": ["boundary-drift", "proof-debt"],
                    "symptom_refs": ["artifact:test-closeout/diagnosis-gap"],
                    "probable_cause_hypotheses": ["reviewed follow-through still needs explicit filtering"],
                    "confidence_band": "medium",
                    "owner_hints": ["aoa-sdk", "aoa-stats"],
                    "blocked_automation_causes": ["public-share-requires-sanitization-review"],
                    "repair_handoff": "aoa-session-self-repair",
                    "unknowns": ["another reviewed run should confirm the route boundary"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    diagnosis_core_receipt_path.write_text(
        json.dumps(
            {
                "event_kind": "core_skill_application_receipt",
                "event_id": "event-diagnosis-submit-reviewed-core-001",
                "observed_at": "2026-04-06T09:03:00Z",
                "run_ref": "run-diagnosis-submit-reviewed-001",
                "session_ref": "session:test-closeout",
                "actor_ref": "aoa-skills:aoa-session-self-diagnose",
                "object_ref": {
                    "repo": "aoa-skills",
                    "kind": "skill",
                    "id": "aoa-session-self-diagnose",
                    "version": "main",
                },
                "evidence_refs": [
                    {
                        "kind": "detail_receipt",
                        "ref": str(diagnosis_receipt_path),
                        "role": "primary",
                    }
                ],
                "payload": {
                    "kernel_id": "project-core-session-growth-v1",
                    "skill_name": "aoa-session-self-diagnose",
                    "application_stage": "finish",
                    "detail_event_kind": "diagnosis_packet_receipt",
                    "detail_receipt_ref": str(diagnosis_receipt_path),
                    "route_ref": "route:test-closeout",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.closeout.submit_reviewed(
        fixture["reviewed_artifact_path"],
        session_ref="session:test-closeout",
        receipt_paths=[diagnosis_receipt_path, diagnosis_core_receipt_path],
        closeout_id="closeout-submit-diagnosis-001",
        enqueue=False,
    )

    assert report.detected_publishers == [
        "aoa-skills.core-kernel-applications",
        "aoa-skills.session-harvest-family",
    ]


def test_closeout_api_submit_reviewed_allows_missing_optional_audit_refs(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    missing_audit_ref = fixture["reviewed_artifact_path"].parent / "missing_audit_ref.md"

    report = sdk.closeout.submit_reviewed(
        fixture["reviewed_artifact_path"],
        session_ref="session:test-audit-only-optional-refs",
        audit_refs=[missing_audit_ref],
        closeout_id="closeout-audit-only-optional-refs-001",
        enqueue=False,
        allow_empty=True,
    )

    request_payload = json.loads(Path(report.request_path).read_text(encoding="utf-8"))
    manifest_payload = json.loads(Path(report.build_report.manifest_path).read_text(encoding="utf-8"))
    assert request_payload["audit_refs"] == [str(missing_audit_ref.resolve())]
    assert manifest_payload["audit_refs"] == [
        str(fixture["reviewed_artifact_path"]),
        str(missing_audit_ref.resolve()),
    ]


def test_closeout_api_submit_reviewed_rejects_mismatched_receipt_session_refs(
    workspace_root: Path,
) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    mismatched_receipt_path = fixture["skill_receipt_path"].parent / "skill-mismatch.json"
    mismatched_receipt = json.loads(fixture["skill_receipt_path"].read_text(encoding="utf-8"))
    mismatched_receipt["session_ref"] = "session:other-closeout"
    mismatched_receipt_path.write_text(
        json.dumps(mismatched_receipt, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match expected"):
        sdk.closeout.submit_reviewed(
            fixture["reviewed_artifact_path"],
            session_ref="session:test-closeout",
            receipt_paths=[mismatched_receipt_path],
            closeout_id="closeout-submit-mismatch-001",
            enqueue=False,
        )


def test_closeout_api_submit_reviewed_can_build_audit_only_closeout(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.submit_reviewed(
        fixture["reviewed_artifact_path"],
        session_ref="session:test-audit-only",
        audit_refs=[fixture["route_summary_path"]],
        closeout_id="closeout-audit-only-001",
        enqueue=False,
        allow_empty=True,
    )

    request_path = Path(report.request_path)
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    manifest_payload = json.loads(Path(report.build_report.manifest_path).read_text(encoding="utf-8"))
    assert report.audit_only is True
    assert report.receipt_paths == []
    assert report.detected_publishers == []
    assert request_payload["audit_only"] is True
    assert request_payload["batches"] == []
    assert manifest_payload["audit_only"] is True
    assert manifest_payload["batches"] == []


def test_closeout_api_run_audit_only_skips_stats_refresh(workspace_root: Path) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.closeout.submit_reviewed(
        fixture["reviewed_artifact_path"],
        session_ref="session:test-audit-only-run",
        audit_refs=[fixture["route_summary_path"]],
        closeout_id="closeout-audit-only-run-001",
        enqueue=False,
        allow_empty=True,
    )
    run_report = sdk.closeout.run(report.build_report.manifest_path)

    assert run_report.audit_only is True
    assert run_report.publisher_runs == []
    assert run_report.stats_refresh.command == []
    assert "audit-only closeout requested" in run_report.stats_refresh.stdout
    assert run_report.kernel_next_step_brief is None


def test_closeout_api_run_returns_shift_to_owner_layer_brief_for_quest_promotion(
    workspace_root: Path,
) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipts_dir = fixture["skill_receipt_path"].parent
    manifest_dir = fixture["manifest_path"].parent
    notes_dir = manifest_dir / "notes"
    triage_path = notes_dir / "QUEST_PROMOTION_TRIAGE.json"
    triage_path.write_text(
        json.dumps(
            {
                "quest_unit_name": "owner-first capability landing campaign",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    quest_receipt = {
        "event_kind": "quest_promotion_receipt",
        "event_id": "event-quest-001",
        "observed_at": "2026-04-06T19:00:00Z",
        "run_ref": "run-quest-001",
        "session_ref": "session:test-closeout-quest",
        "actor_ref": "aoa-skills:aoa-quest-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-quest-harvest"},
        "evidence_refs": [{"kind": "quest_triage", "ref": str(triage_path)}],
        "payload": {
            "promotion_verdict": "promote_to_playbook",
            "owner_repo": "aoa-playbooks",
            "next_surface": "playbooks/owner-first-capability-landing/PLAYBOOK.md",
            "nearest_wrong_target": "promote_to_skill",
            "bounded_unit_ref": "candidate:owner-first-capability-landing-campaign",
        },
    }
    quest_core_receipt = {
        "event_kind": "core_skill_application_receipt",
        "event_id": "event-core-quest-001",
        "observed_at": "2026-04-06T19:00:01Z",
        "run_ref": "run-quest-001",
        "session_ref": "session:test-closeout-quest",
        "actor_ref": "aoa-skills:aoa-quest-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-quest-harvest"},
        "evidence_refs": ["tmp/QUEST_PROMOTION_RECEIPT.json"],
        "payload": {
            "kernel_id": "project-core-session-growth-v1",
            "skill_name": "aoa-quest-harvest",
            "application_stage": "finish",
            "detail_event_kind": "quest_promotion_receipt",
            "detail_receipt_ref": "tmp/QUEST_PROMOTION_RECEIPT.json",
        },
    }
    quest_receipt_path = receipts_dir / "quest.json"
    quest_core_receipt_path = receipts_dir / "quest-core.json"
    quest_receipt_path.write_text(json.dumps(quest_receipt, indent=2) + "\n", encoding="utf-8")
    quest_core_receipt_path.write_text(json.dumps(quest_core_receipt, indent=2) + "\n", encoding="utf-8")

    quest_manifest_path = manifest_dir / "closeout-test-quest.json"
    quest_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "closeout_id": "closeout-test-quest",
                "session_ref": "session:test-closeout-quest",
                "reviewed": True,
                "trigger": "reviewed-closeout",
                "batches": [
                    {
                        "publisher": "aoa-skills.session-harvest-family",
                        "input_paths": ["receipts/quest.json"],
                    },
                    {
                        "publisher": "aoa-skills.core-kernel-applications",
                        "input_paths": ["receipts/quest-core.json"],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.closeout.run(quest_manifest_path)

    assert report.kernel_next_step_brief is not None
    assert report.kernel_next_step_brief.suggested_action == "shift-to-owner-layer"
    assert report.kernel_next_step_brief.suggested_skill_name is None
    assert report.kernel_next_step_brief.suggested_owner_repo == "aoa-playbooks"
    assert report.owner_handoff_path is not None
    assert Path(report.owner_handoff_path).exists()
    assert len(report.owner_follow_through_briefs) == 1
    handoff = report.owner_follow_through_briefs[0]
    assert handoff.suggested_action == "author-owner-artifact"
    assert handoff.owner_repo == "aoa-playbooks"
    assert handoff.next_surface == "playbooks/owner-first-capability-landing/PLAYBOOK.md"
    assert handoff.unit_name == "owner-first capability landing campaign"


def test_closeout_api_run_surfaces_workflow_follow_through_for_reanchor_progression(
    workspace_root: Path,
) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipts_dir = fixture["skill_receipt_path"].parent
    manifest_dir = fixture["manifest_path"].parent
    notes_dir = manifest_dir / "notes"

    triage_path = notes_dir / "QUEST_PROMOTION_TRIAGE.reanchor.json"
    triage_path.write_text(
        json.dumps({"quest_unit_name": "route still needs a bounded follow-through quest"}, indent=2) + "\n",
        encoding="utf-8",
    )
    progression_packet_path = notes_dir / "PROGRESSION_DELTA.reanchor.json"
    progression_packet_path.write_text(
        json.dumps(
            {
                "verdict": "reanchor",
                "axis_deltas": {"boundary_integrity": -1, "execution_reliability": 1},
                "cautions": ["boundary drift still needs reread before the next mutation-heavy loop"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    progression_receipt = {
        "event_kind": "progression_delta_receipt",
        "event_id": "event-progression-reanchor-001",
        "observed_at": "2026-04-06T19:00:00Z",
        "run_ref": "run-progression-reanchor-001",
        "session_ref": "session:test-closeout-reanchor-workflow",
        "actor_ref": "aoa-skills:aoa-session-progression-lift",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-progression-lift"},
        "evidence_refs": [{"kind": "progression_packet", "ref": str(progression_packet_path)}],
        "payload": {
            "verdict": "reanchor",
            "axis_deltas": {"boundary_integrity": -1, "execution_reliability": 1},
            "cautions": ["boundary drift still needs reread before the next mutation-heavy loop"],
        },
    }
    quest_receipt = {
        "event_kind": "quest_promotion_receipt",
        "event_id": "event-quest-reanchor-001",
        "observed_at": "2026-04-06T19:00:01Z",
        "run_ref": "run-quest-reanchor-001",
        "session_ref": "session:test-closeout-reanchor-workflow",
        "actor_ref": "aoa-skills:aoa-quest-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-quest-harvest"},
        "evidence_refs": [{"kind": "quest_triage", "ref": str(triage_path)}],
        "payload": {
            "promotion_verdict": "keep_open_quest",
            "owner_repo": "aoa-playbooks",
            "next_surface": "quests/test-closeout-reanchor-workflow-followup/QUEST.md",
            "nearest_wrong_target": "promote_to_skill",
            "bounded_unit_ref": "candidate:route:aoa-playbooks-playbook-registry-min",
        },
    }
    quest_core_receipt = {
        "event_kind": "core_skill_application_receipt",
        "event_id": "event-core-quest-reanchor-001",
        "observed_at": "2026-04-06T19:00:02Z",
        "run_ref": "run-quest-reanchor-001",
        "session_ref": "session:test-closeout-reanchor-workflow",
        "actor_ref": "aoa-skills:aoa-quest-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-quest-harvest"},
        "evidence_refs": ["tmp/QUEST_PROMOTION_RECEIPT.json"],
        "payload": {
            "kernel_id": "project-core-session-growth-v1",
            "skill_name": "aoa-quest-harvest",
            "application_stage": "finish",
            "detail_event_kind": "quest_promotion_receipt",
            "detail_receipt_ref": "tmp/QUEST_PROMOTION_RECEIPT.json",
        },
    }
    progression_receipt_path = receipts_dir / "progression-reanchor.json"
    quest_receipt_path = receipts_dir / "quest-reanchor.json"
    quest_core_receipt_path = receipts_dir / "quest-reanchor-core.json"
    progression_receipt_path.write_text(json.dumps(progression_receipt, indent=2) + "\n", encoding="utf-8")
    quest_receipt_path.write_text(json.dumps(quest_receipt, indent=2) + "\n", encoding="utf-8")
    quest_core_receipt_path.write_text(json.dumps(quest_core_receipt, indent=2) + "\n", encoding="utf-8")

    manifest_path = manifest_dir / "closeout-test-reanchor-workflow.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "closeout_id": "closeout-test-reanchor-workflow",
                "session_ref": "session:test-closeout-reanchor-workflow",
                "reviewed": True,
                "trigger": "reviewed-closeout",
                "batches": [
                    {
                        "publisher": "aoa-skills.session-harvest-family",
                        "input_paths": [
                            str(progression_receipt_path),
                            str(quest_receipt_path),
                        ],
                    },
                    {
                        "publisher": "aoa-skills.core-kernel-applications",
                        "input_paths": [str(quest_core_receipt_path)],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.closeout.run(manifest_path)

    assert any(
        brief.skill_name == "aoa-session-self-diagnose"
        for brief in report.workflow_follow_through_briefs
    )
    diagnose_brief = next(
        brief
        for brief in report.workflow_follow_through_briefs
        if brief.skill_name == "aoa-session-self-diagnose"
    )
    assert "reanchor" in diagnose_brief.reason
    assert report.owner_handoff_path is not None
    handoff_payload = json.loads(Path(report.owner_handoff_path).read_text(encoding="utf-8"))
    assert any(
        item["skill_name"] == "aoa-session-self-diagnose"
        for item in handoff_payload["workflow_items"]
    )


def test_closeout_api_run_surfaces_self_repair_when_diagnosis_exists_without_repair(
    workspace_root: Path,
) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipts_dir = fixture["skill_receipt_path"].parent
    manifest_dir = fixture["manifest_path"].parent
    notes_dir = manifest_dir / "notes"

    diagnosis_packet_path = notes_dir / "DIAGNOSIS_PACKET.json"
    diagnosis_packet_path.write_text(
        json.dumps({"diagnosis_types": ["boundary-drift", "workflow-gap"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    diagnosis_receipt = {
        "event_kind": "diagnosis_packet_receipt",
        "event_id": "event-diagnosis-001",
        "observed_at": "2026-04-06T19:10:00Z",
        "run_ref": "run-diagnosis-001",
        "session_ref": "session:test-closeout-diagnosis-gap",
        "actor_ref": "aoa-skills:aoa-session-self-diagnose",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-self-diagnose"},
        "evidence_refs": [{"kind": "diagnosis_packet", "ref": str(diagnosis_packet_path)}],
        "payload": {
            "skill_name": "aoa-session-self-diagnose",
            "result_kind": "diagnosis_packet_ready",
            "diagnosis_types": ["boundary-drift", "workflow-gap"],
        },
    }
    diagnosis_receipt_path = receipts_dir / "diagnosis-gap.json"
    diagnosis_receipt_path.write_text(
        json.dumps(diagnosis_receipt, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest_path = manifest_dir / "closeout-test-diagnosis-gap.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "closeout_id": "closeout-test-diagnosis-gap",
                "session_ref": "session:test-closeout-diagnosis-gap",
                "reviewed": True,
                "trigger": "reviewed-closeout",
                "batches": [
                    {
                        "publisher": "aoa-skills.session-harvest-family",
                        "input_paths": [str(diagnosis_receipt_path)],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.closeout.run(manifest_path)

    assert any(
        brief.skill_name == "aoa-session-self-repair"
        for brief in report.workflow_follow_through_briefs
    )
    repair_brief = next(
        brief
        for brief in report.workflow_follow_through_briefs
        if brief.skill_name == "aoa-session-self-repair"
    )
    assert "no repair_cycle_receipt landed yet" in repair_brief.reason
    assert report.owner_handoff_path is not None
    handoff_payload = json.loads(Path(report.owner_handoff_path).read_text(encoding="utf-8"))
    assert any(
        item["skill_name"] == "aoa-session-self-repair"
        for item in handoff_payload["workflow_items"]
    )


def test_closeout_api_run_surfaces_self_repair_for_legacy_skill_run_receipt(
    workspace_root: Path,
) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipts_dir = fixture["skill_receipt_path"].parent
    manifest_dir = fixture["manifest_path"].parent
    notes_dir = manifest_dir / "notes"

    diagnosis_packet_path = notes_dir / "DIAGNOSIS_PACKET_LEGACY.json"
    diagnosis_packet_path.write_text(
        json.dumps({"diagnosis_types": ["authority-seam"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    diagnosis_receipt = {
        "event_kind": "skill_run_receipt",
        "event_id": "event-diagnosis-legacy-001",
        "observed_at": "2026-04-06T19:11:00Z",
        "run_ref": "run-diagnosis-legacy-001",
        "session_ref": "session:test-closeout-diagnosis-gap-legacy",
        "actor_ref": "aoa-skills:aoa-session-self-diagnose",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-self-diagnose"},
        "evidence_refs": [{"kind": "diagnosis_packet", "ref": str(diagnosis_packet_path)}],
        "payload": {"diagnosis_types": ["authority-seam"]},
    }
    diagnosis_receipt_path = receipts_dir / "diagnosis-gap-legacy.json"
    diagnosis_receipt_path.write_text(
        json.dumps(diagnosis_receipt, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest_path = manifest_dir / "closeout-test-diagnosis-gap-legacy.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "closeout_id": "closeout-test-diagnosis-gap-legacy",
                "session_ref": "session:test-closeout-diagnosis-gap-legacy",
                "reviewed": True,
                "trigger": "reviewed-closeout",
                "batches": [
                    {
                        "publisher": "aoa-skills.session-harvest-family",
                        "input_paths": [str(diagnosis_receipt_path)],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.closeout.run(manifest_path)

    assert any(
        brief.skill_name == "aoa-session-self-repair"
        for brief in report.workflow_follow_through_briefs
    )


def test_closeout_api_run_builds_owner_follow_through_from_harvest_packet(
    workspace_root: Path,
) -> None:
    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipts_dir = fixture["skill_receipt_path"].parent
    manifest_dir = fixture["manifest_path"].parent
    notes_dir = manifest_dir / "notes"

    harvest_packet_path = notes_dir / "HARVEST_PACKET.json"
    harvest_packet_path.write_text(
        json.dumps(
            {
                "accepted_candidates": [
                    {
                        "candidate_ref": "candidate:project-foundation-workspace-landing-route",
                        "unit_name": "project-foundation workspace landing route",
                        "abstraction_shape": "playbook",
                        "owner_repo_recommendation": "aoa-playbooks",
                        "chosen_next_artifact": "playbooks/project-foundation-workspace-landing/PLAYBOOK.md",
                        "nearest_wrong_target": "skill",
                        "owner_reason": "The surviving object is a multi-step route rather than a leaf workflow.",
                        "evidence_anchors": ["/srv/AbyssOS/8Dionysus/docs/WORKSPACE_INSTALL.md"],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    harvest_receipt = {
        "event_kind": "harvest_packet_receipt",
        "event_id": "event-harvest-002",
        "observed_at": "2026-04-06T20:00:00Z",
        "run_ref": "run-harvest-002",
        "session_ref": "session:test-closeout-harvest-handoff",
        "actor_ref": "aoa-skills:aoa-session-donor-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "evidence_refs": [{"kind": "harvest_packet", "ref": str(harvest_packet_path)}],
        "payload": {"route_ref": "route:test-harvest-handoff"},
    }
    harvest_core_receipt = {
        "event_kind": "core_skill_application_receipt",
        "event_id": "event-core-harvest-002",
        "observed_at": "2026-04-06T20:00:01Z",
        "run_ref": "run-harvest-002",
        "session_ref": "session:test-closeout-harvest-handoff",
        "actor_ref": "aoa-skills:aoa-session-donor-harvest",
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "evidence_refs": [{"kind": "receipt", "ref": "tmp/HARVEST_PACKET_RECEIPT.json"}],
        "payload": {
            "kernel_id": "project-core-session-growth-v1",
            "skill_name": "aoa-session-donor-harvest",
            "application_stage": "finish",
            "detail_event_kind": "harvest_packet_receipt",
            "detail_receipt_ref": "tmp/HARVEST_PACKET_RECEIPT.json",
            "route_ref": "route:test-harvest-handoff",
        },
    }
    harvest_receipt_path = receipts_dir / "harvest-handoff.json"
    harvest_core_receipt_path = receipts_dir / "harvest-handoff-core.json"
    harvest_receipt_path.write_text(
        json.dumps(harvest_receipt, indent=2) + "\n", encoding="utf-8"
    )
    harvest_core_receipt_path.write_text(
        json.dumps(harvest_core_receipt, indent=2) + "\n", encoding="utf-8"
    )

    harvest_manifest_path = manifest_dir / "closeout-test-harvest-handoff.json"
    harvest_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "closeout_id": "closeout-test-harvest-handoff",
                "session_ref": "session:test-closeout-harvest-handoff",
                "reviewed": True,
                "audit_only": False,
                "trigger": "reviewed-closeout",
                "batches": [
                    {
                        "publisher": "aoa-skills.session-harvest-family",
                        "input_paths": [str(harvest_receipt_path)],
                    },
                    {
                        "publisher": "aoa-skills.core-kernel-applications",
                        "input_paths": [str(harvest_core_receipt_path)],
                    },
                ],
                "audit_refs": [str(harvest_packet_path)],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.closeout.run(harvest_manifest_path)

    assert len(report.owner_follow_through_briefs) == 1
    handoff = report.owner_follow_through_briefs[0]
    assert handoff.source_kind == "harvest-candidate"
    assert handoff.suggested_action == "draft-owner-artifact"
    assert handoff.owner_repo == "aoa-playbooks"
    assert handoff.next_surface == "playbooks/project-foundation-workspace-landing/PLAYBOOK.md"
    assert handoff.unit_name == "project-foundation workspace landing route"
    assert report.owner_handoff_path is not None
    assert Path(report.owner_handoff_path).exists()


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
    assert payload["items"][0]["kernel_next_step_brief"]["suggested_skill_name"] == "aoa-automation-opportunity-scan"
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
    assert payload["handoff_count"] == 0
    assert payload["pending_manifest_paths"]
    assert payload["latest_request_path"].endswith(
        ".aoa/closeout/requests/closeout-build-001.request.json"
    )
    assert payload["latest_manifest_path"].endswith(".aoa/closeout/manifests/closeout-test-001.json")
