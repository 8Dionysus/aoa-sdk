#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from aoa_sdk import AoASDK


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the aoa-sdk sibling compatibility canary against an explicit matrix."
    )
    parser.add_argument("--repo-root", default=".", help="Path to the local aoa-sdk checkout.")
    parser.add_argument(
        "--matrix",
        default="scripts/sibling_canary_matrix.json",
        help="Path to the sibling canary matrix JSON file.",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        help="Limit the canary to one or more explicit sibling repos from the matrix.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def selected_entries(
    payload: dict[str, Any],
    selected_repos: Sequence[str] | None,
) -> list[dict[str, Any]]:
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("sibling canary matrix must define a non-empty 'entries' array")

    normalized_entries: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("sibling canary matrix entries must be objects")
        repo = entry.get("repo")
        if not isinstance(repo, str) or not repo:
            raise ValueError("each sibling canary matrix entry must declare a non-empty 'repo'")
        normalized_entries.append(entry)

    if not selected_repos:
        return normalized_entries

    selected = set(selected_repos)
    available = {str(entry["repo"]) for entry in normalized_entries}
    missing = sorted(selected - available)
    if missing:
        raise ValueError(
            "requested repo is not present in sibling canary matrix: " + ", ".join(missing)
        )
    return [entry for entry in normalized_entries if entry["repo"] in selected]


def compatibility_summary(repo_root: Path, matrix_path: Path, entries: Sequence[dict[str, Any]]) -> dict[str, Any]:
    sdk = AoASDK.from_workspace(repo_root)
    results: list[dict[str, Any]] = []
    for entry in entries:
        repo = str(entry["repo"])
        checks = sdk.compatibility.check_repo(repo)
        if not checks:
            raise ValueError(f"no compatibility rules registered for repo {repo!r}")
        incompatible = [
            {
                "surface_id": check.surface_id,
                "reason": check.reason,
            }
            for check in checks
            if not check.compatible
        ]
        results.append(
            {
                "repo": repo,
                "target_ref": entry.get("target_ref", "main"),
                "purpose": entry.get("purpose", ""),
                "check_count": len(checks),
                "compatible": not incompatible,
                "incompatible_surfaces": incompatible,
            }
        )
    return {
        "matrix_path": matrix_path.as_posix(),
        "repo_root": repo_root.as_posix(),
        "results": results,
        "failed_count": sum(1 for result in results if not result["compatible"]),
    }


def render_text(summary: dict[str, Any]) -> str:
    lines = [
        f"Sibling canary matrix: {summary['matrix_path']}",
        f"aoa-sdk repo root: {summary['repo_root']}",
    ]
    for result in summary["results"]:
        status = "ok" if result["compatible"] else "failed"
        lines.extend(
            [
                "",
                f"{result['repo']} [{status}]",
                f"- target_ref: {result['target_ref']}",
                f"- purpose: {result['purpose']}",
                f"- compatibility checks: {result['check_count']}",
            ]
        )
        for issue in result["incompatible_surfaces"]:
            lines.append(f"- incompatible: {issue['surface_id']} :: {issue['reason']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    matrix_path = (repo_root / args.matrix).resolve()
    try:
        payload = load_json(matrix_path)
        entries = selected_entries(payload, args.repos)
        summary = compatibility_summary(repo_root, matrix_path, entries)
    except (FileNotFoundError, ValueError) as exc:
        if args.format == "json":
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2) + "\n", end="")
        else:
            print(f"[error] {exc}")
        return 2

    if args.format == "json":
        print(json.dumps(summary, indent=2) + "\n", end="")
    else:
        print(render_text(summary))

    return 1 if summary["failed_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
