import json
import subprocess
import sys
from pathlib import Path

from aoa_sdk.titans.appserver_bridge import (
    AppServerJsonRpcBuilder,
    BRIDGE_TITAN_ROSTER,
    TitanAppServerBridgeSession,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "titan_appserver_bridge.py"


def test_builder_and_session():
    b = AppServerJsonRpcBuilder()
    assert b.initialize()["method"] == "initialize"
    assert (
        b.thread_start(cwd="/srv/AbyssOS")["params"]["sandboxPolicy"]["networkAccess"] is False
    )
    s = TitanAppServerBridgeSession.new(
        "/srv/AbyssOS",
        source_kind="bridge-session",
        source_ref="test:user-request",
    )
    assert s.source_kind == "bridge-session"
    assert s.source_ref == "test:user-request"
    assert s.surface_role == "titan_appserver_bridge_witness"
    assert s.authority == "witness_only"
    assert s.runtime_execution_state == "not_run"
    assert s.transport_state == "not_sent"
    assert s.state_semantics == "helper_projection_only"
    assert {t["state"] for t in s.titans} == {"declared", "locked"}
    assert not any(t["state"] == "active" for t in s.titans)
    incomplete = s.to_dict()
    incomplete.pop("transport_state")
    incomplete_session = TitanAppServerBridgeSession.from_dict(incomplete)
    assert "transport_state must equal 'not_sent'" in incomplete_session.validate()
    s.ingest({"jsonrpc": "2.0", "id": 1, "result": {"threadId": "t1"}})
    s.ingest({"method": "turn/started", "params": {"threadId": "t1", "turnId": "u1"}})
    s.ingest(
        {
            "method": "item/approval/requested",
            "params": {"requestId": "r1", "type": "command", "summary": "run"},
        }
    )
    assert s.metrics()["approvals_pending"] == 1
    s.decide_approval(
        "r1",
        "decline",
        "no",
        decision_ref="manual-trial://operator-decision/r1",
        decided_by="manual-trial-operator",
    )
    assert s.metrics()["approvals_pending"] == 0
    approval = s.approvals[0]
    assert approval["decision_ref"] == "manual-trial://operator-decision/r1"
    assert approval["decided_by"] == "manual-trial-operator"
    assert approval["decided_by_authenticated"] is False
    assert approval["authority"] == "witness_only"
    try:
        s.decide_approval(
            "r1",
            "accept",
            "overwrite",
            decision_ref="manual-trial://operator-decision/r1-overwrite",
            decided_by="manual-trial-operator",
        )
    except ValueError as e:
        assert "already decided" in str(e)
    else:
        raise AssertionError("existing approval decision was overwritten")
    try:
        s.unlock(
            "Forge",
            "judgment",
            "wrong",
            decision_ref="manual-trial://operator-decision/wrong-gate",
            approved_by="manual-trial-operator",
        )
    except ValueError as e:
        assert "requires gate 'mutation'" in str(e)
    else:
        raise AssertionError("wrong gate accepted")
    s.unlock(
        "Forge",
        "mutation",
        "ok",
        decision_ref="manual-trial://operator-decision/forge-gate",
        approved_by="manual-trial-operator",
    )
    s.unlock(
        "Delta",
        "judgment",
        "ok",
        decision_ref="manual-trial://operator-decision/delta-gate",
        approved_by="manual-trial-operator",
    )
    assert not s.validate()
    assert [gate["decision_ref"] for gate in s.gates] == [
        "manual-trial://operator-decision/forge-gate",
        "manual-trial://operator-decision/delta-gate",
    ]
    assert all(
        gate["approved_by_authenticated"] is False
        and gate["authority"] == "witness_only"
        for gate in s.gates
    )


def test_from_dict_copies_default_titan_roster() -> None:
    first = TitanAppServerBridgeSession.from_dict(
        {
            "session_id": "s1",
            "workspace_root": "/srv/AbyssOS",
            "source_kind": "bridge-session",
            "source_ref": "test:first",
        }
    )
    first.unlock(
        "Forge",
        "mutation",
        "ok",
        decision_ref="manual-trial://operator-decision/copy-check",
        approved_by="manual-trial-operator",
    )

    second = TitanAppServerBridgeSession.from_dict(
        {
            "session_id": "s2",
            "workspace_root": "/srv/AbyssOS",
            "source_kind": "bridge-session",
            "source_ref": "test:second",
        }
    )

    assert next(titan for titan in BRIDGE_TITAN_ROSTER if titan["name"] == "Forge")["state"] == "locked"
    assert next(titan for titan in second.titans if titan["name"] == "Forge")["state"] == "locked"


def test_cli_binds_owner_source_when_run_outside_repo(tmp_path: Path) -> None:
    session = tmp_path / "bridge.json"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "init",
            "--workspace",
            str(tmp_path),
            "--source-kind",
            "bridge-session",
            "--source-ref",
            "test:user-request",
            "--out",
            str(session),
        ],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "gate",
            "--session",
            str(session),
            "--titan",
            "Delta",
            "--gate",
            "judgment",
            "--reason",
            "manual bridge-ledger judgment witness only; no runtime action",
            "--decision-ref",
            "manual-trial://operator-decision/bridge-delta-1",
            "--approved-by",
            "manual-trial-operator",
        ],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "validate",
            "--session",
            str(session),
        ],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
    )

    data = json.loads(session.read_text(encoding="utf-8"))
    assert data["source_kind"] == "bridge-session"
    assert data["source_ref"] == "test:user-request"
    assert data["surface_role"] == "titan_appserver_bridge_witness"
    assert data["runtime_execution_state"] == "not_run"
    assert data["transport_state"] == "not_sent"
    assert data["state_semantics"] == "helper_projection_only"
    assert len(data["gates"]) == 1
    gate = data["gates"][0]
    assert gate["decision_ref"] == (
        "manual-trial://operator-decision/bridge-delta-1"
    )
    assert gate["approved_by"] == "manual-trial-operator"
    assert gate["approved_by_authenticated"] is False
    assert gate["authority"] == "witness_only"
    delta = next(titan for titan in data["titans"] if titan["name"] == "Delta")
    assert delta["state"] == "active"


def test_validate_reports_missing_titans_without_crashing() -> None:
    session = TitanAppServerBridgeSession.from_dict(
        {
            "session_id": "s1",
            "workspace_root": "/srv/AbyssOS",
            "source_kind": "bridge-session",
            "source_ref": "test:user-request",
            "titans": [{"name": "Atlas", "role": "architect", "state": "active"}],
        }
    )

    errors = session.validate()

    assert "missing titan Forge" in errors
    assert "missing titan Delta" in errors
