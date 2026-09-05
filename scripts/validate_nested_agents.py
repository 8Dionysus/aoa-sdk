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
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_NAME = 'aoa-sdk'

REPEATED_VALIDATION_PARAGRAPH = (
    'Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, '
    'or requested operation requires executable checks. For repository-wide, release-facing, '
    'generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains '
    '`scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, '
    'and serial completeness oracle remain authoritative.'
)
GENERIC_NESTED_ROUTE_PREFIX = (
    'Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, '
    'DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by '
    'the touched path, semantic question, or requested operation. This is a conditional route, '
    'not an unconditional reading inventory. '
)


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
    ),
    'scripts/AGENTS.md': (
        'repo-wide builders, validators, release gates',
        'single-mechanic scripts',
        'mechanics/<parent>/parts/<part>/scripts/',
    ),
    'tests/AGENTS.md': (
        'Root tests prove repo-wide routes',
        'single-mechanic regressions',
        'mechanics/<parent>/parts/<part>/tests/',
    ),
    'evals/AGENTS.md': (
        'SDK-layer eval pressure',
        '`aoa-evals` owns central verdict',
    ),
    'kag/AGENTS.md': (
        'local KAG provider home',
        'shared KAG schema',
        '`aoa-kag` local subtree validator',
    ),
    'stats/AGENTS.md': (
        'SDK-local statistical questions',
        'Shared statistical grammar',
    ),
    'skills/AGENTS.md': (
        'canonical `aoa-sdk/skills/` owner home',
        'Global exposure comes from the single OS user profile',
        'Do not add a duplicate',
        'Manual isolated',
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
    ),
    'quests/AGENTS.md': (
        'SDK source quest record district',
        'Stay on the control plane',
        'quests/<lane>/<state>/<quest-file>',
    ),
    'sdk/AGENTS.md': (
        'source-authored SDK home',
        'Do not add `PARTS.md` to `sdk/`',
        'sdk/source_home.manifest.json',
    ),
    'sdk/public-interface/AGENTS.md': (
        'public SDK contract posture',
        'src/aoa_sdk/',
        'Do not document a supported entrypoint',
    ),
    'sdk/facade-boundary/AGENTS.md': (
        'SDK facades read sibling-owned surfaces',
        'truth labels',
        'Route source-meaning changes to the sibling owner',
    ),
    'sdk/runtime-entry/AGENTS.md': (
        'Workspace, Codex, explicit Runner, and reviewed',
        'below runtime authority',
        'Do not make path guessing stronger than `.aoa/workspace.toml`',
    ),
    'sdk/distribution/AGENTS.md': (
        'package, release, and public support posture',
        'Do not treat dry-run output as a GitHub Release',
    ),
    'mechanics/AGENTS.md': (
        'SDK operation topology layer',
        'Stay on the control plane',
        'mechanics/topology.json',
    ),
    'mechanics/agon/AGENTS.md': (
        'Agon mechanic',
        'Stay on the control plane',
        'candidate-only',
    ),
    'mechanics/agon/parts/AGENTS.md': (
        'functioning Agon SDK operation parts',
        'Stay on the control plane',
        'old root paths',
    ),
    'mechanics/antifragility/AGENTS.md': (
        'Antifragility mechanic',
        'Stay on the control plane',
        'stress fixtures proof verdicts',
    ),
    'mechanics/antifragility/parts/AGENTS.md': (
        'Functioning Antifragility parts',
        'Stay on the control plane',
        'old root paths',
    ),
    'mechanics/boundary-bridge/AGENTS.md': (
        'boundary-bridge mechanic',
        'Stay on the control plane',
        'Do not make a facade a source owner',
    ),
    'mechanics/boundary-bridge/parts/AGENTS.md': (
        'Boundary Bridge Parts Route',
        'owner-layer-signal-handoff',
        'source-owned truth',
        'reviewed handoff packets only',
    ),
    'mechanics/checkpoint/AGENTS.md': (
        'checkpoint mechanic',
        'Stay on the control plane',
        'session-local',
    ),
    'mechanics/checkpoint/parts/AGENTS.md': (
        'Checkpoint Parts Route',
        'child-task-reentry',
        'owner verdict authority',
        'Do not strengthen a checkpoint packet',
    ),
    'mechanics/codex-projection/AGENTS.md': (
        'Codex Projection mechanic',
        'Stay on the control plane',
        'not make SDK Codex reads a Codex runtime',
    ),
    'mechanics/codex-projection/parts/AGENTS.md': (
        'functioning Codex Projection parts',
        'Stay on the control plane',
        'external rollout artifact names as compatibility inputs',
    ),
    'mechanics/experience/AGENTS.md': (
        'Experience mechanic',
        'Stay on the control plane',
        'API helper calls as contracts',
    ),
    'mechanics/experience/parts/AGENTS.md': (
        'functioning Experience SDK helper-contract parts',
        'Stay on the control plane',
        'active routes',
    ),
    'mechanics/questbook/AGENTS.md': (
        'Questbook is the SDK operation package',
        'Stay on the control plane',
        'Source quest records live in root `quests/`',
    ),
    'mechanics/questbook/parts/AGENTS.md': (
        'Questbook parts keep root quest source records',
        'Stay on the control plane',
        'future dispatch readers',
    ),
    'mechanics/recurrence/AGENTS.md': (
        'recurrence mechanic',
        'Stay on the control plane',
        'Keep component truth with owner surfaces',
    ),
    'mechanics/recurrence/parts/AGENTS.md': (
        'mechanics/recurrence/parts/',
        'Route recurrence payload by active owner part',
        'Keep `src/aoa_sdk/recurrence/` as the importable SDK source package',
    ),
    'mechanics/release-support/AGENTS.md': (
        'release-support mechanic',
        'Stay on the control plane',
        'GitHub Release or package publication',
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
    ),
    'mechanics/rpg/parts/AGENTS.md': (
        'Functioning RPG parts',
        'Stay on the control plane',
        'old root paths',
    ),
    'mechanics/runtime-seam/AGENTS.md': (
        'Runtime Seam mechanic',
        'Stay on the control plane',
        'Do not make path guessing stronger than `.aoa/workspace.toml`',
    ),
    'mechanics/runtime-seam/parts/AGENTS.md': (
        'Runtime Seam Parts Route',
        'workspace path resolution',
        'portable workspace bootstrap',
        'Do not hide path guessing',
    ),
    'mechanics/titan/AGENTS.md': (
        'Titan mechanic',
        'Stay on the control plane',
        'runtime, role, identity, or memory authority',
    ),
    'mechanics/titan/parts/AGENTS.md': (
        'Route active Titan SDK helper parts',
        'Stay on the control plane',
        'Do not add root active Titan docs',
    ),
}
ADVISORY_AGENT_DIRS: tuple[str, ...] = ('config', 'examples', 'manifests/recurrence')
HEADING_PREFIXES = ("# AGENTS.md", "# AGENTS")
IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
FENCE_MARKER = chr(96) * 3
RUNNABLE_FENCE_LANGS = {"bash", "sh", "shell", "console", "zsh", "shell-session"}
COMMAND_NAMES = (
    r"python3?|pytest|uv|pip3?|aoa|git|ruff|mypy|make|tox|hatch|poetry|"
    r"bash|sh|shellcheck|systemctl|systemd-analyze|curl|jq|rg|grep|sed|"
    r"awk|find|chmod|mkdir|cp|mv|rm"
)
COMMAND_LINE_PATTERN = re.compile(
    r"^[ \t]*(?:(?:[-*+]|[0-9]+[.)])[ \t]+)?(?:\$[ \t]+)?"
    r"(?:[A-Z_][A-Z0-9_]*=\S+[ \t]+)*"
    + "(?:" + COMMAND_NAMES + ")"
    r"(?=\s|$)",
    re.IGNORECASE | re.MULTILINE,
)
INLINE_COMMAND_PATTERN = re.compile(
    FENCE_MARKER[:1]
    + r"(?:(?:[A-Z_][A-Z0-9_]*=\S+[ \t]+)*\$?[ \t]*)"
    + "(?:" + COMMAND_NAMES + ")"
    r"(?=\s|$)[^"
    + FENCE_MARKER[:1]
    + r"\n]*"
    + FENCE_MARKER[:1],
    re.IGNORECASE,
)
FENCE_PATTERN = re.compile(
    re.escape(FENCE_MARKER) + r"([^\n]*)\n(.*?)\n" + re.escape(FENCE_MARKER),
    re.MULTILINE | re.DOTALL,
)
LEGACY_ROUTE_HEADINGS = re.compile(
    r"^(?:start here|read before editing|reading order(?: shape)?|route stack|"
    r"route inventory|required reading)$",
    re.IGNORECASE,
)
README_ROUTE_PATTERN = re.compile(
    r"\b(?:read|open|review|start\s+with|use)\b.*\bREADME(?:\.md)?\b",
    re.IGNORECASE,
)
README_CONDITIONAL_MARKERS = (
    "when ",
    "if ",
    "only ",
    "where ",
    "as needed",
    "needed",
    "relevant",
    "selected",
    "known",
    "target",
    "named",
    "for ",
)


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


def _unconditional_readme_violations(relative_path: str, text: str) -> tuple[str, ...]:
    """Reject mandatory README inventories while allowing task-conditional routes."""

    issues: list[str] = []
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not README_ROUTE_PATTERN.search(line):
            continue
        lowered = line.casefold()
        if not any(marker in lowered for marker in README_CONDITIONAL_MARKERS):
            issues.append(f"{relative_path}:{line_number}: unconditional README inventory")

    for index, line in enumerate(lines):
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not heading or not LEGACY_ROUTE_HEADINGS.match(heading.group(1).strip()):
            continue
        end = index + 1
        while end < len(lines) and not lines[end].lstrip().startswith("#"):
            end += 1
        section = lines[index + 1 : end]
        if any("readme" in item.casefold() for item in section) and not any(
            any(marker in item.casefold() for marker in README_CONDITIONAL_MARKERS)
            for item in section
        ):
            issues.append(f"{relative_path}:{index + 1}: unconditional README inventory section")
    return tuple(issues)


def _inherited_route_violations(relative_path: str, text: str) -> tuple[str, ...]:
    if relative_path == 'AGENTS.md':
        return ()
    issues: list[str] = []
    if REPEATED_VALIDATION_PARAGRAPH in text:
        issues.append(
            f"{relative_path}: repeated repository validation route; inherit it from the root card"
        )
    if GENERIC_NESTED_ROUTE_PREFIX in text:
        issues.append(
            f"{relative_path}: repeated root conditional route; retain only local route delta"
        )
    return tuple(issues)


def _procedure_violations(relative_path: str, text: str) -> tuple[str, ...]:
    """Keep inherited cards semantic and route procedures on demand."""

    issues: list[str] = []
    for match in FENCE_PATTERN.finditer(text):
        language = match.group(1).strip().lower()
        body = match.group(2)
        if language in RUNNABLE_FENCE_LANGS or COMMAND_LINE_PATTERN.search(body):
            label = language or "command"
            issues.append(f"{relative_path}: runnable procedure fence ({label})")

    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(FENCE_MARKER):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if COMMAND_LINE_PATTERN.match(line):
            issues.append(f"{relative_path}:{line_number}: runnable command line")
        if INLINE_COMMAND_PATTERN.search(line):
            issues.append(f"{relative_path}:{line_number}: inline runnable command")

    issues.extend(_unconditional_readme_violations(relative_path, text))
    return tuple(issues)


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
        if "## Validation route" not in root_text:
            issues.append("AGENTS.md: root validation route is missing")
        if "](VALIDATION.md)" not in root_text:
            issues.append("AGENTS.md: root validation route must link to VALIDATION.md")
        for required_root_route in ("scripts/release_check.py", "accepted graph runner"):
            if required_root_route not in root_text:
                issues.append(f"AGENTS.md: root validation route missing {required_root_route!r}")
        issues.extend(_procedure_violations("AGENTS.md", root_text))

    validation_entrypoint = repo_root / "VALIDATION.md"
    if not validation_entrypoint.is_file():
        issues.append("VALIDATION.md: root human validation entrypoint is missing")

    design_agents = repo_root / "DESIGN.AGENTS.md"
    if not design_agents.is_file():
        issues.append("DESIGN.AGENTS.md: design surface is missing")
    else:
        design_text = design_agents.read_text(encoding="utf-8")
        for required_heading in ("## Conditional route shape", "## Relevant routes"):
            if required_heading not in design_text:
                issues.append(f"DESIGN.AGENTS.md: missing required route heading {required_heading!r}")
        if "Executable procedures live in root" not in design_text:
            issues.append("DESIGN.AGENTS.md: validation procedures do not route through VALIDATION.md")

    for rel_path, snippets in REQUIRED_AGENTS_DOCS.items():
        path = repo_root / rel_path
        if not path.is_file():
            issues.append(f"{rel_path}: required nested AGENTS.md is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if not _has_agents_heading(text):
            issues.append(f"{rel_path}: missing AGENTS heading")
        issues.extend(_procedure_violations(rel_path, text))
        issues.extend(_inherited_route_violations(rel_path, text))
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
