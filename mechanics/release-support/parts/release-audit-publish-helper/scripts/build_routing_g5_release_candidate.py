#!/usr/bin/env python3
"""Build or validate the exact public routing G5 release candidate."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.release_candidate import (
    build_g5_release_candidate_bundle,
    load_g5_release_candidate_bundle,
    validate_g5_release_candidate_bundle,
    write_deterministic_release_archive,
)
from aoa_sdk.control_plane.routing.shadow import RoutingProducerInputs


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
DEFAULT_INPUT_LOCK = (
    REPO_ROOT
    / "sdk"
    / "distribution"
    / "manifests"
    / "routing_g5_release_candidate.input-lock.json"
)
GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
EXPECTED_INPUTS = {
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
    "aoa-memo",
    "aoa-stats",
    "aoa-agents",
    "Agents-of-Abyss",
    "aoa-playbooks",
    "aoa-kag",
    "Tree-of-Sophia",
    "aoa-sdk",
    "Dionysus",
    "8Dionysus",
    "abyss-stack",
}


def _read_lock(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load release-candidate input lock: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError("release-candidate input lock must contain an object")
    if payload.get("schema_version") != (
        "aoa_sdk_routing_g5_release_candidate_input_lock_v1"
    ):
        raise RouterError("release-candidate input lock schema drifted")
    refs = payload.get("input_source_refs")
    if not isinstance(refs, dict) or set(refs) != EXPECTED_INPUTS:
        raise RouterError(
            "release-candidate input lock must name every exact producer input"
        )
    for owner, source_ref in refs.items():
        if owner == "aoa-sdk" and source_ref == "SELF":
            continue
        if not isinstance(source_ref, str) or not GIT_OBJECT_ID.fullmatch(source_ref):
            raise RouterError(f"input_source_refs[{owner!r}] must be an exact Git ref")
    predecessor = payload.get("predecessor")
    verifier = payload.get("artifact_verifier")
    for label, record in (
        ("predecessor", predecessor),
        ("artifact_verifier", verifier),
    ):
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("source_ref"), str)
            or not GIT_OBJECT_ID.fullmatch(record["source_ref"])
        ):
            raise RouterError(f"{label} must carry an exact Git ref")
    authority = payload.get("authority")
    if authority != {
        "canonical_owner_repo": "aoa-routing",
        "candidate_owner_repo": "aoa-sdk",
        "g5_authority_flags": False,
        "production_runtime_allowed": False,
    }:
        raise RouterError("release-candidate input lock authority stop line drifted")
    return payload


def _git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RouterError(f"could not inspect exact Git checkout {root}") from exc


def _require_exact_checkout(root: Path, source_ref: str, label: str) -> None:
    if _git_output(root, "rev-parse", "HEAD") != source_ref:
        raise RouterError(f"{label} checkout does not match {source_ref}")
    if _git_output(root, "status", "--porcelain", "--untracked-files=all"):
        raise RouterError(f"{label} checkout must be clean")


def _inputs(workspace_root: Path, sdk_root: Path) -> RoutingProducerInputs:
    return RoutingProducerInputs(
        techniques_root=workspace_root / "aoa-techniques",
        skills_root=workspace_root / "aoa-skills",
        evals_root=workspace_root / "aoa-evals",
        memo_root=workspace_root / "aoa-memo",
        stats_root=workspace_root / "aoa-stats",
        agents_root=workspace_root / "aoa-agents",
        aoa_root=workspace_root / "Agents-of-Abyss",
        playbooks_root=workspace_root / "aoa-playbooks",
        kag_root=workspace_root / "aoa-kag",
        tos_root=workspace_root / "Tree-of-Sophia",
        sdk_root=sdk_root,
        source_route_root=workspace_root / "Dionysus",
        profile_root=workspace_root / "8Dionysus",
        abyss_stack_root=workspace_root / "abyss-stack",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-lock", type=Path, default=DEFAULT_INPUT_LOCK)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--predecessor-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--archive-output", type=Path)
    parser.add_argument("--checksum-output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    lock = _read_lock(args.input_lock.resolve())
    sdk_root = args.sdk_root.resolve()
    sdk_ref = _git_output(sdk_root, "rev-parse", "HEAD")
    if not GIT_OBJECT_ID.fullmatch(sdk_ref):
        raise RouterError("aoa-sdk HEAD must be an exact Git object ID")
    source_refs = dict(lock["input_source_refs"])
    source_refs["aoa-sdk"] = sdk_ref
    if lock.get("sdk_source_ref") != "SELF":
        raise RouterError("release-candidate lock must bind SDK through SELF")

    inputs = _inputs(args.workspace_root.resolve(), sdk_root)
    for owner, root in sorted(inputs.source_roots().items()):
        _require_exact_checkout(root, source_refs[owner], owner)
    predecessor_root = (
        args.predecessor_root.resolve()
        if args.predecessor_root
        else (args.workspace_root / "aoa-routing").resolve()
    )
    predecessor_ref = str(lock["predecessor"]["source_ref"])
    _require_exact_checkout(predecessor_root, predecessor_ref, "aoa-routing")

    if args.check:
        bundle = load_g5_release_candidate_bundle(args.output_dir)
        validate_g5_release_candidate_bundle(bundle, inputs)
    else:
        observed_at_text = _git_output(sdk_root, "show", "-s", "--format=%cI", sdk_ref)
        try:
            observed_at = datetime.fromisoformat(observed_at_text)
        except ValueError as exc:
            raise RouterError("aoa-sdk commit time must be RFC 3339") from exc
        bundle = build_g5_release_candidate_bundle(
            inputs,
            args.output_dir,
            predecessor_source_ref=predecessor_ref,
            sdk_source_ref=sdk_ref,
            input_source_refs=source_refs,
            observed_at=observed_at,
        )

    archive_sha256: str | None = None
    if args.archive_output:
        archive_sha256 = write_deterministic_release_archive(
            bundle,
            args.archive_output,
        )
        if args.checksum_output:
            checksum_path = args.checksum_output.expanduser().absolute()
            checksum_path.parent.mkdir(parents=True, exist_ok=True)
            checksum_path.write_text(
                f"{archive_sha256}  {args.archive_output.name}\n",
                encoding="utf-8",
                newline="\n",
            )
    elif args.checksum_output:
        raise RouterError("--checksum-output requires --archive-output")

    print(
        json.dumps(
            {
                "ok": True,
                "schema": "aoa_sdk_routing_g5_release_candidate_build_v1",
                "sdk_source_ref": bundle.sdk_source_ref,
                "predecessor_source_ref": bundle.predecessor_source_ref,
                "output_root": str(bundle.output_root),
                "artifact_manifest": str(bundle.manifest_path),
                "archive": str(args.archive_output) if args.archive_output else None,
                "archive_sha256": archive_sha256,
                "g5_authority": False,
                "production_runtime_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouterError as exc:
        print(f"[error] {exc}")
        raise SystemExit(1)
