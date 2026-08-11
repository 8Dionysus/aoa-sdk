#!/usr/bin/env python3
"""Generate the JSON Schema projection for AgentIncarnationBinding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[5]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from aoa_sdk.contracts.incarnation import (  # noqa: E402
    AgentIncarnationBinding,
    AgentIncarnationBindingV2,
)


OUTPUT = (
    ROOT
    / "mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas/agent-incarnation-binding.schema.json"
)
OUTPUT_V2 = (
    ROOT
    / "mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas/agent-incarnation-binding-v2.schema.json"
)


def render(model: type[BaseModel], *, schema_id: str) -> str:
    schema = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = schema_id
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = {
        OUTPUT: render(
            AgentIncarnationBinding,
            schema_id="urn:aoa-sdk:agent-incarnation-binding:v1",
        ),
        OUTPUT_V2: render(
            AgentIncarnationBindingV2,
            schema_id="urn:aoa-sdk:agent-incarnation-binding:v2",
        ),
    }
    if args.check:
        stale = [
            path
            for path, content in expected.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            for path in stale:
                print(
                    f"ERROR: {path.relative_to(ROOT)} is missing or stale",
                    file=sys.stderr,
                )
            return 1
        print("OK: AgentIncarnationBinding v1/v2 schemas are current")
        return 0
    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
