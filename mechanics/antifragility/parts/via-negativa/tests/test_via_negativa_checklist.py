from __future__ import annotations

from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]


def test_via_negativa_checklist_is_routed_from_readme() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    checklist_ref = "mechanics/antifragility/parts/via-negativa/docs/via-negativa-checklist.md"

    assert checklist_ref in readme


def test_via_negativa_checklist_names_subtraction_before_addition() -> None:
    checklist = (PART_ROOT / "docs" / "via-negativa-checklist.md").read_text(encoding="utf-8")

    assert "Merge, move, suppress, quarantine, deprecate, or remove" in checklist
    assert "Does this helper clarify ownership, or hide it?" in checklist
    assert "SDK should feel like a scalpel" in checklist
