from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CARRY_PART = "mechanics/checkpoint/parts/reviewed-closeout-context-carry"
PRIMARY_COMMAND_DOCS = frozenset(
    {"mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md"}
)
EXECUTABLE_MARKDOWN_PREFIXES = (".agents/skills/",)
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


def changelog_release_section(changelog: str, version: str) -> str:
    heading = f"## [{version}]"
    start = changelog.index(heading)
    next_release = changelog.find("\n## [", start + len(heading))
    end = next_release if next_release != -1 else len(changelog)
    return changelog[start:end]


def test_readme_is_public_front_door_not_command_authority() -> None:
    readme = read_text("README.md")

    assert "This README is the public front door" in readme
    assert "The root README should not become that inventory." in readme
    assert "Use this README to choose the route, not to run the route." in readme
    assert "AGENTS.md#verify" in readme
    assert "part `VALIDATION.md`" in readme

    forbidden_command_text = [
        "```",
        "python scripts/",
        "python -m ",
        "aoa workspace ",
        "aoa compatibility ",
        "aoa skills ",
        "aoa surfaces ",
        "aoa checkpoint ",
        "git commit",
    ]
    for text in forbidden_command_text:
        assert text not in readme


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


def test_readme_license_matches_project_license() -> None:
    readme = read_text("README.md")
    license_text = read_text("LICENSE")
    pyproject = read_text("pyproject.toml")

    assert license_text.startswith("Apache License\nVersion 2.0")
    assert 'license = {text = "Apache-2.0"}' in pyproject
    assert "Licensed under the [Apache License 2.0](LICENSE)." in readme
    assert "[MIT]" not in readme


def test_docs_map_is_entrypoint_not_flat_archive() -> None:
    readme = read_text("README.md")
    agents = read_text("AGENTS.md")
    docs_agents = read_text("docs/AGENTS.md")
    docs_map = read_text("docs/README.md")
    decision = read_text("docs/decisions/AOA-SDK-D-0047-docs-map-and-stale-flat-docs-retirement.md")

    assert "Documentation map" in readme
    assert "docs/README.md" in readme
    assert "This is the entrypoint for the `docs/` surface of `aoa-sdk`." in docs_map
    assert "`docs/` is not a flat shelf" in docs_map
    assert "Current operational" in docs_map
    assert "docs entry map" in docs_agents
    assert "Retired root reference" in agents
    assert "former preserved root-guidance dump is retired from active docs" in agents
    assert "Retire `docs/AGENTS_ROOT_REFERENCE.md` and `docs/ecosystem-impact.md`" in decision

    assert not (REPO_ROOT / "docs" / "AGENTS_ROOT_REFERENCE.md").exists()
    assert not (REPO_ROOT / "docs" / "ecosystem-impact.md").exists()


def test_decision_readme_routes_lookup_through_generated_indexes() -> None:
    decisions = read_text("docs/decisions/README.md")

    assert "## Lookup Route" in decisions
    assert "Do not hand-maintain a \"latest decision\" roster" in decisions
    assert "indexes/by-number.md" in decisions
    assert "indexes/by-date.md" in decisions
    assert "indexes/by-surface.md" in decisions
    assert "indexes/by-sdk-facet.md" in decisions
    assert "indexes/by-mechanic.md" in decisions
    assert "indexes/by-guard.md" in decisions
    assert "## Active Mechanics Decision" not in decisions
    assert "The corrected parent mechanics topology is recorded in" not in decisions


def test_agents_lists_compatibility_checks_in_minimum_validation() -> None:
    agents = read_text("AGENTS.md")

    assert "python scripts/generate_decision_indexes.py --check" in agents
    assert "python scripts/validate_sdk_source_home.py" in agents
    assert "python scripts/validate_mechanics_topology.py" in agents
    assert "python scripts/build_source_topology_index.py --check" in agents
    assert "python scripts/validate_source_topology_index.py" in agents
    assert "python scripts/build_workspace_control_plane.py --check" in agents
    assert "python scripts/validate_workspace_control_plane.py" in agents
    assert "aoa compatibility check /srv/AbyssOS/aoa-sdk" in agents
    assert "aoa compatibility check /srv/AbyssOS/aoa-sdk --repo aoa-skills --json" in agents


def test_decision_lane_is_routed_before_mechanics() -> None:
    readme = read_text("README.md")
    agents = read_text("AGENTS.md")
    roadmap = read_text("ROADMAP.md")
    decision = read_text("docs/decisions/AOA-SDK-D-0001-decision-rationale-lane-before-mechanics.md")

    assert "docs/decisions/README.md" in readme
    assert "docs/decisions/README.md" in agents
    assert "docs/decisions/indexes/" in roadmap
    assert "Create `docs/decisions/` as the canonical rationale lane" in decision
    assert "before" in decision
    assert "introducing `mechanics/`" in decision


def test_design_lane_is_routed_before_mechanics() -> None:
    readme = read_text("README.md")
    agents = read_text("AGENTS.md")
    roadmap = read_text("ROADMAP.md")
    decision = read_text("docs/decisions/AOA-SDK-D-0002-root-design-surfaces-before-mechanics.md")

    assert "DESIGN.md" in readme
    assert "DESIGN.AGENTS.md" in readme
    assert "DESIGN.md" in agents
    assert "DESIGN.AGENTS.md" in agents
    assert "DESIGN.md" in roadmap
    assert "DESIGN.AGENTS.md" in roadmap
    assert "Create root `DESIGN.md` and `DESIGN.AGENTS.md` before introducing" in decision


def test_changelog_records_current_release_contour() -> None:
    changelog = read_text("CHANGELOG.md")
    release = changelog_release_section(changelog, "0.5.0")

    required_sections = [
        "### Summary",
        "### Reconciliation Basis",
        "### Added",
        "### Changed",
        "### Fixed",
        "### Validation",
        "### Notes",
        "### Included in this release",
    ]
    for section in required_sections:
        assert section in release
    assert "38 first-parent commits" in release
    assert "193 changed tracked paths" in release
    assert "34 of the 38 first-parent commits" in release
    assert "This dated section is the canonical `v0.5.0` reconciliation contour" in release
    assert "package version, CLI version, README banner, roadmap marker" in release
    included_commits = re.findall(r"^- `([0-9a-f]{7})` ", release, flags=re.MULTILINE)
    assert len(included_commits) == 38
    assert included_commits[0] == "1908d93"
    assert included_commits[-1] == "f17634f"


def test_changelog_unreleased_avoids_live_reconciliation_counters() -> None:
    changelog = read_text("CHANGELOG.md")
    unreleased = changelog_unreleased_section(changelog)

    forbidden_live_fragments = [
        "first-parent commits",
        "changed tracked paths",
        "merged PRs #",
        "through #",
        "PR #",
        "Repo Validation for PR",
    ]
    for fragment in forbidden_live_fragments:
        assert fragment not in unreleased

    assert "Add future changes here after the release tag lands" in unreleased
    assert "Dated release sections own exact reconciliation spans" in unreleased
    assert "complete commit\n  inventories" in unreleased


def test_readme_routes_sibling_canary_surfaces_without_roster() -> None:
    readme = read_text("README.md")
    release_support = read_text("mechanics/release-support/README.md")
    posture_route = read_text("docs/RELEASE_CI_POSTURE.md")
    support_part = read_text("mechanics/release-support/parts/public-support-ci-posture/README.md")

    assert "generated/workspace_control_plane.min.json" in readme
    assert "docs/RELEASE_CI_POSTURE.md" in readme
    assert "mechanics/release-support/README.md" in readme
    assert "mechanics/release-support/parts/public-support-ci-posture/" in release_support
    assert ".github/workflows/latest-sibling-canary.yml" in release_support
    assert (
        "mechanics/release-support/parts/public-support-ci-posture/docs/public-support-ci-posture.md"
        in posture_route
    )
    assert "config/sibling_canary_matrix.json" in support_part
    assert "scripts/run_sibling_canary.py" in support_part


def test_readme_routes_surface_detection_to_owner_surfaces() -> None:
    readme = read_text("README.md")
    boundary_bridge = read_text("mechanics/boundary-bridge/README.md")
    owner_handoff = read_text("mechanics/boundary-bridge/parts/owner-layer-signal-handoff/README.md")
    initial_boundary = read_text(
        "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/initial-surface-detection-boundary.md"
    )
    enrichment = read_text(
        "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-detection-enrichment.md"
    )
    experience = read_text("mechanics/experience/README.md")
    checkpoint = read_text(
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md"
    )

    assert "mechanics/boundary-bridge/README.md" in readme
    assert "mechanics/checkpoint/README.md" in readme
    assert "surface-detection" in readme
    assert "owner-layer-signal-handoff" in boundary_bridge
    assert "aoa surfaces detect" in owner_handoff
    assert "without\nselecting, loading, or executing a skill" in initial_boundary
    assert "`aoa-skills.agent_skill_catalog`; it is not a dispatch result" in initial_boundary
    assert "`surface-detection-heuristics.md`" in initial_boundary
    assert "`surface-closeout-handoff.md`" in initial_boundary
    assert "descriptive stats re-grounding signals from owner-published stats surfaces" in enrichment
    assert "all surface items remain non-executable" in enrichment
    assert "mechanics/experience/parts/capture-pipeline-helper/" in experience
    assert "preserves\nintermediate evidence" in checkpoint
    assert "agent_review=pending" in checkpoint
    assert "capability_execution_claimed=false" in checkpoint
    assert "`lifecycle-audit`, `backlog-audit`, `close-archive`" in checkpoint
    assert "does not\n  mutate session memory" in checkpoint


def test_agents_documents_passive_skill_inspection_and_checkpoint_truth_rules() -> None:
    agents = read_text("AGENTS.md")

    assert "## Inspection And Checkpoint Loop" in agents
    assert "aoa skills inspect /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json" in agents
    assert "aoa skills capability workflow.operations.checkpoint-closeout" in agents
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress" in agents
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint" in agents
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note" in agents
    assert "aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json" in agents
    assert "aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD --auto" in agents
    assert "aoa checkpoint materialize-closeout-handoff" in agents
    assert "aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in agents
    assert "aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in agents
    assert "`aoa skills ...` is passive inspection only" in agents
    assert "does not detect, rank,\ndispatch, activate, or create skill-session state" in agents
    assert "Presence never\n  becomes selection, activation, capability execution, or owner authority" in agents
    assert "skipped_no_active_session" in agents
    assert "agent_review=pending" in agents
    assert "capability_execution_claimed=false" in agents


def test_reviewed_handoffs_explicitly_keep_capability_execution_separate() -> None:
    checkpoint = read_text(
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md"
    )
    child_return = read_text(
        "mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md"
    )
    surface_handoff = read_text(
        "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-closeout-handoff.md"
    )

    assert "materialize-closeout-handoff" in checkpoint
    assert "Every output keeps `capability_execution_claimed=false`" in checkpoint
    assert "No checkpoint command invokes inferred sibling publishers" in checkpoint
    assert "without selecting a skill" in child_return
    assert "No step invokes an owner publisher, runs a skill" in child_return
    assert "`capability_execution_claimed=false`" in child_return
    assert "requires `reviewed=True`" in surface_handoff
    assert "they are not\n  SDK dispatch instructions" in surface_handoff
    assert "No target is auto-run, installed, admitted, or promoted" in surface_handoff


def test_session_growth_checkpoint_doc_explains_reviewed_evidence_lifecycle() -> None:
    checkpoints = read_text(
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md"
    )

    assert "session-local checkpoint control plane" in checkpoints
    assert "intermediate evidence, requires semantic review" in checkpoints
    assert "agent_review=pending" in checkpoints
    assert "review-note --auto" in checkpoints
    assert "build-closeout-context" in checkpoints
    assert "materialize-closeout-handoff" in checkpoints
    assert "Every output keeps `capability_execution_claimed=false`" in checkpoints
    assert "No checkpoint command invokes inferred sibling publishers" in checkpoints
    assert "chooses a next skill" in checkpoints
    assert "post-commit-report.json" in checkpoints
    assert "archived_without_closeout" in checkpoints
    assert "aoa-session-memory refs are read-only evidence coordinates" in checkpoints
    assert "Manual lifecycle trials are the behavioral authority" in checkpoints
    assert "Tests and validators must not replace the reviewed artifact" in checkpoints


def test_readme_routes_to_reviewed_closeout_context_carry() -> None:
    readme = read_text("README.md")
    checkpoint_route = read_text("mechanics/checkpoint/README.md")
    carry_readme = read_text(f"{CARRY_PART}/README.md")
    carry = read_text(f"{CARRY_PART}/docs/candidate-lineage-carry.md")
    component_carry = read_text(f"{CARRY_PART}/docs/component-refresh-followthrough.md")
    followthrough = read_text(f"{CARRY_PART}/docs/owner-followthrough-map.md")
    kernel_rules = read_text(f"{CARRY_PART}/docs/next-kernel-followthrough-decision.md")
    continuity = read_text(f"{CARRY_PART}/docs/self-agency-continuity-carry.md")

    assert "mechanics/checkpoint/README.md" in readme
    assert CARRY_PART in checkpoint_route
    assert "docs/owner-followthrough-map.md" in carry_readme
    assert "docs/component-refresh-followthrough.md" in carry_readme
    assert "docs/self-agency-continuity-carry.md" in carry_readme
    assert "docs/next-kernel-followthrough-decision.md" in carry_readme
    assert "owner repo, route class" in component_carry
    assert "weaker than owner refresh laws and owner" in component_carry
    assert "owner_followthrough_map" in carry
    assert "must not carry `candidate_ref`" in followthrough
    assert f"{CARRY_PART}/docs/component-refresh-followthrough.md" in followthrough
    assert "It does not execute that class" in kernel_rules
    assert f"{CARRY_PART}/docs/component-refresh-followthrough.md" in kernel_rules
    assert "It does not define self-agency meaning." in continuity
    assert "do not turn this carry into runtime self-modification authority" in continuity


def test_codex_projection_portability_boundary_stays_routeable() -> None:
    readme = read_text("README.md")
    codex_projection = read_text("mechanics/codex-projection/README.md")
    workspace_layout = read_text("docs/workspace-layout.md")
    portability_ref = (
        "mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md"
    )
    portability = read_text(portability_ref)

    assert "mechanics/codex-projection/README.md" in readme
    assert portability_ref in codex_projection
    assert "Workspace discovery overrides in `aoa-sdk` are not a substitute for" in workspace_layout
    assert "Codex Projection deployment regeneration" in workspace_layout
    assert "`aoa-sdk` owns:" in portability
    assert "It does not own:" in portability
    assert "8Dionysus/.codex/config.toml" in portability
    assert "8Dionysus/.codex/hooks.json" in portability
    assert "Do not patch SDK code or MCP server names" in portability


def test_codex_projection_live_rollout_status_routes_from_readme() -> None:
    readme = read_text("README.md")
    codex_projection = read_text("mechanics/codex-projection/README.md")
    status_ref = (
        "mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md"
    )
    boundary_ref = (
        "mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md"
    )
    campaign_ref = (
        "mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md"
    )
    schema_ref = (
        "mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json"
    )
    example_ref = (
        "mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json"
    )
    status_doc = read_text(status_ref)
    campaign_doc = read_text(campaign_ref)

    assert "mechanics/codex-projection/README.md" in readme
    assert status_ref in codex_projection
    assert boundary_ref in codex_projection
    assert campaign_ref in codex_projection
    assert schema_ref in codex_projection
    assert example_ref in codex_projection
    assert "src/aoa_sdk/codex/" in codex_projection
    assert "typed live read over deploy-local Codex rollout" in status_doc
    assert "It does not own rollout authority." in status_doc
    assert "`/.codex/generated/rollout/codex_plane_trust_state.current.json`" in status_doc
    assert "`rerollout`" in status_doc
    boundary_doc = read_text(boundary_ref)
    assert "`aoa-sdk` may surface typed references related to Codex rollout operations." in boundary_doc
    assert "It does not own:" in boundary_doc
    assert "rollout success authority" in boundary_doc
    assert "`campaign_ref`" in boundary_doc
    assert "`review_ref`" in boundary_doc
    assert "`rollback_ref`" in campaign_doc
    assert "These refs stay source-owned in `8Dionysus` cadence windows" in campaign_doc
    assert "Acceptable seam:" in boundary_doc
    assert "Unacceptable seam:" in boundary_doc


def test_readme_routes_current_direction_through_roadmap() -> None:
    readme = read_text("README.md")
    agents = read_text("AGENTS.md")
    roadmap = read_text("ROADMAP.md")
    blueprint = read_text("docs/blueprint.md")

    assert "ROADMAP.md" in readme
    assert "ROADMAP.md" in agents
    assert "control-plane contract hardening" in roadmap
    assert "docs/blueprint.md" in readme
    assert "original seed blueprint and historical design context" in readme
    assert "original seed blueprint and historical design note" in blueprint
    assert "It is not the current-direction surface" in blueprint
    assert "Treat any module, command, or layout entry that is not present in the current tree as planned or aspirational rather than landed." in blueprint
