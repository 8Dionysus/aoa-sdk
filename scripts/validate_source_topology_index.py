#!/usr/bin/env python3
"""Validate the generated source topology index for src/aoa_sdk."""

from __future__ import annotations

import json
from typing import Any

from source_topology_common import (
    ARTIFACT_TYPE,
    REPO_ROOT,
    SCHEMA_VERSION,
    SOURCE_TOPOLOGY_PATH,
    build_payload,
)


def _walk_packages(package: dict[str, Any]) -> list[dict[str, Any]]:
    packages = [package]
    for child in package["packages"]:
        packages.extend(_walk_packages(child))
    return packages


def _walk_modules(package: dict[str, Any]) -> list[dict[str, Any]]:
    modules = list(package["modules"])
    for child in package["packages"]:
        modules.extend(_walk_modules(child))
    return modules


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    expected = build_payload()
    current = json.loads(SOURCE_TOPOLOGY_PATH.read_text(encoding="utf-8"))
    _require(current == expected, "generated/source_topology.min.json does not match the canonical rebuild")
    _require(current.get("schema_version") == SCHEMA_VERSION, "source topology index has wrong schema_version")
    _require(current.get("artifact_type") == ARTIFACT_TYPE, "source topology index has wrong artifact_type")
    _require(current.get("source_root") == "src/aoa_sdk", "source topology index has wrong source_root")
    _require(
        current.get("boundary_note", "").startswith("Generated read-model only"),
        "source topology index must publish read-model boundary",
    )

    tree = current.get("tree")
    _require(isinstance(tree, dict), "source topology index tree must be an object")
    packages = _walk_packages(tree)
    modules = _walk_modules(tree)
    package_paths = {package["path"] for package in packages}
    module_paths = {module["path"] for module in modules}
    _require(current.get("package_count") == len(packages), "source topology package_count mismatch")
    _require(current.get("module_count") == len(modules), "source topology module_count mismatch")
    _require("src/aoa_sdk/checkpoints/topology" in package_paths, "checkpoint topology package must be indexed")
    _require("src/aoa_sdk/checkpoints/topology/paths.py" in module_paths, "checkpoint topology paths module must be indexed")
    _require(not any("__pycache__" in path for path in package_paths | module_paths), "cache paths must not be indexed")

    for node in [*packages, *modules]:
        _require(isinstance(node.get("route_key"), str) and node["route_key"], f"{node['path']}: missing route_key")
        _require(isinstance(node.get("role"), str) and node["role"], f"{node['path']}: missing role")
        _require(isinstance(node.get("next_route"), str) and node["next_route"], f"{node['path']}: missing next_route")
        evidence_refs = node.get("evidence_refs")
        _require(isinstance(evidence_refs, list) and evidence_refs, f"{node['path']}: missing evidence_refs")
        for ref in evidence_refs:
            _require(isinstance(ref, str), f"{node['path']}: evidence_refs must contain strings")
            _require((REPO_ROOT / ref).exists(), f"{node['path']}: missing evidence ref {ref}")

    print("[ok] validated generated/source_topology.min.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
