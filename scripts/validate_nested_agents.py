#!/usr/bin/env python3
"""Validate AGENTS.md coverage, route presence, and command placement.

This structural checker does not validate natural-language meaning, conditional
reading, or owner authority. Those remain source-aware review obligations.
High-risk directories without an existing card are advisory until admitted.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_NAME = 'aoa-sdk'

# This inventory protects local card coverage, not any particular wording.
# Meaning, reading conditions, and owner boundaries require source-aware review.
REQUIRED_AGENTS_DOCS: tuple[str, ...] = (
    ".aoa/AGENTS.md",
    "src/aoa_sdk/AGENTS.md",
    ".github/AGENTS.md",
    "docs/AGENTS.md",
    "scripts/AGENTS.md",
    "tests/AGENTS.md",
    "evals/AGENTS.md",
    "kag/AGENTS.md",
    "stats/AGENTS.md",
    "skills/AGENTS.md",
    "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md",
    "generated/AGENTS.md",
    "schemas/AGENTS.md",
    "docs/decisions/AGENTS.md",
    "quests/AGENTS.md",
    "sdk/AGENTS.md",
    "sdk/public-interface/AGENTS.md",
    "sdk/facade-boundary/AGENTS.md",
    "sdk/runtime-entry/AGENTS.md",
    "sdk/distribution/AGENTS.md",
    "mechanics/AGENTS.md",
    "mechanics/agon/AGENTS.md",
    "mechanics/agon/parts/AGENTS.md",
    "mechanics/antifragility/AGENTS.md",
    "mechanics/antifragility/parts/AGENTS.md",
    "mechanics/boundary-bridge/AGENTS.md",
    "mechanics/boundary-bridge/parts/AGENTS.md",
    "mechanics/checkpoint/AGENTS.md",
    "mechanics/checkpoint/parts/AGENTS.md",
    "mechanics/codex-projection/AGENTS.md",
    "mechanics/codex-projection/parts/AGENTS.md",
    "mechanics/experience/AGENTS.md",
    "mechanics/experience/parts/AGENTS.md",
    "mechanics/questbook/AGENTS.md",
    "mechanics/questbook/parts/AGENTS.md",
    "mechanics/recurrence/AGENTS.md",
    "mechanics/recurrence/parts/AGENTS.md",
    "mechanics/release-support/AGENTS.md",
    "mechanics/release-support/parts/AGENTS.md",
    "mechanics/rpg/AGENTS.md",
    "mechanics/rpg/parts/AGENTS.md",
    "mechanics/runtime-seam/AGENTS.md",
    "mechanics/runtime-seam/parts/AGENTS.md",
    "mechanics/titan/AGENTS.md",
    "mechanics/titan/parts/AGENTS.md",
)
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


def _has_validation_link(text: str) -> bool:
    # Parse Markdown so examples and images cannot substitute for navigation.
    for token in MarkdownIt().parse(text):
        for child in token.children or ():
            if child.type != "link_open":
                continue
            target = urlsplit(child.attrGet("href") or "")
            if not target.scheme and not target.netloc and unquote(target.path) in {
                "VALIDATION.md", "./VALIDATION.md",
            }:
                return True
    return False


def _has_source_ref(text: str, target: str) -> bool:
    return re.search(rf"(?<![\w./-]){re.escape(target)}(?![\w/-]|\.[\w./-])", text) is not None


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[str, ...]
    warnings: tuple[str, ...]


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


def _procedure_violations(relative_path: str, text: str) -> tuple[str, ...]:
    """Reject recognized runnable command forms in inherited route cards."""

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
        if not _has_validation_link(root_text):
            issues.append("AGENTS.md: root validation route must link to VALIDATION.md")
        if not _has_source_ref(root_text, "scripts/release_check.py"):
            issues.append("AGENTS.md: root validation route missing 'scripts/release_check.py'")
        issues.extend(_procedure_violations("AGENTS.md", root_text))

    if not (repo_root / "scripts/release_check.py").is_file():
        issues.append("scripts/release_check.py: root executable gate is missing")

    validation_entrypoint = repo_root / "VALIDATION.md"
    if not validation_entrypoint.is_file():
        issues.append("VALIDATION.md: root human validation entrypoint is missing")

    design_agents = repo_root / "DESIGN.AGENTS.md"
    if not design_agents.is_file():
        issues.append("DESIGN.AGENTS.md: design surface is missing")
    else:
        design_text = design_agents.read_text(encoding="utf-8")
        if not _has_source_ref(design_text, "VALIDATION.md"):
            issues.append("DESIGN.AGENTS.md: validation procedures do not route through VALIDATION.md")

    for rel_path in REQUIRED_AGENTS_DOCS:
        path = repo_root / rel_path
        if not path.is_file():
            issues.append(f"{rel_path}: required nested AGENTS.md is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if not _has_agents_heading(text):
            issues.append(f"{rel_path}: missing AGENTS heading")
        issues.extend(_procedure_violations(rel_path, text))

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
    print("Scope: card coverage, route presence, and recognized command placement; "
          "semantic guidance review is separate.")
    for warning in result.warnings:
        print(f"[advisory] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
