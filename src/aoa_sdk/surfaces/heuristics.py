from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SurfaceHeuristicRule:
    id: str
    owner_repo: Literal[
        "aoa-techniques",
        "aoa-evals",
        "aoa-memo",
        "aoa-playbooks",
        "aoa-agents",
    ]
    object_kind: Literal["technique", "eval", "memo", "playbook", "agent"]
    surface_ref: str
    display_name: str
    default_state: Literal["candidate-now", "candidate-later"]
    execution_lane: Literal["inspect-expand-use", "closeout-harvest", "defer"]
    reason_template: str
    signal: Literal["repeated-pattern", "proof-need", "recall-need", "scenario-recurring", "role-posture"]
    tokens: tuple[str, ...] = ()
    existing_surface: str | None = None
    closeout_family_candidates: tuple[str, ...] = ()
    promotion_hint: str | None = None
    confidence: Literal["low", "medium", "high"] = "medium"


@dataclass(frozen=True)
class ExplicitLayerRule:
    token: str
    owner_repo: Literal[
        "aoa-techniques",
        "aoa-skills",
        "aoa-evals",
        "aoa-memo",
        "aoa-playbooks",
        "aoa-agents",
    ]
    object_kind: Literal["technique", "skill", "eval", "memo", "playbook", "agent"]
    surface_ref: str
    display_name: str
    existing_surface: str | None = None


PROOF_NEED_RULE = SurfaceHeuristicRule(
    id="proof-need",
    owner_repo="aoa-evals",
    object_kind="eval",
    surface_ref="aoa-evals.runtime_candidate_template_index.min",
    display_name="Bounded proof surface needed",
    default_state="candidate-now",
    execution_lane="inspect-expand-use",
    reason_template="intent suggests bounded proof or verification posture",
    signal="proof-need",
    tokens=("verify", "proof", "regression", "quality", "score", "eval", "invariant", "property", "contract"),
    existing_surface="aoa-evals.runtime_candidate_template_index.min",
    closeout_family_candidates=("aoa-session-donor-harvest",),
    promotion_hint="consider a bounded eval bundle if the same claim recurs across reviewed sessions",
)

RECALL_NEED_RULE = SurfaceHeuristicRule(
    id="recall-need",
    owner_repo="aoa-memo",
    object_kind="memo",
    surface_ref="aoa-memo.memory_catalog.min",
    display_name="Memo semantic recall",
    default_state="candidate-now",
    execution_lane="inspect-expand-use",
    reason_template="intent suggests provenance-aware recall rather than only fresh context",
    signal="recall-need",
    tokens=("recall", "memory", "previous", "prior", "why", "history", "provenance", "earlier", "context"),
    existing_surface="aoa-memo.memory_catalog.min",
    closeout_family_candidates=("aoa-session-donor-harvest",),
    promotion_hint="write back only bounded, provenance-aware memory; memory is not proof",
)

SCENARIO_RECURRING_RULE = SurfaceHeuristicRule(
    id="scenario-recurring",
    owner_repo="aoa-playbooks",
    object_kind="playbook",
    surface_ref="aoa-playbooks.playbook_registry.min",
    display_name="Recurring route candidate",
    default_state="candidate-later",
    execution_lane="closeout-harvest",
    reason_template="intent suggests a recurring multi-surface route rather than one bounded workflow",
    signal="scenario-recurring",
    tokens=("recurring", "repeat", "again", "runbook", "workflow", "handoff", "sequence", "campaign", "checkpoint"),
    existing_surface="aoa-playbooks.playbook_registry.min",
    closeout_family_candidates=("aoa-automation-opportunity-scan", "aoa-quest-harvest"),
    promotion_hint="promote only after repeated reviewed runs show a stable recurring scenario",
)

ROLE_POSTURE_RULE = SurfaceHeuristicRule(
    id="role-posture",
    owner_repo="aoa-agents",
    object_kind="agent",
    surface_ref="aoa-agents.runtime_seam_bindings",
    display_name="Role posture check",
    default_state="candidate-now",
    execution_lane="inspect-expand-use",
    reason_template="intent suggests role contract or handoff posture work",
    signal="role-posture",
    tokens=("agent", "role", "handoff", "orchestrator", "subagent", "persona", "tier", "cohort"),
    existing_surface="aoa-agents.runtime_seam_bindings",
    closeout_family_candidates=("aoa-session-donor-harvest",),
)

REPEATED_PATTERN_RULE = SurfaceHeuristicRule(
    id="repeated-pattern",
    owner_repo="aoa-techniques",
    object_kind="technique",
    surface_ref="aoa-techniques.technique_promotion_readiness.min",
    display_name="Reusable practice candidate",
    default_state="candidate-later",
    execution_lane="closeout-harvest",
    reason_template="repeated bounded discipline suggests technique extraction rather than one-off residue",
    signal="repeated-pattern",
    tokens=("repeat", "repeated", "again", "pattern", "recurring"),
    existing_surface="aoa-techniques.technique_promotion_readiness.min",
    closeout_family_candidates=("aoa-session-donor-harvest", "aoa-quest-harvest"),
    promotion_hint="keep this as a promotion hint until repeated evidence exists across reviewed sessions",
)

HEURISTIC_RULES: tuple[SurfaceHeuristicRule, ...] = (
    PROOF_NEED_RULE,
    RECALL_NEED_RULE,
    SCENARIO_RECURRING_RULE,
    ROLE_POSTURE_RULE,
    REPEATED_PATTERN_RULE,
)

EXPLICIT_LAYER_RULES: tuple[ExplicitLayerRule, ...] = (
    ExplicitLayerRule(
        token="technique",
        owner_repo="aoa-techniques",
        object_kind="technique",
        surface_ref="aoa-techniques.technique_promotion_readiness.min",
        display_name="Technique layer request",
        existing_surface="aoa-techniques.technique_promotion_readiness.min",
    ),
    ExplicitLayerRule(
        token="skill",
        owner_repo="aoa-skills",
        object_kind="skill",
        surface_ref="aoa-skills:layer-request",
        display_name="Skill layer request",
        existing_surface="aoa-skills.runtime_discovery_index",
    ),
    ExplicitLayerRule(
        token="playbook",
        owner_repo="aoa-playbooks",
        object_kind="playbook",
        surface_ref="aoa-playbooks.playbook_registry.min",
        display_name="Playbook layer request",
        existing_surface="aoa-playbooks.playbook_registry.min",
    ),
    ExplicitLayerRule(
        token="eval",
        owner_repo="aoa-evals",
        object_kind="eval",
        surface_ref="aoa-evals.runtime_candidate_template_index.min",
        display_name="Eval layer request",
        existing_surface="aoa-evals.runtime_candidate_template_index.min",
    ),
    ExplicitLayerRule(
        token="memo",
        owner_repo="aoa-memo",
        object_kind="memo",
        surface_ref="aoa-memo.memory_catalog.min",
        display_name="Memo layer request",
        existing_surface="aoa-memo.memory_catalog.min",
    ),
    ExplicitLayerRule(
        token="memory",
        owner_repo="aoa-memo",
        object_kind="memo",
        surface_ref="aoa-memo.memory_catalog.min",
        display_name="Memo layer request",
        existing_surface="aoa-memo.memory_catalog.min",
    ),
    ExplicitLayerRule(
        token="agent",
        owner_repo="aoa-agents",
        object_kind="agent",
        surface_ref="aoa-agents.runtime_seam_bindings",
        display_name="Agent layer request",
        existing_surface="aoa-agents.runtime_seam_bindings",
    ),
)

EXPLICIT_LAYER_RULES_BY_TOKEN = {rule.token: rule for rule in EXPLICIT_LAYER_RULES}
HEURISTIC_RULES_BY_ID = {rule.id: rule for rule in HEURISTIC_RULES}
