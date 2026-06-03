#!/usr/bin/env python3
"""Build the generated source topology index for src/aoa_sdk."""

from __future__ import annotations

import argparse

from source_topology_common import SOURCE_TOPOLOGY_PATH, build_payload, render_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build aoa-sdk generated/source_topology.min.json."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated file matches the canonical rebuild instead of rewriting it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered = render_payload(build_payload())
    SOURCE_TOPOLOGY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        current = SOURCE_TOPOLOGY_PATH.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit("generated/source_topology.min.json is out of date")
        print("[ok] verified generated/source_topology.min.json")
        return 0
    SOURCE_TOPOLOGY_PATH.write_text(rendered, encoding="utf-8")
    print("[ok] wrote generated/source_topology.min.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
