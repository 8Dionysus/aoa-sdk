from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_mechanics_topology.py"
SPEC = importlib.util.spec_from_file_location("validate_mechanics_topology", SCRIPT_PATH)
mechanics_validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = mechanics_validator
SPEC.loader.exec_module(mechanics_validator)


def test_live_mechanics_topology_is_valid() -> None:
    assert mechanics_validator.validate(REPO_ROOT) == []


def test_mechanics_package_set_is_explicit() -> None:
    assert mechanics_validator.EXPECTED_PACKAGES == (
        "agon",
        "antifragility",
        "boundary-bridge",
        "checkpoint",
        "codex-projection",
        "experience",
        "questbook",
        "recurrence",
        "release-support",
        "rpg",
        "runtime-seam",
        "titan",
    )


def test_demoted_parent_candidates_are_explicit_parts() -> None:
    assert mechanics_validator.DEMOTED_PARENT_CANDIDATES == (
        "workspace-topology",
        "compatibility",
        "skill-routing",
        "surface-detection",
        "closeout",
        "a2a-return",
        "codex-plane",
    )
