#!/usr/bin/env python3
"""Validate nested AGENTS.md guidance for aoa-sdk.

This validator-first spine protects local AGENTS.md surfaces that already exist.
It also reports high-risk directories that are likely to need future local
guidance, without making those future files blocking before they land.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_NAME = 'aoa-sdk'

REQUIRED_AGENTS_DOCS: dict[str, tuple[str, ...]] = {
    '.aoa/AGENTS.md': (
        'workspace topology metadata',
        '.aoa/workspace.toml',
        'no hidden path guessing',
        '/srv/AbyssOS/abyss-stack is a deployed runtime mirror',
    ),
    'src/aoa_sdk/AGENTS.md': (
        'typed control-plane facades',
        'Stay on the control plane',
        'truth labels',
        'python -m pytest -q',
    ),
    '.github/AGENTS.md': (
        "GitHub platform surface",
        "Repo Validation",
        "Do not add secrets",
        "weaker than source-owned repository docs",
    ),
    'docs/AGENTS.md': (
        'Root docs are public route',
        'part-local docs lane',
        'historical note',
        'python -m pytest -q tests/test_docs_routes.py tests/test_design_surfaces.py',
    ),
    'scripts/AGENTS.md': (
        'repo-wide builders, validators, release gates',
        'single-mechanic scripts',
        'mechanics/<parent>/parts/<part>/scripts/',
        'python scripts/release_check.py',
    ),
    'tests/AGENTS.md': (
        'Root tests prove repo-wide routes',
        'single-mechanic regressions',
        'mechanics/<parent>/parts/<part>/tests/',
        'python -m pytest -q tests',
    ),
    'evals/AGENTS.md': (
        'SDK-layer eval pressure',
        '`aoa-evals` owns central verdict',
        'python ../aoa-evals/scripts/validate_local_eval_port.py --target-root .',
    ),
    'kag/AGENTS.md': (
        'local KAG provider home',
        'shared KAG schema',
        '`aoa-kag` local subtree validator',
    ),
    'stats/AGENTS.md': (
        'SDK-local statistical questions',
        'Shared statistical grammar',
        'python scripts/validate_local_stats_port.py',
    ),
    'mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md': (
        'post-commit',
        'active-session-only',
        'must not create a new session',
        'never run closeout, promotion, harvest, push, or release',
    ),
    'generated/AGENTS.md': (
        'generated control-plane summaries',
        'Generated artifacts are lower authority than their sources',
        'workspace_control_plane.min.json',
        'source_topology.min.json',
        'python scripts/build_workspace_control_plane.py --check',
        'python scripts/build_source_topology_index.py --check',
    ),
    'schemas/AGENTS.md': (
        'root-published SDK helper contract schemas',
        'schema changes are contract changes',
        '$schema',
        'owner-subordinate',
    ),
    'docs/decisions/AGENTS.md': (
        'durable rationale',
        'AOA-SDK-D-####',
        'Index Metadata',
        'python scripts/generate_decision_indexes.py --check',
    ),
    'quests/AGENTS.md': (
        'SDK source quest record district',
        'Stay on the control plane',
        'quests/<lane>/<state>/<quest-file>',
        'python scripts/validate_mechanics_topology.py',
    ),
    'sdk/AGENTS.md': (
        'source-authored SDK home',
        'Do not add `PARTS.md` to `sdk/`',
        'sdk/source_home.manifest.json',
        'python scripts/validate_sdk_source_home.py',
    ),
    'sdk/public-interface/AGENTS.md': (
        'public SDK contract posture',
        'src/aoa_sdk/',
        'Do not document a supported entrypoint',
        'python scripts/validate_sdk_source_home.py',
    ),
    'sdk/facade-boundary/AGENTS.md': (
        'SDK facades read sibling-owned surfaces',
        'truth labels',
        'Route source-meaning changes to the sibling owner',
        'python scripts/validate_sdk_source_home.py',
    ),
    'sdk/runtime-entry/AGENTS.md': (
        'Workspace, Codex, and reviewed closeout entry posture',
        'below runtime authority',
        'Do not make path guessing stronger than `.aoa/workspace.toml`',
        'python scripts/validate_sdk_source_home.py',
    ),
    'sdk/distribution/AGENTS.md': (
        'package, release, and public support posture',
        'Do not treat dry-run output as a GitHub Release',
        'python scripts/release_check.py',
        'python scripts/validate_sdk_source_home.py',
    ),
    'mechanics/AGENTS.md': (
        'SDK operation topology layer',
        'Stay on the control plane',
        'mechanics/topology.json',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/agon/AGENTS.md': (
        'Agon mechanic',
        'Stay on the control plane',
        'candidate-only',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/agon/parts/AGENTS.md': (
        'functioning Agon SDK operation parts',
        'Stay on the control plane',
        'old root paths',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/antifragility/AGENTS.md': (
        'Antifragility mechanic',
        'Stay on the control plane',
        'stress fixtures proof verdicts',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/antifragility/parts/AGENTS.md': (
        'Functioning Antifragility parts',
        'Stay on the control plane',
        'old root paths',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/boundary-bridge/AGENTS.md': (
        'boundary-bridge mechanic',
        'Stay on the control plane',
        'Do not make a facade a source owner',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/boundary-bridge/parts/AGENTS.md': (
        'Boundary Bridge Parts Route',
        'owner-layer-signal-handoff',
        'source-owned truth',
        'reviewed handoff packets only',
    ),
    'mechanics/boundary-bridge/legacy/AGENTS.md': (
        'Boundary Bridge mechanics parent names',
        'Stay on the control plane',
        'Do not treat former parent names as active route ids',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/checkpoint/AGENTS.md': (
        'checkpoint mechanic',
        'Stay on the control plane',
        'session-local',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/checkpoint/parts/AGENTS.md': (
        'Checkpoint Parts Route',
        'child-task-reentry',
        'owner verdict authority',
        'Do not strengthen a checkpoint packet',
    ),
    'mechanics/checkpoint/legacy/AGENTS.md': (
        'Checkpoint mechanics parent names',
        'Stay on the control plane',
        'Do not treat former parent names as active route ids',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/codex-projection/AGENTS.md': (
        'Codex Projection mechanic',
        'Stay on the control plane',
        'not make SDK Codex reads a Codex runtime',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/codex-projection/parts/AGENTS.md': (
        'functioning Codex Projection parts',
        'Stay on the control plane',
        'external rollout artifact names as compatibility inputs',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/codex-projection/legacy/AGENTS.md': (
        'Codex Projection mechanics parent names',
        'Stay on the control plane',
        'Do not treat former parent names as active route ids',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/experience/AGENTS.md': (
        'Experience mechanic',
        'Stay on the control plane',
        'API helper calls as contracts',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/experience/parts/AGENTS.md': (
        'functioning Experience SDK helper-contract parts',
        'Stay on the control plane',
        'active routes',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/questbook/AGENTS.md': (
        'Questbook is the SDK operation package',
        'Stay on the control plane',
        'Source quest records live in root `quests/`',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/questbook/parts/AGENTS.md': (
        'Questbook parts keep root quest source records',
        'Stay on the control plane',
        'future dispatch readers',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/recurrence/AGENTS.md': (
        'recurrence mechanic',
        'Stay on the control plane',
        'Keep component truth with owner surfaces',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/recurrence/parts/AGENTS.md': (
        'mechanics/recurrence/parts/',
        'Route recurrence payload by active owner part',
        'Keep `src/aoa_sdk/recurrence/` as the importable SDK source package',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/release-support/AGENTS.md': (
        'release-support mechanic',
        'Stay on the control plane',
        'GitHub Release or package publication',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/release-support/parts/AGENTS.md': (
        'Release Support Parts Route',
        'release-audit-publish-helper',
        'public-support-ci-posture',
        'do not invent release state',
    ),
    'mechanics/rpg/AGENTS.md': (
        'RPG mechanic',
        'Stay on the control plane',
        'gameplay, frontend, or RPG runtime authority',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/rpg/parts/AGENTS.md': (
        'Functioning RPG parts',
        'Stay on the control plane',
        'old root paths',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/runtime-seam/AGENTS.md': (
        'Runtime Seam mechanic',
        'Stay on the control plane',
        'Do not make path guessing stronger than `.aoa/workspace.toml`',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/runtime-seam/parts/AGENTS.md': (
        'Runtime Seam Parts Route',
        'workspace path resolution',
        'portable workspace bootstrap',
        'Do not hide path guessing',
    ),
    'mechanics/runtime-seam/legacy/AGENTS.md': (
        'Runtime Seam mechanics parent names',
        'Stay on the control plane',
        'Do not treat former parent names as active route ids',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/titan/AGENTS.md': (
        'Titan mechanic',
        'Stay on the control plane',
        'runtime, role, identity, or memory authority',
        'python scripts/validate_mechanics_topology.py',
    ),
    'mechanics/titan/parts/AGENTS.md': (
        'Route active Titan SDK helper parts',
        'Stay on the control plane',
        'Do not add root active Titan docs',
        'python scripts/validate_mechanics_topology.py',
    ),
}
ADVISORY_AGENT_DIRS: tuple[str, ...] = ('config', 'examples', 'manifests/recurrence')
HEADING_PREFIXES = ("# AGENTS.md", "# AGENTS")
IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[str, ...]
    warnings: tuple[str, ...]


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _has_agents_heading(text: str) -> bool:
    stripped = text.lstrip()
    return any(stripped.startswith(prefix) for prefix in HEADING_PREFIXES)


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_ignored(path: Path, repo_root: Path) -> bool:
    try:
        parts = path.relative_to(repo_root).parts
    except ValueError:
        return False
    return any(part in IGNORED_DIRS for part in parts)


def discover_nested_agents(repo_root: Path) -> set[str]:
    found: set[str] = set()
    for path in repo_root.rglob("AGENTS.md"):
        if _is_ignored(path, repo_root):
            continue
        rel = _relative(path, repo_root)
        if rel != "AGENTS.md":
            found.add(rel)
    return found


def validate(
    repo_root: Path = REPO_ROOT,
    *,
    strict_advisory: bool = False,
    fail_on_untracked: bool = False,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    issues: list[str] = []
    warnings: list[str] = []

    root_agents = repo_root / "AGENTS.md"
    if not root_agents.is_file():
        issues.append("AGENTS.md: root guidance file is missing")
    else:
        root_text = root_agents.read_text(encoding="utf-8")
        if not _has_agents_heading(root_text):
            issues.append("AGENTS.md: missing AGENTS heading")

    for rel_path, snippets in REQUIRED_AGENTS_DOCS.items():
        path = repo_root / rel_path
        if not path.is_file():
            issues.append(f"{rel_path}: required nested AGENTS.md is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if not _has_agents_heading(text):
            issues.append(f"{rel_path}: missing AGENTS heading")
        normalized = _normalize(text)
        for snippet in snippets:
            if _normalize(snippet) not in normalized:
                issues.append(f"{rel_path}: missing required snippet {snippet!r}")

    required = set(REQUIRED_AGENTS_DOCS)
    actual = discover_nested_agents(repo_root)
    untracked = sorted(actual - required)
    if untracked:
        message = "untracked nested AGENTS.md not yet in validator map: " + ", ".join(untracked)
        warnings.append(message)
        if fail_on_untracked:
            issues.append(message)

    for rel_dir in ADVISORY_AGENT_DIRS:
        dir_path = repo_root / rel_dir
        agent_path = f"{rel_dir.rstrip('/')}/AGENTS.md"
        if not dir_path.is_dir():
            continue
        if agent_path in required or agent_path in actual:
            continue
        warnings.append(f"{rel_dir}: high-risk directory has no local AGENTS.md yet")

    if strict_advisory:
        issues.extend(warnings)

    return ValidationResult(tuple(issues), tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--strict-advisory", action="store_true")
    parser.add_argument("--fail-on-untracked", action="store_true")
    args = parser.parse_args(argv)

    result = validate(
        args.repo_root,
        strict_advisory=args.strict_advisory,
        fail_on_untracked=args.fail_on_untracked,
    )
    if result.issues:
        print(f"Nested AGENTS validation failed for {REPOSITORY_NAME}.")
        for issue in result.issues:
            print(f"- {issue}")
        return 1
    print(
        f"Nested AGENTS validation passed for {REPOSITORY_NAME}: "
        f"{len(REQUIRED_AGENTS_DOCS)} required nested document(s)."
    )
    for warning in result.warnings:
        print(f"[advisory] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
