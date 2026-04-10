#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    ("build workspace control plane", [sys.executable, "scripts/build_workspace_control_plane.py", "--check"]),
    ("validate workspace control plane", [sys.executable, "scripts/validate_workspace_control_plane.py"]),
    ("run tests", [sys.executable, "-m", "pytest", "-q"]),
    ("run Ruff", [sys.executable, "-m", "ruff", "check", "."]),
    ("run mypy", [sys.executable, "-m", "mypy", "src"]),
    ("build package", [sys.executable, "-m", "build"]),
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
