from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_boundaries_names_existing_design_sources() -> None:
    # The boundary document names repo-root sources in code spans, not links.
    # Public navigation and root guidance are checked in test_docs_routes.py.
    boundaries = read_text("docs/boundaries.md")
    for relative in ("DESIGN.md", "DESIGN.AGENTS.md"):
        assert re.search(rf"(?<![\w./-]){re.escape(relative)}(?![\w/-]|\.[\w./-])", boundaries)
        assert (REPO_ROOT / relative).exists()
