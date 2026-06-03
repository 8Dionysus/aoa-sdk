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

    assert modules["src/aoa_sdk/checkpoints/registry.py"]["split_pressure"] == "medium"
    assert "route-role orchestrator" in modules["src/aoa_sdk/checkpoints/registry.py"]["role"]
    assert "named checkpoint branch" in modules["src/aoa_sdk/checkpoints/registry.py"]["next_route"]
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
    assert modules["src/aoa_sdk/checkpoints/ledger/notes.py"]["split_pressure"] == "low"
    assert "runtime note loading" in modules["src/aoa_sdk/checkpoints/ledger/notes.py"]["role"]


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


def test_source_topology_index_keeps_large_modules_as_split_pressure() -> None:
    payload = source_topology.build_payload()
    largest_paths = {entry["path"]: entry for entry in payload["largest_modules"]}

    assert largest_paths["src/aoa_sdk/cli/main.py"]["split_pressure"] == "high"
    assert largest_paths["src/aoa_sdk/models.py"]["split_pressure"] == "high"
    assert largest_paths["src/aoa_sdk/checkpoints/registry.py"]["split_pressure"] == "medium"
    assert "named checkpoint branch" in largest_paths["src/aoa_sdk/checkpoints/registry.py"]["next_route"]
