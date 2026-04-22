#!/usr/bin/env python3
"""titanctl: local Titan runtime receipt and gate helper.

The CLI keeps the earlier summon/gate/note/closeout shape, but the persisted
receipt now uses the Titan incarnation spine v2 contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aoa_sdk.titans.incarnation_spine import (  # noqa: E402
    DEFAULT_ACTIVE,
    LOCKED,
    TITAN_BEARERS,
    cohort_projection,
    gate_titan,
    new_receipt,
    utc_now,
    validate_gate_payload,
    validate_receipt as validate_spine_receipt,
)


TITANS = {
    name: {
        "bearer_id": data["bearer_id"],
        "role_key": data["role_key"],
        "role_class": data["role_class"],
        "state": "locked" if name in LOCKED else "active",
        "gate": LOCKED.get(name, "none"),
    }
    for name, data in TITAN_BEARERS.items()
}

REQUIRED_GATES = dict(LOCKED)


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"receipt not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"receipt must be a JSON object: {path}")
    return data


def write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def sync_projection(receipt: Dict[str, Any]) -> Dict[str, Any]:
    receipt["cohort"] = cohort_projection(receipt)
    return receipt


def append_event(
    receipt: Dict[str, Any],
    *,
    event_type: str,
    message: str,
    agent: str | None = None,
    gate: str | None = None,
) -> None:
    event: Dict[str, Any] = {
        "at": utc_now(),
        "type": event_type,
        "message": message,
    }
    if agent:
        event["agent"] = agent
    if gate:
        event["gate"] = gate
    receipt.setdefault("events", []).append(event)


def default_receipt(workspace: str, operator: str) -> Dict[str, Any]:
    receipt = new_receipt(
        workspace=workspace,
        operator=operator,
        source_ref="scripts/titanctl.py:summon",
    )
    append_event(
        receipt,
        event_type="summon",
        message=(
            "Atlas, Sentinel, and Mneme summoned as named Titan incarnations. "
            "Forge and Delta remain locked behind payload gates."
        ),
    )
    return sync_projection(receipt)


def validate_receipt(receipt: Mapping[str, Any]) -> list[str]:
    errors = validate_spine_receipt(receipt)

    if receipt.get("status") not in {"open", "closed", "aborted"}:
        errors.append("status must be open, closed, or aborted")

    if receipt.get("status") == "closed" and not receipt.get("closed_at"):
        errors.append("closed receipt requires closed_at")

    cohort = receipt.get("cohort")
    if cohort is not None and not isinstance(cohort, Mapping):
        errors.append("cohort projection must be an object when present")

    by_name = {
        inc.get("titan_name"): inc
        for inc in receipt.get("incarnations", [])
        if isinstance(inc, Mapping)
    }
    for titan, required_gate in REQUIRED_GATES.items():
        inc = by_name.get(titan)
        if not isinstance(inc, Mapping):
            continue
        if inc.get("state") == "active":
            matching = [
                event
                for event in receipt.get("gate_events", [])
                if event.get("titan_name") == titan
                and event.get("gate_kind") == required_gate
            ]
            if not matching:
                errors.append(f"{titan} active without recorded {required_gate} gate")

    for titan in DEFAULT_ACTIVE:
        inc = by_name.get(titan)
        if isinstance(inc, Mapping) and inc.get("state") != "active":
            errors.append(f"{titan} should be active in default service cohort")

    return errors


def read_payload(path: str) -> Dict[str, Any]:
    payload = read_json(Path(path))
    if not isinstance(payload, dict):
        raise SystemExit(f"payload must be a JSON object: {path}")
    return payload


def fallback_gate_payload(args: argparse.Namespace, receipt: Mapping[str, Any]) -> Dict[str, Any]:
    approval_ref = args.approval_ref or (
        f"titanctl:{receipt.get('session_id', 'session')}:"
        f"{args.agent.lower()}:{args.kind}"
    )
    intent = args.intent.strip()
    if args.agent == "Forge":
        return {
            "mutation_surface": args.mutation_surface or "operator_declared",
            "scope": args.scope or [intent],
            "expected_files": args.expected_file or ["operator-scoped"],
            "rollback_note": args.rollback_note
            or f"Rollback the operator-scoped mutation opened by {approval_ref}.",
            "approval_ref": approval_ref,
            "test_plan": args.test_plan or ["operator validation"],
        }
    if args.agent == "Delta":
        return {
            "claim": args.claim or intent,
            "criteria": args.criterion or ["operator-declared judgment criteria"],
            "evidence_refs": args.evidence_ref or [approval_ref],
            "verdict_scope": args.verdict_scope or "operator-declared judgment scope",
        }
    raise SystemExit(f"{args.agent} does not accept runtime gates")


def cmd_roster(args: argparse.Namespace) -> int:
    roster = {
        "schema_version": "titan_roster/v2",
        "cohort": [{"name": name, **state} for name, state in TITANS.items()],
        "default_active": list(DEFAULT_ACTIVE),
        "locked": REQUIRED_GATES,
    }
    if args.json:
        print(json.dumps(roster, indent=2, ensure_ascii=False))
    else:
        for item in roster["cohort"]:
            print(
                f"{item['name']}: {item['role_key']} "
                f"bearer={item['bearer_id']} "
                f"state={item['state']} gate={item['gate']}"
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

    payload = read_payload(args.payload) if args.payload else fallback_gate_payload(args, receipt)
    errors = validate_gate_payload(args.agent, args.kind, payload)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 2

    receipt = gate_titan(
        receipt,
        titan_name=args.agent,
        gate_kind=args.kind,
        payload=payload,
        approved_by=args.approved_by,
    )
    append_event(
        receipt,
        event_type="gate",
        agent=args.agent,
        gate=args.kind,
        message=args.intent,
    )
    sync_projection(receipt)

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
    append_event(receipt, event_type="note", agent=args.agent, message=args.message)
    write_json(path, sync_projection(receipt))
    print(f"noted {path}")
    return 0


def cmd_closeout(args: argparse.Namespace) -> int:
    path = Path(args.receipt)
    receipt = read_json(path)
    receipt["status"] = "closed"
    receipt["closed_at"] = utc_now()
    receipt["summary"] = args.summary
    if args.memory_candidate:
        receipt.setdefault("memory_candidates", []).extend(args.memory_candidate)
    append_event(receipt, event_type="closeout", message=args.summary)
    sync_projection(receipt)

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
    p.add_argument("--payload", help="Path to a structured gate payload JSON object")
    p.add_argument("--approved-by")
    p.add_argument("--approval-ref")
    p.add_argument("--mutation-surface")
    p.add_argument("--scope", action="append")
    p.add_argument("--expected-file", action="append")
    p.add_argument("--rollback-note")
    p.add_argument("--test-plan", action="append")
    p.add_argument("--claim")
    p.add_argument("--criterion", action="append")
    p.add_argument("--evidence-ref", action="append")
    p.add_argument("--verdict-scope")
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
