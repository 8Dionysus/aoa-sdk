#!/usr/bin/env python3
"""Shared builder helpers for the aoa-sdk implementation source topology index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src" / "aoa_sdk"
SOURCE_TOPOLOGY_PATH = REPO_ROOT / "generated" / "source_topology.min.json"

SCHEMA_VERSION = "aoa_sdk_source_topology_v1"
ARTIFACT_TYPE = "implementation_source_topology_index"
AUTHORITY_REF = "src/aoa_sdk/AGENTS.md"
SOURCE_INPUT_REFS = (
    "src/aoa_sdk/AGENTS.md",
    "sdk/source_home.manifest.json",
    "docs/decisions/AOA-SDK-D-0043-sdk-source-home-tree.md",
    "docs/decisions/AOA-SDK-D-0050-checkpoint-path-topology-tree.md",
    "docs/decisions/AOA-SDK-D-0051-implementation-source-topology-index.md",
    "docs/decisions/AOA-SDK-D-0052-checkpoint-route-role-implementation-branches.md",
    "docs/decisions/AOA-SDK-D-0053-checkpoint-closeout-pipeline-branches.md",
    "docs/decisions/AOA-SDK-D-0054-surface-registry-route-role-branches.md",
)
VALIDATION_REFS = (
    "scripts/build_source_topology_index.py",
    "scripts/validate_source_topology_index.py",
    "tests/test_source_topology_index.py",
)
IGNORED_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}

TOP_LEVEL_ROLES = {
    "a2a": "child-task handoff and rebase control-plane helpers",
    "agents": "agent projection and role-surface readers",
    "checkpoints": "checkpoint capture, review, closeout, and handoff control-plane behavior",
    "cli": "Typer CLI command surface",
    "closeout": "reviewed closeout helper API",
    "codex": "Codex workspace and rollout-facing helpers",
    "compatibility": "consumed-surface compatibility checks",
    "evals": "eval-surface readers and bounded helper posture",
    "governed_runs": "governed run metadata and helper surface",
    "kag": "KAG bridge reader helpers",
    "loaders": "shared JSON and file loading utilities",
    "memo": "memo-surface readers and bounded memory helper posture",
    "playbooks": "playbook-surface readers",
    "recurrence": "recurrence planning, observation, and reentry control-plane helpers",
    "release": "release audit and publish helper surface",
    "routing": "routing-surface readers and picker helpers",
    "rpg": "RPG typed consumer API helpers",
    "skills": "skill discovery and runtime-session helpers",
    "stats": "stats-surface readers",
    "surfaces": "owner-layer signal detection and reviewed surface handoff helpers",
    "techniques": "technique-surface readers",
    "titans": "Titan-facing helper surface",
    "workspace": "workspace discovery and root resolution helpers",
}

PACKAGE_ROLE_OVERRIDES = {
    "src/aoa_sdk": "importable Python implementation root and AoASDK aggregate entrypoint",
    "src/aoa_sdk/a2a/rebase": "A2A rebase route helpers",
    "src/aoa_sdk/checkpoints/closeout": "checkpoint reviewed closeout pipeline branches for context, evidence, execution, followthrough, and owner-handoff",
    "src/aoa_sdk/checkpoints/hooks": "checkpoint managed Git hook and dirty-boundary branch",
    "src/aoa_sdk/checkpoints/ledger": "checkpoint note ledger assembly and runtime note loading branch",
    "src/aoa_sdk/checkpoints/promotion": "checkpoint reviewed promotion target writer branch",
    "src/aoa_sdk/checkpoints/render": "checkpoint note presentation render branch",
    "src/aoa_sdk/checkpoints/review": "checkpoint after-commit and agent-review branch",
    "src/aoa_sdk/checkpoints/runtime": "checkpoint runtime-session lookup branch",
    "src/aoa_sdk/checkpoints/topology": "checkpoint topology branch for path naming and static routing helpers",
    "src/aoa_sdk/surfaces": "surface detection owner-layer signal handoff route-role branches",
}

MODULE_ROLE_OVERRIDES = {
    "src/aoa_sdk/__init__.py": "public import package marker",
    "src/aoa_sdk/api.py": "AoASDK aggregate API constructor and facet attachment point",
    "src/aoa_sdk/models.py": "shared typed SDK model contracts",
    "src/aoa_sdk/checkpoints/closeout/bridge.py": "checkpoint closeout compatibility facade over pipeline branches",
    "src/aoa_sdk/checkpoints/closeout/common.py": "checkpoint closeout shared small helper owner",
    "src/aoa_sdk/checkpoints/closeout/context.py": "checkpoint closeout context scope, handoff, receipt, and candidate-map owner",
    "src/aoa_sdk/checkpoints/closeout/contracts.py": "checkpoint closeout mechanical artifact contract owner",
    "src/aoa_sdk/checkpoints/closeout/evidence.py": "checkpoint closeout reviewed artifact and Codex trace evidence reader owner",
    "src/aoa_sdk/checkpoints/closeout/execution.py": "checkpoint closeout mechanical packet and receipt builder owner",
    "src/aoa_sdk/checkpoints/closeout/followthrough.py": "checkpoint closeout followthrough decision and next-skill posture owner",
    "src/aoa_sdk/checkpoints/closeout/owner_handoff.py": "checkpoint closeout owner follow-through handoff owner",
    "src/aoa_sdk/checkpoints/hooks/git_boundary.py": "checkpoint Git hook template, git metadata, and dirty-boundary helper owner",
    "src/aoa_sdk/checkpoints/kinds.py": "checkpoint kind inference helper owner",
    "src/aoa_sdk/checkpoints/ledger/notes.py": "checkpoint note ledger assembly, rotation, and runtime note loading owner",
    "src/aoa_sdk/checkpoints/naming.py": "checkpoint slug naming helper owner",
    "src/aoa_sdk/checkpoints/promotion/targets.py": "checkpoint reviewed promotion target writer owner",
    "src/aoa_sdk/checkpoints/registry.py": "checkpoint public API facade and route-role orchestrator",
    "src/aoa_sdk/checkpoints/render/markdown.py": "checkpoint note markdown render owner",
    "src/aoa_sdk/checkpoints/review/after_commit.py": "checkpoint after-commit report and auto-observation owner",
    "src/aoa_sdk/checkpoints/review/agent_review.py": "checkpoint agent-review autofill and review-carry owner",
    "src/aoa_sdk/checkpoints/runtime/sessions.py": "checkpoint runtime-session lookup and probe owner",
    "src/aoa_sdk/checkpoints/timestamps.py": "checkpoint timestamp normalization helper owner",
    "src/aoa_sdk/checkpoints/topology/paths.py": "checkpoint filesystem path topology owner",
    "src/aoa_sdk/cli/main.py": "CLI command assembly surface",
    "src/aoa_sdk/surfaces/checkpoint_candidates.py": "surface checkpoint candidate cluster, lineage, promotion, and note-ref owner",
    "src/aoa_sdk/surfaces/closeout_handoff.py": "surface reviewed closeout handoff assembly owner",
    "src/aoa_sdk/surfaces/common.py": "surface shared type aliases and small pure helper owner",
    "src/aoa_sdk/surfaces/context.py": "surface session, shortlist, stats, and receipt context owner",
    "src/aoa_sdk/surfaces/heuristics.py": "surface deterministic heuristic rule owner",
    "src/aoa_sdk/surfaces/items.py": "surface opportunity item derivation and merge owner",
    "src/aoa_sdk/surfaces/progression.py": "surface progression-axis signal owner",
    "src/aoa_sdk/surfaces/registry.py": "surface public API facade and owner-layer signal orchestrator",
}


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _module_route_key(path: Path) -> str:
    rel = path.relative_to(SOURCE_ROOT).as_posix()
    if rel == "__init__.py":
        return "root-package"
    return rel.removesuffix(".py").replace("/", ".")


def _package_route_key(path: Path) -> str:
    if path == SOURCE_ROOT:
        return "root-package"
    return path.relative_to(SOURCE_ROOT).as_posix().replace("/", ".")


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _split_pressure(line_count: int) -> str:
    if line_count >= 2000:
        return "high"
    if line_count >= 1000:
        return "medium"
    return "low"


def _module_kind(path: Path) -> str:
    if path.name == "__init__.py":
        return "init_module"
    if path.name == "api.py":
        return "api_module"
    if path.name == "models.py":
        return "model_module"
    if path.name == "main.py" and path.parent.name == "cli":
        return "cli_module"
    if "topology" in path.parts:
        return "topology_module"
    if path.name == "registry.py":
        return "registry_module"
    return "implementation_module"


def _package_kind(path: Path) -> str:
    if path == SOURCE_ROOT:
        return "root_package"
    if path.name == "topology":
        return "topology_package"
    return "package"


def _module_role(path: Path) -> str:
    rel = _rel(path)
    if rel in MODULE_ROLE_OVERRIDES:
        return MODULE_ROLE_OVERRIDES[rel]
    if path.name == "__init__.py":
        return "package initializer and import boundary marker"
    stem = path.stem.replace("_", " ")
    return f"{stem} implementation module"


def _package_role(path: Path) -> str:
    rel = _rel(path)
    if rel in PACKAGE_ROLE_OVERRIDES:
        return PACKAGE_ROLE_OVERRIDES[rel]
    route_key = _package_route_key(path)
    top_level = route_key.split(".", 1)[0]
    top_role = TOP_LEVEL_ROLES.get(top_level)
    if top_role and route_key == top_level:
        return top_role
    if top_role:
        return f"{route_key} branch under {top_role}"
    return f"{route_key} implementation package"


def _package_dirs(path: Path) -> list[Path]:
    return sorted(
        child
        for child in path.iterdir()
        if child.is_dir()
        and child.name not in IGNORED_DIRS
        and any(grandchild.suffix == ".py" for grandchild in child.rglob("*.py"))
    )


def _package_modules(path: Path) -> list[Path]:
    return sorted(child for child in path.iterdir() if child.is_file() and child.suffix == ".py")


def _module_payload(path: Path) -> dict[str, Any]:
    rel = _rel(path)
    line_count = _count_lines(path)
    return {
        "path": rel,
        "route_key": _module_route_key(path),
        "node_kind": _module_kind(path),
        "role": _module_role(path),
        "line_count": line_count,
        "split_pressure": _split_pressure(line_count),
        "evidence_refs": [rel],
        "next_route": _module_next_route(path, line_count),
    }


def _module_next_route(path: Path, line_count: int) -> str:
    rel = _rel(path)
    if rel == "src/aoa_sdk/checkpoints/registry.py":
        return "keep public CheckpointsAPI orchestration here; add behavior in the named checkpoint branch that owns it"
    if rel == "src/aoa_sdk/checkpoints/closeout/bridge.py":
        return "keep this facade thin; add behavior in the owning closeout context, evidence, execution, followthrough, or owner-handoff branch"
    if rel == "src/aoa_sdk/surfaces/registry.py":
        return "keep public SurfacesAPI orchestration here; add behavior in the named surface branch that owns it"
    if rel == "src/aoa_sdk/checkpoints/topology/paths.py":
        return "keep static checkpoint path naming here; route behavior back to checkpoint registry or a route-role branch"
    if line_count >= 1000:
        return "consider the next route-role split before adding more behavior"
    return "inspect owning package, tests, and mechanic route before changing behavior"


def _package_payload(path: Path) -> dict[str, Any]:
    rel = _rel(path)
    module_payloads = [_module_payload(module) for module in _package_modules(path)]
    child_payloads = [_package_payload(child) for child in _package_dirs(path)]
    line_count = sum(module["line_count"] for module in module_payloads) + sum(
        child["line_count"] for child in child_payloads
    )
    module_count = len(module_payloads) + sum(child["module_count"] for child in child_payloads)
    return {
        "path": rel,
        "route_key": _package_route_key(path),
        "node_kind": _package_kind(path),
        "role": _package_role(path),
        "line_count": line_count,
        "module_count": module_count,
        "split_pressure": _split_pressure(line_count),
        "evidence_refs": [rel],
        "modules": module_payloads,
        "packages": child_payloads,
        "next_route": _package_next_route(path, line_count, module_count),
    }


def _package_next_route(path: Path, line_count: int, module_count: int) -> str:
    rel = _rel(path)
    if rel == "src/aoa_sdk/surfaces":
        return "route behavior to the named surface branch that owns it; add a new branch only when a new owner role appears"
    if path.name == "topology":
        return "keep topology branches static and behavior-free unless a new route role is named"
    if line_count >= 2000 or module_count >= 10:
        return "use this index to choose a route-role split before adding broad behavior"
    return "open package modules, tests, and owning mechanic route before editing"


def _walk_modules(package: dict[str, Any]) -> list[dict[str, Any]]:
    modules = list(package["modules"])
    for child in package["packages"]:
        modules.extend(_walk_modules(child))
    return modules


def build_payload() -> dict[str, Any]:
    if not SOURCE_ROOT.is_dir():
        raise ValueError("src/aoa_sdk is missing")
    root_package = _package_payload(SOURCE_ROOT)
    modules = _walk_modules(root_package)
    largest_modules = sorted(modules, key=lambda module: module["line_count"], reverse=True)[:12]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "owner_repo": "aoa-sdk",
        "source_root": "src/aoa_sdk",
        "authority_ref": AUTHORITY_REF,
        "generated_by": "scripts/build_source_topology_index.py",
        "source_inputs": list(SOURCE_INPUT_REFS),
        "validation_refs": list(VALIDATION_REFS),
        "boundary_note": "Generated read-model only; source files, AGENTS.md, decisions, mechanics, and tests remain stronger.",
        "package_count": _count_packages(root_package),
        "module_count": len(modules),
        "line_count": root_package["line_count"],
        "largest_modules": [
            {
                "path": module["path"],
                "route_key": module["route_key"],
                "line_count": module["line_count"],
                "split_pressure": module["split_pressure"],
                "next_route": module["next_route"],
            }
            for module in largest_modules
        ],
        "tree": root_package,
    }
    _validate_refs(payload)
    return payload


def _count_packages(package: dict[str, Any]) -> int:
    return 1 + sum(_count_packages(child) for child in package["packages"])


def _validate_refs(payload: dict[str, Any]) -> None:
    refs = [payload["authority_ref"], *payload["source_inputs"], *payload["validation_refs"]]
    for ref in refs:
        if not (REPO_ROOT / ref).exists():
            raise ValueError(f"missing source topology ref: {ref}")


def render_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
