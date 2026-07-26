#!/usr/bin/env python3
"""Verify an installed SDK wheel can load and run the C2 plan compiler."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import tomllib
import venv
from importlib import resources
from importlib.metadata import version
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
EXAMPLE_ROOT = PART_ROOT / "examples"
EXPECTED_RESOURCES = {
    "playbook-plan-contours-source-lock.v1.json",
    "playbook-plan-contours.schema.json",
    "playbook-plan-contours.v1.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed-probe", action="store_true")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--expected-plan", type=Path)
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


def _installed_probe(fixture_path: Path, expected_plan_path: Path) -> int:
    from aoa_sdk.contracts.control_plane import (
        ProvenanceRef,
        RouteDecision,
        RunPlan,
        RuntimeProfile,
        ScenarioBinding,
        assert_run_plan_digest,
    )
    from aoa_sdk.control_plane.planning import (
        compile_run_plan,
        load_plan_compilation_snapshot,
    )

    import aoa_sdk.control_plane.planning.compiler as compiler_module

    module_path = Path(compiler_module.__file__).resolve()
    if REPO_ROOT.resolve() in module_path.parents:
        raise SystemExit(f"probe imported plan compiler from checkout: {module_path}")

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("schema_version") != ("aoa_control_plane_plan_wheel_smoke_v1"):
        raise SystemExit("installed-wheel smoke fixture schema drifted")
    decision = RouteDecision.model_validate(fixture["decision"])
    scenario = ScenarioBinding.model_validate(fixture["scenario_binding"])
    runtime = RuntimeProfile.model_validate(fixture["runtime_profile"])
    compiler_provenance = ProvenanceRef.model_validate(fixture["compiler_provenance"])
    snapshot = load_plan_compilation_snapshot()
    plan = compile_run_plan(
        decision,
        scenario,
        runtime,
        snapshot,
        compiler_provenance=compiler_provenance,
    )
    expected_plan = RunPlan.model_validate_json(expected_plan_path.read_bytes())
    if plan != expected_plan:
        raise SystemExit(
            "installed wheel compiled bytes differ from the source golden plan"
        )
    assert_run_plan_digest(plan)
    default_plan = compile_run_plan(
        decision,
        scenario,
        runtime,
        snapshot,
    )
    repeated_default_plan = compile_run_plan(
        decision,
        scenario,
        runtime,
        snapshot,
    )
    if default_plan != repeated_default_plan:
        raise SystemExit(
            "installed wheel default compiler provenance is not repeatable"
        )
    assert_run_plan_digest(default_plan)
    module_digest = "sha256:" + hashlib.sha256(module_path.read_bytes()).hexdigest()
    if (
        default_plan.provenance.artifact_digest != module_digest
        or default_plan.provenance.source_ref
        != f"aoa_control_plane_plan_compiler_v1@{module_digest}"
    ):
        raise SystemExit(
            "installed wheel default compiler provenance does not bind "
            "the installed module bytes"
        )

    data_root = resources.files("aoa_sdk.control_plane.planning").joinpath("data")
    packaged_resources = {item.name for item in data_root.iterdir() if item.is_file()}
    missing_resources = EXPECTED_RESOURCES - packaged_resources
    if missing_resources:
        raise SystemExit(
            "installed wheel lacks plan compiler resources: "
            f"{sorted(missing_resources)}"
        )
    if (
        snapshot.source_lock.owner_source_ref
        != "056cac249a353ae94abedbd4048e6730f70c064d"
    ):
        raise SystemExit("installed wheel owner contour source ref drifted")

    print(
        json.dumps(
            {
                "module_path": str(module_path),
                "owner_source_ref": snapshot.source_lock.owner_source_ref,
                "package_version": version("aoa-sdk"),
                "default_plan_digest": default_plan.plan_digest,
                "plan_digest": plan.plan_digest,
                "resource_count": len(EXPECTED_RESOURCES),
                "scenario_id": plan.scenario_binding.scenario.scenario_id,
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    fixture_path = EXAMPLE_ROOT / "installed-wheel-smoke.inputs.json"
    expected_plan_path = EXAMPLE_ROOT / "bounded-preview-pruned.run-plan.json"
    if not fixture_path.is_file() or not expected_plan_path.is_file():
        raise SystemExit("C2 installed-wheel fixtures are missing")

    with tempfile.TemporaryDirectory(prefix="aoa-sdk-plan-compiler-wheel-") as temp_dir:
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
                "--fixture",
                str(fixture_path),
                "--expected-plan",
                str(expected_plan_path),
            ],
            cwd=probe_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel C2 plan compiler probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        if any(path.name == "aoa-playbooks" for path in probe_root.iterdir()):
            raise SystemExit("clean wheel probe unexpectedly contains aoa-playbooks")
        print(completed.stdout.strip())
    print(
        "[ok] installed wheel loaded admitted C2 resources and reproduced "
        "the deterministic plan without an aoa-playbooks checkout"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.installed_probe:
        if args.fixture is None or args.expected_plan is None:
            raise SystemExit("--installed-probe requires --fixture and --expected-plan")
        return _installed_probe(
            args.fixture.resolve(),
            args.expected_plan.resolve(),
        )
    return _outer_probe(_wheel_path(args.wheel))


if __name__ == "__main__":
    raise SystemExit(main())
