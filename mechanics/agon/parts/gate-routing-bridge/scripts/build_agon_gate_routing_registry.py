#!/usr/bin/env python3
"""Build or freshness-check the wheel-packaged Agon gate routing registry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = REPO_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from aoa_sdk.control_plane.routing.agon import (  # noqa: E402
    AGON_GATE_REGISTRY_PATH,
    render_agon_gate_routing_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render_agon_gate_routing_registry()
    if args.check:
        if not AGON_GATE_REGISTRY_PATH.is_file():
            raise SystemExit(
                f"missing packaged Agon routing registry: {AGON_GATE_REGISTRY_PATH}"
            )
        if AGON_GATE_REGISTRY_PATH.read_text(encoding="utf-8") != expected:
            raise SystemExit("packaged Agon gate routing registry is stale")
        print("SDK Agon gate routing registry is up to date")
        return 0

    AGON_GATE_REGISTRY_PATH.write_text(expected, encoding="utf-8")
    print(f"wrote {AGON_GATE_REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
