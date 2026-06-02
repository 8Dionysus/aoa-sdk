from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_mechanics_topology.py"
SPEC = importlib.util.spec_from_file_location("validate_mechanics_topology", SCRIPT_PATH)
mechanics_validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = mechanics_validator
SPEC.loader.exec_module(mechanics_validator)


def test_live_mechanics_topology_is_valid() -> None:
    assert mechanics_validator.validate(REPO_ROOT) == []


def test_mechanics_package_set_is_explicit() -> None:
    assert mechanics_validator.EXPECTED_PACKAGES == (
        "agon",
        "antifragility",
        "boundary-bridge",
        "checkpoint",
        "codex-projection",
        "experience",
        "questbook",
        "recurrence",
        "release-support",
        "rpg",
        "runtime-seam",
        "titan",
    )


def test_mechanics_roadmaps_are_required_route_surfaces() -> None:
    assert mechanics_validator.REQUIRED_ROOT_FILES == (
        mechanics_validator.MECHANICS_DIR / "AGENTS.md",
        mechanics_validator.MECHANICS_DIR / "README.md",
        mechanics_validator.MECHANICS_DIR / "ROADMAP.md",
        mechanics_validator.TOPOLOGY_PATH,
    )
    assert mechanics_validator.REQUIRED_PACKAGE_FILES == (
        "AGENTS.md",
        "README.md",
        "ROADMAP.md",
        "PARTS.md",
        "PROVENANCE.md",
    )

    root_roadmap = (REPO_ROOT / "mechanics" / "ROADMAP.md").read_text(encoding="utf-8")
    for slug in mechanics_validator.EXPECTED_PACKAGES:
        assert f"[`{slug}`]({slug}/ROADMAP.md)" in root_roadmap
        package_roadmap = (REPO_ROOT / "mechanics" / slug / "ROADMAP.md").read_text(encoding="utf-8")
        assert "## Current Contour" in package_roadmap
        assert "## Update Trigger" in package_roadmap


def test_former_parent_names_are_legacy_indexed_not_active_topology() -> None:
    topology = mechanics_validator._read_json(  # noqa: SLF001
        REPO_ROOT / mechanics_validator.TOPOLOGY_PATH,
        [],
    )

    assert "demoted_" + "parent_candidates" not in topology
    assert topology["legacy_route_indexes"] == [
        path.as_posix() for path in mechanics_validator.LEGACY_INDEX_FILES
    ]
    assert set(topology["active_part_routes"]["boundary-bridge"]) >= {
        "consumed-surface-posture-gate",
        "owner-layer-signal-handoff",
    }


def test_active_topology_status_names_current_payload_posture() -> None:
    topology = mechanics_validator._read_json(  # noqa: SLF001
        REPO_ROOT / mechanics_validator.TOPOLOGY_PATH,
        [],
    )

    assert topology["status"] == mechanics_validator.EXPECTED_TOPOLOGY_STATUS
    assert topology["payload_movement_status"] == mechanics_validator.EXPECTED_PAYLOAD_MOVEMENT_STATUS


def test_active_route_ids_do_not_use_legacy_or_migration_vocabulary() -> None:
    topology = mechanics_validator._read_json(  # noqa: SLF001
        REPO_ROOT / mechanics_validator.TOPOLOGY_PATH,
        [],
    )

    active_routes = {
        f"{parent}/{part}"
        for parent, parts in topology["active_part_routes"].items()
        for part in parts
    }
    assert all(
        token not in route
        for route in active_routes
        for token in mechanics_validator.FORBIDDEN_ACTIVE_ROUTE_TOKENS
    )


def test_source_family_routes_cover_current_sdk_source_tree() -> None:
    topology = mechanics_validator._read_json(  # noqa: SLF001
        REPO_ROOT / mechanics_validator.TOPOLOGY_PATH,
        [],
    )
    assert set(topology["source_family_routes"]) == mechanics_validator._source_families(REPO_ROOT)  # noqa: SLF001


def test_root_technical_district_files_are_explicitly_allowlisted() -> None:
    issues: list[str] = []
    mechanics_validator._validate_root_technical_districts(REPO_ROOT, issues)  # noqa: SLF001

    assert issues == []


def test_questbook_source_store_is_root_routed_not_part_local() -> None:
    assert (REPO_ROOT / "QUESTBOOK.md").is_file()
    assert (REPO_ROOT / "quests" / "README.md").is_file()
    assert (REPO_ROOT / "quests" / "AGENTS.md").is_file()
    assert (REPO_ROOT / "quests" / "agon" / "ready").is_dir()
    assert (REPO_ROOT / "mechanics" / "questbook" / "README.md").is_file()

    part_local_quest_dirs = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "mechanics").glob("*/parts/*/quests")
    )
    assert part_local_quest_dirs == []


def test_boundary_bridge_covers_sibling_facade_source_families() -> None:
    topology = mechanics_validator._read_json(  # noqa: SLF001
        REPO_ROOT / mechanics_validator.TOPOLOGY_PATH,
        [],
    )
    boundary_bridge = next(item for item in topology["packages"] if item["slug"] == "boundary-bridge")
    source_surfaces = set(boundary_bridge["source_surfaces"])

    assert {
        "src/aoa_sdk/governed_runs",
        "src/aoa_sdk/kag",
        "src/aoa_sdk/loaders",
        "src/aoa_sdk/playbooks",
        "src/aoa_sdk/techniques",
    }.issubset(source_surfaces)
