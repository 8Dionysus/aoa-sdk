#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def find_bearer(doc, bearer_id):
    for b in doc.get("bearers", []):
        if b.get("bearer_id") == bearer_id:
            return b
    return None


def event_id(bearer_id: str, event_type: str) -> str:
    clean = bearer_id.replace(":", "-")
    ts = now().replace(":", "").replace("+", "Z")
    return f"evt:{clean}:{event_type}:{ts}"


def cmd_list(args) -> int:
    doc = load(args.bearers)
    for b in doc.get("bearers", []):
        print(f"{b['titan_name']}\t{b['bearer_id']}\t{b['role_key']}\t{b['status']}")
    return 0


def cmd_fall(args) -> int:
    bearers = load(args.bearers)
    ledger = load(args.ledger)
    b = find_bearer(bearers, args.bearer_id)
    if not b:
        print(f"unknown bearer_id: {args.bearer_id}", file=sys.stderr)
        return 2
    b["status"] = "fallen"
    b["last_seen_at"] = now()
    b["epitaph"] = args.epitaph or b.get("epitaph")
    ev = {
        "event_id": event_id(args.bearer_id, "fall"),
        "event_type": "fall",
        "bearer_id": args.bearer_id,
        "occurred_at": now(),
        "summary": args.summary,
        "source_ref": args.source_ref,
        "related_bearer_id": None,
        "lessons": args.lesson or [],
        "metadata": {"titan_name": b.get("titan_name"), "role_key": b.get("role_key")},
    }
    ledger.setdefault("events", []).append(ev)
    if not args.dry_run:
        save(args.bearers, bearers)
        save(args.ledger, ledger)
    print(json.dumps(ev, ensure_ascii=False, indent=2))
    return 0


def cmd_succeed(args) -> int:
    bearers = load(args.bearers)
    ledger = load(args.ledger)
    predecessor = find_bearer(bearers, args.predecessor_id)
    successor = find_bearer(bearers, args.successor_id)
    if not predecessor:
        print(f"unknown predecessor_id: {args.predecessor_id}", file=sys.stderr)
        return 2
    if not successor:
        print(f"unknown successor_id: {args.successor_id}", file=sys.stderr)
        return 2
    predecessor.setdefault("successors", [])
    if args.successor_id not in predecessor["successors"]:
        predecessor["successors"].append(args.successor_id)
    successor["successor_of"] = args.predecessor_id
    predecessor["status"] = "succeeded"
    ev = {
        "event_id": event_id(args.successor_id, "successor_named"),
        "event_type": "successor_named",
        "bearer_id": args.successor_id,
        "occurred_at": now(),
        "summary": args.summary,
        "source_ref": args.source_ref,
        "related_bearer_id": args.predecessor_id,
        "lessons": args.lesson or [],
        "metadata": {
            "predecessor_name": predecessor.get("titan_name"),
            "successor_name": successor.get("titan_name"),
            "role_key": successor.get("role_key"),
        },
    }
    ledger.setdefault("events", []).append(ev)
    if not args.dry_run:
        save(args.bearers, bearers)
        save(args.ledger, ledger)
    print(json.dumps(ev, ensure_ascii=False, indent=2))
    return 0


def cmd_remember(args) -> int:
    ledger = load(args.ledger)
    ev = {
        "event_id": event_id(args.bearer_id, "remembrance"),
        "event_type": "remembrance",
        "bearer_id": args.bearer_id,
        "occurred_at": now(),
        "summary": args.summary,
        "source_ref": args.source_ref,
        "related_bearer_id": None,
        "lessons": args.lesson or [],
        "metadata": {},
    }
    ledger.setdefault("events", []).append(ev)
    if not args.dry_run:
        save(args.ledger, ledger)
    print(json.dumps(ev, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list")
    p.add_argument("--bearers", required=True, type=Path)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("fall")
    p.add_argument("--bearers", required=True, type=Path)
    p.add_argument("--ledger", required=True, type=Path)
    p.add_argument("--bearer-id", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--lesson", action="append")
    p.add_argument("--epitaph")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_fall)

    p = sub.add_parser("succeed")
    p.add_argument("--bearers", required=True, type=Path)
    p.add_argument("--ledger", required=True, type=Path)
    p.add_argument("--predecessor-id", required=True)
    p.add_argument("--successor-id", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--lesson", action="append")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_succeed)

    p = sub.add_parser("remember")
    p.add_argument("--ledger", required=True, type=Path)
    p.add_argument("--bearer-id", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--lesson", action="append")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_remember)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
