#!/usr/bin/env python3
"""Pin one admitted aoa-playbooks plan-contour ABI into the SDK wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
RESOURCE_ROOT = REPO_ROOT / "src" / "aoa_sdk" / "control_plane" / "planning" / "data"
LOCK_PATH = RESOURCE_ROOT / "playbook-plan-contours-source-lock.v1.json"
CONTOUR_PATH = RESOURCE_ROOT / "playbook-plan-contours.v1.json"
SCHEMA_PATH = RESOURCE_ROOT / "playbook-plan-contours.schema.json"
OWNER_CONTOUR_REF = "generated/playbook_plan_contours.min.json"
OWNER_SCHEMA_REF = (
    "mechanics/scenario-composition/parts/plan-contours/"
    "schemas/playbook-plan-contours.schema.json"
)
REGISTRY_REF = "dist/abyss-artifact-registry/aoa-playbooks-playbook-registry"
REQUIRED_CONTROLS = {"abi_signature", "slsa_in_toto"}
_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class PinError(RuntimeError):
    """The owner artifact cannot be admitted as the exact SDK pin."""


def _sha256(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _load_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PinError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PinError(f"{label} must contain a JSON object")
    return payload


def _stable_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _resolve_bounded_dir(root: Path, relative: str, label: str) -> Path:
    root = root.resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise PinError(f"{label} must be a bounded relative path")
    candidate = root
    for part in relative_path.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PinError(f"{label} must not traverse a symlink")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PinError(f"{label} escapes its owner root") from exc
    if not resolved.is_dir():
        raise PinError(f"{label} is not a directory")
    return resolved


def _read_bounded_regular_file(root: Path, relative: str, label: str) -> bytes:
    root = root.resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise PinError(f"{label} must be a bounded relative path")
    candidate = root
    for part in relative_path.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PinError(f"{label} must not traverse a symlink")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PinError(f"{label} escapes its owner root") from exc
    if not resolved.is_file():
        raise PinError(f"{label} is not a regular file")
    return resolved.read_bytes()


def _git(owner_root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(owner_root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _trust_gate(owner_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "abyss-machine",
            "artifacts",
            "trust-gate",
            "--registry-dir",
            str(owner_root / REGISTRY_REF),
            "--artifact-class",
            "playbook_registry_bundle",
            "--consumer-intent",
            "agent",
            "--source-repo",
            "aoa-playbooks",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return _load_object(result.stdout.encode("utf-8"), "trust-gate verdict")


def build_outputs(owner_root: Path) -> dict[Path, bytes]:
    owner_root = owner_root.resolve()
    source_ref = _git(owner_root, "rev-parse", "HEAD")
    if not _OID_RE.fullmatch(source_ref):
        raise PinError("aoa-playbooks owner ref must be an exact Git object id")
    if _git(owner_root, "status", "--short"):
        raise PinError("aoa-playbooks owner checkout must be clean")
    verdict = _trust_gate(owner_root)
    decision = verdict.get("decision")
    record = verdict.get("record")
    if (
        verdict.get("schema") != "abyss_machine_artifact_trust_gate_v1"
        or verdict.get("ok") is not True
        or verdict.get("verdict") != "allow"
        or not isinstance(decision, dict)
        or decision.get("allow") is not True
        or not isinstance(record, dict)
    ):
        raise PinError("aoa-playbooks trust gate did not return an allow record")
    record_id = record.get("record_id")
    latest_record_id = verdict.get("latest_record_id")
    subject_store = record.get("artifact_subject_store")
    controls = record.get("controls")
    if (
        record.get("artifact_class") != "playbook_registry_bundle"
        or record.get("source_repo") != "aoa-playbooks"
        or record.get("latest_eligible") is not True
        or record.get("terminal_state") is not False
        or record.get("verification_ok") is not True
        or record_id != latest_record_id
        or not isinstance(record_id, str)
        or not isinstance(subject_store, dict)
        or subject_store.get("required") is not True
        or subject_store.get("ok") is not True
        or not isinstance(controls, dict)
    ):
        raise PinError("aoa-playbooks trust record is not latest and admissible")
    required_items = controls.get("required")
    verified_items = controls.get("verified")
    if (
        not isinstance(required_items, list)
        or not all(isinstance(item, str) for item in required_items)
        or len(required_items) != len(set(required_items))
        or not isinstance(verified_items, list)
        or not all(isinstance(item, str) for item in verified_items)
        or len(verified_items) != len(set(verified_items))
    ):
        raise PinError("aoa-playbooks trust controls are malformed")
    required = set(required_items)
    verified = set(verified_items)
    if not REQUIRED_CONTROLS.issubset(required & verified):
        raise PinError("aoa-playbooks trust record lacks required controls")
    store_path = subject_store.get("path")
    aggregate_digest = subject_store.get("aggregate_digest")
    if (
        not isinstance(store_path, str)
        or not isinstance(aggregate_digest, str)
        or not _DIGEST_RE.fullmatch(aggregate_digest)
        or not isinstance(record_id, str)
        or not _DIGEST_RE.fullmatch(record_id)
        or not isinstance(latest_record_id, str)
        or not _DIGEST_RE.fullmatch(latest_record_id)
    ):
        raise PinError("aoa-playbooks subject store identity is incomplete")
    store_root = _resolve_bounded_dir(
        owner_root,
        store_path,
        "aoa-playbooks subject store",
    )
    contour_raw = _read_bounded_regular_file(
        store_root,
        OWNER_CONTOUR_REF,
        "materialized playbook plan contours",
    )
    schema_raw = _read_bounded_regular_file(
        store_root,
        OWNER_SCHEMA_REF,
        "materialized playbook plan-contour schema",
    )
    if contour_raw != _read_bounded_regular_file(
        owner_root,
        OWNER_CONTOUR_REF,
        "current owner playbook plan contours",
    ) or schema_raw != _read_bounded_regular_file(
        owner_root,
        OWNER_SCHEMA_REF,
        "current owner playbook plan-contour schema",
    ):
        raise PinError(
            "aoa-playbooks subject store does not match the exact owner checkout"
        )
    contour = _load_object(contour_raw, "playbook plan contours")
    schema = _load_object(schema_raw, "playbook plan-contour schema")
    abi = contour.get("abi")
    if (
        contour.get("schema_version") != "aoa_playbook_plan_contours_v1"
        or contour.get("layer") != "aoa-playbooks"
        or not isinstance(abi, dict)
        or abi.get("abi_id") != "aoa_playbook_plan_contour_v1"
        or abi.get("abi_version") != "aoa_playbook_plan_contour_v1"
        or abi.get("owner_repo") != "aoa-playbooks"
        or abi.get("schema_ref") != OWNER_SCHEMA_REF
    ):
        raise PinError("aoa-playbooks plan-contour ABI identity drifted")
    lock = {
        "schema_version": "aoa_control_plane_plan_contour_source_lock_v1",
        "owner_repo": "aoa-playbooks",
        "owner_source_ref": source_ref,
        "artifact_class": "playbook_registry_bundle",
        "trust_admission": {
            "schema_version": "abyss_machine_artifact_trust_gate_v1",
            "consumer_intent": "agent",
            "verdict": "allow",
            "record_id": record_id,
            "latest_record_id": latest_record_id,
            "latest_required": True,
            "subject_store_required": True,
            "subject_store_ok": True,
            "subject_store_aggregate_digest": aggregate_digest,
            "required_controls": sorted(required),
            "verified_controls": sorted(verified),
        },
        "abi": {
            **abi,
            "source_ref": source_ref,
            "artifact_digest": _sha256(contour_raw),
        },
        "contours": {
            "owner_artifact_ref": OWNER_CONTOUR_REF,
            "packaged_resource": CONTOUR_PATH.name,
            "artifact_digest": _sha256(contour_raw),
            "schema_ref": OWNER_SCHEMA_REF,
            "schema_version": contour["schema_version"],
        },
        "schema": {
            "owner_artifact_ref": OWNER_SCHEMA_REF,
            "packaged_resource": SCHEMA_PATH.name,
            "artifact_digest": _sha256(schema_raw),
            "schema_ref": str(schema.get("$id", OWNER_SCHEMA_REF)),
            "schema_version": str(schema.get("$schema", "unknown")),
        },
    }
    return {
        CONTOUR_PATH: contour_raw,
        SCHEMA_PATH: schema_raw,
        LOCK_PATH: _stable_json(lock),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        outputs = build_outputs(args.owner_root)
    except (OSError, subprocess.CalledProcessError, PinError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    stale = [
        path
        for path, expected in outputs.items()
        if not path.is_file() or path.read_bytes() != expected
    ]
    if args.check:
        if stale:
            raise SystemExit(
                "stale plan-contour pin: "
                + ", ".join(path.relative_to(REPO_ROOT).as_posix() for path in stale)
            )
        print("[ok] exact admitted aoa-playbooks plan-contour pin is current")
        return 0
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print("[ok] pinned exact admitted aoa-playbooks plan-contour ABI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
