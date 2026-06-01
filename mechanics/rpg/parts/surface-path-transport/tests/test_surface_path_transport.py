from __future__ import annotations

from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]


def test_surface_path_transport_doc_is_routed_from_readme() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    surface_path_ref = "mechanics/rpg/parts/surface-path-transport/docs/surface-path-transport.md"

    assert surface_path_ref in readme


def test_surface_path_transport_keeps_consumer_expectations_bounded() -> None:
    doc = (PART_ROOT / "docs" / "surface-path-transport.md").read_text(encoding="utf-8")

    assert "These are consumer expectations, not owner-side doctrine." in doc
    assert "It should not rewrite them silently." in doc
    assert "That staging is a reader-path convenience only." in doc
