#!/usr/bin/env python3
"""Verify the installed golden chain in a federation without aoa-routing."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_CHAIN = PART_ROOT / "scripts" / "verify_golden_scenario_chain.py"
REQUIRED_REPOS = (
    "aoa-sdk",
    "aoa-agents",
    "aoa-skills",
    "aoa-playbooks",
    "aoa-evals",
    "aoa-memo",
)
FORBIDDEN_REPO = "aoa-routing"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-federation", type=Path, required=True)
    parser.add_argument("--routing-bundle-root", type=Path, required=True)
    return parser.parse_args()


def _require_directory(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"{label} is not a directory: {resolved}")
    return resolved


def main() -> int:
    args = parse_args()
    source_federation = _require_directory(
        args.source_federation,
        "source federation",
    )
    routing_bundle_root = _require_directory(
        args.routing_bundle_root,
        "routing bundle root",
    )
    missing = [
        repo for repo in REQUIRED_REPOS if not (source_federation / repo).is_dir()
    ]
    if missing:
        raise SystemExit(f"required owner repositories are missing: {missing}")

    with tempfile.TemporaryDirectory(
        prefix="aoa-sdk-clean-federation-",
    ) as temp_dir:
        clean_root = Path(temp_dir)
        for repo in REQUIRED_REPOS:
            (clean_root / repo).symlink_to(
                source_federation / repo,
                target_is_directory=True,
            )
        if (clean_root / FORBIDDEN_REPO).exists():
            raise SystemExit("clean federation unexpectedly contains aoa-routing")

        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["AOA_SDK_FEDERATION_ROOT"] = str(clean_root)
        environment["AOA_SDK_ROUTING_BUNDLE_ROOT"] = str(routing_bundle_root)
        result = subprocess.run(
            [
                sys.executable,
                str(GOLDEN_CHAIN),
                "--workspace",
                str(clean_root / "aoa-sdk"),
            ],
            cwd=clean_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(
                "clean-federation golden chain failed: "
                + (result.stderr.strip() or result.stdout.strip())
            )
        try:
            child_report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"clean-federation verifier returned invalid JSON: {exc}"
            ) from exc

    print(
        json.dumps(
            {
                "forbidden_repo": FORBIDDEN_REPO,
                "forbidden_repo_present": False,
                "linked_owner_repos": list(REQUIRED_REPOS),
                "schema_version": "aoa_sdk_clean_federation_chain_v1",
                "verdict": child_report.get("verdict"),
                "verified_scenarios": sorted(
                    child_report.get("scenarios", {}).keys()
                ),
                "wheel_module_path": child_report.get("package", {}).get(
                    "module_path"
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
