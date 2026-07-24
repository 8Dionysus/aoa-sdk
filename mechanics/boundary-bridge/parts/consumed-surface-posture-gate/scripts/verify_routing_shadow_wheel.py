#!/usr/bin/env python3
"""Verify the installed SDK wheel can build and validate the shadow bundle."""

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
EXPECTED_HASHES_PATH = (
    PART_ROOT / "fixtures" / "routing-shadow" / "expected-hashes.json"
)
PINNED_PREDECESSOR_REF = "7e2fe467ad26aa645b61849001a456dda4562ffc"
SOURCE_REFS = {
    "aoa-techniques": "1" * 64,
    "aoa-skills": "2" * 64,
    "aoa-evals": "3" * 64,
    "aoa-memo": "4" * 64,
    "aoa-stats": "5" * 64,
    "aoa-agents": "6" * 64,
    "Agents-of-Abyss": "7" * 64,
    "aoa-playbooks": "8" * 64,
    "aoa-kag": "9" * 64,
    "Tree-of-Sophia": "a" * 64,
    "aoa-sdk": "b" * 64,
    "Dionysus": "c" * 64,
    "8Dionysus": "d" * 64,
    "abyss-stack": "e" * 64,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install an aoa-sdk wheel and verify its routing shadow package."
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
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = project["project"]["version"]
    wheels = sorted((REPO_ROOT / "dist").glob(f"aoa_sdk-{project_version}-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(
            f"expected exactly one aoa-sdk {project_version} wheel under dist/, "
            f"found {len(wheels)}"
        )
    return wheels[0].resolve()


def _installed_probe(output_dir: Path) -> int:
    from aoa_sdk.control_plane.routing.shadow import (
        RoutingProducerInputs,
        build_shadow_bundle,
        validate_shadow_bundle,
    )
    from aoa_sdk.control_plane.routing.validator import SCHEMA_ROOT

    def fixture_inputs(root: Path) -> RoutingProducerInputs:
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

    with materialized_fixture_archive("inputs") as hydrated_fixture_root:
        inputs = fixture_inputs(hydrated_fixture_root)
        bundle = build_shadow_bundle(
            inputs,
            output_dir,
            predecessor_source_ref=PINNED_PREDECESSOR_REF,
            sdk_source_ref="0" * 64,
            input_source_refs=SOURCE_REFS,
            observed_at=datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
        )
        validate_shadow_bundle(bundle, inputs)
        expected_hashes_payload = json.loads(
            EXPECTED_HASHES_PATH.read_text(encoding="utf-8")
        )
        if expected_hashes_payload.get("predecessor_ref") != PINNED_PREDECESSOR_REF:
            raise SystemExit("installed wheel expected-hash predecessor ref drifted")
        if bundle.artifact_sha256 != expected_hashes_payload.get("output_sha256"):
            raise SystemExit(
                "installed wheel output hashes differ from pinned predecessor"
            )

    import aoa_sdk.control_plane.routing.shadow as shadow_module

    module_path = Path(shadow_module.__file__).resolve()
    if REPO_ROOT.resolve() in module_path.parents:
        raise SystemExit(f"probe imported routing source from checkout: {module_path}")
    packaged_schemas = sorted(SCHEMA_ROOT.glob("*.json"))
    if len(packaged_schemas) != 17:
        raise SystemExit(
            f"expected 17 packaged routing schemas, found {len(packaged_schemas)}"
        )
    print(
        json.dumps(
            {
                "artifact_count": len(bundle.artifact_sha256),
                "module_path": str(module_path),
                "package_version": version("aoa-sdk"),
                "schema_count": len(packaged_schemas),
                "sidecar": bundle.provenance_path.name,
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="aoa-sdk-routing-wheel-") as temp_dir:
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
                str(probe_root / "shadow"),
            ],
            cwd=probe_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        if any(path.name == "aoa-routing" for path in probe_root.iterdir()):
            raise SystemExit("clean wheel probe unexpectedly contains aoa-routing")
        print(completed.stdout.strip())
    print("[ok] installed wheel produced and validated 14/14 shadow artifacts")
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
