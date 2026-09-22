from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CARRY_PART = "mechanics/checkpoint/parts/reviewed-closeout-context-carry"
PRIMARY_COMMAND_DOCS = frozenset(
    {"mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md"}
)
EXECUTABLE_MARKDOWN_PREFIXES = (".agents/skills/", "skills/")
SHELL_FENCE_PATTERN = re.compile(
    r"^ {0,3}```(?:bash|console|sh|shell|zsh)(?:\s+.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
REPO_COMMAND_LINE_PATTERN = re.compile(
    r"^[ \t]*(?:[-*][ \t]+)?`?(?:"
    r"python3?(?:[ \t]+-m)?[ \t]+|pytest(?=[ \t])|"
    r"uv[ \t]+run[ \t]+pytest\b|git[ \t]+(?:status|diff)\b|"
    r"aoa[ \t]+release\b)",
    re.MULTILINE,
)
INLINE_REPO_COMMAND_PATTERN = re.compile(
    r"(?<!`)`(?!``)(?:python3?(?:\s+-m)?\s+|pytest(?=\s)|"
    r"uv\s+run\s+pytest\b|git\s+(?:status|diff)\b|"
    r"aoa\s+release\b)[^`\n]+`(?!`)"
)
FENCE_OPEN_PATTERN = re.compile(r"^ {0,3}```")
COMMAND_BLOCK_LINE_PATTERN = re.compile(
    r"^[ \t]*(?:\$[ \t]+)?(?:python3?|pytest|uv|pip3?|aoa|git|ruff|mypy|"
    r"make|tox|hatch|poetry)(?:[ \t]+(?![=:])\S+)"
)


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def tracked_markdown_paths() -> tuple[Path, ...]:
    completed = subprocess.run(
        ("git", "ls-files", "--", "*.md"),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        path
        for line in completed.stdout.splitlines()
        if line and (path := Path(line)) and (REPO_ROOT / path).is_file()
    )


def markdown_command_violations(content: str) -> set[str]:
    violations: set[str] = set()
    if SHELL_FENCE_PATTERN.search(content):
        violations.add("shell command block")
    elif fenced_command_block_present(content):
        violations.add("command block")
    if REPO_COMMAND_LINE_PATTERN.search(content):
        violations.add("repo command line")
    if INLINE_REPO_COMMAND_PATTERN.search(content):
        violations.add("inline repo command")
    return violations


def fenced_command_block_present(content: str) -> bool:
    in_fence = False
    for line in content.splitlines():
        if not in_fence and FENCE_OPEN_PATTERN.match(line):
            in_fence = True
            continue
        if in_fence and line.strip() == "```":
            in_fence = False
            continue
        if in_fence and COMMAND_BLOCK_LINE_PATTERN.match(line):
            return True
    return False


def changelog_unreleased_section(changelog: str) -> str:
    start = changelog.index("## [Unreleased]")
    next_release = changelog.index("\n## [", start + len("## [Unreleased]"))
    return changelog[start:next_release]


def assert_doc_links(document: str, *targets: str, content: str | None = None) -> None:
    """Check parsed Markdown links, excluding images, comments, and code examples."""
    text = read_text(document) if content is None else content
    links: set[Path] = set()
    for token in MarkdownIt().parse(text):
        for child in token.children or ():
            if child.type != "link_open":
                continue
            target = urlsplit(child.attrGet("href") or "")
            if target.scheme or target.netloc or not target.path:
                continue
            links.add((REPO_ROOT / document).parent.joinpath(unquote(target.path)).resolve())
    for target in targets:
        expected = (REPO_ROOT / target).resolve()
        assert expected in links, f"{document}: missing link to {target}"
        assert expected.exists(), f"{document}: broken link to {target}"


def assert_source_refs(document: str, *targets: str) -> None:
    """Source lists may use code spans; check exact path tokens and real targets."""
    text = read_text(document)
    for target in targets:
        assert re.search(rf"(?<![\w./-]){re.escape(target)}(?![\w/-]|\.[\w./-])", text), (
            f"{document}: missing source ref {target}"
        )
        assert (REPO_ROOT / target).exists(), f"{document}: missing source target {target}"


def test_readme_is_public_front_door_not_command_authority() -> None:
    assert_doc_links(
        "README.md", "VALIDATION.md", "docs/README.md", "DESIGN.md",
        "DESIGN.AGENTS.md", "docs/decisions/README.md", "ROADMAP.md",
        "docs/blueprint.md", "sdk/source_home.manifest.json",
    )
    assert markdown_command_violations(read_text("README.md")) == set()


def test_route_check_allows_editorial_change_but_rejects_wrong_destinations() -> None:
    assert_doc_links(
        "README.md", "VALIDATION.md",
        content="Choose [checks appropriate to your change](./VALIDATION.md#focused-repository-checks).",
    )
    for content in (
        "VALIDATION.md is mentioned but not linked.",
        "[VALIDATION.md](elsewhere.md)",
        "[Checks](VALIDATION.md.bak)",
        "[Checks](https://example.invalid/VALIDATION.md)",
        "![Checks](VALIDATION.md)",
        "```text\n[Checks](VALIDATION.md)\n```",
        "`[Checks](VALIDATION.md)`",
        "<!-- [Checks](VALIDATION.md) -->",
    ):
        with pytest.raises(AssertionError, match="missing link"):
            assert_doc_links("README.md", "VALIDATION.md", content=content)
    assert_doc_links(
        "README.md", "VALIDATION.md",
        content="[Check here][checks]\n\n[checks]: ./VALIDATION.md#focused-repository-checks\n",
    )
    with pytest.raises(AssertionError, match="broken link"):
        assert_doc_links(
            "README.md", "missing-owner-procedure.md",
            content="[Checks](missing-owner-procedure.md)",
        )


def test_non_owner_markdown_routes_runnable_commands_to_command_owners() -> None:
    offenders: list[str] = []
    for relative_path in tracked_markdown_paths():
        route = relative_path.as_posix()
        if route.startswith(EXECUTABLE_MARKDOWN_PREFIXES):
            continue
        if relative_path.name in {"AGENTS.md", "VALIDATION.md"}:
            continue
        if route in PRIMARY_COMMAND_DOCS:
            continue
        content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for violation in sorted(markdown_command_violations(content)):
            offenders.append(f"{route}: {violation}")

    assert offenders == []


def test_markdown_command_guard_rejects_scattered_command_forms() -> None:
    content = """# Drift

```bash
python scripts/validate_sdk_source_home.py
```

- `python -m pytest -q`
- git status -sb
"""

    assert markdown_command_violations(content) == {
        "inline repo command",
        "repo command line",
        "shell command block",
    }

    assert markdown_command_violations("```text\naoa recur agents spawn\n```\n") == {
        "command block"
    }
    assert markdown_command_violations("```python\nfrom aoa_sdk import AoASDK\n```\n") == set()


def test_readme_license_routes_to_declared_project_license() -> None:
    metadata = tomllib.loads(read_text("pyproject.toml"))
    assert metadata["project"]["license"]["text"] == "Apache-2.0"
    assert read_text("LICENSE").startswith("Apache License\nVersion 2.0")
    assert_doc_links("README.md", "LICENSE")


def test_docs_map_routes_to_current_owners_without_retired_flat_docs() -> None:
    assert_doc_links("README.md", "docs/README.md")
    assert_doc_links(
        "docs/README.md", "docs/boundaries.md", "docs/AGENTS.md",
        "docs/decisions/README.md", "DESIGN.md", "ROADMAP.md", "docs/blueprint.md",
    )
    assert_source_refs("docs/AGENTS.md", "docs/README.md")
    assert not (REPO_ROOT / "docs/AGENTS_ROOT_REFERENCE.md").exists()
    assert not (REPO_ROOT / "docs/ecosystem-impact.md").exists()


def test_decision_readme_routes_lookup_through_generated_indexes() -> None:
    assert_doc_links(
        "docs/decisions/README.md",
        *(f"docs/decisions/indexes/{name}.md" for name in (
            "by-number", "by-date", "by-surface", "by-sdk-facet", "by-mechanic", "by-guard"
        )),
    )


def test_validation_entrypoint_retains_executable_owner_checks() -> None:
    validation = read_text("VALIDATION.md")
    assert_doc_links("AGENTS.md", "VALIDATION.md")
    for command in (
        "python scripts/generate_decision_indexes.py --check",
        "python scripts/validate_sdk_source_home.py",
        "python scripts/validate_mechanics_topology.py",
        "python scripts/build_source_topology_index.py --check",
        "python scripts/validate_source_topology_index.py",
        "python scripts/build_workspace_control_plane.py --check",
        "python scripts/validate_workspace_control_plane.py",
        "aoa compatibility check /srv/AbyssOS/aoa-sdk",
        "aoa compatibility check /srv/AbyssOS/aoa-sdk --repo aoa-skills --json",
    ):
        assert command in validation


def test_root_guidance_retains_design_and_decision_routes() -> None:
    assert_source_refs(
        "AGENTS.md", "DESIGN.md", "DESIGN.AGENTS.md", "docs/decisions/README.md",
        "mechanics/", "sdk/source_home.manifest.json",
    )
    assert_source_refs(
        "ROADMAP.md", "DESIGN.md", "DESIGN.AGENTS.md", "docs/decisions/indexes/",
    )


def test_changelog_unreleased_avoids_live_reconciliation_counters() -> None:
    # A bounded editorial lint, not proof of a release's historical facts.
    unreleased = changelog_unreleased_section(read_text("CHANGELOG.md"))
    for fragment in (
        "first-parent commits", "changed tracked paths", "merged PRs #",
        "through #", "PR #", "Repo Validation for PR",
    ):
        assert fragment not in unreleased


def test_readme_routes_sibling_canary_surfaces() -> None:
    assert_doc_links(
        "README.md", "generated/workspace_control_plane.min.json",
        "docs/RELEASE_CI_POSTURE.md", "mechanics/release-support/README.md",
    )
    assert_source_refs(
        "mechanics/release-support/README.md",
        "mechanics/release-support/parts/public-support-ci-posture/",
        ".github/workflows/latest-sibling-canary.yml",
    )
    assert_source_refs(
        "docs/RELEASE_CI_POSTURE.md",
        "mechanics/release-support/parts/public-support-ci-posture/docs/public-support-ci-posture.md",
    )
    part = "mechanics/release-support/parts/public-support-ci-posture"
    assert_doc_links(
        f"{part}/README.md", f"{part}/config/sibling_canary_matrix.json",
        f"{part}/scripts/run_sibling_canary.py",
    )


def test_readme_routes_surface_detection_to_owner_surfaces() -> None:
    assert_doc_links("README.md", "mechanics/boundary-bridge/README.md", "mechanics/checkpoint/README.md")
    assert_source_refs(
        "mechanics/boundary-bridge/README.md",
        "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/",
    )
    assert_source_refs(
        "mechanics/experience/README.md",
        "mechanics/experience/parts/capture-pipeline-helper/",
    )


def test_validation_entrypoint_retains_inspection_and_checkpoint_commands() -> None:
    validation = read_text("VALIDATION.md")
    for command in (
        "aoa skills inspect /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json",
        "aoa skills capability workflow.operations.checkpoint-closeout",
        "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress",
        "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint",
        "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note",
        "aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json",
        "aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD --auto",
        "aoa checkpoint materialize-closeout-handoff",
        "aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json",
        "aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json",
    ):
        assert command in validation


def test_readme_routes_to_reviewed_closeout_context_carry() -> None:
    assert_doc_links("README.md", "mechanics/checkpoint/README.md")
    assert_source_refs("mechanics/checkpoint/README.md", f"{CARRY_PART}/")
    assert_doc_links(
        f"{CARRY_PART}/README.md",
        *(f"{CARRY_PART}/docs/{name}.md" for name in (
            "owner-followthrough-map", "component-refresh-followthrough",
            "self-agency-continuity-carry", "next-kernel-followthrough-decision",
        )),
    )
    for name in ("owner-followthrough-map", "next-kernel-followthrough-decision"):
        assert_source_refs(
            f"{CARRY_PART}/docs/{name}.md",
            f"{CARRY_PART}/docs/component-refresh-followthrough.md",
        )


def test_codex_projection_owner_routes_remain_reachable() -> None:
    assert_doc_links("README.md", "mechanics/codex-projection/README.md")
    parent = "mechanics/codex-projection/parts"
    assert_source_refs(
        "mechanics/codex-projection/README.md",
        f"{parent}/portability-boundary/docs/portability-boundary.md",
        f"{parent}/live-rollout-status-readout/docs/live-rollout-status-readout.md",
        f"{parent}/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md",
        f"{parent}/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md",
        f"{parent}/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json",
        f"{parent}/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json",
        "src/aoa_sdk/codex/",
    )
