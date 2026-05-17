from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from aoa_sdk.titans.swarm_ledger import add_grade, add_timeout, new_ledger, validate_ledger


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_grade_records_orchestration_fault_separately_from_titan_fault() -> None:
    ledger = new_ledger(session_id="session:test", operator="Dionysus")
    add_grade(
        ledger,
        titan_name="Delta",
        grade="B+",
        reason="Good verdict after prompt compression.",
        titan_fault=False,
        orchestration_fault=True,
        prompt_fault=True,
        timeout_fault=True,
        next_prompt_rule="Give Delta one bounded claim and one residual risk question.",
    )
    assert validate_ledger(ledger) == []
    record = ledger["grades"][0]
    assert record["orchestration_fault"] is True
    assert record["titan_fault"] is False


def test_timeout_record_tracks_prompt_compression_features() -> None:
    ledger = new_ledger(session_id="session:test", operator="Dionysus")
    add_timeout(
        ledger,
        titan_name="Sentinel",
        task_id="task:1",
        wait_count=2,
        timeout_count=1,
        turn_aborted=True,
        interrupt_used=True,
        final_verdict_returned=False,
        scope_width="broad",
        diff_excerpt_present=False,
        residual_question_present=False,
    )
    assert validate_ledger(ledger) == []
    timeout = ledger["timeouts"][0]
    assert timeout["scope_width"] == "broad"
    assert timeout["diff_excerpt_present"] is False


def test_titan_closeout_audit_schema_accepts_emitted_created_at() -> None:
    schema = json.loads((REPO_ROOT / "schemas/titan_closeout_audit.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(
        {
            "schema_version": "titan_closeout_audit/v1",
            "closeout_id": "closeout:test",
            "ledger_id": "ledger:test",
            "session_id": "session:test",
            "created_at": "2026-05-17T16:00:00Z",
            "counts": {},
            "memory_candidates": [],
            "summary": "closed",
        }
    )
