from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CARRY_PART = "mechanics/checkpoint/parts/reviewed-closeout-context-carry"


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_lists_full_current_state_battery() -> None:
    readme = read_text("README.md")

    commands = [
        "python scripts/validate_mechanics_topology.py",
        "python scripts/validate_sdk_source_home.py",
        "python scripts/build_workspace_control_plane.py --check",
        "python scripts/validate_workspace_control_plane.py",
        "python -m pytest -q",
        "python -m ruff check .",
        "aoa workspace inspect /srv/AbyssOS/aoa-sdk",
        "aoa compatibility check /srv/AbyssOS/aoa-sdk",
        "aoa compatibility check /srv/AbyssOS/aoa-sdk --repo aoa-skills --json",
    ]
    for command in commands:
        assert command in readme


def test_agents_lists_compatibility_checks_in_minimum_validation() -> None:
    agents = read_text("AGENTS.md")

    assert "python scripts/generate_decision_indexes.py --check" in agents
    assert "python scripts/validate_sdk_source_home.py" in agents
    assert "python scripts/validate_mechanics_topology.py" in agents
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


def test_changelog_records_current_unreleased_contour() -> None:
    changelog = read_text("CHANGELOG.md")

    required_sections = [
        "### Summary",
        "### Reconciliation Basis",
        "### Final Route Sweep",
        "### Control-Plane Authority And Boundary",
        "### Added",
        "### Changed",
        "### Moved Or Retired",
        "### Validation",
        "### Notes",
    ]
    for section in required_sections:
        assert section in changelog
    assert "22 first-parent commits and 382 changed tracked paths" in changelog
    assert "DESIGN.md" in changelog
    assert "DESIGN.AGENTS.md" in changelog
    assert "docs/decisions/" in changelog
    assert "root-level generated paths" in changelog
    assert "active routes" in changelog
    assert "This unreleased section is a release-ready reconciliation surface" in changelog
    assert "mechanics topology" in changelog
    assert "mechanics/ARTIFACT_TOPOLOGY.md" in changelog
    assert "python scripts/validate_mechanics_topology.py" in changelog


def test_readme_lists_sibling_canary_surfaces() -> None:
    readme = read_text("README.md")

    assert "generated/workspace_control_plane.min.json" in readme
    assert (
        "mechanics/release-support/parts/public-support-ci-posture/"
        "config/sibling_canary_matrix.json"
    ) in readme
    assert (
        "mechanics/release-support/parts/public-support-ci-posture/"
        "scripts/run_sibling_canary.py"
    ) in readme
    assert ".github/workflows/latest-sibling-canary.yml" in readme


def test_surface_detection_routes_are_documented_as_additive_and_skill_only() -> None:
    readme = read_text("README.md")

    assert "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/initial-surface-detection-boundary.md" in readme
    assert "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-detection-enrichment.md" in readme
    assert "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-detection-heuristics.md" in readme
    assert "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-closeout-handoff.md" in readme
    assert "mechanics/experience/parts/capture-pipeline-helper/docs/capture-pipeline-helper.md" in readme
    assert "mechanics/experience/parts/capture-pipeline-helper/schemas/capture-pipeline-helper.schema.json" in readme
    assert "mechanics/experience/parts/capture-pipeline-helper/examples/capture-pipeline-helper.example.json" in readme
    assert "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md" in readme
    assert (
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/reviewed-checkpoint-note-promotion.md"
        in readme
    )
    assert "It does not make `aoa skills detect/dispatch/enter/guard` mean anything other than skills." in readme
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress" in readme
    assert "aoa skills detect /srv/AbyssOS/aoa-sdk --phase checkpoint" in readme
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint" in readme
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note" in readme
    assert 'aoa skills enter /srv/AbyssOS/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --root /srv/AbyssOS --json' in readme
    assert 'aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/AbyssOS --json' in readme
    assert 'aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/AbyssOS --json' in readme
    assert "aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text \"reviewable verify-green checkpoint\" --mutation-surface code --checkpoint-kind verify_green" in readme
    assert 'aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/AbyssOS --json' in readme
    assert "aoa checkpoint append /srv/AbyssOS/aoa-sdk" in readme
    assert "aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json" in readme
    assert "aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD" in readme
    assert "aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in readme
    assert "aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in readme
    assert "aoa checkpoint build-closeout-context /srv/AbyssOS/aoa-sdk" in readme
    assert "aoa checkpoint execute-closeout-chain /srv/AbyssOS/aoa-sdk" in readme
    assert "aoa checkpoint promote /srv/AbyssOS/aoa-sdk --target dionysus-note" in readme
    assert "aoa surfaces handoff /srv/AbyssOS/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json" in readme
    assert "sdk.stats.surface_detection()" in readme
    assert "carries harvest, progression, and upgrade candidates through the session" in readme
    assert "plain `git commit`" in readme
    assert "post-commit-report.json" in readme
    assert "agent_review=pending" in readme
    assert "checkpoint_capture.session_end_skill_targets" in readme
    assert "checkpoint_capture.progression_axis_signals" in readme
    assert "checkpoint_capture.session_end_next_honest_move" in readme
    assert "aoa-session-progression-lift" in readme
    assert "aoa-checkpoint-closeout-bridge" in readme


def test_agents_documents_surface_detection_loop_and_truth_rules() -> None:
    agents = read_text("AGENTS.md")

    assert "## Surface Detection Loop" in agents
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress" in agents
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint" in agents
    assert "aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note" in agents
    assert 'aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/AbyssOS/aoa-sdk --json' in agents
    assert 'aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/AbyssOS/aoa-sdk --json' in agents
    assert "aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text \"reviewable verify-green checkpoint\" --mutation-surface code --checkpoint-kind verify_green" in agents
    assert 'aoa skills guard /srv/AbyssOS/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/AbyssOS/aoa-sdk --json' in agents
    assert "aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json" in agents
    assert "aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD" in agents
    assert "aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in agents
    assert "aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in agents
    assert "aoa skills ...` remains skill-only" in agents
    assert "checkpoint notes stay lower-authority than harvest verdicts" in agents
    assert "skipped_no_active_session" in agents
    assert "agent_review=pending" in agents
    assert "session-local ledger for harvest, progression, and" in agents
    assert "checkpoint_capture.session_end_skill_targets" in agents
    assert "checkpoint_capture.progression_axis_signals" in agents
    assert "checkpoint_capture.session_end_next_honest_move" in agents
    assert "aoa-session-progression-lift" in agents
    assert "aoa-checkpoint-closeout-bridge" in agents
    assert "manual-equivalent` never becomes `activated`" in agents
    assert "routing shortlist hints stay advisory only" in agents


def test_session_closeout_explicitly_keeps_surface_handoff_separate() -> None:
    closeout = read_text(
        "mechanics/checkpoint/parts/reviewed-session-handoff-runner/docs/reviewed-session-handoff-runner.md"
    )

    assert "`aoa closeout run` does not auto-run `aoa surfaces handoff`" in closeout
    assert "`aoa surfaces handoff` is reviewed-only" in closeout
    assert "`checkpoint_note_ref`" in closeout
    assert "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-closeout-handoff.md" in closeout
    assert "mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-detection-enrichment.md" in closeout
    assert "`owner_followthrough_map`" in closeout
    assert "`followthrough_decision`" in closeout
    assert "without minting `candidate_ref`, `seed_ref`, or `object_ref`" in closeout


def test_session_growth_checkpoint_doc_explains_session_end_ledger() -> None:
    checkpoints = read_text(
        "mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md"
    )

    assert "carry harvest, progression, and upgrade candidates through the end of the session" in checkpoints
    assert "candidate movement and stats refresh stay reviewed-closeout decisions" in checkpoints
    assert "land promptly in tracked owner status surfaces" in checkpoints
    assert "provenance, and blockers preserved" in checkpoints
    assert "the final stats-refresh hint" in checkpoints
    assert "checkpoint_capture.session_end_skill_targets" in checkpoints
    assert "checkpoint_capture.progression_axis_signals" in checkpoints
    assert "checkpoint_capture.session_end_next_honest_move" in checkpoints
    assert "aoa-session-progression-lift" in checkpoints
    assert "plain `git commit` can trigger one active-session-only checkpoint pass" in checkpoints
    assert "post-commit-report.json" in checkpoints
    assert "aoa-sdk/.aoa/session-growth/post-commit-status/<repo>.latest.json" in checkpoints
    assert "aoa checkpoint after-commit /srv/AbyssOS/aoa-sdk --commit-ref HEAD --root /srv/AbyssOS --json" in checkpoints
    assert "aoa checkpoint review-note /srv/AbyssOS/aoa-sdk --commit-ref HEAD" in checkpoints
    assert "aoa checkpoint install-hook --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in checkpoints
    assert "aoa checkpoint hook-status --repo aoa-sdk --hook all --root /srv/AbyssOS --json" in checkpoints
    assert "real intermediate findings, candidate notes, stats hints" in checkpoints
    assert "aoa checkpoint build-closeout-context /srv/AbyssOS/aoa-sdk" in checkpoints
    assert "aoa checkpoint execute-closeout-chain /srv/AbyssOS/aoa-sdk" in checkpoints
    assert "aoa-checkpoint-closeout-bridge" in checkpoints
    assert "continuity_ref_hint -> revision_window_ref_hint -> anchor_artifact_ref" in checkpoints
    assert "reanchor_need" in checkpoints
    assert f"{CARRY_PART}/docs/self-agency-continuity-carry.md" in checkpoints


def test_readme_routes_to_reviewed_closeout_context_carry() -> None:
    readme = read_text("README.md")
    carry = read_text(f"{CARRY_PART}/docs/candidate-lineage-carry.md")
    component_carry = read_text(f"{CARRY_PART}/docs/component-refresh-followthrough.md")
    followthrough = read_text(f"{CARRY_PART}/docs/owner-followthrough-map.md")
    kernel_rules = read_text(f"{CARRY_PART}/docs/next-kernel-followthrough-decision.md")
    continuity = read_text(f"{CARRY_PART}/docs/self-agency-continuity-carry.md")

    assert f"{CARRY_PART}/docs/owner-followthrough-map.md" in readme
    assert f"{CARRY_PART}/docs/component-refresh-followthrough.md" in readme
    assert f"{CARRY_PART}/schemas/component_drift_hint_set.schema.json" in readme
    assert f"{CARRY_PART}/examples/component_drift_hints.example.json" in readme
    assert f"{CARRY_PART}/schemas/component_refresh_followthrough_decision_set.schema.json" in readme
    assert f"{CARRY_PART}/examples/component_refresh_followthrough_decision.example.json" in readme
    assert f"{CARRY_PART}/schemas/closeout_owner_followthrough_map.schema.json" in readme
    assert f"{CARRY_PART}/examples/closeout_owner_followthrough_map.example.json" in readme
    assert f"{CARRY_PART}/docs/self-agency-continuity-carry.md" in readme
    assert f"{CARRY_PART}/schemas/closeout_continuity_window.schema.json" in readme
    assert f"{CARRY_PART}/examples/closeout_continuity_window.example.json" in readme
    assert f"{CARRY_PART}/docs/next-kernel-followthrough-decision.md" in readme
    assert f"{CARRY_PART}/schemas/closeout_followthrough_decision.schema.json" in readme
    assert f"{CARRY_PART}/examples/closeout_followthrough_decision.example.json" in readme
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
    workspace_layout = read_text("docs/workspace-layout.md")
    portability_ref = (
        "mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md"
    )
    portability = read_text(portability_ref)

    assert portability_ref in readme
    assert "8Dionysus/docs/CODEX_PLANE_REGENERATION.md" in readme
    assert "Workspace discovery overrides in `aoa-sdk` are not a substitute for" in workspace_layout
    assert "Codex Projection deployment regeneration" in workspace_layout
    assert "`aoa-sdk` owns:" in portability
    assert "It does not own:" in portability
    assert "8Dionysus/.codex/config.toml" in portability
    assert "8Dionysus/.codex/hooks.json" in portability
    assert "Do not patch SDK code or MCP server names" in portability


def test_codex_projection_live_rollout_status_routes_from_readme() -> None:
    readme = read_text("README.md")
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

    assert status_ref in readme
    assert boundary_ref in readme
    assert campaign_ref in readme
    assert schema_ref in readme
    assert example_ref in readme
    assert "src/aoa_sdk/codex/registry.py" in readme
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
