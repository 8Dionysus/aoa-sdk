#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    ("generate decision indexes", [sys.executable, "scripts/generate_decision_indexes.py", "--check"]),
    ("validate SDK source home", [sys.executable, "scripts/validate_sdk_source_home.py"]),
    ("validate owner-local stats port", [sys.executable, "scripts/validate_local_stats_port.py"]),
    ("validate mechanics topology", [sys.executable, "scripts/validate_mechanics_topology.py"]),
    ("build source topology index", [sys.executable, "scripts/build_source_topology_index.py", "--check"]),
    ("validate source topology index", [sys.executable, "scripts/validate_source_topology_index.py"]),
    ("build workspace control plane", [sys.executable, "scripts/build_workspace_control_plane.py", "--check"]),
    ("validate workspace control plane", [sys.executable, "scripts/validate_workspace_control_plane.py"]),
    ("run tests", [sys.executable, "-m", "pytest", "-q"]),
    (
        "run Ruff",
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            ".",
            "--extend-exclude",
            ".abyss-machine-verifier,.aoa-stats-validator",
        ],
    ),
    ("run mypy", [sys.executable, "-m", "mypy", "src"]),
    ("build package", [sys.executable, "-m", "build"]),
    (
        "verify installed routing shadow wheel",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/"
            "verify_routing_shadow_wheel.py",
        ],
    ),
    (
        "validate OS Abyss package artifact bundle",
        [
            sys.executable,
            "mechanics/release-support/parts/release-audit-publish-helper/scripts/validate_abyss_machine_package_artifact_bundle.py",
        ],
    ),
]


def run_step(label: str, command: list[str]) -> int:
    print(f"[run] {label}: {subprocess.list2cmdline(command)}", flush=True)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=os.environ.copy(),
        check=False,
    )
    if completed.returncode != 0:
        print(f"[error] {label} failed with exit code {completed.returncode}", flush=True)
        return completed.returncode
    print(f"[ok] {label}", flush=True)
    return 0


def main() -> int:
    for label, command in COMMANDS:
        exit_code = run_step(label, command)
        if exit_code != 0:
            return exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
