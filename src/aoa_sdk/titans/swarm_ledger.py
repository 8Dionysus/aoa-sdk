"""Titan swarm ledger.

Local-first helpers for recording Titan task contracts, agent reports,
finding lifecycle, grades, timeouts and closeout audits.

This module is intentionally stdlib-only. It does not spawn Codex agents.
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

GRADE_SCALE = {
    "D-", "D", "D+",
    "C-", "C", "C+",
    "B-", "B", "B+",
    "A-", "A", "A+",
    "S-", "S", "S+",
}
FINDING_STATES = {
    "reported", "confirmed", "fixed", "validated", "merged",
    "stale", "duplicate", "rejected", "memory_candidate",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex}"


@dataclass(frozen=True)
class TitanTaskContract:
    task_id: str
    titan_name: str
    bearer_id: str
    role_key: str
    mode: str
    scope: list[str]
    question: str
    expected_output: str = "titan_agent_report.v1"
    diff_excerpt_required: bool = False
    residual_question_required: bool = False
    source_refs: list[str] = field(default_factory=list)
    must_not: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class TitanFinding:
    finding_id: str
    report_id: str
    titan_name: str
    severity: str
    claim: str
    evidence_refs: list[str]
    recommended_action: str
    status: str = "reported"


@dataclass(frozen=True)
class TitanGradeRecord:
    grade_id: str
    titan_name: str
    grade: str
    reason: str
    titan_fault: bool
    orchestration_fault: bool
    prompt_fault: bool
    tooling_fault: bool
    timeout_fault: bool
    next_prompt_rule: str | None = None
    created_at: str = field(default_factory=utc_now)


def _bearer(titan_name: str) -> dict[str, str]:
    if titan_name not in TITAN_BEARERS:
        raise ValueError(f"unknown Titan: {titan_name}")
    return TITAN_BEARERS[titan_name]


def new_ledger(*, session_id: str, operator: str, source_ref: str | None = None) -> dict[str, Any]:
    roster = []
    for titan_name, bearer in TITAN_BEARERS.items():
        roster.append({
            "titan_name": titan_name,
            "bearer_id": bearer["bearer_id"],
            "role_key": bearer["role_key"],
            "role_class": bearer["role_class"],
            "state": "active" if titan_name in ("Atlas", "Sentinel", "Mneme") else "locked",
        })
    return {
        "schema_version": "titan_swarm_ledger/v1",
        "ledger_id": _id("titan-swarm-ledger"),
        "session_id": session_id,
        "summon_id": _id("summon"),
        "operator": operator,
        "source_ref": source_ref,
        "created_at": utc_now(),
        "closed_at": None,
        "roster": roster,
        "tasks": [],
        "reports": [],
        "findings": [],
        "finding_lifecycle": [],
        "grades": [],
        "timeouts": [],
        "memory_candidates": [],
        "status": "open",
    }


def add_task(
    ledger: dict[str, Any],
    *,
    titan_name: str,
    mode: str,
    scope: list[str],
    question: str,
    expected_output: str = "titan_agent_report.v1",
    diff_excerpt_required: bool = False,
    residual_question_required: bool = False,
    source_refs: list[str] | None = None,
    must_not: list[str] | None = None,
) -> dict[str, Any]:
    bearer = _bearer(titan_name)
    if titan_name == "Sentinel" and not diff_excerpt_required and mode in {"compact_review", "closeout_review"}:
        raise ValueError("Sentinel compact review requires diff_excerpt_required=true")
    if titan_name == "Delta" and not residual_question_required and mode in {"bounded_judgment", "closeout_judgment"}:
        raise ValueError("Delta bounded judgment requires residual_question_required=true")
    if not scope:
        raise ValueError("task scope must be non-empty")
    if not question.strip():
        raise ValueError("task question required")
    task = TitanTaskContract(
        task_id=_id(f"task:{titan_name.lower()}"),
        titan_name=titan_name,
        bearer_id=bearer["bearer_id"],
        role_key=bearer["role_key"],
        mode=mode,
        scope=scope,
        question=question,
        expected_output=expected_output,
        diff_excerpt_required=diff_excerpt_required,
        residual_question_required=residual_question_required,
        source_refs=source_refs or [],
        must_not=must_not or [],
    )
    ledger.setdefault("tasks", []).append(asdict(task))
    return ledger


def add_report(ledger: dict[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    titan_name = str(report.get("titan_name") or "")
    if titan_name not in TITAN_BEARERS:
        raise ValueError("report must name a known titan_name")
    if not report.get("task_id"):
        raise ValueError("report must reference task_id")
    source_refs = report.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        raise ValueError("report requires non-empty source_refs")
    report_id = str(report.get("report_id") or _id(f"report:{titan_name.lower()}"))
    normalized = dict(report)
    normalized["schema_version"] = normalized.get("schema_version", "titan_agent_report/v1")
    normalized["report_id"] = report_id
    normalized["created_at"] = normalized.get("created_at", utc_now())
    ledger.setdefault("reports", []).append(normalized)
    for raw in normalized.get("findings", []):
        if not isinstance(raw, Mapping):
            continue
        finding = TitanFinding(
            finding_id=str(raw.get("finding_id") or _id("finding")),
            report_id=report_id,
            titan_name=titan_name,
            severity=str(raw.get("severity") or "P2"),
            claim=str(raw.get("claim") or ""),
            evidence_refs=[str(x) for x in raw.get("evidence_refs", [])],
            recommended_action=str(raw.get("recommended_action") or ""),
            status=str(raw.get("status") or "reported"),
        )
        if finding.status not in FINDING_STATES:
            raise ValueError(f"invalid finding status: {finding.status}")
        if not finding.evidence_refs:
            raise ValueError("finding requires evidence_refs")
        ledger.setdefault("findings", []).append(asdict(finding))
    return ledger


def set_finding_status(ledger: dict[str, Any], *, finding_id: str, status: str, reason: str) -> dict[str, Any]:
    if status not in FINDING_STATES:
        raise ValueError(f"invalid finding status: {status}")
    found = False
    for finding in ledger.get("findings", []):
        if finding.get("finding_id") == finding_id:
            finding["status"] = status
            found = True
            break
    if not found:
        raise ValueError(f"unknown finding_id: {finding_id}")
    ledger.setdefault("finding_lifecycle", []).append({
        "event_id": _id("finding-event"),
        "finding_id": finding_id,
        "status": status,
        "reason": reason,
        "created_at": utc_now(),
    })
    return ledger


def add_grade(
    ledger: dict[str, Any],
    *,
    titan_name: str,
    grade: str,
    reason: str,
    titan_fault: bool = False,
    orchestration_fault: bool = False,
    prompt_fault: bool = False,
    tooling_fault: bool = False,
    timeout_fault: bool = False,
    next_prompt_rule: str | None = None,
) -> dict[str, Any]:
    _bearer(titan_name)
    if grade not in GRADE_SCALE:
        raise ValueError(f"invalid grade: {grade}")
    if not reason.strip():
        raise ValueError("grade reason required")
    record = TitanGradeRecord(
        grade_id=_id("grade"),
        titan_name=titan_name,
        grade=grade,
        reason=reason,
        titan_fault=titan_fault,
        orchestration_fault=orchestration_fault,
        prompt_fault=prompt_fault,
        tooling_fault=tooling_fault,
        timeout_fault=timeout_fault,
        next_prompt_rule=next_prompt_rule,
    )
    ledger.setdefault("grades", []).append(asdict(record))
    return ledger


def add_timeout(
    ledger: dict[str, Any],
    *,
    titan_name: str,
    task_id: str,
    wait_count: int,
    timeout_count: int,
    turn_aborted: bool,
    interrupt_used: bool,
    final_verdict_returned: bool,
    scope_width: str,
    diff_excerpt_present: bool,
    residual_question_present: bool,
) -> dict[str, Any]:
    _bearer(titan_name)
    ledger.setdefault("timeouts", []).append({
        "timeout_id": _id("timeout"),
        "titan_name": titan_name,
        "task_id": task_id,
        "wait_count": wait_count,
        "timeout_count": timeout_count,
        "turn_aborted": turn_aborted,
        "interrupt_used": interrupt_used,
        "final_verdict_returned": final_verdict_returned,
        "scope_width": scope_width,
        "diff_excerpt_present": diff_excerpt_present,
        "residual_question_present": residual_question_present,
        "created_at": utc_now(),
    })
    return ledger


def closeout(ledger: dict[str, Any]) -> dict[str, Any]:
    findings = ledger.get("findings", [])
    memory_candidates = []
    for finding in findings:
        if finding.get("status") in {"validated", "merged", "memory_candidate"}:
            memory_candidates.append({
                "memory_candidate_id": _id("titan-memory-candidate"),
                "kind": "titan_swarm_lesson",
                "claim": finding.get("claim"),
                "source_refs": finding.get("evidence_refs", []),
                "titan_name": finding.get("titan_name"),
                "authority": "candidate",
                "promotion_status": "candidate",
            })
    ledger["memory_candidates"] = memory_candidates
    ledger["closed_at"] = utc_now()
    ledger["status"] = "closed"
    return {
        "schema_version": "titan_closeout_audit/v1",
        "closeout_id": _id("closeout"),
        "ledger_id": ledger.get("ledger_id"),
        "session_id": ledger.get("session_id"),
        "created_at": utc_now(),
        "counts": {
            "tasks": len(ledger.get("tasks", [])),
            "reports": len(ledger.get("reports", [])),
            "findings": len(ledger.get("findings", [])),
            "grades": len(ledger.get("grades", [])),
            "timeouts": len(ledger.get("timeouts", [])),
            "memory_candidates": len(memory_candidates),
        },
        "memory_candidates": memory_candidates,
        "summary": "Titan swarm closeout completed. Reports remain weaker than owner truth.",
    }


def validate_ledger(ledger: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if ledger.get("schema_version") != "titan_swarm_ledger/v1":
        errors.append("schema_version must be titan_swarm_ledger/v1")
    if not ledger.get("session_id"):
        errors.append("session_id required")
    tasks = ledger.get("tasks", [])
    reports = ledger.get("reports", [])
    findings = ledger.get("findings", [])
    if not isinstance(tasks, list) or not isinstance(reports, list) or not isinstance(findings, list):
        errors.append("tasks/reports/findings must be arrays")
    for task in tasks if isinstance(tasks, list) else []:
        if task.get("titan_name") == "Sentinel" and task.get("mode") in {"compact_review", "closeout_review"}:
            if not task.get("diff_excerpt_required"):
                errors.append("Sentinel compact task missing diff_excerpt_required")
        if task.get("titan_name") == "Delta" and task.get("mode") in {"bounded_judgment", "closeout_judgment"}:
            if not task.get("residual_question_required"):
                errors.append("Delta judgment task missing residual_question_required")
    for report in reports if isinstance(reports, list) else []:
        if not report.get("source_refs"):
            errors.append("report missing source_refs")
    for finding in findings if isinstance(findings, list) else []:
        if finding.get("status") not in FINDING_STATES:
            errors.append(f"invalid finding status {finding.get('status')}")
        if not finding.get("evidence_refs"):
            errors.append("finding missing evidence_refs")
    return errors


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"ledger input not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Titan swarm ledger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start")
    p_start.add_argument("--session-id", required=True)
    p_start.add_argument("--operator", required=True)
    p_start.add_argument("--source-ref")
    p_start.add_argument("--out", required=True)

    p_assign = sub.add_parser("assign")
    p_assign.add_argument("--ledger", required=True)
    p_assign.add_argument("--titan", required=True)
    p_assign.add_argument("--mode", required=True)
    p_assign.add_argument("--scope", action="append", required=True)
    p_assign.add_argument("--question", required=True)
    p_assign.add_argument("--source-ref", action="append", default=[])
    p_assign.add_argument("--diff-excerpt-required", action="store_true")
    p_assign.add_argument("--residual-question-required", action="store_true")

    p_report = sub.add_parser("report")
    p_report.add_argument("--ledger", required=True)
    p_report.add_argument("--report", required=True)

    p_status = sub.add_parser("finding-status")
    p_status.add_argument("--ledger", required=True)
    p_status.add_argument("--finding-id", required=True)
    p_status.add_argument("--status", required=True)
    p_status.add_argument("--reason", required=True)

    p_grade = sub.add_parser("grade")
    p_grade.add_argument("--ledger", required=True)
    p_grade.add_argument("--titan", required=True)
    p_grade.add_argument("--grade", required=True)
    p_grade.add_argument("--reason", required=True)
    p_grade.add_argument("--titan-fault", action="store_true")
    p_grade.add_argument("--orchestration-fault", action="store_true")
    p_grade.add_argument("--prompt-fault", action="store_true")
    p_grade.add_argument("--tooling-fault", action="store_true")
    p_grade.add_argument("--timeout-fault", action="store_true")
    p_grade.add_argument("--next-prompt-rule")

    p_timeout = sub.add_parser("timeout")
    p_timeout.add_argument("--ledger", required=True)
    p_timeout.add_argument("--titan", required=True)
    p_timeout.add_argument("--task-id", required=True)
    p_timeout.add_argument("--wait-count", type=int, default=0)
    p_timeout.add_argument("--timeout-count", type=int, default=0)
    p_timeout.add_argument("--turn-aborted", action="store_true")
    p_timeout.add_argument("--interrupt-used", action="store_true")
    p_timeout.add_argument("--final-verdict-returned", action="store_true")
    p_timeout.add_argument("--scope-width", default="unknown")
    p_timeout.add_argument("--diff-excerpt-present", action="store_true")
    p_timeout.add_argument("--residual-question-present", action="store_true")

    p_close = sub.add_parser("closeout")
    p_close.add_argument("--ledger", required=True)
    p_close.add_argument("--out")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--ledger", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "start":
        write_json(Path(args.out), new_ledger(session_id=args.session_id, operator=args.operator, source_ref=args.source_ref))
        return 0

    if args.cmd in {"assign", "report", "finding-status", "grade", "timeout", "closeout", "validate"}:
        path = Path(args.ledger)
        ledger = read_json(path)

    if args.cmd == "assign":
        ledger = add_task(
            ledger,
            titan_name=args.titan,
            mode=args.mode,
            scope=args.scope,
            question=args.question,
            diff_excerpt_required=args.diff_excerpt_required,
            residual_question_required=args.residual_question_required,
            source_refs=args.source_ref,
        )
        write_json(path, ledger)
        return 0

    if args.cmd == "report":
        ledger = add_report(ledger, read_json(Path(args.report)))
        write_json(path, ledger)
        return 0

    if args.cmd == "finding-status":
        ledger = set_finding_status(ledger, finding_id=args.finding_id, status=args.status, reason=args.reason)
        write_json(path, ledger)
        return 0

    if args.cmd == "grade":
        ledger = add_grade(
            ledger,
            titan_name=args.titan,
            grade=args.grade,
            reason=args.reason,
            titan_fault=args.titan_fault,
            orchestration_fault=args.orchestration_fault,
            prompt_fault=args.prompt_fault,
            tooling_fault=args.tooling_fault,
            timeout_fault=args.timeout_fault,
            next_prompt_rule=args.next_prompt_rule,
        )
        write_json(path, ledger)
        return 0

    if args.cmd == "timeout":
        ledger = add_timeout(
            ledger,
            titan_name=args.titan,
            task_id=args.task_id,
            wait_count=args.wait_count,
            timeout_count=args.timeout_count,
            turn_aborted=args.turn_aborted,
            interrupt_used=args.interrupt_used,
            final_verdict_returned=args.final_verdict_returned,
            scope_width=args.scope_width,
            diff_excerpt_present=args.diff_excerpt_present,
            residual_question_present=args.residual_question_present,
        )
        write_json(path, ledger)
        return 0

    if args.cmd == "closeout":
        audit = closeout(ledger)
        write_json(path, ledger)
        if args.out:
            write_json(Path(args.out), audit)
        else:
            print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "validate":
        errors = validate_ledger(ledger)
        if errors:
            print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
            return 2
        print(json.dumps({"status": "pass"}, ensure_ascii=False))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(cli())
