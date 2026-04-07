from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_lists_full_current_state_battery() -> None:
    readme = read_text("README.md")

    commands = [
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

    assert "aoa compatibility check /srv/aoa-sdk" in agents
    assert "aoa compatibility check /srv/aoa-sdk --repo aoa-skills --json" in agents


def test_readme_lists_sibling_canary_surfaces() -> None:
    readme = read_text("README.md")

    assert "scripts/sibling_canary_matrix.json" in readme
    assert "scripts/run_sibling_canary.py" in readme
    assert ".github/workflows/latest-sibling-canary.yml" in readme


def test_blueprint_is_marked_as_direction_surface() -> None:
    blueprint = read_text("docs/blueprint.md")

    assert "original seed blueprint and direction surface" in blueprint
    assert "not the current-state source of truth" in blueprint
    assert "Treat any module, command, or layout entry that is not present in the current tree as planned or aspirational rather than landed." in blueprint
