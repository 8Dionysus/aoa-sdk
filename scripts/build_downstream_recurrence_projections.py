#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SDK_ROOT / "src"))

from aoa_sdk.recurrence.api import RecurrenceAPI  # noqa: E402
from aoa_sdk.recurrence.io import (  # noqa: E402
    persist_downstream_projection_bundle,
    persist_projection_guard_report,
)
from aoa_sdk.workspace.discovery import Workspace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build narrow recurrence downstream projections for routing/stats/KAG."
    )
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--plan")
    parser.add_argument("--doctor")
    parser.add_argument("--handoff")
    parser.add_argument("--beacon")
    parser.add_argument("--review-queue")
    parser.add_argument("--review-summary")
    parser.add_argument("--decision-report")
    parser.add_argument("--no-routing", action="store_true")
    parser.add_argument("--no-stats", action="store_true")
    parser.add_argument("--no-kag", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--guard-output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    workspace = Workspace.discover(args.workspace_root)
    api = RecurrenceAPI(workspace)
    bundle = api.downstream_projection_bundle(
        plan_or_path=args.plan,
        gap_report_or_path=args.doctor,
        return_handoff_or_path=args.handoff,
        beacon_or_path=args.beacon,
        review_queue_or_path=args.review_queue,
        review_summary_or_path=args.review_summary,
        decision_report_or_path=args.decision_report,
        include_routing=not args.no_routing,
        include_stats=not args.no_stats,
        include_kag=not args.no_kag,
    )
    bundle_path = persist_downstream_projection_bundle(
        workspace, bundle, output=args.output
    )
    guard_path = persist_projection_guard_report(
        workspace, bundle.guard_report, output=args.guard_output
    )
    payload = bundle.model_dump(mode="json")
    payload["report_path"] = str(bundle_path)
    payload["guard_report_path"] = str(guard_path)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(f"report_path: {bundle_path}")
        print(f"guard_report_path: {guard_path}")
        print(f"surfaces: {len(bundle.surfaces)}")
        print(f"guard_violations: {len(bundle.guard_report.violations)}")
    return 20 if bundle.guard_report.violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
