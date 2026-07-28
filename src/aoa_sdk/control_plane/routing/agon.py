"""SDK-owned pre-protocol Agon gate routing bridge.

The bridge emits advisory route candidates only.  It does not open an arena,
activate a capability, execute a plan, issue a verdict, or mutate Agon-owned
state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .core import RouterError
from .validator import get_schema_validator


DATA_ROOT = Path(__file__).resolve().parent / "data"
AGON_GATE_CONFIG_PATH = DATA_ROOT / "agon_gate_routing.config.json"
AGON_GATE_REGISTRY_PATH = DATA_ROOT / "agon_gate_routing_registry.min.json"
AGON_GATE_REGISTRY_SCHEMA = "agon-gate-routing-registry.schema.json"

ROUTING_ACTION_TO_DECISION_STATE = {
    "block_activation_and_reroute": "owner_review_required",
    "emit_agon_gate_candidate": "agon_gate_candidate",
    "emit_owner_review_or_gate_candidate": "owner_review_required",
    "emit_quarantine_hint_and_owner_review": "quarantine_hint",
    "emit_summon_intent_review_hint": "owner_review_required",
    "route_to_agonic_actor_or_gate_candidate": "agon_gate_candidate",
}

FORBIDDEN_HINT_FIELDS = {
    "arena_session",
    "rank_mutation",
    "retention",
    "scar",
    "sealed_commit",
    "tos_promotion",
    "verdict",
}

FORBIDDEN_ASSISTANT_RIGHTS = {
    "become_contestant",
    "grant_closure",
    "initiate_summon",
    "issue_verdict",
    "mutate_rank",
    "promote_to_tos",
    "promote_to_tree_of_sophia",
    "write_scar",
}

REQUIRED_STOP_LINES = {
    "no_arena_session_creation",
    "no_rank_mutation",
    "no_retention_scheduling",
    "no_scar_write",
    "no_tos_promotion",
    "no_verdict",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load Agon routing data {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError(f"Agon routing data {path} must contain an object")
    return payload


def _decision_state_for(action: str) -> str:
    try:
        return ROUTING_ACTION_TO_DECISION_STATE[action]
    except KeyError as exc:
        raise RouterError(f"unknown Agon routing action: {action}") from exc


def load_agon_gate_routing_config() -> dict[str, Any]:
    """Load the SDK-owned packaged source config."""

    return _load_json(AGON_GATE_CONFIG_PATH)


def build_agon_gate_routing_registry(
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deterministic advisory registry from the packaged config."""

    source = dict(config or load_agon_gate_routing_config())
    triggers = source.get("triggers")
    if not isinstance(triggers, list):
        raise RouterError("Agon routing config triggers must be a list")
    stop_lines = source.get("stop_lines")
    if not isinstance(stop_lines, list):
        raise RouterError("Agon routing config stop_lines must be a list")

    route_hints: list[dict[str, Any]] = []
    for trigger_value in triggers:
        if not isinstance(trigger_value, dict):
            raise RouterError("each Agon routing trigger must be an object")
        trigger = dict(trigger_value)
        action = trigger.get("routing_action")
        if not isinstance(action, str):
            raise RouterError("each Agon routing trigger requires routing_action")
        trigger_id = trigger.get("trigger_id")
        if not isinstance(trigger_id, str):
            raise RouterError("each Agon routing trigger requires trigger_id")
        route_hints.append(
            {
                "assistant_allowed": trigger["assistant_allowed"],
                "assistant_forbidden": trigger["assistant_forbidden"],
                "decision_state": _decision_state_for(action),
                "hint_id": f"agon_gate.{trigger_id}.v1",
                "live_protocol": False,
                "primary_next_hop": trigger["primary_next_hop"],
                "recommended_lawful_moves": trigger["recommended_lawful_moves"],
                "routing_action": action,
                "routing_must_not_own": stop_lines,
                "routing_owns": [
                    "thin pre-protocol gate hint",
                    "next-hop orientation",
                ],
                "runtime_effect": "none",
                "secondary_next_hops": trigger["secondary_next_hops"],
                "trigger_class": trigger["trigger_class"],
                "trigger_id": trigger_id,
            }
        )

    registry = {
        "center_repo": source["center_repo"],
        "decision_states": source["decision_states"],
        "owner_repo": source["owner_repo"],
        "route_hint_count": len(route_hints),
        "route_hints": route_hints,
        "routing_contour": source["routing_contour"],
        "schema_version": "agon_gate_routing_registry.v1",
        "source_authority_refs": source["source_authority_refs"],
        "status": source["status"],
        "stop_lines": stop_lines,
        "trigger_classes": sorted(
            {
                str(trigger["trigger_class"])
                for trigger in triggers
                if isinstance(trigger, dict)
            }
        ),
        "trigger_count": len(triggers),
        "triggers": triggers,
        "validation_invariants": [
            "all route hints are pre-protocol",
            "no route hint may open an arena session",
            "no assistant route may grant arena authority",
            "routing emits candidates and next-hop orientation only",
            "center-owned Agon law remains outside aoa-sdk",
        ],
    }
    validate_agon_gate_routing_registry(registry)
    return registry


def render_agon_gate_routing_registry(
    registry: Mapping[str, Any] | None = None,
) -> str:
    """Render stable minified JSON for compatibility and package data."""

    payload = dict(registry or build_agon_gate_routing_registry())
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"


def validate_agon_gate_routing_registry(
    registry: Mapping[str, Any],
    *,
    center_lawful_moves: set[str] | None = None,
) -> None:
    """Validate schema, owner succession, and the pre-protocol stop lines."""

    payload = dict(registry)
    errors = sorted(
        get_schema_validator(AGON_GATE_REGISTRY_SCHEMA).iter_errors(payload),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path)
        suffix = f" at {location}" if location else ""
        raise RouterError(f"Agon routing schema violation{suffix}: {first.message}")

    if payload.get("owner_repo") != "aoa-sdk":
        raise RouterError("Agon gate routing owner must be aoa-sdk after succession")
    if payload.get("center_repo") != "Agents-of-Abyss":
        raise RouterError("Agon center owner must remain Agents-of-Abyss")
    triggers = payload.get("triggers")
    hints = payload.get("route_hints")
    if not isinstance(triggers, list) or not isinstance(hints, list):
        raise RouterError("Agon routing registry triggers and route_hints must be lists")
    if len(triggers) < 10 or len(triggers) != len(hints):
        raise RouterError("Agon routing registry trigger/hint coverage is incomplete")

    trigger_ids = [trigger.get("trigger_id") for trigger in triggers]
    hint_ids = [hint.get("hint_id") for hint in hints]
    if len(trigger_ids) != len(set(trigger_ids)):
        raise RouterError("Agon routing registry contains duplicate trigger_id")
    if len(hint_ids) != len(set(hint_ids)):
        raise RouterError("Agon routing registry contains duplicate hint_id")

    stop_lines = set(payload.get("stop_lines", []))
    missing_stop_lines = sorted(REQUIRED_STOP_LINES - stop_lines)
    if missing_stop_lines:
        raise RouterError(f"Agon routing stop-lines are incomplete: {missing_stop_lines}")

    config = load_agon_gate_routing_config()
    lawful_moves = set(config.get("lawful_moves_known", []))
    if center_lawful_moves is not None:
        drift = sorted(lawful_moves - center_lawful_moves)
        if drift:
            raise RouterError(
                f"Agon routing lawful move vocabulary drifted from center: {drift}"
            )
        lawful_moves = center_lawful_moves
    if "escalate_to_agon_gate" not in lawful_moves:
        raise RouterError("Agon routing lacks escalate_to_agon_gate")

    trigger_by_id = {trigger["trigger_id"]: trigger for trigger in triggers}
    for route in [*triggers, *hints]:
        next_hops = {
            route["primary_next_hop"],
            *route.get("secondary_next_hops", []),
        }
        if "aoa-routing" in next_hops:
            raise RouterError(
                "Agon routing contains an active next hop to retired predecessor "
                "aoa-routing"
            )

    for hint in hints:
        hint_id = hint["hint_id"]
        if hint["trigger_id"] not in trigger_by_id:
            raise RouterError(f"Agon hint references unknown trigger: {hint_id}")
        if hint["live_protocol"] is not False or hint["runtime_effect"] != "none":
            raise RouterError(f"Agon hint is not runtime-neutral: {hint_id}")
        leaked_fields = sorted(FORBIDDEN_HINT_FIELDS & set(hint))
        if leaked_fields:
            raise RouterError(
                f"Agon hint contains forbidden fields {leaked_fields}: {hint_id}"
            )
        leaked_rights = sorted(
            FORBIDDEN_ASSISTANT_RIGHTS & set(hint.get("assistant_allowed", []))
        )
        if leaked_rights:
            raise RouterError(
                f"Agon hint grants forbidden assistant rights {leaked_rights}: "
                f"{hint_id}"
            )
        unknown_moves = sorted(
            set(hint.get("recommended_lawful_moves", [])) - lawful_moves
        )
        if unknown_moves:
            raise RouterError(
                f"Agon hint contains unknown lawful moves {unknown_moves}: {hint_id}"
            )


def load_packaged_agon_gate_routing_registry() -> dict[str, Any]:
    """Load and rebuild-check the wheel-packaged registry."""

    payload = _load_json(AGON_GATE_REGISTRY_PATH)
    validate_agon_gate_routing_registry(payload)
    expected = render_agon_gate_routing_registry()
    actual = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"
    if actual != expected:
        raise RouterError("packaged Agon gate routing registry is stale")
    return payload


__all__ = [
    "AGON_GATE_CONFIG_PATH",
    "AGON_GATE_REGISTRY_PATH",
    "build_agon_gate_routing_registry",
    "load_agon_gate_routing_config",
    "load_packaged_agon_gate_routing_registry",
    "render_agon_gate_routing_registry",
    "validate_agon_gate_routing_registry",
]
