from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from aoa_sdk.control_plane.routing.agon import (
    build_agon_gate_routing_registry,
    load_packaged_agon_gate_routing_registry,
    validate_agon_gate_routing_registry,
)
from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.validator import get_schema_validator


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]


def test_packaged_registry_is_deterministic_and_sdk_owned() -> None:
    packaged = load_packaged_agon_gate_routing_registry()
    rebuilt = build_agon_gate_routing_registry()

    assert packaged == rebuilt
    assert packaged["schema_version"] == "agon_gate_routing_registry.v1"
    assert packaged["owner_repo"] == "aoa-sdk"
    assert packaged["center_repo"] == "Agents-of-Abyss"
    assert packaged["trigger_count"] == 12
    assert packaged["route_hint_count"] == 12
    active_next_hops = {
        next_hop
        for route in [*packaged["triggers"], *packaged["route_hints"]]
        for next_hop in [
            route["primary_next_hop"],
            *route["secondary_next_hops"],
        ]
    }
    assert "aoa-routing" not in active_next_hops


def test_bridge_preserves_pre_protocol_stop_lines() -> None:
    registry = load_packaged_agon_gate_routing_registry()

    assert {
        "no_arena_session_creation",
        "no_verdict",
        "no_scar_write",
        "no_retention_scheduling",
        "no_rank_mutation",
        "no_tos_promotion",
        "no_runtime_dispatch_authority",
    } <= set(registry["stop_lines"])
    for hint in registry["route_hints"]:
        assert hint["live_protocol"] is False
        assert hint["runtime_effect"] == "none"
        assert "open_arena" not in hint["assistant_allowed"]
        assert "issue_verdict" not in hint["assistant_allowed"]


def test_bridge_rejects_owner_and_authority_drift() -> None:
    registry = load_packaged_agon_gate_routing_registry()
    predecessor_owned = copy.deepcopy(registry)
    predecessor_owned["owner_repo"] = "aoa-routing"
    with pytest.raises(RouterError, match="owner"):
        validate_agon_gate_routing_registry(predecessor_owned)

    authority_leak = copy.deepcopy(registry)
    authority_leak["route_hints"][0]["assistant_allowed"].append("issue_verdict")
    with pytest.raises(RouterError, match="forbidden assistant rights"):
        validate_agon_gate_routing_registry(authority_leak)

    predecessor_hop = copy.deepcopy(registry)
    predecessor_hop["triggers"][0]["secondary_next_hops"].append("aoa-routing")
    with pytest.raises(RouterError, match="active next hop"):
        validate_agon_gate_routing_registry(predecessor_hop)


def test_owner_dispatch_seam_is_sdk_owned_and_schema_valid() -> None:
    schema = get_schema_validator("owner-dispatch-seam.schema.json")
    example = json.loads(
        (PART_ROOT / "examples" / "owner_dispatch_seam.example.json").read_text(
            encoding="utf-8"
        )
    )

    schema.validate(example)
    assert example["contract_id"] == "aoa-sdk.owner-dispatch-seam.v1"
    assert example["owner_dispatch"]["owner_repo"] == "aoa-agents"


def test_part_validator_passes_without_predecessor_checkout() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PART_ROOT / "scripts" / "validate_agon_gate_routing.py"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "aoa-routing" not in result.stdout
