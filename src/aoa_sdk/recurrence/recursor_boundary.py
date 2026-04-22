"""Boundary checks for recurrence recursor readiness surfaces.

This module is intentionally read-only. It does not spawn agents, install Codex
subagents, open Agon sessions, or mutate owner surfaces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

GLOBAL_FORBIDDEN_ACTIONS = {
    "spawn_agent",
    "open_arena_session",
    "issue_verdict",
    "write_scar",
    "mutate_rank",
    "promote_to_tree_of_sophia",
    "hidden_scheduler_action",
}
ROLE_REQUIRED_STOP_LINES = {
    "projection_candidate_is_not_install",
    "assistant_is_not_contestant",
}
PAIR_REQUIRED_SEPARATION = {
    "witness_cannot_apply_mutations",
    "executor_cannot_close_review",
    "executor_cannot_self_verify_without_external_check",
    "neither_can_spawn_additional_agents",
}
PAIR_REQUIRED_HANDOFF_ORDER = {
    "witness_preflight",
    "executor_bounded_work",
    "witness_trace_check",
    "owner_or_main_codex_review",
}
PROJECTION_REQUIRED_ROLES = {"recursor.witness", "recursor.executor"}
PROJECTION_REQUIRED_FORBIDDEN = {
    "global": {
        "agent_spawn",
        "arena_session",
        "verdict",
        "scar_write",
        "rank_mutation",
        "hidden_scheduler",
    },
    "recursor.witness": {
        "workspace_write",
    },
    "recursor.executor": {
        "execute_without_plan",
        "self_verify_as_final",
    },
}
PROJECTION_REQUIRED_ACTIVATION = {"explicit_main_codex_call", "no_agonic_runtime_claim"}

BOUNDARY_STOP_LINES = [
    "no_arena_session",
    "no_verdict",
    "no_scar_write",
    "no_rank_mutation",
    "no_assistant_contestant_drift",
    "no_hidden_scheduler",
    "no_tos_promotion",
    "no_codex_projection_absorption",
]


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def check_role_contract(role: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return boundary violations for a recursor role contract."""
    violations: List[Dict[str, Any]] = []
    rid = str(role.get("recursor_id", "<missing>"))

    def add(kind: str, message: str, severity: str = "critical") -> None:
        violations.append(
            {"kind": kind, "severity": severity, "recursor_id": rid, "message": message}
        )

    if role.get("schema_version") != "recursor-role-contract/v1":
        add("invalid_role_schema", "Role must use recursor-role-contract/v1.")
    if role.get("owner_repo") != "aoa-agents":
        add("invalid_role_owner", "Role owner_repo must be aoa-agents.")
    if role.get("readiness_status") != "candidate":
        add("recursor_not_candidate", "Recursor readiness seed only allows candidate status.")
    form = role.get("default_form", {})
    if form.get("kind") != "assistant":
        add("recursor_not_assistant_default", "Default recursor form must remain assistant.")
    if form.get("arena_eligible") is not False:
        add("assistant_arena_eligible", "Assistant recursor must not be arena eligible.")
    future = role.get("future_agonic_candidate", {})
    if future.get("enabled") is not False or future.get("live_authority") is not False:
        add("future_agonic_candidate_live", "Future agonic candidate must be disabled and non-live.")
    projection = role.get("codex_projection", {})
    if projection.get("status") != "candidate_only":
        add("projection_not_candidate_only", "Codex projection must remain candidate_only.")
    if projection.get("install_by_default") is not False:
        add("projection_installs_by_default", "Projection candidates must not install by default.")
    if projection.get("requires_owner_review") is not True:
        add("projection_no_owner_review", "Projection candidate must require owner review.")
    if role.get("receipts_required") is not True:
        add("receipts_not_required", "Recursor role must require receipts.")
    forbidden = _string_set(role.get("forbidden_actions", []))
    missing = GLOBAL_FORBIDDEN_ACTIONS - forbidden
    if rid == "recursor.witness":
        missing |= {"apply_patch", "close_review_decision"} - forbidden
    if rid == "recursor.executor":
        missing |= {"execute_without_approved_plan", "self_verify_final_truth"} - forbidden
    if missing:
        add("missing_forbidden_actions", f"Missing forbidden actions: {sorted(missing)}")
    memory = role.get("memory_policy", {})
    if memory.get("direct_durable_write_allowed") is not False:
        add("recursor_direct_memory_write", "Recursor cannot directly write durable memory.")
    stop_lines = _string_set(role.get("stop_lines", []))
    missing_stop_lines = ROLE_REQUIRED_STOP_LINES - stop_lines
    if missing_stop_lines:
        add("missing_role_stop_lines", f"Missing stop-lines: {sorted(missing_stop_lines)}")
    return violations


def check_pair_contract(pair: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return boundary violations for the witness/executor pair contract."""
    violations: List[Dict[str, Any]] = []

    def add(kind: str, message: str, severity: str = "critical") -> None:
        violations.append({"kind": kind, "severity": severity, "message": message})

    if pair.get("schema_version") != "recursor-pair-contract/v1":
        add("invalid_pair_schema", "Pair must use recursor-pair-contract/v1.")
    if pair.get("pair_ref") != "recursor_pair:witness_executor:v1":
        add("invalid_pair_ref", "Pair must use recursor_pair:witness_executor:v1.")
    roles = pair.get("roles", {})
    if not isinstance(roles, dict):
        add("invalid_pair_roles_shape", "Pair roles must be an object.")
        roles = {}
    if roles.get("witness") != "recursor.witness" or roles.get("executor") != "recursor.executor":
        add("invalid_pair_roles", "Pair must bind witness and executor exactly.")
    if pair.get("activation_status") != "readiness_only":
        add("pair_not_readiness_only", "Pair activation_status must remain readiness_only.")

    separation = _string_set(pair.get("required_separation", []))
    missing_separation = PAIR_REQUIRED_SEPARATION - separation
    if missing_separation:
        add("missing_pair_separation", f"Missing pair separation: {sorted(missing_separation)}")

    handoff_order = _string_set(pair.get("handoff_order", []))
    missing_handoff = PAIR_REQUIRED_HANDOFF_ORDER - handoff_order
    if missing_handoff:
        add("missing_pair_handoff_order", f"Missing pair handoff order: {sorted(missing_handoff)}")
    return violations


def check_projection_candidate(projection: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return boundary violations for Codex recursor projection candidates."""
    violations: List[Dict[str, Any]] = []

    def add(kind: str, message: str, severity: str = "critical") -> None:
        violations.append({"kind": kind, "severity": severity, "message": message})

    if projection.get("projection_status") != "candidate_only":
        add("projection_not_candidate_only", "Projection status must be candidate_only.")
    if projection.get("install_by_default") is not False:
        add("projection_installs_by_default", "Projection must not install by default.")
    if projection.get("requires_owner_review") is not True:
        add("projection_no_owner_review", "Projection must require owner review.")
    agents = [agent for agent in projection.get("candidate_agents", []) if isinstance(agent, dict)]
    agent_ids = [str(agent.get("recursor_id", "<missing>")) for agent in agents]
    agent_id_set = set(agent_ids)
    unexpected = agent_id_set - PROJECTION_REQUIRED_ROLES
    missing_roles = PROJECTION_REQUIRED_ROLES - agent_id_set
    duplicate_ids = sorted({rid for rid in agent_ids if agent_ids.count(rid) > 1})
    if unexpected:
        add("unexpected_projection_agent", f"Unexpected projection candidate roles: {sorted(unexpected)}")
    if missing_roles:
        add("missing_projection_agent", f"Missing projection candidates: {sorted(missing_roles)}")
    if duplicate_ids:
        add("duplicate_projection_agent", f"Duplicate projection candidate roles: {duplicate_ids}")
    if len(agents) != len(PROJECTION_REQUIRED_ROLES):
        add("invalid_projection_agent_count", "Projection must contain exactly witness and executor.")
    for agent in agents:
        rid = str(agent.get("recursor_id", "<missing>"))
        if agent.get("activation_status") != "candidate_only":
            add("projection_agent_not_candidate_only", f"{rid} must remain candidate_only.")
        forbidden = _string_set(agent.get("forbidden", []))
        required_forbidden = set(PROJECTION_REQUIRED_FORBIDDEN["global"])
        required_forbidden |= PROJECTION_REQUIRED_FORBIDDEN.get(rid, set())
        missing = required_forbidden - forbidden
        if missing:
            add("projection_agent_missing_forbidden", f"{rid} missing forbidden tokens: {sorted(missing)}")
        activation_requires = _string_set(agent.get("activation_requires", []))
        missing_activation = PROJECTION_REQUIRED_ACTIVATION - activation_requires
        if missing_activation:
            add("projection_agent_missing_activation_guard", f"{rid} missing activation guards: {sorted(missing_activation)}")
    return violations


def boundary_status(violations: Sequence[Dict[str, Any]]) -> str:
    return "fail" if violations else "pass"
