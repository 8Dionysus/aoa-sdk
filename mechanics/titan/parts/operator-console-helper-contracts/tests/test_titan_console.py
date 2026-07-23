from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "titan_console.py"


def run(*args, check=True):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def test_new_validate_and_gates(tmp_path):
    state = tmp_path / "state.json"
    run(
        "new", "--workspace", str(tmp_path), "--operator", "tester", "--out", str(state)
    )
    run("validate", "--state", str(state))
    initial = json.loads(state.read_text())
    assert initial["surface_role"] == "titan_console_witness"
    assert initial["authority"] == "witness_only"
    assert initial["runtime_execution_state"] == "not_run"
    assert initial["transport_state"] == "not_sent"
    assert initial["state_semantics"] == "helper_projection_only"
    assert initial["operator_field_authenticated"] is False
    assert initial["digest"]["active"] == []
    assert initial["digest"]["declared"] == ["Atlas", "Sentinel", "Mneme"]
    assert initial["titans"]["Atlas"]["state"] == "declared"
    assert initial["titans"]["Forge"]["state"] == "locked"
    missing_explicit_witness = tmp_path / "missing-explicit-witness.json"
    incomplete = dict(initial)
    incomplete.pop("authority")
    missing_explicit_witness.write_text(json.dumps(incomplete), encoding="utf-8")
    rejected = run(
        "validate",
        "--state",
        str(missing_explicit_witness),
        check=False,
    )
    assert rejected.returncode != 0
    assert "missing key: authority" in rejected.stderr
    bad = run(
        "gate",
        "--state",
        str(state),
        "--titan",
        "Forge",
        "--gate",
        "judgment",
        "--reason",
        "wrong",
        "--decision-ref",
        "manual-trial://wrong-gate",
        "--approved-by",
        "manual-trial-operator",
        check=False,
    )
    assert bad.returncode != 0
    run(
        "gate",
        "--state",
        str(state),
        "--titan",
        "Forge",
        "--gate",
        "mutation",
        "--reason",
        "bounded patch",
        "--decision-ref",
        "manual-trial://forge-mutation",
        "--approved-by",
        "manual-trial-operator",
    )
    run(
        "gate",
        "--state",
        str(state),
        "--titan",
        "Delta",
        "--gate",
        "judgment",
        "--reason",
        "regression verdict",
        "--decision-ref",
        "manual-trial://delta-judgment",
        "--approved-by",
        "manual-trial-operator",
    )
    run("validate", "--state", str(state))
    data = json.loads(state.read_text())
    assert (
        data["titans"]["Forge"]["active"] is True
        and data["titans"]["Delta"]["active"] is True
    )
    assert (
        data["titans"]["Forge"]["state"] == "active"
        and data["titans"]["Delta"]["state"] == "active"
    )
    assert [approval["decision_ref"] for approval in data["approvals"]] == [
        "manual-trial://forge-mutation",
        "manual-trial://delta-judgment",
    ]
    assert all(
        approval["approved_by_authenticated"] is False
        and approval["authority"] == "witness_only"
        for approval in data["approvals"]
    )


def test_gate_rejects_closed_state(tmp_path):
    state = tmp_path / "state.json"
    run(
        "new", "--workspace", str(tmp_path), "--operator", "tester", "--out", str(state)
    )
    run("close", "--state", str(state), "--reason", "done")

    result = run(
        "gate",
        "--state",
        str(state),
        "--titan",
        "Forge",
        "--gate",
        "mutation",
        "--reason",
        "late mutation",
        "--decision-ref",
        "manual-trial://late-mutation",
        "--approved-by",
        "manual-trial-operator",
        check=False,
    )

    assert result.returncode != 0
    assert "state is closed" in result.stderr


def test_appserver_plan(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Summon Atlas, Sentinel, and Mneme.", encoding="utf-8")
    out = tmp_path / "plan.jsonl"
    run(
        "appserver-plan",
        "--workspace",
        str(tmp_path),
        "--prompt-file",
        str(prompt),
        "--out",
        str(out),
    )
    lines = [json.loads(x) for x in out.read_text().splitlines()]
    assert [x["method"] for x in lines] == [
        "initialize",
        "initialized",
        "thread/start",
        "turn/start",
    ]
    assert "model" not in lines[2]["params"]
    assert lines[3]["params"]["input"][0]["text"] == "Summon Atlas, Sentinel, and Mneme."
