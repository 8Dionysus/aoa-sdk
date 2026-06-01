#!/usr/bin/env python3
"""Validate the aoa-sdk SDK source-home topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SDK_DIR = Path("sdk")
MANIFEST_PATH = SDK_DIR / "source_home.manifest.json"

EXPECTED_SCHEMA_VERSION = "aoa_sdk_source_home_v1"
EXPECTED_BRANCHES = {
    "public_interface": {
        "path": "sdk/public-interface",
        "owner_surface": "sdk/public-interface/AGENTS.md",
        "families": {
            "python_api_contract",
            "cli_contract",
            "model_contract",
        },
    },
    "facade_boundary": {
        "path": "sdk/facade-boundary",
        "owner_surface": "sdk/facade-boundary/AGENTS.md",
        "families": {
            "sibling_surface_readers",
            "compatibility_policy",
            "truth_label_posture",
        },
    },
    "runtime_entry": {
        "path": "sdk/runtime-entry",
        "owner_surface": "sdk/runtime-entry/AGENTS.md",
        "families": {
            "workspace_context",
            "codex_entrypoints",
            "closeout_entrypoints",
        },
    },
    "distribution": {
        "path": "sdk/distribution",
        "owner_surface": "sdk/distribution/AGENTS.md",
        "families": {
            "package_contract",
            "release_posture",
            "public_support",
        },
    },
}
REQUIRED_ROOT_FILES = (
    SDK_DIR / "AGENTS.md",
    SDK_DIR / "README.md",
    SDK_DIR / "SDK_SHAPE.md",
    MANIFEST_PATH,
)
REQUIRED_BRANCH_FILES = ("AGENTS.md", "README.md")
REQUIRED_FAMILY_FILES = ("README.md",)
FORBIDDEN_SDK_FILES = ("PARTS.md",)


def _read_json(path: Path, issues: list[str]) -> dict[str, Any]:
    if not path.is_file():
        issues.append(f"{path.as_posix()}: manifest is missing")
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


def _path_exists(repo_root: Path, rel_path: str) -> bool:
    return (repo_root / rel_path).exists()


def _validate_text_snippet(
    repo_root: Path,
    rel_path: str,
    snippets: tuple[str, ...],
    issues: list[str],
) -> None:
    path = repo_root / rel_path
    if not path.is_file():
        issues.append(f"{rel_path}: required file is missing")
        return
    text = path.read_text(encoding="utf-8")
    for snippet in snippets:
        if snippet not in text:
            issues.append(f"{rel_path}: missing required snippet {snippet!r}")


def validate(repo_root: Path = REPO_ROOT) -> list[str]:
    repo_root = repo_root.resolve()
    issues: list[str] = []

    for rel_path in REQUIRED_ROOT_FILES:
        if not (repo_root / rel_path).is_file():
            issues.append(f"{rel_path.as_posix()}: required SDK source-home file is missing")

    for file_name in FORBIDDEN_SDK_FILES:
        if (repo_root / SDK_DIR / file_name).exists():
            issues.append(f"sdk/{file_name}: sdk/ must not use mechanics PARTS.md vocabulary")

    _validate_text_snippet(
        repo_root,
        "sdk/AGENTS.md",
        (
            "source-authored SDK home",
            "Do not add `PARTS.md` to `sdk/`",
            "python scripts/validate_sdk_source_home.py",
        ),
        issues,
    )
    _validate_text_snippet(
        repo_root,
        "sdk/SDK_SHAPE.md",
        (
            "public-interface/",
            "facade-boundary/",
            "runtime-entry/",
            "distribution/",
            "Do not add `PARTS.md`",
        ),
        issues,
    )

    manifest = _read_json(repo_root / MANIFEST_PATH, issues)
    if not manifest:
        return issues

    if manifest.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        issues.append(f"{MANIFEST_PATH.as_posix()}: unexpected schema_version")
    if manifest.get("owner_repo") != "aoa-sdk":
        issues.append(f"{MANIFEST_PATH.as_posix()}: owner_repo must be aoa-sdk")
    if manifest.get("home") != "sdk/":
        issues.append(f"{MANIFEST_PATH.as_posix()}: home must be sdk/")

    branches = manifest.get("branches")
    if not isinstance(branches, list):
        issues.append(f"{MANIFEST_PATH.as_posix()}: branches must be a list")
        branches = []

    seen_branch_ids: set[str] = set()
    manifest_branch_families: dict[str, set[str]] = {}
    for branch in branches:
        if not isinstance(branch, dict):
            issues.append(f"{MANIFEST_PATH.as_posix()}: each branch must be an object")
            continue
        branch_id = branch.get("id")
        if branch_id not in EXPECTED_BRANCHES:
            issues.append(f"{MANIFEST_PATH.as_posix()}: unexpected branch id {branch_id!r}")
            continue
        expected = EXPECTED_BRANCHES[branch_id]
        seen_branch_ids.add(branch_id)

        path = branch.get("path")
        if path != expected["path"]:
            issues.append(f"{MANIFEST_PATH.as_posix()}: branch {branch_id} has wrong path {path!r}")
        owner_surface = branch.get("owner_surface")
        if owner_surface != expected["owner_surface"]:
            issues.append(
                f"{MANIFEST_PATH.as_posix()}: branch {branch_id} has wrong owner_surface {owner_surface!r}"
            )
        if isinstance(path, str):
            branch_dir = repo_root / path
            if not branch_dir.is_dir():
                issues.append(f"{path}: branch directory is missing")
            else:
                for file_name in REQUIRED_BRANCH_FILES:
                    if not (branch_dir / file_name).is_file():
                        issues.append(f"{path}/{file_name}: required branch file is missing")
        if isinstance(owner_surface, str) and not _path_exists(repo_root, owner_surface):
            issues.append(f"{owner_surface}: branch owner surface is missing")

        families = branch.get("families")
        if not isinstance(families, list):
            issues.append(f"{MANIFEST_PATH.as_posix()}: branch {branch_id} families must be a list")
            families = []
        family_set = {family for family in families if isinstance(family, str)}
        manifest_branch_families[branch_id] = family_set
        if family_set != expected["families"]:
            issues.append(
                f"{MANIFEST_PATH.as_posix()}: branch {branch_id} families mismatch; "
                f"expected {sorted(expected['families'])!r}, found {sorted(family_set)!r}"
            )

    missing_branches = sorted(set(EXPECTED_BRANCHES) - seen_branch_ids)
    for branch_id in missing_branches:
        issues.append(f"{MANIFEST_PATH.as_posix()}: missing branch {branch_id}")

    families = manifest.get("families")
    if not isinstance(families, list):
        issues.append(f"{MANIFEST_PATH.as_posix()}: families must be a list")
        families = []

    expected_family_ids = {
        family_id
        for branch in EXPECTED_BRANCHES.values()
        for family_id in branch["families"]
    }
    seen_family_ids: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            issues.append(f"{MANIFEST_PATH.as_posix()}: each family must be an object")
            continue
        family_id = family.get("id")
        if not isinstance(family_id, str) or not family_id:
            issues.append(f"{MANIFEST_PATH.as_posix()}: family missing id")
            continue
        seen_family_ids.add(family_id)
        if family_id not in expected_family_ids:
            issues.append(f"{MANIFEST_PATH.as_posix()}: unexpected family id {family_id!r}")

        branch_id = family.get("branch")
        if branch_id not in EXPECTED_BRANCHES:
            issues.append(f"{MANIFEST_PATH.as_posix()}: family {family_id} has invalid branch {branch_id!r}")
        elif family_id not in manifest_branch_families.get(branch_id, set()):
            issues.append(
                f"{MANIFEST_PATH.as_posix()}: family {family_id} is not declared by branch {branch_id}"
            )

        path = family.get("path")
        if not isinstance(path, str) or not path.startswith("sdk/"):
            issues.append(f"{MANIFEST_PATH.as_posix()}: family {family_id} has invalid path")
        else:
            family_dir = repo_root / path
            if not family_dir.is_dir():
                issues.append(f"{path}: family directory is missing")
            for file_name in REQUIRED_FAMILY_FILES:
                if not (family_dir / file_name).is_file():
                    issues.append(f"{path}/{file_name}: required family file is missing")

        owner_surface = family.get("owner_surface")
        if not isinstance(owner_surface, str) or not _path_exists(repo_root, owner_surface):
            issues.append(f"{MANIFEST_PATH.as_posix()}: family {family_id} owner_surface is missing")

        for route_key in ("implementation_routes", "mechanic_routes"):
            raw_routes = family.get(route_key)
            if not isinstance(raw_routes, list) or not raw_routes:
                issues.append(f"{MANIFEST_PATH.as_posix()}: family {family_id} has no {route_key}")
                continue
            for rel_path in raw_routes:
                if not isinstance(rel_path, str) or not rel_path:
                    issues.append(f"{MANIFEST_PATH.as_posix()}: family {family_id} has invalid {route_key}")
                elif not _path_exists(repo_root, rel_path):
                    issues.append(
                        f"{MANIFEST_PATH.as_posix()}: family {family_id} missing {route_key} path {rel_path}"
                    )

        validators = family.get("validators")
        if not isinstance(validators, list) or "scripts/validate_sdk_source_home.py" not in validators:
            issues.append(
                f"{MANIFEST_PATH.as_posix()}: family {family_id} must include scripts/validate_sdk_source_home.py"
            )

    missing_families = sorted(expected_family_ids - seen_family_ids)
    for family_id in missing_families:
        issues.append(f"{MANIFEST_PATH.as_posix()}: missing family {family_id}")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    issues = validate(args.repo_root)
    if issues:
        print("SDK source-home validation failed.")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"SDK source-home validation passed: {len(EXPECTED_BRANCHES)} branch(es).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
