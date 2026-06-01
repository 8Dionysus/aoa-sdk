#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
ROOT = next(
    parent for parent in SCRIPT_PATH.parents if (parent / "src" / "aoa_sdk").is_dir()
)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aoa_sdk.recurrence.api import RecurrenceAPI  # noqa: E402
from aoa_sdk.recurrence.io import persist_graph_snapshot  # noqa: E402
from aoa_sdk.workspace.discovery import Workspace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a recurrence graph snapshot without running mutation."
    )
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--output", default=None)
    parser.add_argument("--skip-manifest-diagnostics", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    workspace = Workspace.discover(Path(args.workspace_root))
    api = RecurrenceAPI(workspace)
    snapshot = api.graph_snapshot(
        include_manifest_diagnostics=not args.skip_manifest_diagnostics
    )
    path = persist_graph_snapshot(workspace, snapshot, output=args.output)
    payload = snapshot.model_dump(mode="json")
    payload["report_path"] = str(path)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(f"report_path: {path}")
        print(f"nodes: {snapshot.node_count}")
        print(f"edges: {snapshot.edge_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
