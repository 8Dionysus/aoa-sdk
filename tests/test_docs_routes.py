from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_lists_full_current_state_battery() -> None:
    readme = read_text("README.md")

    commands = [
        "python scripts/build_workspace_control_plane.py --check",
        "python scripts/validate_workspace_control_plane.py",
        "python -m pytest -q",
        "python -m ruff check .",
        "aoa workspace inspect /srv/aoa-sdk",
        "aoa compatibility check /srv/aoa-sdk",
        "aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json",
    ]
    for command in commands:
        assert command in readme


def test_agents_lists_compatibility_checks_in_minimum_validation() -> None:
    agents = read_text("AGENTS.md")

    assert "python scripts/build_workspace_control_plane.py --check" in agents
    assert "python scripts/validate_workspace_control_plane.py" in agents
    assert "aoa compatibility check /srv/aoa-sdk" in agents
    assert "aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json" in agents


def test_readme_lists_sibling_canary_surfaces() -> None:
    readme = read_text("README.md")

    assert "generated/workspace_control_plane.min.json" in readme
    assert "scripts/sibling_canary_matrix.json" in readme
    assert "scripts/run_sibling_canary.py" in readme
    assert ".github/workflows/latest-sibling-canary.yml" in readme


def test_surface_detection_routes_are_documented_as_additive_and_skill_only() -> None:
    readme = read_text("README.md")

    assert "docs/aoa-surface-detection-first-wave.md" in readme
    assert "docs/aoa-surface-detection-second-wave.md" in readme
    assert "docs/aoa-surface-detection-heuristics.md" in readme
    assert "docs/aoa-surface-detection-closeout-handoff.md" in readme
    assert "docs/session-growth-checkpoints.md" in readme
    assert "docs/checkpoint-note-promotion.md" in readme
    assert "It does not make `aoa skills detect/dispatch/enter/guard` mean anything other than skills." in readme
    assert "aoa surfaces detect /srv/aoa-sdk --phase ingress" in readme
    assert "aoa skills detect /srv/aoa-sdk --phase checkpoint" in readme
    assert "aoa surfaces detect /srv/aoa-sdk --phase checkpoint" in readme
    assert "aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note" in readme
    assert 'aoa skills enter /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --root /srv --json' in readme
    assert 'aoa skills guard /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv --json' in readme
    assert 'aoa skills guard /srv/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv --json' in readme
    assert "aoa skills guard /srv/aoa-sdk --intent-text \"reviewable verify-green checkpoint\" --mutation-surface code --checkpoint-kind verify_green" in readme
    assert 'aoa skills guard /srv/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv --json' in readme
    assert "aoa checkpoint append /srv/aoa-sdk" in readme
    assert "aoa checkpoint promote /srv/aoa-sdk --target dionysus-note" in readme
    assert "aoa surfaces handoff /srv/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json" in readme
    assert "sdk.stats.surface_detection()" in readme
    assert "carries harvest, progression, and upgrade candidates through the session" in readme
    assert "checkpoint_capture.session_end_skill_targets" in readme
    assert "checkpoint_capture.progression_axis_signals" in readme
    assert "checkpoint_capture.session_end_next_honest_move" in readme
    assert "aoa-session-progression-lift" in readme


def test_agents_documents_surface_detection_loop_and_truth_rules() -> None:
    agents = read_text("AGENTS.md")

    assert "## Surface Detection Loop" in agents
    assert "aoa surfaces detect /srv/aoa-sdk --phase ingress" in agents
    assert "aoa surfaces detect /srv/aoa-sdk --phase checkpoint" in agents
    assert "aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note" in agents
    assert 'aoa skills guard /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/aoa-sdk --json' in agents
    assert 'aoa skills guard /srv/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/aoa-sdk --json' in agents
    assert "aoa skills guard /srv/aoa-sdk --intent-text \"reviewable verify-green checkpoint\" --mutation-surface code --checkpoint-kind verify_green" in agents
    assert 'aoa skills guard /srv/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/aoa-sdk --json' in agents
    assert "aoa skills ...` remains skill-only" in agents
    assert "checkpoint notes stay lower-authority than harvest verdicts" in agents
    assert "session-local ledger for harvest, progression, and" in agents
    assert "checkpoint_capture.session_end_skill_targets" in agents
    assert "checkpoint_capture.progression_axis_signals" in agents
    assert "checkpoint_capture.session_end_next_honest_move" in agents
    assert "aoa-session-progression-lift" in agents
    assert "manual-equivalent` never becomes `activated`" in agents
    assert "routing shortlist hints stay advisory only" in agents


def test_session_closeout_explicitly_keeps_surface_handoff_separate() -> None:
    closeout = read_text("docs/session-closeout.md")

    assert "`aoa closeout run` does not auto-run `aoa surfaces handoff`" in closeout
    assert "`aoa surfaces handoff` is reviewed-only" in closeout
    assert "`checkpoint_note_ref`" in closeout
    assert "docs/aoa-surface-detection-closeout-handoff.md" in closeout
    assert "docs/aoa-surface-detection-second-wave.md" in closeout


def test_session_growth_checkpoint_doc_explains_session_end_ledger() -> None:
    checkpoints = read_text("docs/session-growth-checkpoints.md")

    assert "carry harvest, progression, and upgrade candidates through the end of the session" in checkpoints
    assert "candidate movement and stats refresh stay end-of-session decisions" in checkpoints
    assert "the final stats-refresh hint" in checkpoints
    assert "checkpoint_capture.session_end_skill_targets" in checkpoints
    assert "checkpoint_capture.progression_axis_signals" in checkpoints
    assert "checkpoint_capture.session_end_next_honest_move" in checkpoints
    assert "aoa-session-progression-lift" in checkpoints


def test_blueprint_is_marked_as_direction_surface() -> None:
    blueprint = read_text("docs/blueprint.md")

    assert "original seed blueprint and direction surface" in blueprint
    assert "not the current-state source of truth" in blueprint
    assert "Treat any module, command, or layout entry that is not present in the current tree as planned or aspirational rather than landed." in blueprint
