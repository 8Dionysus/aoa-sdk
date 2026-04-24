from __future__ import annotations

from aoa_sdk.titans.swarm_ledger import (
    add_grade,
    add_report,
    add_task,
    closeout,
    new_ledger,
    set_finding_status,
    validate_ledger,
)


def test_swarm_ledger_records_task_report_and_closeout() -> None:
    ledger = new_ledger(session_id="session:test", operator="Dionysus", source_ref="test")
    add_task(
        ledger,
        titan_name="Sentinel",
        mode="compact_review",
        scope=["diff excerpt"],
        question="Does this overclaim?",
        diff_excerpt_required=True,
        source_refs=["diff:1"],
    )
    task_id = ledger["tasks"][0]["task_id"]
    report = {
        "schema_version": "titan_agent_report/v1",
        "task_id": task_id,
        "titan_name": "Sentinel",
        "source_refs": ["diff:1"],
        "findings": [
            {
                "severity": "P2",
                "claim": "Closeout wording is bounded.",
                "evidence_refs": ["diff:1"],
                "recommended_action": "Keep wording.",
            }
        ],
    }
    add_report(ledger, report)
    finding_id = ledger["findings"][0]["finding_id"]
    set_finding_status(ledger, finding_id=finding_id, status="validated", reason="Local diff review confirmed.")
    add_grade(
        ledger,
        titan_name="Sentinel",
        grade="B+",
        reason="Useful narrow review.",
        orchestration_fault=False,
    )
    audit = closeout(ledger)
    assert validate_ledger(ledger) == []
    assert audit["counts"]["memory_candidates"] == 1


def test_sentinel_compact_task_requires_diff_excerpt_flag() -> None:
    ledger = new_ledger(session_id="session:test", operator="Dionysus")
    try:
        add_task(
            ledger,
            titan_name="Sentinel",
            mode="compact_review",
            scope=["files only"],
            question="Review broadly?",
        )
    except ValueError as exc:
        assert "diff_excerpt_required" in str(exc)
    else:
        raise AssertionError("Sentinel compact review without diff excerpts should fail")


def test_delta_judgment_requires_residual_question_flag() -> None:
    ledger = new_ledger(session_id="session:test", operator="Dionysus")
    try:
        add_task(
            ledger,
            titan_name="Delta",
            mode="bounded_judgment",
            scope=["evidence"],
            question="Pass?",
        )
    except ValueError as exc:
        assert "residual_question_required" in str(exc)
    else:
        raise AssertionError("Delta bounded judgment without residual question should fail")


def test_report_requires_source_refs() -> None:
    ledger = new_ledger(session_id="session:test", operator="Dionysus")
    add_task(
        ledger,
        titan_name="Mneme",
        mode="provenance_check",
        scope=["receipt"],
        question="What should be remembered?",
    )
    task_id = ledger["tasks"][0]["task_id"]
    try:
        add_report(ledger, {"task_id": task_id, "titan_name": "Mneme", "findings": []})
    except ValueError as exc:
        assert "source_refs" in str(exc)
    else:
        raise AssertionError("source-less report should fail")
