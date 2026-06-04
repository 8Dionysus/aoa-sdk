from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("source_topology_common", SCRIPT_DIR / "source_topology_common.py")
source_topology = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = source_topology
SPEC.loader.exec_module(source_topology)


def _walk_packages(package: dict[str, object]) -> list[dict[str, object]]:
    packages = [package]
    for child in package["packages"]:
        assert isinstance(child, dict)
        packages.extend(_walk_packages(child))
    return packages


def _walk_modules(package: dict[str, object]) -> list[dict[str, object]]:
    modules = list(package["modules"])
    for child in package["packages"]:
        assert isinstance(child, dict)
        modules.extend(_walk_modules(child))
    return modules


def test_source_topology_index_is_current() -> None:
    expected = source_topology.render_payload(source_topology.build_payload())
    current = source_topology.SOURCE_TOPOLOGY_PATH.read_text(encoding="utf-8")

    assert current == expected


def test_source_topology_index_names_checkpoint_topology_branch() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    assert packages["src/aoa_sdk/checkpoints/topology"]["node_kind"] == "topology_package"
    assert "path naming" in packages["src/aoa_sdk/checkpoints/topology"]["role"]
    assert modules["src/aoa_sdk/checkpoints/topology/paths.py"]["node_kind"] == "topology_module"
    assert modules["src/aoa_sdk/checkpoints/topology/paths.py"]["route_key"] == "checkpoints.topology.paths"
    assert "filesystem path topology" in modules["src/aoa_sdk/checkpoints/topology/paths.py"]["role"]
    assert "behavior" in modules["src/aoa_sdk/checkpoints/topology/paths.py"]["next_route"]


def test_source_topology_index_names_checkpoint_route_role_branches() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    expected_packages = {
        "src/aoa_sdk/checkpoints/closeout": "closeout pipeline",
        "src/aoa_sdk/checkpoints/hooks": "Git hook",
        "src/aoa_sdk/checkpoints/ledger": "note ledger",
        "src/aoa_sdk/checkpoints/promotion": "promotion target",
        "src/aoa_sdk/checkpoints/render": "presentation render",
        "src/aoa_sdk/checkpoints/review": "agent-review",
        "src/aoa_sdk/checkpoints/runtime": "runtime-session",
    }
    for path, role_fragment in expected_packages.items():
        assert role_fragment in packages[path]["role"]
    assert "skipped-session recovery" in packages["src/aoa_sdk/checkpoints/review"]["role"]

    assert modules["src/aoa_sdk/checkpoints/registry.py"]["split_pressure"] == "medium"
    assert "route-role orchestrator" in modules["src/aoa_sdk/checkpoints/registry.py"]["role"]
    assert "named checkpoint branch" in modules["src/aoa_sdk/checkpoints/registry.py"]["next_route"]
    assert "candidate-intelligence navigation index" in modules[
        "src/aoa_sdk/checkpoints/candidate_indexes.py"
    ]["role"]
    assert "candidate navigation" in modules[
        "src/aoa_sdk/checkpoints/candidate_indexes.py"
    ]["next_route"]
    assert "backlog audit" in modules["src/aoa_sdk/checkpoints/backlog.py"]["role"]
    assert "runtime trace gap navigation" in modules["src/aoa_sdk/checkpoints/backlog.py"]["role"]
    assert "backlog inspection read-only" in modules[
        "src/aoa_sdk/checkpoints/backlog.py"
    ]["next_route"]
    assert "backlog navigation index" in modules[
        "src/aoa_sdk/checkpoints/backlog_indexes.py"
    ]["role"]
    assert "action-signature" in modules[
        "src/aoa_sdk/checkpoints/candidate_intelligence.py"
    ]["role"]
    assert "classifier route evidence" in modules[
        "src/aoa_sdk/checkpoints/candidate_intelligence.py"
    ]["next_route"]
    assert "carrier-candidate navigation index" in modules[
        "src/aoa_sdk/checkpoints/carrier_indexes.py"
    ]["role"]
    assert "carrier-candidate classifier" in modules[
        "src/aoa_sdk/checkpoints/carrier_intelligence.py"
    ]["role"]
    assert "checkpoint lifecycle audit" in modules["src/aoa_sdk/checkpoints/lifecycle.py"]["role"]
    assert "close/archive orchestration" in modules["src/aoa_sdk/checkpoints/lifecycle.py"]["role"]
    assert modules["src/aoa_sdk/checkpoints/closeout/bridge.py"]["split_pressure"] == "low"
    assert "compatibility facade" in modules["src/aoa_sdk/checkpoints/closeout/bridge.py"]["role"]
    assert "facade thin" in modules["src/aoa_sdk/checkpoints/closeout/bridge.py"]["next_route"]
    closeout_module_roles = {
        "src/aoa_sdk/checkpoints/closeout/context.py": "candidate-map owner",
        "src/aoa_sdk/checkpoints/closeout/evidence.py": "Codex trace evidence reader owner",
        "src/aoa_sdk/checkpoints/closeout/execution.py": "mechanical packet and receipt builder owner",
        "src/aoa_sdk/checkpoints/closeout/followthrough.py": "next-skill posture owner",
        "src/aoa_sdk/checkpoints/closeout/owner_handoff.py": "owner follow-through handoff owner",
    }
    for path, role_fragment in closeout_module_roles.items():
        assert role_fragment in modules[path]["role"]
    assert modules["src/aoa_sdk/checkpoints/ledger/notes.py"]["split_pressure"] == "medium"
    assert "runtime note loading" in modules["src/aoa_sdk/checkpoints/ledger/notes.py"]["role"]
    assert "lifecycle ledger event normalization" in modules[
        "src/aoa_sdk/checkpoints/ledger/lifecycle_events.py"
    ]["role"]
    assert "skipped-session recovery" in modules[
        "src/aoa_sdk/checkpoints/review/skipped_recovery.py"
    ]["role"]
    assert "blocking required-action" in modules[
        "src/aoa_sdk/checkpoints/review/skipped_recovery.py"
    ]["role"]


def test_source_topology_index_names_surface_route_role_branches() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    assert "owner-layer signal handoff" in packages["src/aoa_sdk/surfaces"]["role"]
    assert "named surface branch" in packages["src/aoa_sdk/surfaces"]["next_route"]
    assert modules["src/aoa_sdk/surfaces/registry.py"]["split_pressure"] == "low"
    assert "public API facade" in modules["src/aoa_sdk/surfaces/registry.py"]["role"]
    assert "named surface branch" in modules["src/aoa_sdk/surfaces/registry.py"]["next_route"]
    surface_module_roles = {
        "src/aoa_sdk/surfaces/items.py": "opportunity item derivation",
        "src/aoa_sdk/surfaces/context.py": "receipt context owner",
        "src/aoa_sdk/surfaces/checkpoint_candidates.py": "checkpoint candidate cluster",
        "src/aoa_sdk/surfaces/progression.py": "progression-axis signal owner",
        "src/aoa_sdk/surfaces/closeout_handoff.py": "reviewed closeout handoff assembly",
        "src/aoa_sdk/surfaces/common.py": "small pure helper owner",
        "src/aoa_sdk/surfaces/heuristics.py": "heuristic rule owner",
    }
    for path, role_fragment in surface_module_roles.items():
        assert role_fragment in modules[path]["role"]


def test_source_topology_index_names_cli_command_family_modules() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    assert "command-family route modules" in packages["src/aoa_sdk/cli"]["role"]
    assert "main.py as root app assembly" in packages["src/aoa_sdk/cli"]["next_route"]
    assert modules["src/aoa_sdk/cli/main.py"]["split_pressure"] == "low"
    assert "root Typer app assembly" in modules["src/aoa_sdk/cli/main.py"]["role"]
    assert "command-family module" in modules["src/aoa_sdk/cli/main.py"]["next_route"]
    cli_module_roles = {
        "src/aoa_sdk/cli/checkpoint.py": "checkpoint capture",
        "src/aoa_sdk/cli/closeout.py": "reviewed closeout run",
        "src/aoa_sdk/cli/common.py": "shared path resolution",
        "src/aoa_sdk/cli/compatibility.py": "compatibility check",
        "src/aoa_sdk/cli/release.py": "release audit",
        "src/aoa_sdk/cli/rendering.py": "human-readable report rendering",
        "src/aoa_sdk/cli/skills.py": "skill detect",
        "src/aoa_sdk/cli/surfaces.py": "surface detect",
        "src/aoa_sdk/cli/workspace.py": "workspace inspect",
    }
    for path, role_fragment in cli_module_roles.items():
        assert role_fragment in modules[path]["role"]


def test_source_topology_index_names_closeout_route_role_branches() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    assert "route-role branches" in packages["src/aoa_sdk/closeout"]["role"]
    assert "publisher" in packages["src/aoa_sdk/closeout"]["next_route"]
    assert modules["src/aoa_sdk/closeout/api.py"]["split_pressure"] == "low"
    assert "public facade" in modules["src/aoa_sdk/closeout/api.py"]["role"]
    assert "owning closeout route branch" in modules["src/aoa_sdk/closeout/api.py"]["next_route"]
    closeout_module_roles = {
        "src/aoa_sdk/closeout/filesystem.py": "safe filename",
        "src/aoa_sdk/closeout/followthrough.py": "owner follow-through",
        "src/aoa_sdk/closeout/manifests.py": "manifest assembly",
        "src/aoa_sdk/closeout/publishers.py": "subprocess execution",
        "src/aoa_sdk/closeout/queue.py": "inbox processing",
        "src/aoa_sdk/closeout/receipts.py": "publisher detection",
        "src/aoa_sdk/closeout/runner.py": "reviewed manifest run",
    }
    for path, role_fragment in closeout_module_roles.items():
        assert role_fragment in modules[path]["role"]


def test_source_topology_index_names_recurrence_route_role_branches() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    assert "typed contract route-role branches" in packages[
        "src/aoa_sdk/recurrence/contracts"
    ]["role"]
    assert "live observation producer route-role branches" in packages[
        "src/aoa_sdk/recurrence/live"
    ]["role"]
    assert modules["src/aoa_sdk/recurrence/cli.py"]["split_pressure"] == "low"
    assert "exported app assembly facade" in modules["src/aoa_sdk/recurrence/cli.py"]["role"]
    assert "owning recurrence cli_* module" in modules["src/aoa_sdk/recurrence/cli.py"]["next_route"]
    assert modules["src/aoa_sdk/recurrence/live_observations.py"]["split_pressure"] == "low"
    assert "producer registry facade" in modules["src/aoa_sdk/recurrence/live_observations.py"]["role"]
    assert "recurrence/live branches" in modules[
        "src/aoa_sdk/recurrence/live_observations.py"
    ]["next_route"]
    assert modules["src/aoa_sdk/recurrence/models.py"]["split_pressure"] == "low"
    assert "compatibility re-export" in modules["src/aoa_sdk/recurrence/models.py"]["role"]
    recurrence_module_roles = {
        "src/aoa_sdk/recurrence/cli_core.py": "root command family",
        "src/aoa_sdk/recurrence/cli_project.py": "downstream projection CLI",
        "src/aoa_sdk/recurrence/contracts/projections.py": "projection guard",
        "src/aoa_sdk/recurrence/contracts/review.py": "owner decision",
        "src/aoa_sdk/recurrence/live/techniques.py": "technique intake",
        "src/aoa_sdk/recurrence/live/skills.py": "skill trigger",
        "src/aoa_sdk/recurrence/live/events.py": "event repetition",
    }
    for path, role_fragment in recurrence_module_roles.items():
        assert role_fragment in modules[path]["role"]


def test_source_topology_index_names_shared_contract_branches() -> None:
    payload = source_topology.build_payload()
    packages = {package["path"]: package for package in _walk_packages(payload["tree"])}
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    assert "typed contract route-role branches" in packages["src/aoa_sdk/contracts"]["role"]
    assert "contract branch that owns the SDK family" in packages[
        "src/aoa_sdk/contracts"
    ]["next_route"]
    assert modules["src/aoa_sdk/models.py"]["split_pressure"] == "low"
    assert "compatibility re-export" in modules["src/aoa_sdk/models.py"]["role"]
    assert "aoa_sdk/contracts branches" in modules["src/aoa_sdk/models.py"]["next_route"]
    contract_module_roles = {
        "src/aoa_sdk/contracts/routing.py": "surface compatibility",
        "src/aoa_sdk/contracts/skills.py": "skill card",
        "src/aoa_sdk/contracts/playbooks.py": "playbook registry",
        "src/aoa_sdk/contracts/memo.py": "memo surface",
        "src/aoa_sdk/contracts/evals.py": "eval card",
        "src/aoa_sdk/contracts/checkpoints.py": "checkpoint lineage",
        "src/aoa_sdk/contracts/surfaces.py": "surface opportunity",
        "src/aoa_sdk/contracts/closeout.py": "reviewed closeout runner",
        "src/aoa_sdk/contracts/stats.py": "stats summary",
        "src/aoa_sdk/contracts/project_core.py": "project-core kernel",
    }
    for path, role_fragment in contract_module_roles.items():
        assert role_fragment in modules[path]["role"]


def test_source_topology_index_records_low_pressure_stop_lines() -> None:
    payload = source_topology.build_payload()
    modules = {module["path"]: module for module in _walk_modules(payload["tree"])}

    stop_lines = {
        "src/aoa_sdk/release/api.py": "release-support route owner",
        "src/aoa_sdk/skills/detector.py": "new skill-detection owner route",
        "src/aoa_sdk/compatibility/policy.py": "new compatibility owner route",
        "src/aoa_sdk/recurrence/hooks.py": "hook owner routes diverge",
    }
    assert modules["src/aoa_sdk/checkpoints/ledger/notes.py"]["split_pressure"] == "medium"
    assert "new ledger owner route" in modules[
        "src/aoa_sdk/checkpoints/ledger/notes.py"
    ]["next_route"]
    for path, route_fragment in stop_lines.items():
        assert modules[path]["split_pressure"] == "low"
        assert route_fragment in modules[path]["next_route"]


def test_source_topology_index_keeps_large_modules_as_split_pressure() -> None:
    payload = source_topology.build_payload()
    largest_paths = {entry["path"]: entry for entry in payload["largest_modules"]}

    assert "src/aoa_sdk/cli/main.py" not in largest_paths
    assert "src/aoa_sdk/models.py" not in largest_paths
    assert largest_paths["src/aoa_sdk/checkpoints/registry.py"]["split_pressure"] == "medium"
    assert "named checkpoint branch" in largest_paths["src/aoa_sdk/checkpoints/registry.py"]["next_route"]
