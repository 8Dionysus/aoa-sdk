#!/usr/bin/env python3
"""Validate the aoa-sdk mechanics skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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

DEMOTED_PARENT_CANDIDATES = (
    "workspace-topology",
    "compatibility",
    "skill-routing",
    "surface-detection",
    "closeout",
    "a2a-return",
    "codex-plane",
)

REQUIRED_ROOT_FILES = (
    MECHANICS_DIR / "AGENTS.md",
    MECHANICS_DIR / "README.md",
    MECHANICS_DIR / "TOPOLOGY_PREP.md",
    TOPOLOGY_PATH,
)

REQUIRED_PACKAGE_FILES = ("AGENTS.md", "README.md", "PARTS.md", "PROVENANCE.md")

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


def _source_families(repo_root: Path) -> set[str]:
    source_root = repo_root / "src" / "aoa_sdk"
    families: set[str] = set()
    root_files = False
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


def validate(repo_root: Path = REPO_ROOT) -> list[str]:
    repo_root = repo_root.resolve()
    issues: list[str] = []

    for rel_path in REQUIRED_ROOT_FILES:
        if not (repo_root / rel_path).is_file():
            issues.append(f"{_rel(rel_path)}: required root mechanics file is missing")

    topology = _read_json(repo_root / TOPOLOGY_PATH, issues)
    if not topology:
        return issues

    if topology.get("schema_version") != "aoa_sdk_mechanics_topology_v1":
        issues.append("mechanics/topology.json: unexpected schema_version")
    if topology.get("status") != "skeleton":
        issues.append("mechanics/topology.json: status must be skeleton")
    if topology.get("payload_moved") is not False:
        issues.append("mechanics/topology.json: payload_moved must be false")
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

    demoted = topology.get("demoted_parent_candidates")
    if not isinstance(demoted, dict):
        issues.append("mechanics/topology.json: demoted_parent_candidates must be an object")
    else:
        for slug in DEMOTED_PARENT_CANDIDATES:
            if slug not in demoted:
                issues.append(f"mechanics/topology.json: missing demoted parent candidate {slug}")
            if (repo_root / MECHANICS_DIR / slug).exists():
                issues.append(f"mechanics/{slug}: demoted parent candidate must not exist as top-level package")

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

        validation = item.get("validation")
        if not isinstance(validation, list) or not validation:
            issues.append(f"mechanics/topology.json: {slug} has no validation routes")

    expected = list(EXPECTED_PACKAGES)
    if package_slugs != expected:
        issues.append(
            "mechanics/topology.json: package order or set mismatch; "
            f"expected {expected!r}, found {package_slugs!r}"
        )

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

    topology_prep = repo_root / MECHANICS_DIR / "TOPOLOGY_PREP.md"
    if topology_prep.is_file():
        text = topology_prep.read_text(encoding="utf-8")
        if "tracked files: 1056" not in text:
            issues.append("mechanics/TOPOLOGY_PREP.md: missing tracked-file inventory")
        for slug in EXPECTED_PACKAGES:
            if f"`{slug}`" not in text:
                issues.append(f"mechanics/TOPOLOGY_PREP.md: missing package {slug}")
        for family in _source_families(repo_root):
            label = "root package" if family == "root-package" else f"`{family}`"
            if label not in text:
                issues.append(f"mechanics/TOPOLOGY_PREP.md: missing source family {family}")

    return issues


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
