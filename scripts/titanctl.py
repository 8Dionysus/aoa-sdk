#!/usr/bin/env python3
"""titanctl: local Titan runtime receipt and gate seed.

No external dependencies. This is intentionally small enough to audit.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


TITANS = {
    "Atlas": {"role_key": "architect", "state": "active", "gate": "none"},
    "Sentinel": {"role_key": "reviewer", "state": "active", "gate": "none"},
    "Mneme": {"role_key": "memory-keeper", "state": "active", "gate": "none"},
    "Forge": {"role_key": "coder", "state": "locked", "gate": "mutation"},
    "Delta": {"role_key": "evaluator", "state": "locked", "gate": "judgment"},
}

REQUIRED_GATES = {"Forge": "mutation", "Delta": "judgment"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"receipt not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def default_receipt(workspace: str, operator: str) -> Dict[str, Any]:
    stamp = now()
    receipt_id = f"titan-session-{stamp.replace(':', '').replace('+', 'Z')}-{uuid.uuid4().hex[:8]}"
    return {
        "version": 1,
        "receipt_id": receipt_id,
        "created_at": stamp,
        "closed_at": None,
        "workspace": workspace,
        "operator": operator,
        "cohort": TITANS,
        "events": [
            {
                "at": stamp,
                "type": "summon",
                "message": "Atlas, Sentinel, and Mneme summoned. Forge and Delta locked.",
            }
        ],
        "status": "open",
        "summary": None,
        "memory_candidates": [],
    }


def validate_receipt(receipt: Dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in [
        "version",
        "receipt_id",
        "created_at",
        "workspace",
        "operator",
        "cohort",
        "events",
        "status",
    ]:
        if key not in receipt:
            errors.append(f"missing key: {key}")

    if receipt.get("version") != 1:
        errors.append("version must be 1")

    cohort = receipt.get("cohort", {})
    for titan in TITANS:
        if titan not in cohort:
            errors.append(f"missing titan: {titan}")

    for titan, required_gate in REQUIRED_GATES.items():
        state = cohort.get(titan, {})
        gate = state.get("gate")
        if gate != required_gate:
            errors.append(f"{titan} gate must be {required_gate}, got {gate!r}")
        if state.get("state") == "active":
            matching = [
                event
                for event in receipt.get("events", [])
                if event.get("type") == "gate"
                and event.get("agent") == titan
                and event.get("gate") == required_gate
            ]
            if not matching:
                errors.append(f"{titan} active without recorded {required_gate} gate")

    for titan in ["Atlas", "Sentinel", "Mneme"]:
        state = cohort.get(titan, {})
        if state.get("state") != "active":
            errors.append(f"{titan} should be active in default service cohort")
        if state.get("gate") != "none":
            errors.append(f"{titan} gate should be none")

    if receipt.get("status") not in {"open", "closed"}:
        errors.append("status must be open or closed")

    if receipt.get("status") == "closed" and not receipt.get("closed_at"):
        errors.append("closed receipt requires closed_at")

    return errors


def cmd_roster(args: argparse.Namespace) -> int:
    roster = {
        "version": 1,
        "cohort": [{"name": name, **state} for name, state in TITANS.items()],
        "default_active": ["Atlas", "Sentinel", "Mneme"],
        "locked": REQUIRED_GATES,
    }
    if args.json:
        print(json.dumps(roster, indent=2, ensure_ascii=False))
    else:
        for item in roster["cohort"]:
            print(
                f"{item['name']}: {item['role_key']} state={item['state']} gate={item['gate']}"
            )
    return 0


def cmd_summon(args: argparse.Namespace) -> int:
    receipt = default_receipt(args.workspace, args.operator)
    out = Path(args.out)
    if out.exists() and not args.force:
        raise SystemExit(
            f"refusing to overwrite existing receipt without --force: {out}"
        )
    write_json(out, receipt)
    print(f"wrote {out}")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    path = Path(args.receipt)
    receipt = read_json(path)

    if receipt.get("status") != "open":
        raise SystemExit("cannot gate a closed receipt")

    if args.agent not in REQUIRED_GATES:
        raise SystemExit(f"{args.agent} does not accept runtime gates")

    required = REQUIRED_GATES[args.agent]
    if args.kind != required:
        raise SystemExit(f"{args.agent} requires {required} gate, got {args.kind}")

    receipt["cohort"][args.agent]["state"] = "active"
    receipt["events"].append(
        {
            "at": now(),
            "type": "gate",
            "agent": args.agent,
            "gate": args.kind,
            "message": args.intent,
        }
    )

    errors = validate_receipt(receipt)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 2

    write_json(path, receipt)
    print(f"updated {path}: {args.agent} activated by {args.kind} gate")
    return 0


def cmd_note(args: argparse.Namespace) -> int:
    path = Path(args.receipt)
    receipt = read_json(path)
    if receipt.get("status") != "open":
        raise SystemExit("cannot add note to closed receipt")
    event = {"at": now(), "type": "note", "message": args.message}
    if args.agent:
        event["agent"] = args.agent
    receipt["events"].append(event)
    write_json(path, receipt)
    print(f"noted {path}")
    return 0


def cmd_closeout(args: argparse.Namespace) -> int:
    path = Path(args.receipt)
    receipt = read_json(path)
    receipt["status"] = "closed"
    receipt["closed_at"] = now()
    receipt["summary"] = args.summary
    if args.memory_candidate:
        receipt.setdefault("memory_candidates", []).extend(args.memory_candidate)
    receipt["events"].append(
        {"at": receipt["closed_at"], "type": "closeout", "message": args.summary}
    )

    errors = validate_receipt(receipt)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else path
    write_json(out, receipt)
    print(f"closed {out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    receipt = read_json(Path(args.receipt))
    errors = validate_receipt(receipt)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 2
    print("valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Titan runtime receipt and gate tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("roster")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_roster)

    p = sub.add_parser("summon")
    p.add_argument("--workspace", default="/srv")
    p.add_argument("--operator", default="Dionysus")
    p.add_argument("--out", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_summon)

    p = sub.add_parser("gate")
    p.add_argument("--receipt", required=True)
    p.add_argument("--agent", required=True, choices=["Forge", "Delta"])
    p.add_argument("--kind", required=True, choices=["mutation", "judgment"])
    p.add_argument("--intent", required=True)
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("note")
    p.add_argument("--receipt", required=True)
    p.add_argument("--message", required=True)
    p.add_argument("--agent", choices=["Atlas", "Sentinel", "Mneme", "Forge", "Delta"])
    p.set_defaults(func=cmd_note)

    p = sub.add_parser("closeout")
    p.add_argument("--receipt", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--memory-candidate", action="append", default=[])
    p.add_argument("--out")
    p.set_defaults(func=cmd_closeout)

    p = sub.add_parser("validate")
    p.add_argument("--receipt", required=True)
    p.set_defaults(func=cmd_validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
