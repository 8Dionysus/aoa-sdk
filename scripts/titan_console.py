#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROSTER = {
    "Atlas": {
        "role": "architect",
        "lane": "structure",
        "active": True,
        "gate": None,
        "sandbox_mode": "read-only",
    },
    "Sentinel": {
        "role": "reviewer",
        "lane": "risk",
        "active": True,
        "gate": None,
        "sandbox_mode": "read-only",
    },
    "Mneme": {
        "role": "memory-keeper",
        "lane": "memory",
        "active": True,
        "gate": None,
        "sandbox_mode": "read-only",
    },
    "Forge": {
        "role": "coder",
        "lane": "implementation",
        "active": False,
        "gate": "mutation",
        "sandbox_mode": "workspace-write",
    },
    "Delta": {
        "role": "evaluator",
        "lane": "verdict",
        "active": False,
        "gate": "judgment",
        "sandbox_mode": "read-only",
    },
}
ACTORS = {"operator", "console", *ROSTER.keys()}
TYPES = {
    "observation",
    "risk",
    "memory",
    "mutation",
    "judgment",
    "approval",
    "closeout",
    "system",
}


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read(p: Path) -> dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"state file not found: {p}")


def write(p: Path, d: dict[str, Any]):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest(s):
    t = s.get("titans", {})
    ev = s.get("events", [])
    ap = s.get("approvals", [])
    return {
        "event_count": len(ev),
        "approval_count": len(ap),
        "active": [n for n, m in t.items() if m.get("active")],
        "locked": [n for n, m in t.items() if not m.get("active") and m.get("gate")],
        "opened_gates": [f"{a.get('titan')}:{a.get('gate')}" for a in ap],
        "risk_flags": [e["note"] for e in ev if e.get("type") == "risk"],
        "updated_at": now(),
    }


def validate_state(s):
    errs = []
    for k in [
        "version",
        "session_id",
        "workspace",
        "operator",
        "status",
        "titans",
        "events",
        "approvals",
        "created_at",
    ]:
        if k not in s:
            errs.append(f"missing key: {k}")
    if s.get("version") != 1:
        errs.append("version must be 1")
    t = s.get("titans", {})
    for name, exp in ROSTER.items():
        if name not in t:
            errs.append(f"missing titan: {name}")
            continue
        if t[name].get("role") != exp["role"]:
            errs.append(f"{name} role mismatch")
        if t[name].get("gate") != exp["gate"]:
            errs.append(f"{name} gate mismatch")
    approvals = {(a.get("titan"), a.get("gate")) for a in s.get("approvals", [])}
    if t.get("Forge", {}).get("active") and ("Forge", "mutation") not in approvals:
        errs.append("Forge active without mutation approval")
    if t.get("Delta", {}).get("active") and ("Delta", "judgment") not in approvals:
        errs.append("Delta active without judgment approval")
    for i, e in enumerate(s.get("events", [])):
        if e.get("actor") not in ACTORS:
            errs.append(f"event[{i}] invalid actor")
        if e.get("type") not in TYPES:
            errs.append(f"event[{i}] invalid type")
        if not e.get("note"):
            errs.append(f"event[{i}] empty note")
    return errs


def cmd_roster(a):
    payload = {"version": 1, "titans": ROSTER}
    print(
        json.dumps(payload, indent=2, ensure_ascii=False)
        if a.json
        else "\n".join(
            f"{n:8} {m['role']:14} lane={m['lane']:14} {'active' if m['active'] else 'locked':7} gate={m['gate'] or 'none'}"
            for n, m in ROSTER.items()
        )
    )
    return 0


def cmd_new(a):
    s = {
        "version": 1,
        "session_id": a.session_id or "titan-console-" + uuid.uuid4().hex[:12],
        "workspace": str(Path(a.workspace).resolve()),
        "operator": a.operator,
        "status": "open",
        "created_at": now(),
        "closed_at": None,
        "titans": json.loads(json.dumps(ROSTER)),
        "events": [
            {
                "ts": now(),
                "actor": "console",
                "type": "system",
                "note": "Titan operator console state opened.",
            }
        ],
        "approvals": [],
        "digest": {},
    }
    s["digest"] = digest(s)
    write(Path(a.out), s)
    print("created " + a.out)
    return 0


def cmd_event(a):
    p = Path(a.state)
    s = read(p)
    if s.get("status") == "closed" and not a.allow_closed:
        raise SystemExit("state is closed")
    if a.actor not in ACTORS:
        raise SystemExit("invalid actor")
    if a.type not in TYPES:
        raise SystemExit("invalid event type")
    s.setdefault("events", []).append(
        {"ts": now(), "actor": a.actor, "type": a.type, "note": a.note, "metadata": {}}
    )
    s["digest"] = digest(s)
    write(p, s)
    print(f"event appended: {a.actor}/{a.type}")
    return 0


def cmd_gate(a):
    p = Path(a.state)
    s = read(p)
    exp = ROSTER[a.titan]["gate"]
    if exp != a.gate:
        raise SystemExit(f"{a.titan} requires gate={exp}, not {a.gate}")
    approval = {
        "ts": now(),
        "titan": a.titan,
        "gate": a.gate,
        "reason": a.reason,
        "approved_by": a.approved_by or s.get("operator", "operator"),
    }
    s.setdefault("approvals", []).append(approval)
    s.setdefault("events", []).append(
        {
            "ts": now(),
            "actor": "operator",
            "type": "approval",
            "note": f"Opened {a.titan} through {a.gate} gate: {a.reason}",
            "metadata": {"titan": a.titan, "gate": a.gate},
        }
    )
    s["titans"][a.titan]["active"] = True
    s["digest"] = digest(s)
    write(p, s)
    print(f"gate opened: {a.titan}/{a.gate}")
    return 0


def cmd_digest(a):
    s = read(Path(a.state))
    s["digest"] = digest(s)
    if a.write:
        write(Path(a.state), s)
    if a.json:
        print(json.dumps(s["digest"], indent=2, ensure_ascii=False))
    else:
        print(
            f"session: {s.get('session_id')}\nstatus: {s.get('status')}\nevents: {s['digest']['event_count']} approvals: {s['digest']['approval_count']}\nactive: {', '.join(s['digest']['active'])}\nlocked: {', '.join(s['digest']['locked']) or 'none'}"
        )
    return 0


def cmd_close(a):
    p = Path(a.state)
    s = read(p)
    s["status"] = "closed"
    s["closed_at"] = now()
    s.setdefault("events", []).append(
        {
            "ts": now(),
            "actor": "operator",
            "type": "closeout",
            "note": a.reason,
            "metadata": {},
        }
    )
    s["digest"] = digest(s)
    write(p, s)
    print("closed " + a.state)
    return 0


def cmd_validate(a):
    errs = validate_state(read(Path(a.state)))
    if errs:
        print("\n".join("ERROR: " + e for e in errs), file=sys.stderr)
        return 1
    print("titan console state valid")
    return 0


def cmd_plan(a):
    prompt = (
        Path(a.prompt_file).read_text(encoding="utf-8")
        if a.prompt_file
        else "Summon Titan operator console cohort."
    )
    cwd = str(Path(a.workspace).resolve())
    msgs = [
        {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": {
                    "name": "abyss_console",
                    "title": "Abyss Console",
                    "version": "0.1.0",
                }
            },
        },
        {"method": "initialized", "params": {}},
        {
            "method": "thread/start",
            "id": 1,
            "params": {"model": a.model, "cwd": cwd, "serviceName": "abyss_console"},
        },
        {
            "method": "turn/start",
            "id": 2,
            "params": {
                "threadId": "${thread.id}",
                "input": [{"type": "text", "text": prompt}],
            },
        },
    ]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(json.dumps(m, ensure_ascii=False) for m in msgs) + "\n",
        encoding="utf-8",
    )
    print("wrote app-server launch plan: " + str(out))
    return 0


def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("roster")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_roster)
    s = sub.add_parser("new")
    s.add_argument("--workspace", required=True)
    s.add_argument("--operator", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--session-id")
    s.set_defaults(func=cmd_new)
    s = sub.add_parser("event")
    s.add_argument("--state", required=True)
    s.add_argument("--actor", required=True)
    s.add_argument("--type", required=True)
    s.add_argument("--note", required=True)
    s.add_argument("--allow-closed", action="store_true")
    s.set_defaults(func=cmd_event)
    s = sub.add_parser("gate")
    s.add_argument("--state", required=True)
    s.add_argument("--titan", required=True, choices=["Forge", "Delta"])
    s.add_argument("--gate", required=True, choices=["mutation", "judgment"])
    s.add_argument("--reason", required=True)
    s.add_argument("--approved-by")
    s.set_defaults(func=cmd_gate)
    s = sub.add_parser("digest")
    s.add_argument("--state", required=True)
    s.add_argument("--json", action="store_true")
    s.add_argument("--write", action="store_true")
    s.set_defaults(func=cmd_digest)
    s = sub.add_parser("close")
    s.add_argument("--state", required=True)
    s.add_argument("--reason", required=True)
    s.set_defaults(func=cmd_close)
    s = sub.add_parser("validate")
    s.add_argument("--state", required=True)
    s.set_defaults(func=cmd_validate)
    s = sub.add_parser("appserver-plan")
    s.add_argument("--workspace", required=True)
    s.add_argument("--prompt-file")
    s.add_argument("--out", required=True)
    s.add_argument("--model", default="gpt-5.4")
    s.set_defaults(func=cmd_plan)
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    return int(a.func(a))


if __name__ == "__main__":
    raise SystemExit(main())
