#!/usr/bin/env python3
"""Generate the JSON Schema projection for AgentIncarnationBinding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[5]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from aoa_sdk.contracts.incarnation import AgentIncarnationBinding  # noqa: E402


OUTPUT = (
    ROOT
    / "mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas/agent-incarnation-binding.schema.json"
)


def render() -> str:
    schema = AgentIncarnationBinding.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:aoa-sdk:agent-incarnation-binding:v1"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            print(f"ERROR: {OUTPUT.relative_to(ROOT)} is missing or stale", file=sys.stderr)
            return 1
        print("OK: AgentIncarnationBinding schema is current")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
