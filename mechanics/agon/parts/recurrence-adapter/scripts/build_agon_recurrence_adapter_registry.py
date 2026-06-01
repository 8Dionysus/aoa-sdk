#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PART_ROOT = Path(__file__).resolve().parents[1]


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError(f"could not find aoa-sdk repo root from {start}")


ROOT = find_repo_root(Path(__file__).resolve())
SRC = PART_ROOT / "config" / "agon_recurrence_adapter.seed.json"
OUT = PART_ROOT / "generated" / "agon_recurrence_adapter_registry.min.json"
GENERATED_BY = (
    "mechanics/agon/parts/recurrence-adapter/scripts/"
    "build_agon_recurrence_adapter_registry.py"
)

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def build():
    data = dict(load_json(SRC))
    data["generated_by"] = GENERATED_BY
    data["component_count"] = len(data.get("components", []))
    data["owner_repo_count"] = len({c.get("owner_repo") for c in data.get("components", [])})
    data["observed_surface_count"] = sum(len(c.get("observed_surfaces", [])) for c in data.get("components", []))
    data["generated_at"] = "2026-04-20T00:00:00Z"
    return data

def dump_min(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    built = dump_min(build())
    if args.check:
        if not OUT.exists():
            print(f"missing generated file: {OUT}", file=sys.stderr)
            return 1
        if OUT.read_text(encoding="utf-8") != built:
            print(f"generated drift: {OUT}", file=sys.stderr)
            return 1
        print("agon recurrence adapter registry is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(built, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
