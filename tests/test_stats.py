from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk import AoASDK


def install_stats_fixture(workspace_root: Path) -> Path:
    repo = workspace_root / "aoa-stats"
    generated = repo / "generated"
    state_generated = repo / "state" / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    state_generated.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text("# aoa-stats\n", encoding="utf-8")

    generated_from = {
        "receipt_input_paths": [
            "aoa-skills/examples/session_harvest_family.receipts.example.json",
            "aoa-evals/examples/eval_result_receipt.example.json",
        ],
        "total_receipts": 2,
        "latest_observed_at": "2026-04-05T10:35:00Z",
    }
    surfaces = {
        "object_summary.min.json": {
            "schema_version": "aoa_stats_object_summary_v1",
            "generated_from": generated_from,
            "objects": [
                {
                    "object_ref": {
                        "repo": "aoa-skills",
                        "kind": "skill",
                        "id": "aoa-automation-opportunity-scan",
                        "version": "main",
                    },
                    "receipt_count_total": 1,
                    "receipt_counts_by_event_kind": {"automation_candidate_receipt": 1},
                    "first_observed_at": "2026-04-05T10:20:00Z",
                    "last_observed_at": "2026-04-05T10:20:00Z",
                    "latest_session_ref": "session:test-001",
                    "latest_run_ref": "run-test-001",
                    "evidence_ref_count": 1,
                    "latest_eval_verdict": None,
                    "latest_progression_verdict": None,
                    "automation_candidate_counts": {
                        "total": 1,
                        "seed_ready": 1,
                        "checkpoint_required": 0,
                    },
                }
            ],
        },
        "core_skill_application_summary.min.json": {
            "schema_version": "aoa_stats_core_skill_application_summary_v1",
            "generated_from": generated_from,
            "skills": [
                {
                    "kernel_id": "project-core-session-growth-v1",
                    "skill_name": "aoa-session-donor-harvest",
                    "application_count": 1,
                    "latest_observed_at": "2026-04-05T10:20:00Z",
                    "latest_session_ref": "session:test-001",
                    "latest_run_ref": "run-skill-001",
                    "detail_event_kind_counts": {"harvest_packet_receipt": 1},
                }
            ],
        },
        "repeated_window_summary.min.json": {
            "schema_version": "aoa_stats_repeated_window_summary_v1",
            "generated_from": generated_from,
            "windows": [
                {
                    "window_id": "window:2026-04-05",
                    "window_date": "2026-04-05",
                    "total_receipts": 2,
                    "unique_objects": 2,
                    "event_counts_by_kind": {
                        "automation_candidate_receipt": 1,
                        "eval_result_receipt": 1,
                    },
                    "eval_result_count": 1,
                    "progression_delta_count": 0,
                    "automation_candidate_count": 1,
                    "evidence_ref_count": 2,
                }
            ],
        },
        "route_progression_summary.min.json": {
            "schema_version": "aoa_stats_route_progression_summary_v1",
            "generated_from": generated_from,
            "routes": [
                {
                    "route_ref": "route:test",
                    "total_progression_receipts": 1,
                    "latest_verdict": "advance",
                    "latest_observed_at": "2026-04-05T10:30:00Z",
                    "cumulative_axis_deltas": {
                        "boundary_integrity": 0,
                        "execution_reliability": 1,
                        "change_legibility": 1,
                        "review_sharpness": 1,
                        "proof_discipline": 1,
                        "provenance_hygiene": 1,
                        "deep_readiness": 1,
                    },
                    "caution_count": 0,
                    "evidence_ref_count": 1,
                }
            ],
        },
        "fork_calibration_summary.min.json": {
            "schema_version": "aoa_stats_fork_calibration_summary_v1",
            "generated_from": generated_from,
            "routes": [
                {
                    "route_ref": "route:test",
                    "decision_count": 1,
                    "chosen_branch_counts": {"ship-adjunct": 1},
                    "max_option_count": 2,
                    "realized_outcome_link_count": 1,
                    "evidence_ref_count": 1,
                    "latest_observed_at": "2026-04-05T10:25:00Z",
                }
            ],
        },
        "automation_pipeline_summary.min.json": {
            "schema_version": "aoa_stats_automation_pipeline_summary_v1",
            "generated_from": generated_from,
            "pipelines": [
                {
                    "pipeline_ref": "pipeline:test",
                    "candidate_count": 1,
                    "seed_ready_count": 1,
                    "checkpoint_required_count": 0,
                    "deterministic_ready_count": 1,
                    "reversible_ready_count": 1,
                    "next_artifact_hints": ["seed-pack"],
                    "evidence_ref_count": 1,
                    "latest_observed_at": "2026-04-05T10:20:00Z",
                }
            ],
        },
        "summary_surface_catalog.min.json": {
            "schema_version": "aoa_stats_summary_surface_catalog_v1",
            "generated_from": generated_from,
            "surfaces": [
                {
                    "name": "core_skill_application_summary",
                    "path": "generated/core_skill_application_summary.min.json",
                    "schema_ref": "schemas/core-skill-application-summary.schema.json",
                    "primary_question": "Which project-core kernel skills are actually finishing and how often, without inferring usage from general receipt volume?",
                    "derivation_rule": "aggregate core_skill_application_receipt payloads by kernel_id and skill_name",
                },
                {
                    "name": "automation_pipeline_summary",
                    "path": "generated/automation_pipeline_summary.min.json",
                    "schema_ref": "schemas/automation-pipeline-summary.schema.json",
                    "primary_question": "How close is a named automation pipeline to seed-ready bounded use?",
                    "derivation_rule": "aggregate automation_candidate_receipt payloads by pipeline_ref and readiness flags",
                }
            ],
        },
    }

    for name, payload in surfaces.items():
        (generated / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    live_surfaces = dict(surfaces)
    live_generated_from = {
        "receipt_input_paths": [
            "aoa-skills/.aoa/live_receipts/session-harvest-family.jsonl",
            "aoa-evals/.aoa/live_receipts/eval-result-receipts.jsonl",
        ],
        "total_receipts": 3,
        "latest_observed_at": "2026-04-05T11:05:00Z",
    }
    live_automation = dict(live_surfaces["automation_pipeline_summary.min.json"])
    live_automation["generated_from"] = live_generated_from
    live_automation["pipelines"] = [
        {
            "pipeline_ref": "pipeline:test",
            "candidate_count": 2,
            "seed_ready_count": 1,
            "checkpoint_required_count": 1,
            "deterministic_ready_count": 2,
            "reversible_ready_count": 2,
            "next_artifact_hints": ["repair-prompt", "seed-pack"],
            "evidence_ref_count": 2,
            "latest_observed_at": "2026-04-05T11:05:00Z",
        }
    ]
    live_catalog = dict(live_surfaces["summary_surface_catalog.min.json"])
    live_catalog["generated_from"] = live_generated_from
    live_object_summary = dict(live_surfaces["object_summary.min.json"])
    live_object_summary["generated_from"] = live_generated_from
    live_core_skill = dict(live_surfaces["core_skill_application_summary.min.json"])
    live_core_skill["generated_from"] = live_generated_from
    live_core_skill["skills"] = [
        {
            "kernel_id": "project-core-session-growth-v1",
            "skill_name": "aoa-session-donor-harvest",
            "application_count": 2,
            "latest_observed_at": "2026-04-05T11:05:00Z",
            "latest_session_ref": "session:test-001",
            "latest_run_ref": "run-skill-002",
            "detail_event_kind_counts": {"harvest_packet_receipt": 2},
        }
    ]
    live_repeated = dict(live_surfaces["repeated_window_summary.min.json"])
    live_repeated["generated_from"] = live_generated_from
    live_route = dict(live_surfaces["route_progression_summary.min.json"])
    live_route["generated_from"] = live_generated_from
    live_fork = dict(live_surfaces["fork_calibration_summary.min.json"])
    live_fork["generated_from"] = live_generated_from
    for name, payload in {
        "object_summary.min.json": live_object_summary,
        "core_skill_application_summary.min.json": live_core_skill,
        "repeated_window_summary.min.json": live_repeated,
        "route_progression_summary.min.json": live_route,
        "fork_calibration_summary.min.json": live_fork,
        "automation_pipeline_summary.min.json": live_automation,
        "summary_surface_catalog.min.json": live_catalog,
    }.items():
        (state_generated / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return repo


def test_stats_api_reads_generated_surfaces(workspace_root: Path) -> None:
    install_stats_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.has_repo("aoa-stats")
    assert sdk.stats.generated_from().total_receipts == 3
    assert len(sdk.stats.object_summary(repo="aoa-skills")) == 1
    assert sdk.stats.core_skill_applications(skill_name="aoa-session-donor-harvest")[0].application_count == 2
    assert sdk.stats.automation_pipelines("pipeline:test").seed_ready_count == 1
    assert sdk.stats.route_progression("route:test").latest_verdict == "advance"
    assert {item.name for item in sdk.stats.summary_catalog()} == {
        "automation_pipeline_summary",
        "core_skill_application_summary",
    }


def test_stats_compatibility_checks_green_when_repo_is_present(workspace_root: Path) -> None:
    install_stats_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    report = {entry.surface_id: entry for entry in sdk.compatibility.check_repo("aoa-stats")}

    assert report["aoa-stats.object_summary.min"].compatible is True
    assert report["aoa-stats.core_skill_application_summary.min"].compatible is True
    assert (
        report["aoa-stats.object_summary.min"].resolved_relative_path
        == "state/generated/object_summary.min.json"
    )
    assert (
        report["aoa-stats.core_skill_application_summary.min"].detected_version
        == "aoa_stats_core_skill_application_summary_v1"
    )
    assert (
        report["aoa-stats.automation_pipeline_summary.min"].detected_version
        == "aoa_stats_automation_pipeline_summary_v1"
    )
    assert report["aoa-stats.summary_surface_catalog.min"].compatible is True
