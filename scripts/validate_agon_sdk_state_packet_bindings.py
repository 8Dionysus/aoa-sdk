#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "agon_sdk_state_packet_bindings.seed.json"
REGISTRY = ROOT / "generated" / "agon_sdk_state_packet_bindings.min.json"
FORBIDDEN_WRITES = {
    "arena_session",
    "verdict",
    "scar",
    "retention",
    "rank",
    "tree_of_sophia",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def validate() -> int:
    seed = load(CONFIG)
    reg = load(REGISTRY)

    if seed.get("live_protocol") is not False:
        return fail("seed live_protocol must be false")
    if seed.get("runtime_effect") != "none":
        return fail("seed runtime_effect must be none")
    if reg.get("live_protocol") is not False:
        return fail("registry live_protocol must be false")
    if reg.get("runtime_effect") != "none":
        return fail("registry runtime_effect must be none")

    bindings = seed.get("bindings", [])
    if reg.get("binding_count") != len(bindings):
        return fail("binding_count mismatch")

    ids = [binding.get("binding_id") for binding in bindings]
    if len(ids) != len(set(ids)):
        return fail("duplicate binding ids")

    for binding in bindings:
        binding_id = binding.get("binding_id", "")
        if not binding_id.startswith("agon.sdk."):
            return fail(f"invalid binding id: {binding_id}")
        if binding.get("writes"):
            return fail(f"SDK Wave IX binding must not write: {binding_id}")

        joined = " ".join(binding.get("writes", []))
        for forbidden in FORBIDDEN_WRITES:
            if forbidden in joined:
                return fail(f"forbidden write target {forbidden} in {binding_id}")
        if not binding.get("forbidden_effects"):
            return fail(f"missing forbidden effects: {binding_id}")

    return 0


if __name__ == "__main__":
    result = validate()
    if result != 0:
        raise SystemExit(result)
    print("agon sdk state packet bindings: ok")
