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


def check_role_contract(role: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return boundary violations for a recursor role contract."""
    violations: List[Dict[str, Any]] = []
    rid = str(role.get("recursor_id", "<missing>"))

    def add(kind: str, message: str, severity: str = "critical") -> None:
        violations.append(
            {"kind": kind, "severity": severity, "recursor_id": rid, "message": message}
        )

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
    forbidden = set(role.get("forbidden_actions", []))
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
    for agent in projection.get("candidate_agents", []):
        rid = agent.get("recursor_id", "<missing>")
        if agent.get("activation_status") != "candidate_only":
            add("projection_agent_not_candidate_only", f"{rid} must remain candidate_only.")
        forbidden = set(agent.get("forbidden", []))
        missing = {"agent_spawn", "arena_session", "verdict", "scar_write", "hidden_scheduler"} - forbidden
        if missing:
            add("projection_agent_missing_forbidden", f"{rid} missing forbidden tokens: {sorted(missing)}")
    return violations


def boundary_status(violations: Sequence[Dict[str, Any]]) -> str:
    return "fail" if violations else "pass"
