#!/usr/bin/env python3
"""Build or validate the exact receipt-bound SDK canonical routing release."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from aoa_sdk.control_plane.routing.canonical import (
    build_g5_canonical_bundle,
    load_g5_canonical_bundle,
    validate_g5_canonical_bundle,
    write_deterministic_canonical_archive,
)
from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.shadow import RoutingProducerInputs


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
DEFAULT_INPUT_LOCK = (
    REPO_ROOT
    / "sdk"
    / "distribution"
    / "manifests"
    / "routing_g5_canonical.input-lock.json"
)
GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
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
        raise RouterError(
            f"could not load G5 canonical input lock: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RouterError("G5 canonical input lock must contain an object")
    if payload.get("schema_version") != (
        "aoa_sdk_routing_g5_canonical_input_lock_v1"
    ):
        raise RouterError("G5 canonical input lock schema drifted")
    if payload.get("sdk_source_ref") != "SELF":
        raise RouterError("G5 canonical lock must bind SDK through SELF")
    if payload.get("sdk_version") != "0.8.0":
        raise RouterError("G5 canonical lock SDK version drifted")
    refs = payload.get("input_source_refs")
    if not isinstance(refs, dict) or set(refs) != EXPECTED_INPUTS:
        raise RouterError(
            "G5 canonical input lock must name every producer input"
        )
    for owner, source_ref in refs.items():
        if owner == "aoa-sdk" and source_ref == "SELF":
            continue
        if (
            not isinstance(source_ref, str)
            or not GIT_OBJECT_ID.fullmatch(source_ref)
        ):
            raise RouterError(
                f"input_source_refs[{owner!r}] must be an exact Git ref"
            )
    predecessor = payload.get("predecessor")
    public_release = payload.get("public_release_trust_root")
    runtime_consumer = payload.get("runtime_consumer_contract")
    for label, record in (
        ("predecessor", predecessor),
        ("public release", public_release),
        ("runtime consumer", runtime_consumer),
    ):
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("source_ref"), str)
            or not GIT_OBJECT_ID.fullmatch(record["source_ref"])
        ):
            raise RouterError(f"{label} must carry an exact Git ref")
    if (
        not isinstance(public_release.get("asset_digest"), str)
        or not SHA256_DIGEST.fullmatch(public_release["asset_digest"])
        or not isinstance(public_release.get("release_ref"), str)
        or not public_release["release_ref"]
        or not isinstance(public_release.get("asset_name"), str)
        or not public_release["asset_name"]
    ):
        raise RouterError("public release trust root binding drifted")
    if runtime_consumer.get("repo") != "abyss-stack":
        raise RouterError("runtime consumer owner drifted")
    if payload.get("compatibility_window") != {
        "state": "started",
        "started_on": "2026-07-26",
        "started_by_sdk_version": "0.8.0",
    }:
        raise RouterError("G5 compatibility-window lock drifted")
    if payload.get("authority") != {
        "archive_authorized": False,
        "canonical_owner_repo": "aoa-sdk",
        "canonical_producer_switch_authorized": True,
        "compatibility_window_started": True,
        "live_runtime_mutation_authorized": True,
        "predecessor_maintenance_only": True,
        "sdk_canonical": True,
    }:
        raise RouterError("G5 canonical authority lock drifted")
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


def _require_exact_checkout(
    root: Path,
    source_ref: str,
    label: str,
) -> None:
    if _git_output(root, "rev-parse", "HEAD") != source_ref:
        raise RouterError(f"{label} checkout does not match {source_ref}")
    if _git_output(root, "status", "--porcelain", "--untracked-files=all"):
        raise RouterError(f"{label} checkout must be clean")


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError(f"{label} must contain an object")
    return payload


def _require_canonical_lock_bindings(
    *,
    bundle: Any,
    receipt: dict[str, Any],
    provenance: dict[str, Any],
    lock: dict[str, Any],
    sdk_ref: str,
    source_refs: dict[str, str],
) -> None:
    predecessor = lock["predecessor"]
    public_release = lock["public_release_trust_root"]
    runtime_consumer = lock["runtime_consumer_contract"]
    authority = dict(lock["authority"])
    if authority.pop("canonical_owner_repo", None) != "aoa-sdk":
        raise RouterError("G5 canonical owner lock drifted")

    expected_receipt_bindings = {
        "sdk": {
            "owner_repo": "aoa-sdk",
            "source_ref": sdk_ref,
            "version": lock["sdk_version"],
        },
        "predecessor": {
            "owner_repo": predecessor["repo"],
            "source_ref": predecessor["source_ref"],
            "rollback_posture": predecessor["rollback_posture"],
        },
        "public_release": {
            "release_ref": public_release["release_ref"],
            "source_ref": public_release["source_ref"],
            "asset_name": public_release["asset_name"],
            "asset_digest": public_release["asset_digest"],
        },
        "runtime_consumer": {
            "owner_repo": runtime_consumer["repo"],
            "source_ref": runtime_consumer["source_ref"],
            "contract_ref": (
                "docs/decisions/"
                f"{runtime_consumer['decision_id']}"
                "-receipt-bound-sdk-routing-cutover.md"
            ),
        },
        "compatibility_window": lock["compatibility_window"],
        "g5_authority": authority,
    }
    for field, expected in expected_receipt_bindings.items():
        actual = receipt.get(field)
        if field == "sdk" and isinstance(actual, dict):
            actual = {
                key: actual.get(key)
                for key in ("owner_repo", "source_ref", "version")
            }
        if actual != expected:
            raise RouterError(
                f"G5 canonical receipt {field} differs from input lock"
            )

    expected_provenance_bindings = {
        "canonical_producer": {
            "owner_repo": "aoa-sdk",
            "source_ref": sdk_ref,
            "implementation": "aoa_sdk.control_plane.routing",
        },
        "canonical_predecessor": {
            "owner_repo": predecessor["repo"],
            "source_ref": predecessor["source_ref"],
            "posture": "compatibility_security_rollback_deprecation_only",
        },
        "public_release_trust_root": {
            "release_ref": public_release["release_ref"],
            "source_ref": public_release["source_ref"],
            "asset_name": public_release["asset_name"],
            "asset_digest": public_release["asset_digest"],
            "byte_parity": True,
        },
        "runtime_consumer_contract": {
            "owner_repo": runtime_consumer["repo"],
            "source_ref": runtime_consumer["source_ref"],
            "decision_id": runtime_consumer["decision_id"],
            "live_cutover_executed": False,
        },
        "input_source_refs": source_refs,
        "g5_authority": authority,
    }
    for field, expected in expected_provenance_bindings.items():
        if provenance.get(field) != expected:
            raise RouterError(
                f"G5 canonical provenance {field} differs from input lock"
            )

    if (
        bundle.sdk_source_ref != sdk_ref
        or bundle.predecessor_source_ref != predecessor["source_ref"]
        or dict(bundle.input_source_refs) != source_refs
    ):
        raise RouterError("G5 canonical bundle refs differ from input lock")


def _inputs(
    workspace_root: Path,
    sdk_root: Path,
) -> RoutingProducerInputs:
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
    parser.add_argument("--public-release-archive", type=Path, required=True)
    parser.add_argument("--runtime-consumer-root", type=Path, required=True)
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

    inputs = _inputs(args.workspace_root.resolve(), sdk_root)
    for owner, root in sorted(inputs.source_roots().items()):
        _require_exact_checkout(root, source_refs[owner], owner)
    predecessor_root = (
        args.predecessor_root.resolve()
        if args.predecessor_root
        else (args.workspace_root / "aoa-routing").resolve()
    )
    predecessor = lock["predecessor"]
    predecessor_ref = str(predecessor["source_ref"])
    _require_exact_checkout(
        predecessor_root,
        predecessor_ref,
        "aoa-routing",
    )
    public_release = lock["public_release_trust_root"]
    runtime_consumer = lock["runtime_consumer_contract"]
    runtime_consumer_root = args.runtime_consumer_root.resolve()
    _require_exact_checkout(
        runtime_consumer_root,
        str(runtime_consumer["source_ref"]),
        "abyss-stack runtime consumer",
    )

    if args.check:
        bundle = load_g5_canonical_bundle(args.output_dir)
        validate_g5_canonical_bundle(
            bundle,
            inputs,
            public_release_archive=args.public_release_archive,
            runtime_consumer_root=runtime_consumer_root,
        )
        _require_canonical_lock_bindings(
            bundle=bundle,
            receipt=_read_json_object(
                bundle.receipt_path,
                "G5 owner-switch receipt",
            ),
            provenance=_read_json_object(
                bundle.provenance_path,
                "G5 canonical provenance",
            ),
            lock=lock,
            sdk_ref=sdk_ref,
            source_refs=source_refs,
        )
    else:
        observed_at_text = _git_output(
            sdk_root,
            "show",
            "-s",
            "--format=%cI",
            sdk_ref,
        )
        try:
            observed_at = datetime.fromisoformat(observed_at_text)
        except ValueError as exc:
            raise RouterError(
                "aoa-sdk commit time must be RFC 3339"
            ) from exc
        bundle = build_g5_canonical_bundle(
            inputs,
            args.output_dir,
            predecessor_source_ref=predecessor_ref,
            sdk_source_ref=sdk_ref,
            sdk_version=str(lock["sdk_version"]),
            input_source_refs=source_refs,
            public_release_archive=args.public_release_archive,
            public_release_ref=str(public_release["release_ref"]),
            public_release_source_ref=str(public_release["source_ref"]),
            public_release_asset_digest=str(public_release["asset_digest"]),
            runtime_consumer_root=runtime_consumer_root,
            runtime_consumer_source_ref=str(runtime_consumer["source_ref"]),
            compatibility_started_on=str(
                lock["compatibility_window"]["started_on"]
            ),
            observed_at=observed_at,
        )

    archive_sha256: str | None = None
    if args.archive_output:
        archive_sha256 = write_deterministic_canonical_archive(
            bundle,
            args.archive_output,
        )
        if args.checksum_output:
            checksum = args.checksum_output.expanduser().absolute()
            checksum.parent.mkdir(parents=True, exist_ok=True)
            checksum.write_text(
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
                "schema": "aoa_sdk_routing_g5_canonical_build_v1",
                "sdk_source_ref": bundle.sdk_source_ref,
                "predecessor_source_ref": bundle.predecessor_source_ref,
                "output_root": str(bundle.output_root),
                "owner_switch_receipt": str(bundle.receipt_path),
                "artifact_manifest": str(bundle.manifest_path),
                "archive": (
                    str(args.archive_output)
                    if args.archive_output
                    else None
                ),
                "archive_sha256": archive_sha256,
                "g5_authority": True,
                "archive_authorized": False,
                "live_cutover_executed": False,
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
