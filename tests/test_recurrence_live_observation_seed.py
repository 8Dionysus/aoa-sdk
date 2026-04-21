from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.recurrence.live_observations import (
    build_live_observation_packet,
    list_live_producers,
)
from aoa_sdk.recurrence.registry import load_registry
from aoa_sdk.workspace.discovery import Workspace


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _component(
    ref: str,
    owner: str,
    *,
    source: list[str],
    generated: list[str] | None = None,
    beacon_rules: list[dict] | None = None,
    observation_inputs: list[dict] | None = None,
) -> dict:
    return {
        "manifest_kind": "recurrence_component",
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": ref,
        "owner_repo": owner,
        "source_inputs": source,
        "generated_surfaces": generated or [],
        "proof_surfaces": ["python scripts/validate.py"],
        "refresh_routes": [
            {"action": "revalidate", "commands": ["python scripts/validate.py"]}
        ],
        "observation_inputs": observation_inputs or [],
        "beacon_rules": beacon_rules or [],
    }


def _workspace(tmp_path: Path) -> Workspace:
    root = tmp_path / "federation"
    techniques = root / "aoa-techniques"
    skills = root / "aoa-skills"
    evals = root / "aoa-evals"
    playbooks = root / "aoa-playbooks"
    for repo in (techniques, skills, evals, playbooks):
        repo.mkdir(parents=True, exist_ok=True)

    _write_json(
        techniques / "manifests/recurrence/component.techniques.json",
        _component(
            "component:techniques:canon-and-intake-beacons",
            "aoa-techniques",
            source=[
                "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
                "docs/PROMOTION_READINESS_MATRIX.md",
            ],
            generated=["generated/technique_promotion_readiness.min.json"],
            observation_inputs=[
                {
                    "input_ref": "cross-layer-technique-candidates",
                    "kind": "other",
                    "path_globs": ["docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md"],
                },
                {
                    "input_ref": "promotion-readiness",
                    "kind": "evaluation_matrix",
                    "path_globs": ["docs/PROMOTION_READINESS_MATRIX.md"],
                },
            ],
            beacon_rules=[
                {
                    "beacon_ref": "technique.canonical.second_consumer_pressure",
                    "kind": "canonical_pressure",
                    "match_signals": ["second_consumer_pressure_seen"],
                    "match_categories": ["review_signal"],
                    "thresholds": {
                        "watch_observations": 1,
                        "candidate_observations": 1,
                        "review_ready_observations": 2,
                        "min_unique_sources": 1,
                        "min_unique_evidence_refs": 1,
                    },
                },
            ],
        ),
    )
    _write_json(
        skills / "manifests/recurrence/component.skills.json",
        _component(
            "component:skills:bundle-and-activation-beacons",
            "aoa-skills",
            source=["docs/TRIGGER_EVALS.md"],
            generated=["generated/description_trigger_eval_manifest.json"],
            observation_inputs=[
                {
                    "input_ref": "description-trigger-evals",
                    "kind": "trigger_eval",
                    "path_globs": ["generated/description_trigger_eval_cases.jsonl"],
                }
            ],
            beacon_rules=[
                {
                    "beacon_ref": "skills.activation.omission",
                    "kind": "unused_skill_opportunity",
                    "match_signals": ["skill_trigger_gap"],
                    "match_categories": ["usage_gap"],
                    "thresholds": {
                        "watch_observations": 1,
                        "candidate_observations": 1,
                        "review_ready_observations": 2,
                        "min_unique_sources": 1,
                        "min_unique_evidence_refs": 1,
                    },
                }
            ],
        ),
    )
    _write_json(
        evals / "manifests/recurrence/component.evals.json",
        _component(
            "component:evals:portable-proof-beacons",
            "aoa-evals",
            source=["docs/RUNTIME_BENCH_PROMOTION_GUIDE.md"],
        ),
    )
    _write_json(
        playbooks / "manifests/recurrence/component.playbooks.json",
        _component(
            "component:playbooks:scenario-composition-beacons",
            "aoa-playbooks",
            source=["docs/PLAYBOOK_REAL_RUN_HARVEST.md"],
        ),
    )

    _write(
        techniques / "docs/CROSS_LAYER_TECHNIQUE_CANDIDATES.md",
        "## Hold Because Overlap\nneeds layer incubation before distillation here\n",
    )
    _write(
        techniques / "docs/PROMOTION_READINESS_MATRIX.md",
        "dominant blocker: needs another live downstream adopter and second-consumer proof\n",
    )
    _write_json(
        techniques / "generated/technique_promotion_readiness.min.json",
        {"items": [{"technique": "AOA-T-1", "status": "needs another live adopter"}]},
    )

    _write(skills / "docs/TRIGGER_EVALS.md", "trigger eval doctrine changed\n")
    _write(
        skills / "generated/description_trigger_eval_cases.jsonl",
        '{"case_id":"case-1","skill_name":"aoa-change-protocol","case_class":"should-trigger"}\n{"case_id":"case-2","skill_name":"aoa-change-protocol","case_class":"prefer-other-skill"}\n',
    )

    _write(
        evals / "docs/RUNTIME_BENCH_PROMOTION_GUIDE.md",
        "bundle-candidate; human review required; do-not-overread\n",
    )
    _write_json(
        evals / "examples/runtime_evidence_selection.example.json",
        {
            "target_class": "bundle-candidate",
            "claim": "under matched host, variant B lowers latency",
        },
    )

    _write(
        playbooks / "docs/PLAYBOOK_REAL_RUN_HARVEST.md",
        "repeated recurring fallback gate with subagent handoff; automation seed stays review-only\n",
    )

    _write_json(
        root / ".aoa/recurrence/events/one.json",
        {"repo_name": "aoa-skills", "unmatched_paths": ["skills/foo/SKILL.md"]},
    )
    _write_json(
        root / ".aoa/recurrence/events/two.json",
        {"repo_name": "aoa-skills", "unmatched_paths": ["skills/foo/SKILL.md"]},
    )
    return Workspace(
        root=root,
        federation_root=root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={
            "aoa-techniques": techniques,
            "aoa-skills": skills,
            "aoa-evals": evals,
            "aoa-playbooks": playbooks,
        },
        repo_origins={
            "aoa-techniques": "test",
            "aoa-skills": "test",
            "aoa-evals": "test",
            "aoa-playbooks": "test",
        },
    )


def test_live_producer_list_is_stable() -> None:
    assert "skill_trigger_surface_watch" in list_live_producers()
    assert "generated_staleness_watch" in list_live_producers()


def test_live_observations_collect_owner_surfaces(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    registry = load_registry(workspace)
    packet = build_live_observation_packet(workspace, registry=registry)
    signals = {item.signal for item in packet.observations}
    assert "overlap_hold_open" in signals
    assert "second_consumer_pressure_seen" in signals
    assert "skill_trigger_gap" in signals
    assert "skill_collision_pressure" in signals
    assert "runtime_candidate_selected" in signals
    assert "portable_eval_boundary_seen" in signals
    assert "repeated_scenario_shape" in signals
    assert "subagent_handoff_receipt_ready" in signals
    assert "repeated_patch_pattern" in signals


def test_live_observations_feed_existing_beacon_rules(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    api = RecurrenceAPI(workspace)
    packet = api.live_observations(
        producers=["technique_readiness_watch", "skill_trigger_surface_watch"]
    )
    beacons = api.beacon(packet)
    kinds = {entry.kind for entry in beacons.entries}
    assert "canonical_pressure" in kinds
    assert "unused_skill_opportunity" in kinds
