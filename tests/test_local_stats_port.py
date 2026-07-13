from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from aoa_sdk.compatibility.policy import SURFACE_COMPATIBILITY_RULES


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = REPO_ROOT / "stats" / "packets" / (
    "federation-compatibility-version-negotiation-ratio.reference.json"
)


def load_packet() -> dict:
    return json.loads(PACKET_PATH.read_text(encoding="utf-8"))


def version_negotiation_census() -> tuple[set[str], set[str]]:
    versioned = {
        surface_id
        for surface_id, rule in SURFACE_COMPATIBILITY_RULES.items()
        if rule.version_field is not None
    }
    unversioned = set(SURFACE_COMPATIBILITY_RULES) - versioned
    return versioned, unversioned


def assert_packet_matches_owner_policy(packet: dict) -> None:
    versioned, unversioned = version_negotiation_census()
    population_size = len(versioned) + len(unversioned)

    assert packet["population"]["size"] == population_size
    assert packet["sample"]["size"] == population_size
    assert packet["value"]["numerator"] == len(versioned), (
        "packet numerator must match versioned rules in the owner policy"
    )
    assert packet["value"]["denominator"] == population_size
    assert packet["value"]["number"] == len(versioned) / population_size
    assert packet["progress"] == {
        "state": "terminal",
        "completed": population_size,
        "total": population_size,
    }


def test_reference_ratio_matches_current_federation_compatibility_policy() -> None:
    packet = load_packet()
    versioned, unversioned = version_negotiation_census()

    assert len(SURFACE_COMPATIBILITY_RULES) == 80
    assert len(versioned) == 77
    assert unversioned == {
        "aoa-playbooks.playbook_activation_surfaces.min",
        "aoa-playbooks.playbook_federation_surfaces.min",
        "aoa-memo.checkpoint_to_memory_contract.example",
    }
    assert_packet_matches_owner_policy(packet)


def test_false_all_versioned_packet_is_rejected() -> None:
    false_packet = deepcopy(load_packet())
    false_packet["value"]["numerator"] = false_packet["value"]["denominator"]
    false_packet["value"]["number"] = 1.0

    with pytest.raises(
        AssertionError,
        match="packet numerator must match versioned rules in the owner policy",
    ):
        assert_packet_matches_owner_policy(false_packet)
