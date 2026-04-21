#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aoa_sdk.recurrence.agent_readiness import (  # noqa: E402
    build_recursor_boundary_scan_report,
    build_recursor_projection_candidates,
    build_recursor_readiness_projection,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only recursor readiness workspace scan.")
    parser.add_argument(
        "mode",
        choices=["readiness", "boundary-check", "projection-candidates"],
        help="Read-only scan mode.",
    )
    parser.add_argument("--workspace-root", default=".", help="Workspace root containing aoa-agents.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "readiness":
        payload = build_recursor_readiness_projection(args.workspace_root)
    elif args.mode == "boundary-check":
        payload = build_recursor_boundary_scan_report(args.workspace_root)
    else:
        payload = build_recursor_projection_candidates(args.workspace_root)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{args.mode}: {payload.get('status', 'unknown')}")
    return 1 if payload.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
