#!/usr/bin/env python3
"""Fallback command surface for recurrence review decision closure.

Codex may wire this before the Typer CLI merge is complete.
"""

from __future__ import annotations

import argparse
import json

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.recurrence.io import (
    persist_owner_review_decision,
    persist_review_decision_close_report,
    persist_review_decision_ledger,
    persist_review_suppression_memory,
)
from aoa_sdk.workspace.discovery import Workspace


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and close recurrence owner-review decisions."
    )
    parser.add_argument("--workspace-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    template = sub.add_parser(
        "template", help="Create an owner-review-decision template from a queue item."
    )
    template.add_argument("--queue", required=True)
    template.add_argument("--item-ref")
    template.add_argument("--beacon-ref")
    template.add_argument("--decision", default="defer")
    template.add_argument("--reviewer", default="owner-review")
    template.add_argument("--rationale", default="")
    template.add_argument("--cluster-ref")
    template.add_argument("--next-review-after")
    template.add_argument("--output")

    close = sub.add_parser(
        "close", help="Close a review queue with one or more owner-review decisions."
    )
    close.add_argument("--queue", required=True)
    close.add_argument("--decision", action="append", default=[])
    close.add_argument("--output")
    close.add_argument("--ledger-output")
    close.add_argument("--suppression-output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = Workspace.discover(args.workspace_root)
    api = RecurrenceAPI(workspace)

    if args.command == "template":
        decision = api.review_decision_template(
            args.queue,
            item_ref=args.item_ref,
            beacon_ref=args.beacon_ref,
            decision=args.decision,
            reviewer=args.reviewer,
            rationale=args.rationale,
            cluster_ref=args.cluster_ref,
            next_review_after=args.next_review_after,
        )
        path = persist_owner_review_decision(workspace, decision, output=args.output)
        payload = decision.model_dump(mode="json")
        payload["report_path"] = str(path)
        _print(payload)
        return 0

    report = api.review_close(args.queue, decision_paths=args.decision)
    report_path = persist_review_decision_close_report(
        workspace, report, output=args.output
    )
    ledger_path = persist_review_decision_ledger(
        workspace, report.ledger, output=args.ledger_output
    )
    suppression_path = persist_review_suppression_memory(
        workspace, report.suppression_memory, output=args.suppression_output
    )
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    payload["ledger_path"] = str(ledger_path)
    payload["suppression_path"] = str(suppression_path)
    _print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
