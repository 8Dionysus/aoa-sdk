#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_MODE_ENV = "AOA_SDK_VALIDATION_MODE"
GRAPH_RUNNER = (
    "mechanics/release-support/parts/validation-evidence-graph/"
    "scripts/validation_graph.py"
)

COMMANDS = [
    (
        "generate decision indexes",
        [sys.executable, "scripts/generate_decision_indexes.py", "--check"],
    ),
    (
        "validate SDK source home",
        [sys.executable, "scripts/validate_sdk_source_home.py"],
    ),
    (
        "generate organ access schemas",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/organ-access-control-plane/scripts/"
            "generate_organ_access_schemas.py",
            "--check",
        ],
    ),
    (
        "generate organ access examples",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/organ-access-control-plane/scripts/"
            "generate_organ_access_example.py",
            "--check",
        ],
    ),
    (
        "validate owner-local stats port",
        [sys.executable, "scripts/validate_local_stats_port.py"],
    ),
    (
        "validate mechanics topology",
        [sys.executable, "scripts/validate_mechanics_topology.py"],
    ),
    (
        "build source topology index",
        [sys.executable, "scripts/build_source_topology_index.py", "--check"],
    ),
    (
        "validate source topology index",
        [sys.executable, "scripts/validate_source_topology_index.py"],
    ),
    (
        "validate routing succession E1 cost evidence",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
            "scripts/measure_routing_succession_e1.py",
            "--check",
        ],
    ),
    (
        "build workspace control plane",
        [sys.executable, "scripts/build_workspace_control_plane.py", "--check"],
    ),
    (
        "validate workspace control plane",
        [sys.executable, "scripts/validate_workspace_control_plane.py"],
    ),
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
        "verify installed routing G5 canonical wheel",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/"
            "verify_routing_g5_canonical_wheel.py",
        ],
    ),
    (
        "verify installed C2 plan compilation wheel",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/plan-compilation-control-plane/"
            "scripts/verify_plan_compilation_wheel.py",
        ],
    ),
    (
        "verify installed C3 Runner wheel",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
            "scripts/verify_runner_wheel.py",
        ],
    ),
    (
        "verify installed C5 evidence chain wheel",
        [
            sys.executable,
            "mechanics/boundary-bridge/parts/evidence-closeout-chain/"
            "scripts/verify_evidence_chain_wheel.py",
        ],
    ),
    (
        "verify installed Agon gate routing wheel",
        [
            sys.executable,
            "mechanics/agon/parts/gate-routing-bridge/scripts/"
            "verify_agon_gate_routing_wheel.py",
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
        print(
            f"[error] {label} failed with exit code {completed.returncode}", flush=True
        )
        return completed.returncode
    print(f"[ok] {label}", flush=True)
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the complete aoa-sdk validation gate.")
    parser.add_argument(
        "--mode",
        choices=("graph", "serial"),
        default=os.environ.get(VALIDATION_MODE_ENV, "graph"),
        help=(
            "graph is the accepted bounded scheduler; serial is the exact "
            f"completeness oracle and rollback (default: ${VALIDATION_MODE_ENV} or graph)"
        ),
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Atomic full-graph receipt path; serial rollback emits logs only.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Explicit graph worker override; the accepted manifest default is three.",
    )
    return parser.parse_args(argv)


def run_serial() -> int:
    for label, command in COMMANDS:
        exit_code = run_step(label, command)
        if exit_code != 0:
            return exit_code
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"[mode] {args.mode}", flush=True)
    if args.mode == "serial":
        if args.receipt is not None:
            print("[receipt] serial rollback emits no graph receipt", flush=True)
        if args.max_workers is not None:
            print("[workers] serial rollback ignores graph worker overrides", flush=True)
        return run_serial()

    command = [sys.executable, GRAPH_RUNNER, "--profile", "full"]
    if args.receipt is not None:
        command.extend(("--receipt", str(args.receipt)))
    if args.max_workers is not None:
        command.extend(("--max-workers", str(args.max_workers)))
    return run_step("run full claim/evidence validation graph", command)


if __name__ == "__main__":
    raise SystemExit(main())
