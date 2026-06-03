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
    "docs/decisions/AOA-SDK-D-0055-checkpoint-skipped-session-recovery-branch.md",
    "docs/decisions/AOA-SDK-D-0056-cli-command-family-route-modules.md",
    "docs/decisions/AOA-SDK-D-0057-closeout-api-route-role-branches.md",
    "docs/decisions/AOA-SDK-D-0058-recurrence-route-role-branches.md",
    "docs/decisions/AOA-SDK-D-0059-shared-model-contract-branches.md",
    "docs/decisions/AOA-SDK-D-0060-low-pressure-route-stop-lines.md",
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
    "cli": "Typer CLI app assembly, command-family modules, shared CLI rendering, and CLI plumbing",
    "closeout": "reviewed closeout runner facade and route-role branches",
    "codex": "Codex workspace and rollout-facing helpers",
    "compatibility": "consumed-surface compatibility checks",
    "contracts": "shared SDK typed contract route-role branches",
    "evals": "eval-surface readers and bounded helper posture",
    "governed_runs": "governed run metadata and helper surface",
    "kag": "KAG bridge reader helpers",
    "loaders": "shared JSON and file loading utilities",
    "memo": "memo-surface readers and bounded memory helper posture",
    "playbooks": "playbook-surface readers",
    "recurrence": "recurrence planning, observation, CLI, typed contracts, projection, and reentry control-plane helpers",
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
    "src/aoa_sdk/checkpoints/review": "checkpoint after-commit, agent-review, and skipped-session recovery branch",
    "src/aoa_sdk/checkpoints/runtime": "checkpoint runtime-session lookup branch",
    "src/aoa_sdk/checkpoints/topology": "checkpoint topology branch for path naming and static routing helpers",
    "src/aoa_sdk/cli": "CLI app assembly and command-family route modules",
    "src/aoa_sdk/closeout": "reviewed closeout runner facade and route-role branches for manifest, queue, publisher, followthrough, receipt, and filesystem behavior",
    "src/aoa_sdk/contracts": "shared SDK typed contract route-role branches with models.py compatibility re-export",
    "src/aoa_sdk/recurrence/contracts": "recurrence typed contract route-role branches",
    "src/aoa_sdk/recurrence/live": "recurrence live observation producer route-role branches",
    "src/aoa_sdk/surfaces": "surface detection owner-layer signal handoff route-role branches",
}

MODULE_ROLE_OVERRIDES = {
    "src/aoa_sdk/__init__.py": "public import package marker",
    "src/aoa_sdk/api.py": "AoASDK aggregate API constructor and facet attachment point",
    "src/aoa_sdk/models.py": "shared typed SDK model compatibility re-export surface",
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
    "src/aoa_sdk/checkpoints/review/skipped_recovery.py": "checkpoint skipped-session recovery, reachability, and blocking required-action owner",
    "src/aoa_sdk/checkpoints/runtime/sessions.py": "checkpoint runtime-session lookup and probe owner",
    "src/aoa_sdk/checkpoints/timestamps.py": "checkpoint timestamp normalization helper owner",
    "src/aoa_sdk/checkpoints/topology/paths.py": "checkpoint filesystem path topology owner",
    "src/aoa_sdk/cli/checkpoint.py": "CLI checkpoint capture, review, hook, boundary, promotion, and checkpoint-closeout command family owner",
    "src/aoa_sdk/cli/closeout.py": "CLI reviewed closeout run, manifest, queue, inbox, and status command family owner",
    "src/aoa_sdk/cli/common.py": "CLI shared path resolution, persistence, host-skill, and checkpoint hook argument owner",
    "src/aoa_sdk/cli/compatibility.py": "CLI consumed-surface compatibility check command family owner",
    "src/aoa_sdk/cli/main.py": "CLI root Typer app assembly and legacy test re-export surface",
    "src/aoa_sdk/cli/release.py": "CLI release audit and publish command family owner",
    "src/aoa_sdk/cli/rendering.py": "CLI human-readable report rendering owner",
    "src/aoa_sdk/cli/skills.py": "CLI skill detect, dispatch, enter, and guard command family owner",
    "src/aoa_sdk/cli/surfaces.py": "CLI surface detect and reviewed handoff command family owner",
    "src/aoa_sdk/cli/workspace.py": "CLI workspace inspect and bootstrap command family owner",
    "src/aoa_sdk/closeout/api.py": "CloseoutAPI public facade and route-role method binding surface",
    "src/aoa_sdk/closeout/filesystem.py": "closeout queue path, safe filename, archival, and uniqueness helper owner",
    "src/aoa_sdk/closeout/followthrough.py": "closeout kernel next-step, owner follow-through, workflow follow-through, and owner handoff owner",
    "src/aoa_sdk/closeout/manifests.py": "closeout build-request loading, submit-reviewed request writing, validation, and manifest assembly owner",
    "src/aoa_sdk/closeout/publishers.py": "closeout publisher specs, receipt-kind routing, subprocess execution, stats refresh, and stdout parsing owner",
    "src/aoa_sdk/closeout/queue.py": "closeout enqueue, inbox processing, queue status, and manifest archival orchestration owner",
    "src/aoa_sdk/closeout/receipts.py": "closeout receipt collection, receipt-file loading, publisher detection, and evidence-ref resolution owner",
    "src/aoa_sdk/closeout/runner.py": "closeout reviewed manifest run and report emission owner",
    "src/aoa_sdk/contracts/agents.py": "shared agent phase binding and artifact envelope contract owner",
    "src/aoa_sdk/contracts/checkpoints.py": "shared checkpoint lineage, note, capture, review, hook, boundary, and checkpoint-closeout bridge contract owner",
    "src/aoa_sdk/contracts/closeout.py": "shared reviewed closeout runner, publisher, stats refresh, owner follow-through, inbox, and status contract owner",
    "src/aoa_sdk/contracts/codex.py": "shared Codex projection live rollout status contract owner",
    "src/aoa_sdk/contracts/evals.py": "shared eval card, capsule, section, comparison, and runtime candidate intake contract owner",
    "src/aoa_sdk/contracts/governed_runs.py": "shared governed run review packet, audit, and handoff contract owner",
    "src/aoa_sdk/contracts/kag.py": "shared KAG registry, federation, tiny bundle, regrounding, inspect, and query-mode contract owner",
    "src/aoa_sdk/contracts/memo.py": "shared memo surface, capsule, section, object, and writeback contract owner",
    "src/aoa_sdk/contracts/playbooks.py": "shared playbook registry, activation, composition, review, and landing-governance contract owner",
    "src/aoa_sdk/contracts/project_core.py": "shared project-core kernel, outer ring, risk ring, and foundation profile contract owner",
    "src/aoa_sdk/contracts/routing.py": "shared routing hint, registry entry, stats regrounding hint, and surface compatibility contract owner",
    "src/aoa_sdk/contracts/skills.py": "shared skill card, disclosure, activation, session, dispatch, and detection contract owner",
    "src/aoa_sdk/contracts/stats.py": "shared stats summary, source coverage, route progression, automation pipeline, and regrounding signal contract owner",
    "src/aoa_sdk/contracts/surfaces.py": "shared surface opportunity, surface detection, and surface closeout handoff contract owner",
    "src/aoa_sdk/contracts/techniques.py": "shared technique promotion readiness contract owner",
    "src/aoa_sdk/contracts/workspace.py": "shared workspace bootstrap report contract owner",
    "src/aoa_sdk/recurrence/cli.py": "recurrence CLI exported app assembly facade",
    "src/aoa_sdk/recurrence/cli_core.py": "recurrence root command family owner",
    "src/aoa_sdk/recurrence/cli_graph.py": "recurrence graph CLI command family owner",
    "src/aoa_sdk/recurrence/cli_hooks.py": "recurrence hooks CLI command family owner",
    "src/aoa_sdk/recurrence/cli_live.py": "recurrence live producers CLI command family owner",
    "src/aoa_sdk/recurrence/cli_project.py": "recurrence downstream projection CLI command family owner",
    "src/aoa_sdk/recurrence/cli_review.py": "recurrence owner review CLI command family owner",
    "src/aoa_sdk/recurrence/contracts/base.py": "recurrence base literal aliases and strict model owner",
    "src/aoa_sdk/recurrence/contracts/beacons.py": "recurrence beacon, candidate ledger, and usage-gap contract owner",
    "src/aoa_sdk/recurrence/contracts/manifest.py": "recurrence manifest, component, edge, freshness, input, and beacon-rule contract owner",
    "src/aoa_sdk/recurrence/contracts/observations.py": "recurrence observation and hook-run contract owner",
    "src/aoa_sdk/recurrence/contracts/propagation.py": "recurrence change signal, propagation plan, return handoff, and connectivity-gap contract owner",
    "src/aoa_sdk/recurrence/contracts/projections.py": "recurrence downstream routing, stats, KAG, projection guard, and bundle contract owner",
    "src/aoa_sdk/recurrence/contracts/review.py": "recurrence review queue, dossier, owner decision, ledger, suppression, and close-report contract owner",
    "src/aoa_sdk/recurrence/contracts/rollout.py": "recurrence wiring plan and rollout window contract owner",
    "src/aoa_sdk/recurrence/live/common.py": "recurrence live observation shared helper owner",
    "src/aoa_sdk/recurrence/live/events.py": "recurrence event repetition live observation producer owner",
    "src/aoa_sdk/recurrence/live/generated.py": "recurrence generated staleness live observation producer owner",
    "src/aoa_sdk/recurrence/live/playbooks.py": "recurrence playbook harvest live observation producer owner",
    "src/aoa_sdk/recurrence/live/runtime.py": "recurrence runtime evidence selection live observation producer owner",
    "src/aoa_sdk/recurrence/live/skills.py": "recurrence skill trigger and usage-gap live observation producer owner",
    "src/aoa_sdk/recurrence/live/techniques.py": "recurrence technique intake and readiness live observation producer owner",
    "src/aoa_sdk/recurrence/live_observations.py": "recurrence live observation producer registry facade",
    "src/aoa_sdk/recurrence/models.py": "recurrence typed contract compatibility re-export surface",
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
    if rel == "src/aoa_sdk/cli/main.py":
        return "keep root app assembly here; add command behavior in the owning CLI command-family module"
    if rel == "src/aoa_sdk/cli/common.py":
        return "keep shared CLI plumbing here; route command behavior to a command-family module and domain behavior to SDK owners"
    if rel == "src/aoa_sdk/cli/rendering.py":
        return "keep human-readable output formatting here; route command behavior to a command-family module"
    if rel == "src/aoa_sdk/closeout/api.py":
        return "keep CloseoutAPI facade bindings here; add behavior in the owning closeout route branch"
    if rel == "src/aoa_sdk/recurrence/cli.py":
        return "keep exported recur_app assembly here; add command behavior in the owning recurrence cli_* module"
    if rel == "src/aoa_sdk/recurrence/live_observations.py":
        return "keep live producer registry facade here; add producer behavior in recurrence/live branches"
    if rel == "src/aoa_sdk/recurrence/models.py":
        return "keep compatibility re-exports here; add typed contracts in recurrence/contracts branches"
    if rel == "src/aoa_sdk/models.py":
        return "keep compatibility re-exports here; add shared typed contracts in aoa_sdk/contracts branches"
    if rel == "src/aoa_sdk/checkpoints/ledger/notes.py":
        return "keep checkpoint ledger assembly here; split only when a new ledger owner route is named"
    if rel == "src/aoa_sdk/release/api.py":
        return "keep bounded release audit/publish helpers here; split only when a release-support route owner diverges"
    if rel == "src/aoa_sdk/skills/detector.py":
        return "keep skill detection and checkpoint bridge detection here; split only when a new skill-detection owner route appears"
    if rel == "src/aoa_sdk/compatibility/policy.py":
        return "keep consumed-surface compatibility policy here; split only when a new compatibility owner route appears"
    if rel == "src/aoa_sdk/recurrence/hooks.py":
        return "keep recurrence hook binding and run behavior here; split only when hook owner routes diverge"
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
    if rel == "src/aoa_sdk/cli":
        return "route CLI behavior to command-family modules; keep main.py as root app assembly only"
    if rel == "src/aoa_sdk/closeout":
        return "route closeout behavior to manifest, queue, runner, publisher, followthrough, receipt, or filesystem branches"
    if rel == "src/aoa_sdk/contracts":
        return "route shared typed contracts to the contract branch that owns the SDK family"
    if rel == "src/aoa_sdk/recurrence/contracts":
        return "route typed recurrence contracts to the contract branch that owns the packet family"
    if rel == "src/aoa_sdk/recurrence/live":
        return "route live observation behavior to the producer branch that owns the source family"
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
