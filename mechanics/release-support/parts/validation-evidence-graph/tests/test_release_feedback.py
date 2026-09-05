"""Cheap owner-local selection checks; actual product tests remain the payload."""

import json
import sys
from pathlib import Path

import pytest

from scripts import release_check


PART = "mechanics/titan/parts/appserver-bridge-helper-contracts"


@pytest.fixture
def owner(tmp_path: Path) -> Path:
    for path in (f"{PART}/tests/test_bridge.py", "tests/test_smoke.py"):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def test_example(): assert True\n")
    (tmp_path / "mechanics/topology.json").write_text(json.dumps({
        "source_family_routes": {"titans": {"primary_mechanic": "titan"}},
    }))
    return tmp_path


def test_feedback_selects_current_part_without_requiring_a_commit(owner: Path) -> None:
    assert release_check.feedback_test_paths([
        f"{PART}/scripts/new_untracked_script.py", f"{PART}/schemas/input.json",
    ], owner) == [f"{PART}/tests"]
    assert release_check.feedback_test_paths(["tests/test_smoke.py"], owner) == ["tests/test_smoke.py"]


def test_source_family_uses_owner_topology_and_deduplicates_part(owner: Path) -> None:
    assert release_check.feedback_test_paths([
        "src/aoa_sdk/titans/appserver_bridge.py", f"{PART}/tests/test_bridge.py",
    ], owner) == ["mechanics/titan"]


@pytest.mark.parametrize("path", [
    "pyproject.toml", "src/aoa_sdk/__init__.py", "src/aoa_sdk/unknown/new.py",
    "scripts/release_check.py", "mechanics/titan/parts/no-tests/schema.json",
])
def test_shared_unknown_and_uncovered_paths_expand_to_full(owner: Path, path: str) -> None:
    assert release_check.feedback_test_paths([f"{PART}/tests/test_bridge.py", path], owner) is None


def test_invalid_topology_expands_and_path_escape_is_rejected(owner: Path) -> None:
    (owner / "mechanics/topology.json").write_text("invalid")
    assert release_check.feedback_test_paths(["src/aoa_sdk/titans/bridge.py"], owner) is None
    for path in ("../foreign.py", "/tmp/foreign.py", "bad\x00path"):
        with pytest.raises(ValueError):
            release_check.feedback_test_paths([path], owner)


@pytest.mark.parametrize("args", [
    ["--feedback"], ["--changed-path", "tests/test_smoke.py"],
    ["--feedback", "--changed-path", "tests/test_smoke.py", "--receipt", "proof.json"],
    ["--feedback", "--mode", "serial", "--changed-path", "tests/test_smoke.py"],
])
def test_feedback_cannot_silently_become_full_gate_receipt(args: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        release_check.parse_args(args)
    assert error.value.code == 2


def test_feedback_runs_real_pytest_argv_and_propagates_failure(owner: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(release_check, "REPO_ROOT", owner)
    monkeypatch.setattr(release_check, "run_step", lambda label, command: calls.append(command) or 1)
    assert release_check.main(["--feedback", "--changed-path", f"{PART}/scripts/bridge.py"]) == 1
    assert calls == [[sys.executable, "-m", "pytest", "-q", "--", f"{PART}/tests"]]
    calls.clear()
    assert release_check.main(["--feedback", "--changed-path", "pyproject.toml"]) == 1
    assert calls == [[sys.executable, release_check.GRAPH_RUNNER, "--profile", "full"]]
