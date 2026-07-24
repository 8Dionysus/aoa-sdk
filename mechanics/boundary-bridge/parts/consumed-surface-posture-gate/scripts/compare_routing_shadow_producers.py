#!/usr/bin/env python3
"""Run the predecessor and SDK shadow producers on one fixture corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from routing_shadow_fixture_archive import materialized_fixture_archive


PINNED_PREDECESSOR_REF = "7e2fe467ad26aa645b61849001a456dda4562ffc"
PART_ROOT = Path(__file__).resolve().parents[1]
SDK_REPO_ROOT = PART_ROOT.parents[3]
EXPECTED_HASHES_PATH = (
    PART_ROOT / "fixtures" / "routing-shadow" / "expected-hashes.json"
)
OUTPUT_FILENAMES = (
    "aoa_router.min.json",
    "composite_stress_route_hints.min.json",
    "cross_repo_registry.min.json",
    "federation_entrypoints.min.json",
    "kag_source_lift_relation_hints.min.json",
    "owner_layer_shortlist.min.json",
    "pairing_hints.min.json",
    "quest_dispatch_hints.min.json",
    "recommended_paths.min.json",
    "return_navigation_hints.min.json",
    "stats_regrounding_hints.min.json",
    "task_to_surface_hints.json",
    "task_to_tier_hints.json",
    "tiny_model_entrypoints.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare pinned aoa-routing and SDK shadow producer bytes."
    )
    parser.add_argument("--predecessor-root", type=Path, required=True)
    parser.add_argument(
        "--fixture-root",
        type=Path,
        help="Explicit materialized fixture root; defaults to the compact inputs archive.",
    )
    parser.add_argument(
        "--expected-predecessor-ref",
        default=PINNED_PREDECESSOR_REF,
    )
    return parser.parse_args()


def _run(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _common_args(fixture_root: Path, generated_dir: Path) -> list[str]:
    return [
        "--techniques-root",
        str(fixture_root / "aoa-techniques"),
        "--skills-root",
        str(fixture_root / "aoa-skills"),
        "--evals-root",
        str(fixture_root / "aoa-evals"),
        "--memo-root",
        str(fixture_root / "aoa-memo"),
        "--stats-root",
        str(fixture_root / "aoa-stats"),
        "--agents-root",
        str(fixture_root / "aoa-agents"),
        "--aoa-root",
        str(fixture_root / "Agents-of-Abyss"),
        "--playbooks-root",
        str(fixture_root / "aoa-playbooks"),
        "--kag-root",
        str(fixture_root / "aoa-kag"),
        "--tos-root",
        str(fixture_root / "Tree-of-Sophia"),
        "--sdk-root",
        str(fixture_root / "aoa-sdk"),
        "--source-route-root",
        str(fixture_root / "Dionysus"),
        "--profile-root",
        str(fixture_root / "8Dionysus"),
        "--abyss-stack-root",
        str(fixture_root / "abyss-stack"),
        "--generated-dir",
        str(generated_dir),
    ]


def _compare(args: argparse.Namespace, fixture_root: Path) -> int:
    predecessor_root = args.predecessor_root.resolve()
    fixture_root = fixture_root.resolve()
    observed_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=predecessor_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if observed_ref != args.expected_predecessor_ref:
        raise SystemExit(
            f"predecessor ref mismatch: expected {args.expected_predecessor_ref}, "
            f"observed {observed_ref}"
        )

    with tempfile.TemporaryDirectory(prefix="aoa-routing-shadow-parity-") as temp_dir:
        root = Path(temp_dir)
        predecessor_output = root / "predecessor"
        sdk_output = root / "sdk"
        sdk_env = os.environ.copy()
        existing_pythonpath = sdk_env.get("PYTHONPATH")
        source_path = str(SDK_REPO_ROOT / "src")
        sdk_env["PYTHONPATH"] = (
            f"{source_path}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else source_path
        )
        _run(
            [
                sys.executable,
                "scripts/build_router.py",
                *_common_args(fixture_root, predecessor_output),
            ],
            predecessor_root,
        )
        _run(
            [
                sys.executable,
                "-m",
                "aoa_sdk.control_plane.routing.producer",
                *_common_args(fixture_root, sdk_output),
            ],
            SDK_REPO_ROOT,
            env=sdk_env,
        )
        mismatches = [
            filename
            for filename in OUTPUT_FILENAMES
            if (predecessor_output / filename).read_bytes()
            != (sdk_output / filename).read_bytes()
        ]
        if mismatches:
            raise SystemExit(f"routing shadow byte mismatches: {mismatches}")
        actual_hashes = {
            filename: hashlib.sha256(
                (predecessor_output / filename).read_bytes()
            ).hexdigest()
            for filename in OUTPUT_FILENAMES
        }
        expected_hashes_payload = json.loads(
            EXPECTED_HASHES_PATH.read_text(encoding="utf-8")
        )
        if expected_hashes_payload.get("predecessor_ref") != observed_ref:
            raise SystemExit("routing shadow expected-hash predecessor ref drifted")
        expected_hashes = expected_hashes_payload.get("output_sha256")
        if expected_hashes != actual_hashes:
            hash_mismatches = [
                filename
                for filename in OUTPUT_FILENAMES
                if not isinstance(expected_hashes, dict)
                or expected_hashes.get(filename) != actual_hashes[filename]
            ]
            raise SystemExit(
                "routing shadow predecessor output hashes drifted: "
                f"{hash_mismatches}"
            )

    print(
        "[ok] pinned predecessor and SDK shadow producers are byte-identical "
        f"for {len(OUTPUT_FILENAMES)}/{len(OUTPUT_FILENAMES)} outputs"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.fixture_root is not None:
        return _compare(args, args.fixture_root)
    with materialized_fixture_archive("inputs") as fixture_root:
        return _compare(args, fixture_root)


if __name__ == "__main__":
    raise SystemExit(main())
