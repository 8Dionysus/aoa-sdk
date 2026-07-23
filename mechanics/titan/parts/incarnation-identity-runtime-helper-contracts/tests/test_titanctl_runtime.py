import json
import subprocess
import sys
from pathlib import Path


def run_titanctl(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_titanctl_summon_validate_gate_closeout(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "titanctl.py"
    receipt = tmp_path / "receipt.json"

    result = run_titanctl(script, "summon", "--workspace", "/srv/AbyssOS", "--operator", "test", "--out", str(receipt))
    assert result.returncode == 0, result.stderr

    result = run_titanctl(script, "validate", "--receipt", str(receipt))
    assert result.returncode == 0, result.stderr

    result = run_titanctl(
        script,
        "gate",
        "--receipt", str(receipt),
        "--agent", "Forge",
        "--kind", "mutation",
        "--intent", "bounded implementation test",
        "--decision-ref", "manual-trial://operator-decision/forge",
        "--approved-by", "manual-trial-operator",
        "--mutation-surface", "test fixture",
        "--scope", "bounded implementation test",
        "--expected-file", "example.py",
        "--rollback-note", "revert the test fixture",
        "--test-plan", "run focused test",
    )
    assert result.returncode == 0, result.stderr

    result = run_titanctl(
        script,
        "gate",
        "--receipt", str(receipt),
        "--agent", "Delta",
        "--kind", "judgment",
        "--intent", "bounded comparison test",
        "--decision-ref", "manual-trial://operator-decision/delta",
        "--approved-by", "manual-trial-operator",
        "--claim", "the bounded comparison meets its criteria",
        "--criterion", "focused evidence is present",
        "--evidence-ref", "test:bounded-comparison",
        "--verdict-scope", "test fixture only",
    )
    assert result.returncode == 0, result.stderr

    result = run_titanctl(script, "closeout", "--receipt", str(receipt), "--summary", "closed by test")
    assert result.returncode == 0, result.stderr

    data = json.loads(receipt.read_text())
    assert data["schema_version"] == "titan_session_receipt/v2"
    assert data["status"] == "closed"
    assert {i["titan_name"] for i in data["incarnations"]} == {
        "Atlas",
        "Sentinel",
        "Mneme",
        "Forge",
        "Delta",
    }
    assert data["cohort"]["Atlas"]["bearer_id"] == "titan:atlas:founder"
    assert data["cohort"]["Forge"]["state"] == "active"
    assert data["cohort"]["Delta"]["state"] == "active"
    assert data["gate_events"][0]["payload"]["mutation_surface"]
    assert data["gate_events"][1]["payload"]["evidence_refs"]
    assert [event["decision_ref"] for event in data["gate_events"]] == [
        "manual-trial://operator-decision/forge",
        "manual-trial://operator-decision/delta",
    ]
    assert all(
        event["approved_by_authenticated"] is False
        and event["authority"] == "witness_only"
        for event in data["gate_events"]
    )


def test_titanctl_witness_init_has_no_runtime_or_summon_claim(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "titanctl.py"
    receipt = tmp_path / "receipt-witness.json"

    result = run_titanctl(
        script,
        "witness-init",
        "--workspace",
        str(tmp_path),
        "--recorder",
        "unattributed-local-recorder",
        "--event-id",
        "inspect-only-intent",
        "--intent",
        "inspect-only",
        "--lane",
        "inspection",
        "--source-ref",
        "test:user-request",
        "--out",
        str(receipt),
    )
    assert result.returncode == 0, result.stderr

    result = run_titanctl(script, "validate", "--receipt", str(receipt))
    assert result.returncode == 0, result.stderr

    data = json.loads(receipt.read_text())
    assert data["surface_role"] == "titan_receipt_witness"
    assert data["authority"] == "witness_only"
    assert data["runtime_execution_state"] == "not_run"
    assert data["transport_state"] == "not_sent"
    assert data["state_semantics"] == "helper_projection_only"
    assert data["operator_field_authenticated"] is False
    assert data["source_refs"] == ["test:user-request"]
    assert [event["type"] for event in data["events"]] == ["witness-init"]
    assert not any(event["type"] == "summon" for event in data["events"])
    by_name = {item["titan_name"]: item for item in data["incarnations"]}
    assert by_name["Atlas"]["state"] == "declared"
    assert by_name["Sentinel"]["state"] == "declared"
    assert by_name["Mneme"]["state"] == "declared"
    assert by_name["Forge"]["state"] == "locked"
    assert by_name["Delta"]["state"] == "locked"
    assert not any(item["state"] == "active" for item in data["incarnations"])

    result = run_titanctl(
        script,
        "gate",
        "--receipt",
        str(receipt),
        "--agent",
        "Forge",
        "--kind",
        "mutation",
        "--intent",
        "bounded witness-only implementation",
        "--decision-ref",
        "manual-trial://operator-decision/receipt-forge-1",
        "--approved-by",
        "manual-trial-operator",
        "--mutation-surface",
        "test fixture",
        "--scope",
        "receipt witness only",
        "--expected-file",
        "example.py",
        "--rollback-note",
        "remove the test fixture",
        "--test-plan",
        "run focused witness test",
    )
    assert result.returncode == 0, result.stderr

    result = run_titanctl(script, "validate", "--receipt", str(receipt))
    assert result.returncode == 0, result.stderr

    data = json.loads(receipt.read_text())
    by_name = {item["titan_name"]: item for item in data["incarnations"]}
    assert by_name["Forge"]["state"] == "locked"
    assert data["cohort"]["Forge"]["state"] == "locked"
    assert data["runtime_execution_state"] == "not_run"
    assert data["transport_state"] == "not_sent"
    assert not any(event["type"] == "summon" for event in data["events"])
    assert len(data["gate_events"]) == 1
    gate = data["gate_events"][0]
    assert gate["decision_ref"] == (
        "manual-trial://operator-decision/receipt-forge-1"
    )
    assert gate["approved_by"] == "manual-trial-operator"
    assert gate["approved_by_authenticated"] is False
    assert gate["authority"] == "witness_only"


def test_titanctl_standalone_roster_does_not_import_package_root():
    script = Path(__file__).resolve().parents[1] / "scripts" / "titanctl.py"

    result = subprocess.run(
        [sys.executable, "-S", str(script), "roster", "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["schema_version"] == "titan_roster/v2"
