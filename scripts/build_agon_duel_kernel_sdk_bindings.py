#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "config" / "agon_duel_kernel_sdk_bindings.seed.json"
OUT = ROOT / "generated" / "agon_duel_kernel_sdk_bindings.min.json"


def digest_obj(obj):
    payload = json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def build():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    helpers = data.get("helpers", [])
    stop_lines = data.get("stop_lines", [])
    return {
        "registry_id": data["registry_id"],
        "wave": data.get("wave", "XII"),
        "count": len(helpers),
        "status": data.get("status"),
        "helpers": helpers,
        "stop_lines": stop_lines,
        "digest": digest_obj({"helpers": helpers, "stop_lines": stop_lines}),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    txt = json.dumps(
        build(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != txt:
            print("generated SDK binding registry drift", file=sys.stderr)
            return 1
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(txt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
