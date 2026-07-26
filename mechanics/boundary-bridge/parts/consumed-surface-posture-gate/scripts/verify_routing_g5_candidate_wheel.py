#!/usr/bin/env python3
"""Verify an installed SDK wheel can build the non-publishing G5 candidate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import tomllib
import venv
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from routing_shadow_fixture_archive import materialized_fixture_archive


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
PINNED_PREDECESSOR_REF = "97f60de1b5992ef6bf5ff0f051bd452d940d9a85"
EXPECTED_ARTIFACT_COUNT = 14
EXPECTED_ASSEMBLY_FILE_COUNT = 27
EXPECTED_RUNTIME_REQUIRED_FILE_COUNT = 23
EXPECTED_SCHEMA_COUNT = 21


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install an aoa-sdk wheel and verify its non-publishing routing "
            "G5 candidate package."
        )
    )
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed-probe", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def _wheel_path(explicit: Path | None) -> Path:
    if explicit is not None:
        wheel = explicit.resolve()
        if not wheel.is_file():
            raise SystemExit(f"wheel does not exist: {wheel}")
        return wheel
    project = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    project_version = project["project"]["version"]
    wheels = sorted((REPO_ROOT / "dist").glob(f"aoa_sdk-{project_version}-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(
            f"expected exactly one aoa-sdk {project_version} wheel under dist/, "
            f"found {len(wheels)}"
        )
    return wheels[0].resolve()


def _fixture_inputs(root: Path):
    from aoa_sdk.control_plane.routing.shadow import RoutingProducerInputs

    return RoutingProducerInputs(
        techniques_root=root / "aoa-techniques",
        skills_root=root / "aoa-skills",
        evals_root=root / "aoa-evals",
        memo_root=root / "aoa-memo",
        stats_root=root / "aoa-stats",
        agents_root=root / "aoa-agents",
        aoa_root=root / "Agents-of-Abyss",
        playbooks_root=root / "aoa-playbooks",
        kag_root=root / "aoa-kag",
        tos_root=root / "Tree-of-Sophia",
        sdk_root=root / "aoa-sdk",
        source_route_root=root / "Dionysus",
        profile_root=root / "8Dionysus",
        abyss_stack_root=root / "abyss-stack",
    )


def _bind_fixture_to_clean_git_refs(inputs) -> dict[str, str]:
    refs: dict[str, str] = {}
    for owner, root in sorted(inputs.source_roots().items()):
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "AoA SDK Probe"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "config",
                "user.email",
                "aoa-sdk-probe@example.invalid",
            ],
            check=True,
        )
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "fixture"],
            check=True,
        )
        refs[owner] = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    return refs


def _installed_probe(output_dir: Path) -> int:
    from aoa_sdk.control_plane.routing.candidate import (
        CANDIDATE_ASSEMBLY_FILES,
        RUNTIME_COMPATIBILITY_ROOT,
        RUNTIME_REQUIRED_FILES,
        build_g5_candidate_bundle,
        validate_g5_candidate_bundle,
    )
    from aoa_sdk.control_plane.routing.validator import SCHEMA_ROOT

    with materialized_fixture_archive("inputs") as hydrated_fixture_root:
        inputs = _fixture_inputs(hydrated_fixture_root)
        source_refs = _bind_fixture_to_clean_git_refs(inputs)
        bundle = build_g5_candidate_bundle(
            inputs,
            output_dir,
            predecessor_source_ref=PINNED_PREDECESSOR_REF,
            sdk_source_ref=source_refs["aoa-sdk"],
            input_source_refs=source_refs,
            observed_at=datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc),
        )
        validate_g5_candidate_bundle(bundle, inputs)

    import aoa_sdk.control_plane.routing.candidate as candidate_module

    module_path = Path(candidate_module.__file__).resolve()
    if REPO_ROOT.resolve() in module_path.parents:
        raise SystemExit(f"probe imported routing source from checkout: {module_path}")
    packaged_schemas = sorted(SCHEMA_ROOT.glob("*.json"))
    packaged_runtime_docs = sorted(RUNTIME_COMPATIBILITY_ROOT.glob("*.md"))
    if len(packaged_schemas) != EXPECTED_SCHEMA_COUNT:
        raise SystemExit(
            f"expected {EXPECTED_SCHEMA_COUNT} packaged routing schemas, "
            f"found {len(packaged_schemas)}"
        )
    if {path.name for path in packaged_runtime_docs} != {
        "FEDERATION_ENTRY_ABI.md",
        "RECURRENCE_NAVIGATION_BOUNDARY.md",
    }:
        raise SystemExit("installed wheel routing runtime compatibility docs drifted")
    if len(bundle.artifact_sha256) != EXPECTED_ARTIFACT_COUNT:
        raise SystemExit("installed wheel G5 candidate artifact count drifted")
    if len(CANDIDATE_ASSEMBLY_FILES) != EXPECTED_ASSEMBLY_FILE_COUNT:
        raise SystemExit("installed wheel G5 candidate assembly count drifted")
    if len(RUNTIME_REQUIRED_FILES) != EXPECTED_RUNTIME_REQUIRED_FILE_COUNT:
        raise SystemExit("installed wheel runtime-required file count drifted")
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    if set(provenance["g5_authority"].values()) != {False}:
        raise SystemExit("installed wheel candidate unexpectedly carries G5 authority")
    print(
        json.dumps(
            {
                "artifact_count": len(bundle.artifact_sha256),
                "assembly_file_count": len(CANDIDATE_ASSEMBLY_FILES),
                "g5_authority": False,
                "module_path": str(module_path),
                "package_version": version("aoa-sdk"),
                "runtime_required_file_count": len(RUNTIME_REQUIRED_FILES),
                "schema_count": len(packaged_schemas),
                "state": provenance["state"],
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    with tempfile.TemporaryDirectory(
        prefix="aoa-sdk-routing-g5-wheel-"
    ) as temp_dir:
        probe_root = Path(temp_dir)
        venv_root = probe_root / "venv"
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_root)
        python = venv_root / "bin" / "python"
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "--disable-pip-version-check",
                "install",
                str(wheel),
            ],
            cwd=probe_root,
            env=environment,
            check=True,
        )
        completed = subprocess.run(
            [
                str(python),
                str(Path(__file__).resolve()),
                "--installed-probe",
                "--output-dir",
                str(probe_root / "candidate"),
            ],
            cwd=probe_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel G5 candidate probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        if any(path.name == "aoa-routing" for path in probe_root.iterdir()):
            raise SystemExit("clean wheel probe unexpectedly contains aoa-routing")
        print(completed.stdout.strip())
    print(
        "[ok] installed wheel produced and validated a 14/14 "
        "non-publishing SDK G5 candidate"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.installed_probe:
        if args.output_dir is None:
            raise SystemExit("--installed-probe requires --output-dir")
        return _installed_probe(args.output_dir.resolve())
    return _outer_probe(_wheel_path(args.wheel))


if __name__ == "__main__":
    raise SystemExit(main())
