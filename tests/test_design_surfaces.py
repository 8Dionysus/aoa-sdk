from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_root_design_surfaces_define_sdk_shape_with_mechanics() -> None:
    design = read_text("DESIGN.md")
    agents_design = read_text("DESIGN.AGENTS.md")
    decision = read_text("docs/decisions/AOA-SDK-D-0002-root-design-surfaces-before-mechanics.md")
    mechanics_decision = read_text("docs/decisions/AOA-SDK-D-0005-mechanics-parent-boundary-correction.md")
    questbook_decision = read_text("docs/decisions/AOA-SDK-D-0042-questbook-source-store-restoration.md")
    sdk_home_decision = read_text("docs/decisions/AOA-SDK-D-0043-sdk-source-home-tree.md")

    assert "`DESIGN.md` describes the system form of `aoa-sdk`." in design
    assert "The SDK source home is `sdk/`." in design
    assert "The importable SDK implementation remains `src/aoa_sdk/`." in design
    assert "`mechanics/` packages name repeatable SDK operations" in design
    assert "`sdk/` must not duplicate, rename, or absorb `src/aoa_sdk/`" in design
    assert "`DESIGN.AGENTS.md` describes the desired form of agent-facing guidance" in agents_design
    assert "`sdk/` owns SDK source-home posture and route shape." in agents_design
    assert "`mechanics/` owns repeatable operation topology, not SDK source code" in agents_design
    assert "Create root `DESIGN.md` and `DESIGN.AGENTS.md` before introducing" in decision
    assert "Correct `aoa-sdk` mechanics to 12 top-level parent packages" in mechanics_decision
    assert "Restore root `quests/` as the active SDK source quest record district." in questbook_decision
    assert "Add `sdk/` as the source-authored SDK home." in sdk_home_decision


def test_root_routes_point_to_design_surfaces() -> None:
    readme = read_text("README.md")
    agents = read_text("AGENTS.md")
    roadmap = read_text("ROADMAP.md")
    boundaries = read_text("docs/boundaries.md")

    assert "DESIGN.md" in readme
    assert "DESIGN.AGENTS.md" in readme
    assert "DESIGN.md" in agents
    assert "DESIGN.AGENTS.md" in agents
    assert "DESIGN.md" in roadmap
    assert "DESIGN.AGENTS.md" in roadmap
    assert "DESIGN.md" in boundaries
    assert "DESIGN.AGENTS.md" in boundaries
    assert "mechanics/" in readme
    assert "mechanics/" in agents
    assert "sdk/source_home.manifest.json" in readme
    assert "sdk/source_home.manifest.json" in agents
