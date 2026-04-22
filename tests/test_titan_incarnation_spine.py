from __future__ import annotations

from aoa_sdk.titans.incarnation_spine import gate_titan, new_receipt, validate_gate_payload, validate_memory_record, validate_receipt


def test_receipt_carries_all_founder_incarnations():
    receipt = new_receipt(workspace="/srv", operator="Dionysus", source_ref="test")
    assert validate_receipt(receipt) == []
    by_name = {i["titan_name"]: i for i in receipt["incarnations"]}
    assert by_name["Atlas"]["bearer_id"] == "titan:atlas:founder"
    assert by_name["Forge"]["state"] == "locked"
    assert by_name["Delta"]["gate_required"] == "judgment"


def test_forge_gate_requires_payload_contract():
    errors = validate_gate_payload("Forge", "mutation", {"scope": ["x"]})
    assert "Forge gate requires non-empty expected_files" in errors
    payload = {"mutation_surface": "repo", "scope": ["bounded change"], "expected_files": ["a.py"], "rollback_note": "revert commit", "approval_ref": "approval:1", "test_plan": ["pytest"]}
    receipt = gate_titan(new_receipt(workspace="/srv", operator="D"), titan_name="Forge", gate_kind="mutation", payload=payload)
    assert receipt["gate_events"][0]["titan_name"] == "Forge"


def test_delta_gate_requires_evidence_refs():
    errors = validate_gate_payload("Delta", "judgment", {"claim": "x"})
    assert "Delta gate requires non-empty evidence_refs" in errors


def test_memory_record_requires_provenance():
    record = {"record_id": "mem:1", "bearer_id": "titan:mneme:founder", "titan_name": "Mneme", "role_key": "memory-keeper", "memory_kind": "lesson_candidate", "claim": "x", "authority": "candidate"}
    assert "memory record requires source_refs, receipt_id or session_id" in validate_memory_record(record)
    record["source_refs"] = ["receipt:1"]
    assert validate_memory_record(record) == []
