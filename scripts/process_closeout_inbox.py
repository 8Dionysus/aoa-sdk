#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[0]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aoa_sdk.closeout import CloseoutAPI  # noqa: E402
from aoa_sdk.workspace.discovery import Workspace  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process the canonical aoa-sdk closeout inbox.")
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="Workspace root used for federation discovery.",
    )
    parser.add_argument("--inbox-dir", help="Override the inbox directory.")
    parser.add_argument("--processed-dir", help="Override the processed-manifest directory.")
    parser.add_argument("--failed-dir", help="Override the failed-manifest directory.")
    parser.add_argument("--report-dir", help="Override the closeout report directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = Workspace.discover(args.root)
    closeout = CloseoutAPI(workspace)
    report = closeout.process_inbox(
        inbox_dir=args.inbox_dir,
        processed_dir=args.processed_dir,
        failed_dir=args.failed_dir,
        report_dir=args.report_dir,
    )
    payload = report.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(f"inbox: {report.inbox_dir}")
        print(f"processed: {report.processed_count}")
        print(f"failed: {report.failed_count}")
    return 1 if report.failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
