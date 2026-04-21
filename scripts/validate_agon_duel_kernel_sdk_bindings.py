#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "generated" / "agon_duel_kernel_sdk_bindings.min.json"


def fail(message):
    print(message, file=sys.stderr)
    return 1


def main():
    if not REG.exists():
        return fail(f"missing {REG}")

    reg = json.loads(REG.read_text(encoding="utf-8"))
    helpers = reg.get("helpers", [])

    if reg.get("count") != len(helpers):
        return fail("count mismatch")
    if len(helpers) < 5:
        return fail("expected at least five SDK helper candidates")

    forbidden_authorities = [
        "live_verdict",
        "scar_write",
        "rank_mutation",
        "tree_of_sophia_promotion",
    ]
    for helper in helpers:
        if helper.get("activation_status") != "candidate_only":
            return fail(f'{helper.get("id")} must remain candidate_only')

        joined = json.dumps(helper, sort_keys=True)
        for forbidden in forbidden_authorities:
            if forbidden in joined and "stop" not in helper.get("id", ""):
                return fail(
                    f'{helper.get("id")} appears to claim forbidden authority: {forbidden}'
                )

    print("agon duel kernel SDK bindings ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
