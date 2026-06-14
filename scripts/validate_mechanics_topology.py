#!/usr/bin/env python3
"""Validate the aoa-sdk mechanics topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MECHANICS_DIR = Path("mechanics")
TOPOLOGY_PATH = MECHANICS_DIR / "topology.json"

EXPECTED_PACKAGES = (
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
EXPECTED_TOPOLOGY_STATUS = "active-part-localized-topology"
EXPECTED_PAYLOAD_MOVEMENT_STATUS = "complete"
FORBIDDEN_ACTIVE_ROUTE_TOKENS = ("legacy", "fallback", "former", "old-root", "skeleton")
ABSENT_ROOT_TECHNICAL_DISTRICTS = ("config", "examples", "manifests", "githooks", "systemd")
ROOT_TECHNICAL_DISTRICT_FILES = {
    "docs": frozenset(
        {
            "docs/AGENTS.md",
            "docs/README.md",
            "docs/RELEASE_CI_POSTURE.md",
            "docs/RELEASING.md",
            "docs/blueprint.md",
            "docs/boundaries.md",
            "docs/versioning.md",
            "docs/workspace-layout.md",
        }
    ),
    "generated": frozenset(
        {
            "generated/AGENTS.md",
            "generated/source_topology.min.json",
            "generated/workspace_control_plane.min.json",
        }
    ),
    "schemas": frozenset(
        {
            "schemas/AGENTS.md",
            "schemas/workspace-control-plane.schema.json",
        }
    ),
    "scripts": frozenset(
        {
            "scripts/AGENTS.md",
            "scripts/build_source_topology_index.py",
            "scripts/build_workspace_control_plane.py",
            "scripts/generate_decision_indexes.py",
            "scripts/release_check.py",
            "scripts/source_topology_common.py",
            "scripts/validate_mechanics_topology.py",
            "scripts/validate_nested_agents.py",
            "scripts/validate_sdk_source_home.py",
            "scripts/validate_source_topology_index.py",
            "scripts/validate_workspace_control_plane.py",
            "scripts/workspace_control_plane_common.py",
        }
    ),
    "tests": frozenset(
        {
            "tests/AGENTS.md",
            "tests/conftest.py",
            "tests/test_decision_indexes.py",
            "tests/test_design_surfaces.py",
            "tests/test_docs_routes.py",
            "tests/test_mechanics_topology.py",
            "tests/test_sdk_source_home.py",
            "tests/test_smoke.py",
            "tests/test_source_topology_index.py",
            "tests/test_validate_nested_agents.py",
        }
    ),
    "quests": frozenset(
        {
            "quests/AGENTS.md",
            "quests/README.md",
            "quests/agon/README.md",
            "quests/checkpoint/README.md",
        }
    ),
}
ROOT_TECHNICAL_DISTRICT_PREFIXES = {
    "docs": ("docs/decisions/",),
    "quests": ("quests/agon/ready/", "quests/checkpoint/captured/"),
    "tests": ("tests/fixtures/",),
}

REQUIRED_ROOT_FILES = (
    MECHANICS_DIR / "AGENTS.md",
    MECHANICS_DIR / "README.md",
    MECHANICS_DIR / "ROADMAP.md",
    TOPOLOGY_PATH,
)

REQUIRED_PACKAGE_FILES = ("AGENTS.md", "README.md", "ROADMAP.md", "PARTS.md", "PROVENANCE.md")
LEGACY_ROUTE_FILES = (
    MECHANICS_DIR / "runtime-seam" / "legacy" / "former-routes.json",
    MECHANICS_DIR / "boundary-bridge" / "legacy" / "former-routes.json",
    MECHANICS_DIR / "checkpoint" / "legacy" / "former-routes.json",
    MECHANICS_DIR / "codex-projection" / "legacy" / "former-routes.json",
)
LEGACY_INDEX_FILES = tuple(path.with_name("INDEX.md") for path in LEGACY_ROUTE_FILES)

README_SNIPPETS = (
    "## Mechanic Card",
    "### Operation",
    "### Trigger",
    "### SDK owns",
    "### Stronger owner split",
    "### Current source surfaces",
    "### Candidate parts",
    "### Must not claim",
    "### Validation",
    "### Next route",
)


def _read_json(path: Path, issues: list[str]) -> dict[str, Any]:
    if not path.is_file():
        issues.append(f"{path.as_posix()}: topology file is missing")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(f"{path.as_posix()}: invalid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        issues.append(f"{path.as_posix()}: root JSON value must be an object")
        return {}
    return data


def _rel(path: Path) -> str:
    return path.as_posix()


def _path_exists(repo_root: Path, rel_path: str) -> bool:
    return (repo_root / rel_path).exists()


def _tracked_source_paths(repo_root: Path) -> list[Path] | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--", "src/aoa_sdk"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return [Path(line) for line in result.stdout.splitlines() if line]


def _source_families(repo_root: Path) -> set[str]:
    source_root = repo_root / "src" / "aoa_sdk"
    families: set[str] = set()
    root_files = False

    tracked_paths = _tracked_source_paths(repo_root)
    if tracked_paths is not None:
        for rel_path in tracked_paths:
            parts = rel_path.parts
            if len(parts) < 3:
                continue
            if len(parts) == 3:
                name = parts[2]
                if name != "__pycache__" and not name.endswith(".pyc"):
                    root_files = True
                continue
            family = parts[2]
            if family != "__pycache__" and not family.endswith(".pyc"):
                families.add(family)

        if root_files:
            families.add("root-package")
        return families

    if not source_root.is_dir():
        return families

    for path in source_root.iterdir():
        name = path.name
        if name == "__pycache__" or name.endswith(".pyc"):
            continue
        if path.is_dir():
            families.add(name)
        elif path.is_file():
            root_files = True

    if root_files:
        families.add("root-package")
    return families


def _source_family_surface(family: str) -> str:
    if family == "root-package":
        return "src/aoa_sdk/api.py"
    return f"src/aoa_sdk/{family}"


def _is_ignored_generated_path(path: Path) -> bool:
    return any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.parts)


def _validate_root_technical_districts(repo_root: Path, issues: list[str]) -> None:
    for district in ABSENT_ROOT_TECHNICAL_DISTRICTS:
        path = repo_root / district
        if path.exists():
            issues.append(f"{district}/: root technical district must be absent unless a root contract reopens it")

    for district, allowed_files in ROOT_TECHNICAL_DISTRICT_FILES.items():
        root = repo_root / district
        if not root.is_dir():
            issues.append(f"{district}/: required root technical district is missing")
            continue

        allowed_prefixes = ROOT_TECHNICAL_DISTRICT_PREFIXES.get(district, ())
        for path in sorted(root.rglob("*")):
            if path.is_dir() or _is_ignored_generated_path(path):
                continue
            rel_path = path.relative_to(repo_root).as_posix()
            if rel_path in allowed_files:
                continue
            if any(rel_path.startswith(prefix) for prefix in allowed_prefixes):
                continue
            issues.append(
                f"{rel_path}: unexpected root technical-district file; move mechanic-owned payload into mechanics/<parent>/parts/<part>/ or update the root contract"
            )


def _active_part_route_set(active_part_routes: Any, issues: list[str]) -> set[str]:
    if not isinstance(active_part_routes, dict):
        issues.append("mechanics/topology.json: active_part_routes must be an object")
        return set()

    routes: set[str] = set()
    expected_set = set(EXPECTED_PACKAGES)
    for parent, parts in active_part_routes.items():
        if parent not in expected_set:
            issues.append(f"mechanics/topology.json: active_part_routes has invalid parent {parent}")
            continue
        if not isinstance(parts, list) or not parts:
            issues.append(f"mechanics/topology.json: active_part_routes.{parent} must be a non-empty list")
            continue
        for part in parts:
            if not isinstance(part, str) or not part:
                issues.append(f"mechanics/topology.json: active_part_routes.{parent} has invalid part")
                continue
            route_id = f"{parent}/{part}"
            for token in FORBIDDEN_ACTIVE_ROUTE_TOKENS:
                if token in route_id:
                    issues.append(
                        f"mechanics/topology.json: active route {route_id!r} must not contain {token!r}"
                    )
            routes.add(route_id)
    return routes


def _load_legacy_routes(repo_root: Path, active_routes: set[str], issues: list[str]) -> None:
    for rel_path in LEGACY_ROUTE_FILES:
        data = _read_json(repo_root / rel_path, issues)
        if not data:
            continue

        parent = data.get("parent")
        if parent not in EXPECTED_PACKAGES:
            issues.append(f"{rel_path.as_posix()}: parent must be a current mechanics package")
        if data.get("schema_version") != "aoa_sdk_mechanics_legacy_routes_v1":
            issues.append(f"{rel_path.as_posix()}: unexpected schema_version")

        legacy_dir = rel_path.parent
        for file_name in ("AGENTS.md", "README.md", "INDEX.md", "DISTILLATION_LOG.md", "raw/README.md"):
            if not (repo_root / legacy_dir / file_name).is_file():
                issues.append(f"{(legacy_dir / file_name).as_posix()}: required legacy file is missing")

        entries = data.get("entries")
        if not isinstance(entries, list) or not entries:
            issues.append(f"{rel_path.as_posix()}: entries must be a non-empty list")
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                issues.append(f"{rel_path.as_posix()}: each legacy entry must be an object")
                continue
            former_name = entry.get("former_name")
            active_route = entry.get("active_route")
            if not isinstance(former_name, str) or not former_name:
                issues.append(f"{rel_path.as_posix()}: legacy entry missing former_name")
                continue
            if (repo_root / MECHANICS_DIR / former_name).exists():
                issues.append(f"mechanics/{former_name}: former mechanics parent must not exist as top-level package")
            if not isinstance(active_route, str) or active_route not in active_routes:
                issues.append(f"{rel_path.as_posix()}: {former_name} points to unknown active route {active_route!r}")
                continue
            _, active_part = active_route.split("/", 1)
            if former_name in active_part:
                issues.append(
                    f"{rel_path.as_posix()}: active route {active_route!r} must not reuse former name {former_name!r}"
                )


def validate(repo_root: Path = REPO_ROOT) -> list[str]:
    repo_root = repo_root.resolve()
    issues: list[str] = []

    for rel_path in REQUIRED_ROOT_FILES:
        if not (repo_root / rel_path).is_file():
            issues.append(f"{_rel(rel_path)}: required root mechanics file is missing")

    _validate_root_technical_districts(repo_root, issues)

    topology = _read_json(repo_root / TOPOLOGY_PATH, issues)
    if not topology:
        return issues

    if topology.get("schema_version") != "aoa_sdk_mechanics_topology_v1":
        issues.append("mechanics/topology.json: unexpected schema_version")
    if topology.get("status") != EXPECTED_TOPOLOGY_STATUS:
        issues.append(f"mechanics/topology.json: status must be {EXPECTED_TOPOLOGY_STATUS}")
    if topology.get("payload_movement_status") != EXPECTED_PAYLOAD_MOVEMENT_STATUS:
        issues.append(
            f"mechanics/topology.json: payload_movement_status must be {EXPECTED_PAYLOAD_MOVEMENT_STATUS}"
        )
    parent_rule = topology.get("parent_boundary_rule")
    if not isinstance(parent_rule, str) or "SDK-specific lanes become parts" not in parent_rule:
        issues.append("mechanics/topology.json: missing parent boundary rule")

    source_family_routes = topology.get("source_family_routes")
    if not isinstance(source_family_routes, dict):
        issues.append("mechanics/topology.json: source_family_routes must be an object")
        source_family_routes = {}
    else:
        actual_families = _source_families(repo_root)
        routed_families = set(source_family_routes)
        missing_routes = sorted(actual_families - routed_families)
        extra_routes = sorted(routed_families - actual_families)
        for family in missing_routes:
            issues.append(f"mechanics/topology.json: missing source family route for {family}")
        for family in extra_routes:
            issues.append(f"mechanics/topology.json: source family route has no source family {family}")

    former_active_key = "demoted_" + "parent_candidates"
    if former_active_key in topology:
        issues.append("mechanics/topology.json: former parent names must live in mechanics/*/legacy, not active topology")

    legacy_indexes = topology.get("legacy_route_indexes")
    expected_legacy_indexes = [path.as_posix() for path in LEGACY_INDEX_FILES]
    if legacy_indexes != expected_legacy_indexes:
        issues.append(
            "mechanics/topology.json: legacy_route_indexes must point to the canonical package legacy indexes"
        )
    active_part_routes_raw = topology.get("active_part_routes")
    active_routes = _active_part_route_set(active_part_routes_raw, issues)
    _validate_active_part_directories(repo_root, active_part_routes_raw, issues)
    _load_legacy_routes(repo_root, active_routes, issues)

    packages = topology.get("packages")
    if not isinstance(packages, list):
        issues.append("mechanics/topology.json: packages must be a list")
        return issues

    package_slugs: list[str] = []
    package_source_surfaces: dict[str, set[str]] = {}
    for item in packages:
        if not isinstance(item, dict):
            issues.append("mechanics/topology.json: each package must be an object")
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug:
            issues.append("mechanics/topology.json: package missing slug")
            continue
        package_slugs.append(slug)

        package_dir = repo_root / MECHANICS_DIR / slug
        if not package_dir.is_dir():
            issues.append(f"mechanics/{slug}: package directory is missing")
            continue

        for file_name in REQUIRED_PACKAGE_FILES:
            file_path = package_dir / file_name
            if not file_path.is_file():
                issues.append(f"mechanics/{slug}/{file_name}: required file is missing")

        readme_path = package_dir / "README.md"
        if readme_path.is_file():
            text = readme_path.read_text(encoding="utf-8")
            for snippet in README_SNIPPETS:
                if snippet not in text:
                    issues.append(f"mechanics/{slug}/README.md: missing {snippet!r}")

        agents_path = package_dir / "AGENTS.md"
        if agents_path.is_file():
            text = agents_path.read_text(encoding="utf-8")
            for snippet in ("# AGENTS.md", "Stay on the control plane", "Validation"):
                if snippet not in text:
                    issues.append(f"mechanics/{slug}/AGENTS.md: missing {snippet!r}")

        parts_path = package_dir / "PARTS.md"
        if parts_path.is_file() and "## Candidate Parts" not in parts_path.read_text(encoding="utf-8"):
            issues.append(f"mechanics/{slug}/PARTS.md: missing candidate parts section")

        roadmap_path = package_dir / "ROADMAP.md"
        if roadmap_path.is_file():
            roadmap = roadmap_path.read_text(encoding="utf-8")
            for snippet in (
                "## Current Contour",
                "## Next Work",
                "## When Time Comes",
                "## Out Of Scope",
            ):
                if snippet not in roadmap:
                    issues.append(f"mechanics/{slug}/ROADMAP.md: missing {snippet!r}")

        provenance_path = package_dir / "PROVENANCE.md"
        if provenance_path.is_file():
            provenance = provenance_path.read_text(encoding="utf-8")
            if "## Source Surfaces" not in provenance:
                issues.append(f"mechanics/{slug}/PROVENANCE.md: missing source surfaces section")

        source_surfaces = item.get("source_surfaces")
        if not isinstance(source_surfaces, list) or not source_surfaces:
            issues.append(f"mechanics/topology.json: {slug} has no source_surfaces")
        else:
            package_source_surfaces[slug] = {rel_path for rel_path in source_surfaces if isinstance(rel_path, str)}
            for rel_path in source_surfaces:
                if not isinstance(rel_path, str) or not rel_path:
                    issues.append(f"mechanics/topology.json: {slug} has invalid source surface")
                elif not _path_exists(repo_root, rel_path):
                    issues.append(f"mechanics/topology.json: {slug} missing source surface {rel_path}")

        candidate_parts = item.get("candidate_parts")
        if not isinstance(candidate_parts, list) or not candidate_parts:
            issues.append(f"mechanics/topology.json: {slug} has no candidate_parts")
            candidate_parts = []
        else:
            _validate_part_directories(repo_root, slug, set(candidate_parts), issues)

        validation = item.get("validation")
        if not isinstance(validation, list) or not validation:
            issues.append(f"mechanics/topology.json: {slug} has no validation routes")

    expected = list(EXPECTED_PACKAGES)
    if package_slugs != expected:
        issues.append(
            "mechanics/topology.json: package order or set mismatch; "
            f"expected {expected!r}, found {package_slugs!r}"
        )

    _validate_active_part_source_surfaces(active_part_routes_raw, package_source_surfaces, issues)

    expected_set = set(EXPECTED_PACKAGES)
    if isinstance(source_family_routes, dict):
        for family, route in source_family_routes.items():
            if not isinstance(route, dict):
                issues.append(f"mechanics/topology.json: source family route {family} must be an object")
                continue
            primary = route.get("primary_mechanic")
            if primary not in expected_set:
                issues.append(f"mechanics/topology.json: source family route {family} has invalid primary mechanic")
                continue
            secondary = route.get("secondary_mechanics", [])
            if secondary is not None:
                if not isinstance(secondary, list) or any(item not in expected_set for item in secondary):
                    issues.append(f"mechanics/topology.json: source family route {family} has invalid secondary mechanics")
            reason = route.get("reason")
            if not isinstance(reason, str) or not reason:
                issues.append(f"mechanics/topology.json: source family route {family} missing reason")
            surface = _source_family_surface(family)
            primary_surfaces = package_source_surfaces.get(primary, set())
            if surface not in primary_surfaces:
                issues.append(
                    f"mechanics/topology.json: source family route {family} points to {primary}, "
                    f"but {surface} is not listed in that package source_surfaces"
                )

    root_readme = repo_root / MECHANICS_DIR / "README.md"
    if root_readme.is_file():
        text = root_readme.read_text(encoding="utf-8")
        for slug in EXPECTED_PACKAGES:
            if f"[`{slug}`]" not in text:
                issues.append(f"mechanics/README.md: missing registry link for {slug}")

    return issues


def _validate_part_directories(
    repo_root: Path,
    slug: str,
    candidate_parts: set[str],
    issues: list[str],
) -> None:
    parts_dir = repo_root / MECHANICS_DIR / slug / "parts"
    if not parts_dir.exists():
        return
    if not parts_dir.is_dir():
        issues.append(f"mechanics/{slug}/parts: parts path must be a directory")
        return

    for file_name in ("AGENTS.md", "README.md"):
        if not (parts_dir / file_name).is_file():
            issues.append(f"mechanics/{slug}/parts/{file_name}: required parts file is missing")

    for part_dir in sorted(path for path in parts_dir.iterdir() if path.is_dir()):
        part = part_dir.name
        if part.startswith(".") or part == "__pycache__":
            continue
        if part not in candidate_parts:
            issues.append(f"mechanics/{slug}/parts/{part}: part is not listed in topology candidate_parts")
        for file_name in ("README.md", "CONTRACT.md", "VALIDATION.md"):
            if not (part_dir / file_name).is_file():
                issues.append(f"mechanics/{slug}/parts/{part}/{file_name}: required part file is missing")


def _validate_active_part_directories(
    repo_root: Path,
    active_part_routes: Any,
    issues: list[str],
) -> None:
    if not isinstance(active_part_routes, dict):
        return

    for parent in EXPECTED_PACKAGES:
        parts_dir = repo_root / MECHANICS_DIR / parent / "parts"
        actual_parts: set[str] = set()
        if parts_dir.is_dir():
            actual_parts = {
                path.name
                for path in parts_dir.iterdir()
                if path.is_dir() and not path.name.startswith(".") and path.name != "__pycache__"
            }

        raw_active_parts = active_part_routes.get(parent, [])
        if not isinstance(raw_active_parts, list):
            continue
        active_parts = {part for part in raw_active_parts if isinstance(part, str)}

        for part in sorted(actual_parts - active_parts):
            issues.append(f"mechanics/topology.json: active_part_routes.{parent} missing existing part {part}")
        for part in sorted(active_parts - actual_parts):
            issues.append(
                f"mechanics/topology.json: active_part_routes.{parent} points to missing part directory {part}"
            )


def _validate_active_part_source_surfaces(
    active_part_routes: Any,
    package_source_surfaces: dict[str, set[str]],
    issues: list[str],
) -> None:
    if not isinstance(active_part_routes, dict):
        return

    for parent, raw_parts in active_part_routes.items():
        if parent not in EXPECTED_PACKAGES or not isinstance(raw_parts, list):
            continue
        surfaces = package_source_surfaces.get(parent, set())
        for part in raw_parts:
            if not isinstance(part, str) or not part:
                continue
            prefix = f"mechanics/{parent}/parts/{part}"
            if not any(surface == prefix or surface.startswith(prefix + "/") for surface in surfaces):
                issues.append(
                    f"mechanics/topology.json: {parent} active part {part} is not listed in source_surfaces"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    issues = validate(args.repo_root)
    if issues:
        print("Mechanics topology validation failed.")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"Mechanics topology validation passed: {len(EXPECTED_PACKAGES)} package(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
