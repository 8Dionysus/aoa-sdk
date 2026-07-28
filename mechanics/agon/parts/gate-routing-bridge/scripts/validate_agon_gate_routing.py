#!/usr/bin/env python3
"""Validate the SDK Agon routing bridge and pinned succession receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from aoa_sdk.control_plane.routing.agon import (  # noqa: E402
    AGON_GATE_CONFIG_PATH,
    AGON_GATE_REGISTRY_PATH,
    load_packaged_agon_gate_routing_registry,
    validate_agon_gate_routing_registry,
)
from aoa_sdk.control_plane.routing.validator import get_schema_validator  # noqa: E402


RECEIPT_PATH = PART_ROOT / "evidence" / "agon-gate-routing-succession.json"
DISPATCH_EXAMPLE_PATH = PART_ROOT / "examples" / "owner_dispatch_seam.example.json"
DEFAULT_CENTER_ROOT = REPO_ROOT.parent / "Agents-of-Abyss"
DEFAULT_CENTER_LAWFUL_MOVE_REGISTRY_PATH = (
    DEFAULT_CENTER_ROOT
    / "mechanics"
    / "agon"
    / "parts"
    / "lawful-move-grammar"
    / "generated"
    / "agon_lawful_move_registry.min.json"
)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} must contain an object")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _center_lawful_moves(registry_path: Path) -> set[str] | None:
    if not registry_path.is_file():
        return None
    payload = _load_json(registry_path)
    moves = payload.get("moves")
    if not isinstance(moves, list):
        raise AssertionError("center lawful move registry moves must be a list")
    result = {
        move["name"]
        for move in moves
        if isinstance(move, dict) and isinstance(move.get("name"), str)
    }
    return result or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--center-root",
        type=Path,
        help=(
            "explicit Agents-of-Abyss root for optional lawful-move drift "
            "validation"
        ),
    )
    args = parser.parse_args()
    center_registry_path = (
        args.center_root.resolve()
        / "mechanics"
        / "agon"
        / "parts"
        / "lawful-move-grammar"
        / "generated"
        / "agon_lawful_move_registry.min.json"
        if args.center_root is not None
        else DEFAULT_CENTER_LAWFUL_MOVE_REGISTRY_PATH
    )
    subprocess.run(
        [
            sys.executable,
            str(PART_ROOT / "scripts" / "build_agon_gate_routing_registry.py"),
            "--check",
        ],
        check=True,
    )

    registry = load_packaged_agon_gate_routing_registry()
    center_moves = _center_lawful_moves(center_registry_path)
    validate_agon_gate_routing_registry(
        registry,
        center_lawful_moves=center_moves,
    )

    dispatch = _load_json(DISPATCH_EXAMPLE_PATH)
    get_schema_validator("owner-dispatch-seam.schema.json").validate(dispatch)
    if dispatch.get("owner_repo") != "aoa-sdk":
        raise AssertionError("owner dispatch seam must be owned by aoa-sdk")

    receipt = _load_json(RECEIPT_PATH)
    expected_hashes = receipt.get("sdk_sha256")
    if not isinstance(expected_hashes, dict):
        raise AssertionError("succession receipt sdk_sha256 must be an object")
    actual_hashes = {
        "config": _sha256(AGON_GATE_CONFIG_PATH),
        "registry": _sha256(AGON_GATE_REGISTRY_PATH),
    }
    if expected_hashes != actual_hashes:
        raise AssertionError(
            f"Agon succession receipt digest drift: "
            f"expected={expected_hashes}, actual={actual_hashes}"
        )
    expected_trigger_ids = receipt.get("preserved_trigger_ids")
    actual_trigger_ids = [trigger["trigger_id"] for trigger in registry["triggers"]]
    if expected_trigger_ids != actual_trigger_ids:
        raise AssertionError("Agon succession receipt trigger IDs drifted")

    optional_state = (
        "validated"
        if center_moves is not None
        else "not-present; packaged source vocabulary used"
    )
    print(
        "SDK Agon gate routing validation passed; "
        f"optional center lawful moves: {optional_state}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, subprocess.CalledProcessError) as exc:
        print(f"Agon gate routing validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
