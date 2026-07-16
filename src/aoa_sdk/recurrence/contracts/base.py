from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


EdgeKind = Literal[
    "owns",
    "generates",
    "projects_to",
    "validated_by",
    "documents",
    "evaluated_by",
    "routes_via",
    "summarized_by",
    "donates_to_kag",
    "requires_regrounding",
    "handoff_home",
]

RouteClass = Literal[
    "observe",
    "revalidate",
    "rebuild",
    "reexport",
    "regenerate",
    "reproject",
    "repair",
    "reroute",
    "restat",
    "reground",
    "handoff",
    "defer",
]

SurfaceClass = Literal[
    "source",
    "generated",
    "projected",
    "contract",
    "docs",
    "test",
    "proof",
    "receipt",
    "other",
]

ObservationInputKind = Literal[
    "change_signal",
    "receipt",
    "closeout",
    "evaluation_matrix",
    "trigger_eval",
    "review_note",
    "runtime_artifact",
    "harvest",
    "other",
]

ObservationCategory = Literal[
    "change_pressure",
    "evidence_pressure",
    "usage_gap",
    "repeat_pattern",
    "review_signal",
    "overclaim_risk",
]

BeaconStatus = Literal["hint", "watch", "candidate", "review_ready"]

BeaconKind = Literal[
    "new_technique_candidate",
    "technique_overlap_hold",
    "canonical_pressure",
    "unused_skill_opportunity",
    "skill_trigger_drift",
    "skill_bundle_candidate",
    "portable_eval_candidate",
    "progression_evidence_candidate",
    "overclaim_alarm",
    "playbook_candidate",
    "subagent_recipe_candidate",
    "automation_seed_candidate",
]

SignalEdgeKind = Literal[
    "implemented_by_skill",
    "proved_by_eval",
    "composed_by_playbook",
    "incubated_by_technique",
    "documents_decision",
    "summarized_by",
]

HookEvent = Literal[
    "manual_run",
    "session_start",
    "user_prompt_submit",
    "session_stop",
    "receipt_published",
    "generated_surface_refreshed",
    "harvest_written",
    "real_run_published",
    "gate_review_written",
    "runtime_evidence_selected",
]

HookProducerKind = Literal[
    "jsonl_receipt_watch",
    "harvest_pattern_watch",
    "runtime_candidate_watch",
]

HookMatchMode = Literal["always", "exists", "equals", "contains"]

ManifestKind = Literal[
    "recurrence_component",
    "hook_binding_set",
    "agon_recurrence_adapter",
    "review_surface",
    "rollout_bundle",
    "wiring_plan",
    "unknown",
]

ManifestDiagnosticKind = Literal[
    "loaded_manifest",
    "known_foreign_manifest",
    "adapter_required",
    "manifest_json_error",
    "invalid_manifest_shape",
    "unknown_manifest_kind",
    "owner_repo_mismatch",
]

ManifestDiagnosticSeverity = Literal["low", "medium", "high", "critical"]
EdgeStrength = Literal["required", "recommended", "advisory", "forbidden"]


class StrictModel(BaseModel):
    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
    }
