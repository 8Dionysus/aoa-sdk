from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.recurrence.models import RecurrenceComponent
from aoa_sdk.workspace.discovery import Workspace


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _make_workspace(tmp_path: Path) -> Workspace:
    federation_root = tmp_path / "federation"
    sdk_root = federation_root / "aoa-sdk"
    techniques_root = federation_root / "aoa-techniques"
    skills_root = federation_root / "aoa-skills"
    evals_root = federation_root / "aoa-evals"
    playbooks_root = federation_root / "aoa-playbooks"
    for item in (sdk_root, techniques_root, skills_root, evals_root, playbooks_root):
        item.mkdir(parents=True, exist_ok=True)

    techniques_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:techniques:canon-and-intake-beacons",
        "owner_repo": "aoa-techniques",
        "source_inputs": ["docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md"],
        "generated_surfaces": ["generated/technique_promotion_readiness.min.json"],
        "contract_surfaces": [
            "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
            "docs/PROMOTION_READINESS_MATRIX.md"
        ],
        "proof_surfaces": ["python scripts/validate_repo.py"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}],
        "observation_inputs": [
            {"input_ref": "cross-layer-technique-candidates", "kind": "other", "path_globs": ["docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md"]},
            {"input_ref": "promotion-readiness", "kind": "evaluation_matrix", "path_globs": ["generated/technique_promotion_readiness.min.json"]}
        ],
        "beacon_rules": [
            {
                "beacon_ref": "technique.new_candidate.distillation_pressure",
                "kind": "new_technique_candidate",
                "decision_surface": "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
                "observation_inputs": ["change_signal", "cross-layer-technique-candidates", "technique-live-receipts"],
                "match_signals": ["source_changed", "cross_layer_candidate_seen", "distillation_pressure_observed"],
                "match_categories": ["change_pressure", "repeat_pattern", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 4,
                    "min_unique_sources": 2,
                    "min_unique_evidence_refs": 2
                },
                "suppress_when": ["overlap_hold_open"]
            },
            {
                "beacon_ref": "technique.canonical.second_consumer_pressure",
                "kind": "canonical_pressure",
                "decision_surface": "docs/PROMOTION_READINESS_MATRIX.md",
                "observation_inputs": ["change_signal", "promotion-readiness"],
                "match_signals": ["second_consumer_confirmed", "cross_context_evidence_present"],
                "match_categories": ["evidence_pressure", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 2,
                    "min_unique_evidence_refs": 2
                },
                "suppress_when": []
            }
        ]
    }
    skills_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:skills:bundle-and-activation-beacons",
        "owner_repo": "aoa-skills",
        "source_inputs": ["docs/TRIGGER_EVALS.md", "docs/ADAPTIVE_SKILL_ORCHESTRATION.md"],
        "generated_surfaces": ["generated/skill_evaluation_matrix.md"],
        "proof_surfaces": ["python scripts/validate_skills.py --fail-on-review-truth-sync"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_skills.py --fail-on-review-truth-sync"]}],
        "observation_inputs": [
            {"input_ref": "description-trigger-suite", "kind": "trigger_eval", "path_globs": ["generated/description_trigger_eval_cases.jsonl"]},
            {"input_ref": "skill-evaluation-matrix", "kind": "evaluation_matrix", "path_globs": ["generated/skill_evaluation_matrix.md"]}
        ],
        "beacon_rules": [
            {
                "beacon_ref": "skills.unused_skill.activation_gap",
                "kind": "unused_skill_opportunity",
                "decision_surface": "docs/ADAPTIVE_SKILL_ORCHESTRATION.md",
                "observation_inputs": ["description-trigger-suite", "skill-evaluation-matrix"],
                "match_signals": ["should_trigger_missing", "prefer_other_skill_gap"],
                "match_categories": ["usage_gap", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 2,
                    "min_unique_evidence_refs": 2
                },
                "suppress_when": []
            },
            {
                "beacon_ref": "skills.trigger_drift.description_boundary",
                "kind": "skill_trigger_drift",
                "decision_surface": "docs/TRIGGER_EVALS.md",
                "observation_inputs": ["change_signal", "description-trigger-suite"],
                "match_signals": ["description_changed_without_trigger_refresh", "source_changed", "docs_changed"],
                "match_categories": ["change_pressure", "usage_gap"],
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
    evals_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:evals:portable-proof-beacons",
        "owner_repo": "aoa-evals",
        "source_inputs": ["docs/RUNTIME_BENCH_PROMOTION_GUIDE.md", "docs/RECURRENCE_PROOF_PROGRAM.md"],
        "generated_surfaces": ["generated/eval_catalog.min.json"],
        "proof_surfaces": ["python scripts/validate_repo.py"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_repo.py"]}],
        "observation_inputs": [
            {"input_ref": "trace-eval-bridge", "kind": "runtime_artifact", "path_globs": ["docs/TRACE_EVAL_BRIDGE.md"]}
        ],
        "beacon_rules": [
            {
                "beacon_ref": "evals.portable_eval.runtime_pressure",
                "kind": "portable_eval_candidate",
                "decision_surface": "docs/RUNTIME_BENCH_PROMOTION_GUIDE.md",
                "observation_inputs": ["change_signal", "trace-eval-bridge"],
                "match_signals": ["portable_claim_repeat", "trace_bridge_receipt_ready"],
                "match_categories": ["repeat_pattern", "evidence_pressure"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 2,
                    "min_unique_evidence_refs": 2
                },
                "suppress_when": []
            },
            {
                "beacon_ref": "evals.overclaim.guard",
                "kind": "overclaim_alarm",
                "decision_surface": "docs/RECURRENCE_PROOF_PROGRAM.md",
                "observation_inputs": ["trace-eval-bridge"],
                "match_signals": ["overclaim_detected"],
                "match_categories": ["overclaim_risk"],
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
    playbooks_manifest = {
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": "component:playbooks:scenario-composition-beacons",
        "owner_repo": "aoa-playbooks",
        "source_inputs": ["docs/SUBAGENT_PATTERNS.md", "docs/AUTOMATION_SEEDS.md", "playbooks/component-refresh-cycle/PLAYBOOK.md"],
        "generated_surfaces": ["generated/playbook_subagent_recipes.json", "generated/playbook_automation_seeds.json"],
        "proof_surfaces": ["python scripts/validate_playbooks.py"],
        "refresh_routes": [{"action": "revalidate", "commands": ["python scripts/validate_playbooks.py"]}],
        "observation_inputs": [
            {"input_ref": "real-run-harvests", "kind": "harvest", "path_globs": ["examples/harvests/*"]},
            {"input_ref": "composition-gates", "kind": "review_note", "path_globs": ["docs/gate-reviews/*"]}
        ],
        "beacon_rules": [
            {
                "beacon_ref": "playbooks.recurring_scenario.candidate",
                "kind": "playbook_candidate",
                "decision_surface": "playbooks/component-refresh-cycle/PLAYBOOK.md",
                "observation_inputs": ["real-run-harvests", "composition-gates"],
                "match_signals": ["repeated_scenario_shape", "composition_gate_pressure"],
                "match_categories": ["repeat_pattern", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 2,
                    "min_unique_evidence_refs": 2
                },
                "suppress_when": []
            },
            {
                "beacon_ref": "playbooks.subagent.recipe_pressure",
                "kind": "subagent_recipe_candidate",
                "decision_surface": "docs/SUBAGENT_PATTERNS.md",
                "observation_inputs": ["real-run-harvests", "composition-gates"],
                "match_signals": ["bounded_parallel_split_seen", "reviewable_split_repeated"],
                "match_categories": ["repeat_pattern", "review_signal"],
                "thresholds": {
                    "watch_observations": 1,
                    "candidate_observations": 2,
                    "review_ready_observations": 3,
                    "min_unique_sources": 2,
                    "min_unique_evidence_refs": 2
                },
                "suppress_when": ["automatic_orchestration_requested"]
            }
        ]
    }

    _write_json(techniques_root / "manifests/recurrence/techniques.json", techniques_manifest)
    _write_json(skills_root / "manifests/recurrence/skills.json", skills_manifest)
    _write_json(evals_root / "manifests/recurrence/evals.json", evals_manifest)
    _write_json(playbooks_root / "manifests/recurrence/playbooks.json", playbooks_manifest)

    (techniques_root / "docs").mkdir(parents=True, exist_ok=True)
    (techniques_root / "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md").write_text("# candidate\n", encoding="utf-8")
    (skills_root / "docs").mkdir(parents=True, exist_ok=True)
    (skills_root / "docs/TRIGGER_EVALS.md").write_text("# trigger\n", encoding="utf-8")
    (evals_root / "docs").mkdir(parents=True, exist_ok=True)
    (evals_root / "docs/RUNTIME_BENCH_PROMOTION_GUIDE.md").write_text("# runtime\n", encoding="utf-8")
    (playbooks_root / "docs").mkdir(parents=True, exist_ok=True)
    (playbooks_root / "docs/SUBAGENT_PATTERNS.md").write_text("# subagents\n", encoding="utf-8")

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


def _supplemental_observations(tmp_path: Path) -> Path:
    path = tmp_path / "supplemental.json"
    payload = [
        {
            "observation_ref": "obs:supp:0001",
            "component_ref": "component:techniques:canon-and-intake-beacons",
            "owner_repo": "aoa-techniques",
            "observed_at": "2026-04-13T12:00:00Z",
            "category": "repeat_pattern",
            "signal": "cross_layer_candidate_seen",
            "source_inputs": ["cross-layer-technique-candidates"],
            "evidence_refs": ["docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md#candidate"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0002",
            "component_ref": "component:techniques:canon-and-intake-beacons",
            "owner_repo": "aoa-techniques",
            "observed_at": "2026-04-13T12:01:00Z",
            "category": "review_signal",
            "signal": "distillation_pressure_observed",
            "source_inputs": ["technique-live-receipts"],
            "evidence_refs": [".aoa/live_receipts/technique-receipts.jsonl#1"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0003",
            "component_ref": "component:skills:bundle-and-activation-beacons",
            "owner_repo": "aoa-skills",
            "observed_at": "2026-04-13T12:02:00Z",
            "category": "usage_gap",
            "signal": "should_trigger_missing",
            "source_inputs": ["description-trigger-suite"],
            "evidence_refs": ["generated/description_trigger_eval_cases.jsonl#case-17"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0004",
            "component_ref": "component:skills:bundle-and-activation-beacons",
            "owner_repo": "aoa-skills",
            "observed_at": "2026-04-13T12:03:00Z",
            "category": "review_signal",
            "signal": "prefer_other_skill_gap",
            "source_inputs": ["skill-evaluation-matrix"],
            "evidence_refs": ["generated/skill_evaluation_matrix.md#gap-2"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0005",
            "component_ref": "component:evals:portable-proof-beacons",
            "owner_repo": "aoa-evals",
            "observed_at": "2026-04-13T12:04:00Z",
            "category": "repeat_pattern",
            "signal": "portable_claim_repeat",
            "source_inputs": ["trace-eval-bridge"],
            "evidence_refs": ["docs/TRACE_EVAL_BRIDGE.md#portable"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0006",
            "component_ref": "component:evals:portable-proof-beacons",
            "owner_repo": "aoa-evals",
            "observed_at": "2026-04-13T12:05:00Z",
            "category": "evidence_pressure",
            "signal": "trace_bridge_receipt_ready",
            "source_inputs": ["change_signal"],
            "evidence_refs": ["runtime-receipts.json#1"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0007",
            "component_ref": "component:playbooks:scenario-composition-beacons",
            "owner_repo": "aoa-playbooks",
            "observed_at": "2026-04-13T12:06:00Z",
            "category": "repeat_pattern",
            "signal": "bounded_parallel_split_seen",
            "source_inputs": ["real-run-harvests"],
            "evidence_refs": ["examples/harvests/run-2.json"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:0008",
            "component_ref": "component:playbooks:scenario-composition-beacons",
            "owner_repo": "aoa-playbooks",
            "observed_at": "2026-04-13T12:07:00Z",
            "category": "review_signal",
            "signal": "reviewable_split_repeated",
            "source_inputs": ["composition-gates"],
            "evidence_refs": ["docs/gate-reviews/review-2.md"],
            "attributes": {},
            "notes": ""
        }
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def _suppressed_playbook_observations(tmp_path: Path) -> Path:
    path = tmp_path / "suppressed.json"
    payload = [
        {
            "observation_ref": "obs:supp:1001",
            "component_ref": "component:playbooks:scenario-composition-beacons",
            "owner_repo": "aoa-playbooks",
            "observed_at": "2026-04-13T12:06:00Z",
            "category": "repeat_pattern",
            "signal": "bounded_parallel_split_seen",
            "source_inputs": ["real-run-harvests"],
            "evidence_refs": ["examples/harvests/run-3.json"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:1002",
            "component_ref": "component:playbooks:scenario-composition-beacons",
            "owner_repo": "aoa-playbooks",
            "observed_at": "2026-04-13T12:07:00Z",
            "category": "review_signal",
            "signal": "reviewable_split_repeated",
            "source_inputs": ["composition-gates"],
            "evidence_refs": ["docs/gate-reviews/review-3.md"],
            "attributes": {},
            "notes": ""
        },
        {
            "observation_ref": "obs:supp:1003",
            "component_ref": "component:playbooks:scenario-composition-beacons",
            "owner_repo": "aoa-playbooks",
            "observed_at": "2026-04-13T12:08:00Z",
            "category": "review_signal",
            "signal": "automatic_orchestration_requested",
            "source_inputs": ["composition-gates"],
            "evidence_refs": ["docs/gate-reviews/review-3.md#suppression"],
            "attributes": {},
            "notes": ""
        }
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def test_beacon_pipeline_emits_candidate_pressure(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)

    signal = api.detect(
        repo_root=str(workspace.repo_roots["aoa-skills"]),
        paths=["docs/TRIGGER_EVALS.md"],
    )
    supplemental_path = _supplemental_observations(tmp_path)
    observations = api.observe(signal, supplemental_paths=[str(supplemental_path)])
    beacons = api.beacon(observations)
    ledger = api.ledger(beacons, include_lower_status=False)
    usage_gaps = api.usage_gaps(beacons)

    by_ref = {item.beacon_ref: item for item in beacons.entries}
    assert by_ref["technique.new_candidate.distillation_pressure"].status == "candidate"
    assert by_ref["skills.unused_skill.activation_gap"].status == "candidate"
    assert by_ref["evals.portable_eval.runtime_pressure"].status == "candidate"
    assert by_ref["playbooks.subagent.recipe_pressure"].status == "candidate"

    assert len(ledger.entries) >= 4
    assert {item.beacon_ref for item in usage_gaps.items} >= {
        "skills.unused_skill.activation_gap",
        "skills.trigger_drift.description_boundary",
    }


def test_suppression_caps_subagent_recipe_to_watch(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)

    observations = api.observe(supplemental_paths=[str(_suppressed_playbook_observations(tmp_path))])
    beacons = api.beacon(observations)
    entry = next(item for item in beacons.entries if item.beacon_ref == "playbooks.subagent.recipe_pressure")
    assert entry.status == "watch"
    assert "automatic_orchestration_requested" in entry.suppression_flags


def test_component_schema_accepts_first_wave_version() -> None:
    component = RecurrenceComponent.model_validate(
        {
            "schema_version": "aoa_recurrence_component_v1",
            "component_ref": "component:legacy:test",
            "owner_repo": "aoa-sdk",
            "source_inputs": ["docs/LEGACY.md"],
            "generated_surfaces": ["generated/legacy.json"],
            "proof_surfaces": ["python scripts/validate_repo.py"],
            "refresh_routes": [{"action": "repair", "commands": ["python scripts/validate_repo.py"]}],
        }
    )
    assert component.schema_version == "aoa_recurrence_component_v1"


def test_observe_allows_supplemental_only_mode(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)
    packet = api.observe(supplemental_paths=[str(_supplemental_observations(tmp_path))])
    assert packet.signal_ref is None
    assert len(packet.observations) >= 8
