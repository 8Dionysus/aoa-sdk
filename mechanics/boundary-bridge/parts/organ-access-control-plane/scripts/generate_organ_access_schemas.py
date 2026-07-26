#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from aoa_sdk.contracts.organs import (  # noqa: E402
    ActivationRequest,
    CompatibilityObservation,
    OrganActivationPlan,
    OrganRecord,
    OrganRegistryProjection,
    OrganRegistrySource,
    OrganResultEnvelope,
    OrganResultMetadata,
)


OUTPUTS = {
    "organ-contract.schema.json": OrganRecord,
    "organ-registry-source.schema.json": OrganRegistrySource,
    "organ-registry-projection.schema.json": OrganRegistryProjection,
    "organ-activation-request.schema.json": ActivationRequest,
    "organ-activation-plan.schema.json": OrganActivationPlan,
    "organ-compatibility-observation.schema.json": CompatibilityObservation,
    "organ-result-metadata.schema.json": OrganResultMetadata,
    "organ-result-envelope.schema.json": OrganResultEnvelope,
}


def render(filename: str, model: type) -> str:
    schema = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:aoa-sdk:organ-access:{filename}"
    return (
        json.dumps(
            schema,
            indent=2,
            ensure_ascii=True,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output_dir = REPO_ROOT / "schemas" / "organ-access"
    if not args.check:
        output_dir.mkdir(parents=True, exist_ok=True)

    stale: list[str] = []
    for filename, model in OUTPUTS.items():
        destination = output_dir / filename
        expected = render(filename, model)
        if args.check:
            if not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
                stale.append(str(destination.relative_to(REPO_ROOT)))
        else:
            destination.write_text(expected, encoding="utf-8")
    if stale:
        print("stale organ access schemas:")
        for path in stale:
            print(f"  - {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
