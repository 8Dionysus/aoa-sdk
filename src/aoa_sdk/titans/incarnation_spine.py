"""Titan incarnation spine.

Local-first helpers for carrying Titan bearer identity into session receipts,
gate events, console state, bridge traces and memory candidates.

This module is intentionally stdlib-only and does not spawn Codex agents.
"""
from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


TITAN_BEARERS: dict[str, dict[str, str]] = {
    "Atlas": {"bearer_id": "titan:atlas:founder", "role_key": "architect", "role_class": "structure"},
    "Sentinel": {"bearer_id": "titan:sentinel:founder", "role_key": "reviewer", "role_class": "review"},
    "Mneme": {"bearer_id": "titan:mneme:founder", "role_key": "memory-keeper", "role_class": "memory"},
    "Forge": {"bearer_id": "titan:forge:founder", "role_key": "coder", "role_class": "implementation"},
    "Delta": {"bearer_id": "titan:delta:founder", "role_key": "evaluator", "role_class": "judgment"},
}

DEFAULT_ACTIVE = ("Atlas", "Sentinel", "Mneme")
LOCKED = {"Forge": "mutation", "Delta": "judgment"}


@dataclass(frozen=True)
class TitanIncarnation:
    incarnation_id: str
    session_id: str
    bearer_id: str
    titan_name: str
    role_key: str
    role_class: str
    state: str
    gate_required: str | None = None
    thread_id: str | None = None
    turn_id: str | None = None
    source_ref: str | None = None
    created_at: str = field(default_factory=lambda: utc_now())


@dataclass(frozen=True)
class GateEvent:
    gate_ref: str
    session_id: str
    titan_name: str
    bearer_id: str
    gate_kind: str
    payload: dict[str, Any]
    approved_by: str | None
    created_at: str = field(default_factory=lambda: utc_now())


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex}"


def make_incarnation(titan_name: str, session_id: str, *, source_ref: str | None = None) -> TitanIncarnation:
    if titan_name not in TITAN_BEARERS:
        raise ValueError(f"unknown Titan: {titan_name}")
    b = TITAN_BEARERS[titan_name]
    gate = LOCKED.get(titan_name)
    return TitanIncarnation(
        incarnation_id=_id(f"inc:{titan_name.lower()}"),
        session_id=session_id,
        bearer_id=b["bearer_id"],
        titan_name=titan_name,
        role_key=b["role_key"],
        role_class=b["role_class"],
        state="locked" if gate else "active",
        gate_required=gate,
        source_ref=source_ref,
    )


def new_receipt(*, workspace: str, operator: str, source_ref: str | None = None) -> dict[str, Any]:
    session_id = _id("titan-session")
    incarnations = [make_incarnation(name, session_id, source_ref=source_ref) for name in (*DEFAULT_ACTIVE, *LOCKED.keys())]
    return {
        "schema_version": "titan_session_receipt/v2",
        "session_id": session_id,
        "receipt_id": session_id,
        "workspace": workspace,
        "operator": operator,
        "created_at": utc_now(),
        "closed_at": None,
        "source_ref": source_ref,
        "incarnations": [asdict(i) for i in incarnations],
        "gate_events": [],
        "events": [],
        "packets": [],
        "memory_candidates": [],
        "summary": None,
        "status": "open",
    }


def incarnation_by_name(receipt: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return incarnation records keyed by visible Titan bearer name."""
    out: dict[str, dict[str, Any]] = {}
    for inc in receipt.get("incarnations", []):
        if isinstance(inc, Mapping) and isinstance(inc.get("titan_name"), str):
            out[inc["titan_name"]] = dict(inc)
    return out


def cohort_projection(receipt: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a v1-shaped roster projection from v2 incarnation records."""
    cohort: dict[str, dict[str, Any]] = {}
    for name, inc in incarnation_by_name(receipt).items():
        gate = inc.get("gate_required")
        cohort[name] = {
            "bearer_id": inc.get("bearer_id"),
            "incarnation_id": inc.get("incarnation_id"),
            "role_key": inc.get("role_key"),
            "role_class": inc.get("role_class"),
            "state": inc.get("state"),
            "gate": gate if gate else "none",
        }
    return cohort


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def validate_gate_payload(titan_name: str, gate_kind: str, payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if titan_name == "Forge":
        if gate_kind != "mutation":
            errors.append("Forge requires mutation gate")
        for key in ("mutation_surface", "rollback_note", "approval_ref"):
            if not isinstance(payload.get(key), str) or not payload.get(key, "").strip():
                errors.append(f"Forge gate missing {key}")
        if not _non_empty_list(payload.get("scope")):
            errors.append("Forge gate requires non-empty scope")
        if not _non_empty_list(payload.get("expected_files")):
            errors.append("Forge gate requires non-empty expected_files")
        if not _non_empty_list(payload.get("test_plan")):
            errors.append("Forge gate requires non-empty test_plan")
    elif titan_name == "Delta":
        if gate_kind != "judgment":
            errors.append("Delta requires judgment gate")
        for key in ("claim", "verdict_scope"):
            if not isinstance(payload.get(key), str) or not payload.get(key, "").strip():
                errors.append(f"Delta gate missing {key}")
        if not _non_empty_list(payload.get("criteria")):
            errors.append("Delta gate requires non-empty criteria")
        if not _non_empty_list(payload.get("evidence_refs")):
            errors.append("Delta gate requires non-empty evidence_refs")
    else:
        errors.append(f"{titan_name} does not accept gate opening")
    return errors


def gate_titan(receipt: dict[str, Any], *, titan_name: str, gate_kind: str, payload: Mapping[str, Any], approved_by: str | None = None) -> dict[str, Any]:
    errors = validate_gate_payload(titan_name, gate_kind, payload)
    if errors:
        raise ValueError("; ".join(errors))
    matches = [i for i in receipt.get("incarnations", []) if i.get("titan_name") == titan_name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one incarnation for {titan_name}")
    inc = matches[0]
    inc["state"] = "active"
    inc["gate_required"] = None
    event = GateEvent(
        gate_ref=_id(f"gate:{titan_name.lower()}"),
        session_id=receipt["session_id"],
        titan_name=titan_name,
        bearer_id=inc["bearer_id"],
        gate_kind=gate_kind,
        payload=dict(payload),
        approved_by=approved_by,
    )
    receipt.setdefault("gate_events", []).append(asdict(event))
    return receipt


def validate_receipt(receipt: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "titan_session_receipt/v2":
        errors.append("schema_version must be titan_session_receipt/v2")
    if not isinstance(receipt.get("session_id"), str) or not receipt.get("session_id"):
        errors.append("session_id required")
    incs = receipt.get("incarnations")
    if not isinstance(incs, list) or len(incs) != 5:
        errors.append("exactly five incarnations required")
        incs = []
    seen_names: set[str] = set()
    seen_inc: set[str] = set()
    for inc in incs:
        if not isinstance(inc, Mapping):
            errors.append("incarnation must be object")
            continue
        for key in ("incarnation_id", "session_id", "bearer_id", "titan_name", "role_key", "role_class", "state"):
            if not isinstance(inc.get(key), str) or not inc.get(key):
                errors.append(f"incarnation missing {key}")
        name = inc.get("titan_name")
        if name in seen_names:
            errors.append(f"duplicate titan_name {name}")
        if isinstance(name, str):
            seen_names.add(name)
        iid = inc.get("incarnation_id")
        if iid in seen_inc:
            errors.append(f"duplicate incarnation_id {iid}")
        if isinstance(iid, str):
            seen_inc.add(iid)
        if name in TITAN_BEARERS:
            expected = TITAN_BEARERS[name]
            for k, v in expected.items():
                if inc.get(k) != v:
                    errors.append(f"{name} {k} expected {v}, got {inc.get(k)}")
    missing_names = set(TITAN_BEARERS) - seen_names
    if missing_names:
        errors.append(f"missing Titan incarnations: {sorted(missing_names)}")
    return errors


def validate_memory_record(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    source_refs = record.get("source_refs")
    has_source_refs = isinstance(source_refs, list) and any(isinstance(x, str) and x.strip() for x in source_refs)
    has_receipt = isinstance(record.get("receipt_id"), str) and bool(record.get("receipt_id"))
    has_session = isinstance(record.get("session_id"), str) and bool(record.get("session_id"))
    if not (has_source_refs or has_receipt or has_session):
        errors.append("memory record requires source_refs, receipt_id or session_id")
    for key in ("record_id", "bearer_id", "titan_name", "role_key", "memory_kind", "claim"):
        if not isinstance(record.get(key), str) or not record.get(key):
            errors.append(f"memory record missing {key}")
    if record.get("authority") not in ("candidate", "route_to_source"):
        errors.append("memory authority must be candidate or route_to_source")
    return errors


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Titan incarnation spine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new")
    p_new.add_argument("--workspace", required=True)
    p_new.add_argument("--operator", required=True)
    p_new.add_argument("--source-ref")
    p_new.add_argument("--out", required=True)
    p_gate = sub.add_parser("gate")
    p_gate.add_argument("--receipt", required=True)
    p_gate.add_argument("--titan", required=True)
    p_gate.add_argument("--kind", required=True)
    p_gate.add_argument("--payload", required=True, help="Path to JSON payload")
    p_gate.add_argument("--approved-by")
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--receipt", required=True)
    p_memory = sub.add_parser("validate-memory")
    p_memory.add_argument("--record", required=True)
    args = parser.parse_args(argv)

    if args.cmd == "new":
        write_json(Path(args.out), new_receipt(workspace=args.workspace, operator=args.operator, source_ref=args.source_ref))
        return 0
    if args.cmd == "gate":
        receipt = read_json(Path(args.receipt))
        payload = read_json(Path(args.payload))
        write_json(Path(args.receipt), gate_titan(receipt, titan_name=args.titan, gate_kind=args.kind, payload=payload, approved_by=args.approved_by))
        return 0
    if args.cmd == "validate":
        errors = validate_receipt(read_json(Path(args.receipt)))
        if errors:
            print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
            return 2
        print(json.dumps({"status": "pass"}, ensure_ascii=False))
        return 0
    if args.cmd == "validate-memory":
        errors = validate_memory_record(read_json(Path(args.record)))
        if errors:
            print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
            return 2
        print(json.dumps({"status": "pass"}, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(cli())
