#!/usr/bin/env python3
"""Verify an installed SDK wheel carries the Agon gate routing bridge."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import tomllib
import venv
from importlib.metadata import version
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
RECEIPT_PATH = PART_ROOT / "evidence" / "agon-gate-routing-succession.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed-probe", action="store_true")
    parser.add_argument("--expected-registry-sha256")
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
    wheels = sorted(
        (REPO_ROOT / "dist").glob(f"aoa_sdk-{project_version}-*.whl")
    )
    if len(wheels) != 1:
        raise SystemExit(
            f"expected exactly one aoa-sdk {project_version} wheel under dist/, "
            f"found {len(wheels)}"
        )
    return wheels[0].resolve()


def _installed_probe(expected_registry_sha256: str) -> int:
    from aoa_sdk.control_plane.routing.agon import (
        AGON_GATE_CONFIG_PATH,
        AGON_GATE_REGISTRY_PATH,
        build_agon_gate_routing_registry,
        load_packaged_agon_gate_routing_registry,
    )

    import aoa_sdk.control_plane.routing.agon as agon_module

    module_path = Path(agon_module.__file__).resolve()
    if REPO_ROOT.resolve() in module_path.parents:
        raise SystemExit(f"probe imported Agon bridge from checkout: {module_path}")
    for resource in (AGON_GATE_CONFIG_PATH, AGON_GATE_REGISTRY_PATH):
        if not resource.is_file():
            raise SystemExit(f"installed wheel lacks Agon routing resource: {resource}")
        if REPO_ROOT.resolve() in resource.resolve().parents:
            raise SystemExit(f"probe loaded Agon resource from checkout: {resource}")

    packaged = load_packaged_agon_gate_routing_registry()
    if packaged != build_agon_gate_routing_registry():
        raise SystemExit("installed wheel Agon routing rebuild drifted")
    actual_digest = hashlib.sha256(AGON_GATE_REGISTRY_PATH.read_bytes()).hexdigest()
    if actual_digest != expected_registry_sha256:
        raise SystemExit(
            "installed wheel Agon registry digest drifted: "
            f"expected={expected_registry_sha256}, actual={actual_digest}"
        )
    if packaged["owner_repo"] != "aoa-sdk":
        raise SystemExit("installed wheel Agon registry owner drifted")
    if packaged["center_repo"] != "Agents-of-Abyss":
        raise SystemExit("installed wheel Agon center owner drifted")
    if packaged["trigger_count"] != 12:
        raise SystemExit("installed wheel Agon trigger coverage drifted")
    if any(
        hint["live_protocol"] is not False or hint["runtime_effect"] != "none"
        for hint in packaged["route_hints"]
    ):
        raise SystemExit("installed wheel Agon bridge leaked runtime authority")

    print(
        json.dumps(
            {
                "center_repo": packaged["center_repo"],
                "module_path": str(module_path),
                "owner_repo": packaged["owner_repo"],
                "package_version": version("aoa-sdk"),
                "registry_sha256": actual_digest,
                "route_hint_count": packaged["route_hint_count"],
                "runtime_effect": "none",
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    expected_digest = receipt["sdk_sha256"]["registry"]
    with tempfile.TemporaryDirectory(prefix="aoa-sdk-agon-routing-wheel-") as temp_dir:
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
                "--expected-registry-sha256",
                expected_digest,
            ],
            cwd=probe_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel Agon routing probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        forbidden_checkout_names = {"aoa-routing", "Agents-of-Abyss"}
        present = forbidden_checkout_names & {
            path.name for path in probe_root.iterdir()
        }
        if present:
            raise SystemExit(
                f"clean Agon wheel probe unexpectedly contains: {sorted(present)}"
            )
        print(completed.stdout.strip())
    print(
        "[ok] installed wheel rebuilt the SDK Agon routing bridge without "
        "predecessor or center checkouts"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.installed_probe:
        if not args.expected_registry_sha256:
            raise SystemExit(
                "--installed-probe requires --expected-registry-sha256"
            )
        return _installed_probe(args.expected_registry_sha256)
    return _outer_probe(_wheel_path(args.wheel))


if __name__ == "__main__":
    raise SystemExit(main())
