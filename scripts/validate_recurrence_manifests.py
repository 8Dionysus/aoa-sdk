#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _install_src_path() -> None:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _exit_code(by_severity: dict[str, int]) -> int:
    if by_severity.get("critical", 0) or by_severity.get("high", 0):
        return 30
    if by_severity.get("medium", 0):
        return 10
    return 0


def main(argv: list[str] | None = None) -> int:
    _install_src_path()
    from aoa_sdk.recurrence.api import RecurrenceAPI
    from aoa_sdk.workspace.discovery import Workspace

    parser = argparse.ArgumentParser(
        description="Validate recurrence-adjacent manifests without letting mixed shapes abort registry loading."
    )
    parser.add_argument("--workspace-root", "--root", default=".", help="Federation/workspace root.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--fail-on-medium",
        action="store_true",
        help="Use exit code 30 for medium diagnostics too. Default is 10 for warning-level medium diagnostics.",
    )
    args = parser.parse_args(argv)

    workspace = Workspace.discover(args.workspace_root)
    report = RecurrenceAPI(workspace).manifest_scan()
    payload = report.model_dump(mode="json")

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(f"report_ref: {report.report_ref}")
        print(f"loaded_components: {len(report.loaded_components)}")
        print(f"foreign_manifests: {len(report.foreign_manifests)}")
        print(f"diagnostics: {len(report.diagnostics)}")
        for severity, count in sorted(report.by_severity.items()):
            print(f"  {severity}: {count}")
        for item in report.diagnostics:
            if item.diagnostic_kind == "loaded_manifest":
                continue
            print(f"- {item.severity} {item.diagnostic_kind} {item.path}: {item.message}")

    exit_code = _exit_code(report.by_severity)
    if args.fail_on_medium and exit_code == 10:
        return 30
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
