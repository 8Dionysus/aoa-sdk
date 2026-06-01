from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_sdk_source_home.py"
SPEC = importlib.util.spec_from_file_location("validate_sdk_source_home", SCRIPT_PATH)
sdk_home_validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = sdk_home_validator
SPEC.loader.exec_module(sdk_home_validator)


def test_live_sdk_source_home_is_valid() -> None:
    assert sdk_home_validator.validate(REPO_ROOT) == []


def test_sdk_source_home_branches_are_explicit_and_agent_routed() -> None:
    manifest = json.loads((REPO_ROOT / "sdk/source_home.manifest.json").read_text(encoding="utf-8"))
    branch_paths = {branch["path"] for branch in manifest["branches"]}

    assert branch_paths == {
        "sdk/public-interface",
        "sdk/facade-boundary",
        "sdk/runtime-entry",
        "sdk/distribution",
    }

    for branch_path in branch_paths:
        assert (REPO_ROOT / branch_path / "AGENTS.md").is_file()
        assert (REPO_ROOT / branch_path / "README.md").is_file()


def test_sdk_source_home_does_not_use_mechanic_parts_vocabulary() -> None:
    assert not (REPO_ROOT / "sdk/PARTS.md").exists()


def test_sdk_source_home_distinguishes_posture_from_implementation() -> None:
    readme = (REPO_ROOT / "sdk/README.md").read_text(encoding="utf-8")
    shape = (REPO_ROOT / "sdk/SDK_SHAPE.md").read_text(encoding="utf-8")
    agents = (REPO_ROOT / "sdk/AGENTS.md").read_text(encoding="utf-8")

    assert "`sdk/` is not `src/aoa_sdk/`." in readme
    assert "`src/aoa_sdk/` | importable Python implementation" in shape
    assert "Keep `src/aoa_sdk/` as the importable implementation lane." in agents
