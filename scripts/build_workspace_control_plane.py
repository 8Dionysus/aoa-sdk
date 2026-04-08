#!/usr/bin/env python3
"""Build the aoa-sdk control-plane capsule surface."""

from __future__ import annotations

import argparse

from workspace_control_plane_common import (
    WORKSPACE_CONTROL_PLANE_PATH,
    build_payload,
    render_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build aoa-sdk generated/workspace_control_plane.min.json."
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
    WORKSPACE_CONTROL_PLANE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        current = WORKSPACE_CONTROL_PLANE_PATH.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit("generated/workspace_control_plane.min.json is out of date")
        print("[ok] verified generated/workspace_control_plane.min.json")
        return 0
    WORKSPACE_CONTROL_PLANE_PATH.write_text(rendered, encoding="utf-8")
    print("[ok] wrote generated/workspace_control_plane.min.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
