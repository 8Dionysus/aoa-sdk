from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.workspace.discovery import Workspace


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _make_workspace(tmp_path: Path) -> Workspace:
    federation_root = tmp_path / "federation"
    sdk_root = federation_root / "aoa-sdk"
    techniques_root = federation_root / "aoa-techniques"
    skills_root = federation_root / "aoa-skills"
    evals_root = federation_root / "aoa-evals"
    playbooks_root = federation_root / "aoa-playbooks"
    for item in (sdk_root, techniques_root, skills_root, evals_root, playbooks_root):
        item.mkdir(parents=True, exist_ok=True)

    technique_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:techniques:canon-and-intake-beacons",
        "owner_repo": "aoa-techniques",
        "source_inputs": ["docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md"],
        "proof_surfaces": ["python scripts/validate_repo.py"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}],
        "beacon_rules": [
            {
                "beacon_ref": "technique.new_candidate.distillation_pressure",
                "kind": "new_technique_candidate",
                "decision_surface": "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
                "observation_inputs": ["technique-live-receipts"],
                "match_signals": ["candidate_harvested", "distillation_pressure_observed"],
                "match_categories": ["review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 1,
                    "min_unique_evidence_refs": 1
                },
                "suppress_when": []
            },
            {
                "beacon_ref": "technique.canonical.second_consumer_pressure",
                "kind": "canonical_pressure",
                "decision_surface": "docs/PROMOTION_READINESS_MATRIX.md",
                "observation_inputs": ["technique-live-receipts"],
                "match_signals": ["second_consumer_confirmed"],
                "match_categories": ["evidence_pressure"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 1,
                    "review_ready_observations": 2,
                    "min_unique_sources": 1,
                    "min_unique_evidence_refs": 1
                },
                "suppress_when": []
            }
        ]
    }
    evals_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:evals:portable-proof-beacons",
        "owner_repo": "aoa-evals",
        "source_inputs": ["docs/RUNTIME_BENCH_PROMOTION_GUIDE.md"],
        "proof_surfaces": ["python scripts/validate_repo.py"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}],
        "beacon_rules": [
            {
                "beacon_ref": "evals.portable_eval.runtime_pressure",
                "kind": "portable_eval_candidate",
                "decision_surface": "docs/RUNTIME_BENCH_PROMOTION_GUIDE.md",
                "observation_inputs": ["runtime-candidate-guide"],
                "match_signals": ["portable_claim_repeat", "trace_bridge_receipt_ready"],
                "match_categories": ["repeat_pattern", "evidence_pressure"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 4,
                    "min_unique_sources": 1,
                    "min_unique_evidence_refs": 1
                },
                "suppress_when": []
            },
            {
                "beacon_ref": "evals.overclaim.guard",
                "kind": "overclaim_alarm",
                "decision_surface": "docs/RECURRENCE_PROOF_PROGRAM.md",
                "observation_inputs": ["runtime-candidate-guide"],
                "match_signals": ["overclaim_detected"],
                "match_categories": ["overclaim_risk"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 1,
                    "review_ready_observations": 2,
                    "min_unique_sources": 1,
                    "min_unique_evidence_refs": 1
                },
                "suppress_when": []
            }
        ]
    }
    playbooks_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:playbooks:scenario-composition-beacons",
        "owner_repo": "aoa-playbooks",
        "source_inputs": ["playbooks/component-refresh-cycle/PLAYBOOK.md"],
        "proof_surfaces": ["python scripts/validate_playbooks.py"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_playbooks.py"]}],
        "beacon_rules": [
            {
                "beacon_ref": "playbooks.recurring_scenario.candidate",
                "kind": "playbook_candidate",
                "decision_surface": "playbooks/component-refresh-cycle/PLAYBOOK.md",
                "observation_inputs": ["real-run-harvests"],
                "match_signals": ["repeated_scenario_shape", "automation_readiness_signal"],
                "match_categories": ["repeat_pattern", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 1,
                    "min_unique_evidence_refs": 1
                },
                "suppress_when": []
            },
            {
                "beacon_ref": "playbooks.subagent.recipe_pressure",
                "kind": "subagent_recipe_candidate",
                "decision_surface": "docs/SUBAGENT_PATTERNS.md",
                "observation_inputs": ["real-run-harvests"],
                "match_signals": ["bounded_parallel_split_seen", "reviewable_split_repeated"],
                "match_categories": ["repeat_pattern", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 1,
                    "min_unique_evidence_refs": 1
                },
                "suppress_when": []
            }
        ]
    }

    _write_json(
        techniques_root
        / "mechanics/recurrence/parts/live-observation-producers/manifests/recurrence/techniques.json",
        technique_manifest,
    )
    _write_json(evals_root / "manifests/recurrence/evals.json", evals_manifest)
    _write_json(playbooks_root / "manifests/recurrence/playbooks.json", playbooks_manifest)

    _write_json(
        techniques_root
        / "mechanics/recurrence/parts/live-observation-producers/manifests/recurrence/hooks/techniques.hooks.json",
        {
            "schema_version": "aoa_hook_binding_set_v1",
            "component_ref": "component:techniques:canon-and-intake-beacons",
            "owner_repo": "aoa-techniques",
            "bindings": [
                {
                    "binding_ref": "techniques.live_receipts.session_stop",
                    "event": "session_stop",
                    "producer": "jsonl_receipt_watch",
                    "component_ref": "component:techniques:canon-and-intake-beacons",
                    "owner_repo": "aoa-techniques",
                    "input_ref": "technique-live-receipts",
                    "path_globs": [".aoa/live_receipts/technique-receipts.jsonl"],
                    "config": {"record_id_field": "receipt_ref"},
                    "signal_rules": [
                        {"signal": "receipt_changed", "category": "evidence_pressure", "match": "always"},
                        {"signal": "candidate_harvested", "category": "review_signal", "match": "exists", "field": "candidate_ref"},
                        {"signal": "distillation_pressure_observed", "category": "review_signal", "match": "exists", "field": "candidate_ref"},
                        {"signal": "second_consumer_confirmed", "category": "evidence_pressure", "match": "exists", "field": "second_consumer_ref"}
                    ]
                }
            ]
        },
    )
    _write_json(
        evals_root / "manifests/recurrence/hooks/evals.hooks.json",
        {
            "schema_version": "aoa_hook_binding_set_v1",
            "component_ref": "component:evals:portable-proof-beacons",
            "owner_repo": "aoa-evals",
            "bindings": [
                {
                    "binding_ref": "evals.runtime_candidate.session_stop",
                    "event": "session_stop",
                    "producer": "runtime_candidate_watch",
                    "component_ref": "component:evals:portable-proof-beacons",
                    "owner_repo": "aoa-evals",
                    "input_ref": "runtime-candidate-guide",
                    "path_globs": ["examples/runtime/*.json"],
                    "config": {
                        "claim_fields": ["claim_family", "claim", "bounded_claim"],
                        "candidate_class_field": "target_class",
                        "candidate_class_values": ["bundle-candidate", "evidence-sidecar"],
                        "evidence_fields": ["selected_evidence", "evidence_refs", "trace_refs"],
                        "record_id_field": "artifact_ref",
                        "overclaim_phrases": [" is the best", " proves general reasoning growth"]
                    },
                    "signal_rules": []
                }
            ]
        },
    )
    _write_json(
        playbooks_root / "manifests/recurrence/hooks/playbooks.hooks.json",
        {
            "schema_version": "aoa_hook_binding_set_v1",
            "component_ref": "component:playbooks:scenario-composition-beacons",
            "owner_repo": "aoa-playbooks",
            "bindings": [
                {
                    "binding_ref": "playbooks.harvest_patterns.session_stop",
                    "event": "session_stop",
                    "producer": "harvest_pattern_watch",
                    "component_ref": "component:playbooks:scenario-composition-beacons",
                    "owner_repo": "aoa-playbooks",
                    "input_ref": "real-run-harvests",
                    "path_globs": ["examples/harvests/*", "docs/gate-reviews/*"],
                    "config": {
                        "record_id_field": "harvest_ref",
                        "phrase_signals": [
                            {
                                "signal": "bounded_parallel_split_seen",
                                "category": "repeat_pattern",
                                "phrases": ["bounded parallel split", "short ledgers"],
                                "mode": "all"
                            },
                            {
                                "signal": "automation_readiness_signal",
                                "category": "review_signal",
                                "phrases": ["automation readiness", "reviewed automation"],
                                "mode": "any"
                            }
                        ],
                        "json_field_signals": [
                            {
                                "signal": "repeated_scenario_shape",
                                "category": "repeat_pattern",
                                "match": "exists",
                                "field": "scenario_repeat"
                            },
                            {
                                "signal": "bounded_parallel_split_seen",
                                "category": "repeat_pattern",
                                "match": "equals",
                                "field": "bounded_parallel_split",
                                "value": True
                            },
                            {
                                "signal": "reviewable_split_repeated",
                                "category": "review_signal",
                                "match": "equals",
                                "field": "reviewable_split_repeated",
                                "value": True
                            },
                            {
                                "signal": "automation_readiness_signal",
                                "category": "review_signal",
                                "match": "equals",
                                "field": "automation_readiness",
                                "value": True
                            }
                        ]
                    },
                    "signal_rules": []
                }
            ]
        },
    )
    _write_json(
        sdk_root
        / "mechanics/recurrence/parts/hook-observation-pack/manifests/hooks/agon-observation-only.hooks.json",
        {
            "component_id": "component:agon:observation-only",
            "hook_binding_set_id": "hooks:agon:observation-only",
            "hook_mode": "observe_only",
            "observation_producers": ["stop_line_integrity"],
            "forbidden_actions": ["open_session", "issue_verdict"],
            "owner_repo": "aoa-sdk",
        },
    )
    _write_json(
        sdk_root
        / "mechanics/recurrence/parts/hook-observation-pack/manifests/hooks/foreign-review-posture.hooks.json",
        {
            "hook_set_id": "component:agon:review-posture.hooks",
            "observes_component": "component:agon:review-posture",
            "posture": "review_queue_only",
            "allowed_outputs": ["recurrence_observation"],
            "forbidden_effects": ["live_verdict_authority"],
        },
    )

    (techniques_root / "docs").mkdir(parents=True, exist_ok=True)
    (techniques_root / "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md").write_text("# candidates\n", encoding="utf-8")
    _write_jsonl(
        techniques_root / ".aoa/live_receipts/technique-receipts.jsonl",
        [
            {"receipt_ref": "tech-1", "candidate_ref": "AOA-T-CAND-001"},
            {"receipt_ref": "tech-2", "second_consumer_ref": "consumer:mirror-B"}
        ],
    )

    (evals_root / "docs").mkdir(parents=True, exist_ok=True)
    (evals_root / "docs/RUNTIME_BENCH_PROMOTION_GUIDE.md").write_text("# runtime guide\n", encoding="utf-8")
    _write_json(
        evals_root / "examples/runtime/runtime-pack.json",
        [
            {
                "artifact_ref": "runtime-1",
                "claim_family": "latency.boundary",
                "target_class": "bundle-candidate",
                "selected_evidence": ["trace-a"]
            },
            {
                "artifact_ref": "runtime-2",
                "claim_family": "latency.boundary",
                "evidence_refs": ["trace-b"]
            },
            {
                "artifact_ref": "runtime-3",
                "claim": "backend Y is the best",
                "trace_refs": ["trace-c"]
            }
        ],
    )

    (playbooks_root / "docs/gate-reviews").mkdir(parents=True, exist_ok=True)
    (playbooks_root / "docs/gate-reviews/review.md").write_text(
        "This route shows a bounded parallel split that returns through short ledgers. Reviewed automation readiness is now explicit.\n",
        encoding="utf-8",
    )
    _write_json(
        playbooks_root / "examples/harvests/run.json",
        {
            "harvest_ref": "harvest-1",
            "scenario_repeat": 2,
            "bounded_parallel_split": True,
            "reviewable_split_repeated": True,
            "automation_readiness": True,
            "playbook_ref": "AOA-P-0030"
        },
    )

    return Workspace(
        root=federation_root,
        federation_root=federation_root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={
            "aoa-sdk": sdk_root,
            "aoa-techniques": techniques_root,
            "aoa-skills": skills_root,
            "aoa-evals": evals_root,
            "aoa-playbooks": playbooks_root,
        },
        repo_origins={
            "aoa-sdk": "test",
            "aoa-techniques": "test",
            "aoa-skills": "test",
            "aoa-evals": "test",
            "aoa-playbooks": "test",
        },
    )


def test_hooks_list_and_run_session_stop(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)

    bindings = api.hooks(event="session_stop")
    assert len(bindings) == 3

    report = api.run_hooks(event="session_stop")
    signals = {item.signal for item in report.observations}

    assert "candidate_harvested" in signals
    assert "second_consumer_confirmed" in signals
    assert "trace_bridge_receipt_ready" in signals
    assert "portable_claim_repeat" in signals
    assert "overclaim_detected" in signals
    assert "repeated_scenario_shape" in signals
    assert "bounded_parallel_split_seen" in signals
    assert "automation_readiness_signal" in signals

    assert report.missing_paths == []


def test_observe_can_merge_hook_run_report_and_emit_beacons(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)

    hook_report = api.run_hooks(event="session_stop")
    report_path = workspace.repo_roots["aoa-sdk"] / ".aoa/recurrence/hooks/session_stop.latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(hook_report.model_dump(mode="json"), indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    observations = api.observe(hook_run_paths=[str(report_path)])
    beacons = api.beacon(observations)

    by_ref = {item.beacon_ref: item for item in beacons.entries}
    assert by_ref["technique.new_candidate.distillation_pressure"].status == "candidate"
    assert by_ref["technique.canonical.second_consumer_pressure"].status == "candidate"
    assert by_ref["evals.portable_eval.runtime_pressure"].status in {"candidate", "review_ready"}
    assert by_ref["evals.overclaim.guard"].status == "candidate"
    assert by_ref["playbooks.recurring_scenario.candidate"].status in {"candidate", "review_ready"}
    assert by_ref["playbooks.subagent.recipe_pressure"].status in {"candidate", "review_ready"}
